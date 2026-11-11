import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
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

    def test_full_database_keeps_old_entries_and_can_repair_one(self):
        word_cache.save(self.key, self.result, limit=1)
        word_cache.save(('course', 'unit', 'another'), {'means': []}, limit=1)
        self.assertIsNone(word_cache.lookup(('course', 'unit', 'another')))
        self.assertEqual(word_cache.lookup(self.key), self.result)
        replacement = {'means': [{'mean': ['noun', '更新释义']}]}
        word_cache.save(self.key, replacement, limit=1)
        self.assertEqual(word_cache.lookup(self.key), replacement)

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

    def test_frozen_app_stores_cache_beside_executable(self):
        with patch.object(sys, 'frozen', True, create=True), \
                patch.object(sys, 'executable', '/application/Easy_Cidaren.exe'):
            self.assertEqual(word_cache._cache_path(), Path('/application/config/word_cache.sqlite3'))


if __name__ == '__main__':
    unittest.main()
