import json
import os
from contextlib import closing
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from api import main_api
from util import word_cache


class PersistentWordCacheTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'config/word_cache.sqlite3'
        location = patch.object(word_cache, '_cache_path', return_value=self.path)
        location.start()
        self.addCleanup(location.stop)
        self.key = ('course', 'unit', 'word')
        self.result = {'means': [{'mean': ['verb', '测试释义']}], 'word': 'word'}

    def test_new_process_can_answer_from_persisted_query(self):
        self.assertTrue(word_cache.save(self.key, self.result))
        script = '''import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch
from api import main_api
from util import word_cache
info = SimpleNamespace(is_self_built=False, course_id='course', now_unit='unit')
with patch.object(word_cache, '_cache_path', return_value=Path(sys.argv[1])), \\
        patch.object(main_api, 'check_jv_and_retry_get', side_effect=AssertionError('unexpected request')):
    main_api.query_word(info, 'WORD')
assert info.word_query_result == json.loads(sys.argv[2])
'''
        completed = subprocess.run([sys.executable, '-c', script, str(self.path), json.dumps(self.result)],
                                   capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_persisted_data_keeps_course_and_unit_isolation(self):
        word_cache.save(self.key, self.result)
        self.assertEqual(word_cache.lookup(self.key), self.result)
        self.assertIsNone(word_cache.lookup(('course', 'other_unit', 'word')))
        self.assertIsNone(word_cache.lookup(('other_course', 'unit', 'word')))

    def test_full_database_evicts_oldest_and_accepts_new_entry(self):
        word_cache.save(self.key, self.result, limit=1)
        word_cache.save(('course', 'unit', 'another'), {'means': []}, limit=1)
        self.assertEqual(word_cache.lookup(('course', 'unit', 'another')), {'means': []})
        self.assertIsNone(word_cache.lookup(self.key))
        replacement = {'means': [{'mean': ['noun', '更新释义']}]}
        word_cache.save(self.key, replacement, limit=1)
        self.assertEqual(word_cache.lookup(self.key), replacement)

    def test_legacy_schema_uses_existing_row_order_without_migration(self):
        self.path.parent.mkdir(parents=True)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute('CREATE TABLE word_cache (course TEXT NOT NULL, unit TEXT NOT NULL, '
                               'word TEXT NOT NULL, response TEXT NOT NULL, PRIMARY KEY (course, unit, word))')
            for word in ['one', 'two']:
                connection.execute('INSERT INTO word_cache VALUES (?, ?, ?, ?)',
                                   ('course', 'unit', word, json.dumps(self.result)))
            columns = connection.execute('PRAGMA table_info(word_cache)').fetchall()
            original_rowid = connection.execute("SELECT rowid FROM word_cache WHERE word = 'one'").fetchone()
        first = ('course', 'unit', 'one')
        self.assertEqual(word_cache.lookup(first), self.result)
        updated = {'means': ['updated']}
        self.assertTrue(word_cache.save(first, updated, limit=2))
        self.assertEqual(word_cache.lookup(first), updated)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            self.assertEqual(connection.execute("SELECT rowid FROM word_cache WHERE word = 'one'").fetchone(), original_rowid)
        word_cache.save(('course', 'unit', 'three'), self.result, limit=2)
        self.assertIsNone(word_cache.lookup(first))
        self.assertEqual(word_cache.lookup(('course', 'unit', 'two')), self.result)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            self.assertEqual(connection.execute('PRAGMA table_info(word_cache)').fetchall(), columns)

    def test_smaller_limit_trims_multiple_old_entries(self):
        for word in ['one', 'two', 'three']:
            word_cache.save(('course', 'unit', word), self.result, limit=3)
        word_cache.save(('course', 'unit', 'four'), self.result, limit=1)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            self.assertEqual(connection.execute('SELECT word FROM word_cache').fetchall(), [('four',)])

    def test_concurrent_writers_respect_limit(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda i: word_cache.save(('course', 'unit', str(i)), self.result, limit=3), range(12)))
        # Windows 上并发写入可能撞 database is locked 超时, save 按"没缓存上"返回 False(调用方继续正常答题),
        # 因此这里只断言不变量: 至少写进去一条, 且总数不超过 limit
        self.assertTrue(any(results), '并发写入全部失败')
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertLessEqual(connection.execute('SELECT COUNT(*) FROM word_cache').fetchone()[0], 3)

    def test_zero_limit_does_not_create_cache(self):
        self.assertFalse(word_cache.save(self.key, self.result, limit=0))
        self.assertFalse(self.path.exists())

    def test_corrupt_cache_does_not_raise(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text('not a database', encoding='utf-8')
        self.assertIsNone(word_cache.lookup(self.key))
        self.assertFalse(word_cache.save(self.key, self.result))

    def test_invalid_cached_json_is_a_miss(self):
        word_cache.save(self.key, self.result)
        connection = sqlite3.connect(self.path)
        with connection:
            connection.execute("UPDATE word_cache SET response = 'invalid json'")
        connection.close()
        self.assertIsNone(word_cache.lookup(self.key))

    def test_unwritable_cache_does_not_interrupt_query(self):
        self.path.parent.write_text('blocking directory creation', encoding='utf-8')
        info = SimpleNamespace(is_self_built=False, course_id='course', now_unit='unit')
        response = Mock(json=lambda: {'data': 'encoded', 'jv': 'known'})
        with patch.object(main_api, '_word_info_cache', {}), \
                patch.object(main_api, 'check_jv_and_retry_get', return_value=response), \
                patch.object(main_api, 'handle_response'), \
                patch.object(main_api, 'debase64', return_value=self.result), \
                patch.object(main_api.requests, 'rqs_session', SimpleNamespace(get=Mock())), \
                patch.object(main_api.time, 'sleep'):
            main_api.query_word(info, 'word')
            self.assertEqual(info.word_query_result, self.result)

    def test_same_unit_can_reuse_results_after_account_change(self):
        first = SimpleNamespace(is_self_built=False, course_id='course', now_unit='unit', token='account-a')
        second = SimpleNamespace(is_self_built=False, course_id='course', now_unit='unit', token='account-b')
        response = Mock(json=lambda: {'data': 'encoded', 'jv': 'known'})
        cache = {}
        with patch.object(main_api, '_word_info_cache', cache), \
                patch.object(main_api, 'check_jv_and_retry_get', return_value=response) as request, \
                patch.object(main_api, 'handle_response'), \
                patch.object(main_api, 'debase64', return_value=self.result), \
                patch.object(main_api.requests, 'rqs_session', SimpleNamespace(get=Mock())), \
                patch.object(main_api.time, 'sleep'):
            main_api.query_word(first, 'word')
            cache.clear()
            main_api.query_word(second, 'WORD')
            self.assertEqual(second.word_query_result, self.result)
            self.assertEqual(request.call_count, 1)


class CacheLocationTests(unittest.TestCase):
    def test_cache_location_is_independent_of_working_directory(self):
        expected = Path(word_cache.__file__).resolve().parent.parent / 'config/word_cache.sqlite3'
        with patch.object(Path, 'cwd', return_value=Path('/unrelated')):
            self.assertEqual(word_cache._cache_path(), expected)

    def test_frozen_app_uses_local_app_data(self):
        with patch.object(sys, 'frozen', True, create=True), \
                patch.dict(os.environ, {'LOCALAPPDATA': '/user/local-data'}), \
                patch.object(sys, 'executable', '/Program Files/Easy_Cidaren.exe'):
            self.assertEqual(word_cache._cache_path(), Path('/user/local-data/Easy_Cidaren/config/word_cache.sqlite3'))

    def test_frozen_app_falls_back_to_home(self):
        with patch.object(sys, 'frozen', True, create=True), \
                patch.dict(os.environ, {'LOCALAPPDATA': ''}), \
                patch.object(Path, 'home', return_value=Path('/user/home')):
            self.assertEqual(word_cache._cache_path(), Path('/user/home/.Easy_Cidaren/config/word_cache.sqlite3'))

    def test_source_app_ignores_local_app_data(self):
        with patch.object(sys, 'frozen', False, create=True), \
                patch.dict(os.environ, {'LOCALAPPDATA': '/user/local-data'}):
            self.assertEqual(word_cache._cache_path(), Path(word_cache.__file__).resolve().parent.parent / 'config/word_cache.sqlite3')


if __name__ == '__main__':
    unittest.main()
