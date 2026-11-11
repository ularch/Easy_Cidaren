from contextlib import ExitStack
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from api import main_api
from util import word_cache, word_revert


class QueryCacheTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        directory = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.stack.enter_context(patch.object(word_cache, '_cache_path',
                                             return_value=Path(directory) / 'word_cache.sqlite3'))
        self.cache = {}
        self.stack.enter_context(patch.object(main_api, '_word_info_cache', self.cache))
        self.response = Mock(json=lambda: {'data': 'encoded', 'jv': 'known'})
        self.get = self.stack.enter_context(patch.object(
            main_api, 'check_jv_and_retry_get', return_value=self.response))
        self.stack.enter_context(patch.object(main_api, 'handle_response'))
        self.stack.enter_context(patch.object(main_api, 'debase64', return_value={'means': []}))
        self.stack.enter_context(patch.object(main_api.requests, 'rqs_session', SimpleNamespace(get=Mock())))
        self.stack.enter_context(patch.object(main_api.time, 'sleep'))
        self.info = SimpleNamespace(is_self_built=False, course_id='course', now_unit='unit')

    def test_repeat_query_uses_cache_and_restores_result(self):
        main_api.query_word(self.info, 'Insert')
        self.info.word_query_result = None
        main_api.query_word(self.info, 'INSERT')
        self.assertEqual(self.info.word_query_result, {'means': []})
        self.assertEqual(self.get.call_count, 1)

    def test_cache_is_scoped_by_course_and_unit(self):
        main_api.query_word(self.info, 'word')
        self.info.now_unit = 'other_unit'
        main_api.query_word(self.info, 'word')
        self.info.course_id = 'other_course'
        main_api.query_word(self.info, 'word')
        self.assertEqual(self.get.call_count, 3)
        self.assertEqual(len(self.cache), 3)

    def test_cache_limit_evicts_oldest_and_keeps_new_words(self):
        with patch.object(main_api, '_WORD_CACHE_LIMIT', 2):
            for word in ['one', 'two', 'one', 'three', 'three']:
                main_api.query_word(self.info, word)
            self.assertEqual(self.get.call_count, 3)
            self.assertEqual(len(self.cache), 2)
            self.assertEqual([key[2] for key in self.cache], ['two', 'three'])
            self.assertIsNone(word_cache.lookup(('course', 'unit', 'one')))
            self.cache.clear()
            main_api.query_word(self.info, 'three')
            self.assertEqual(self.get.call_count, 3)
            main_api.query_word(self.info, 'one')
            self.assertEqual(self.get.call_count, 4)

    def test_failed_request_is_not_cached(self):
        error = main_api.requests.exceptions.ConnectionError('offline')
        self.get.side_effect = [error, self.response]
        with self.assertRaises(type(error)):
            main_api.query_word(self.info, 'word')
        self.assertEqual(self.cache, {})
        main_api.query_word(self.info, 'word')
        self.assertEqual(self.get.call_count, 2)
        self.assertEqual(self.info.word_query_result, {'means': []})


class ModelCacheTests(unittest.TestCase):
    def test_model_is_loaded_once_for_multiple_words(self):
        model = Mock(return_value=[SimpleNamespace(lemma_='run')])
        fake_spacy = SimpleNamespace(load=Mock(return_value=model))
        # 用 sys.modules 顶替 spacy: patch('spacy.load') 会真去 import spacy,
        # 而进程里已加载的 requests/brotli DLL 会让 torch 初始化失败(实测 WinError 1114)
        with patch.dict(sys.modules, {'spacy': fake_spacy}), \
                patch.object(word_revert, '_nlp', None), \
                patch.object(word_revert, '_model_broken', False):
            self.assertEqual(word_revert.word_revert('running'), 'run')
            self.assertEqual(word_revert.word_revert('runs'), 'run')
            fake_spacy.load.assert_called_once()

    def test_model_load_failure_uses_upstream_stop_policy(self):
        fake_spacy = SimpleNamespace(load=Mock(side_effect=RuntimeError('load failed')))
        with patch.dict(sys.modules, {'spacy': fake_spacy}), \
                patch.object(word_revert, '_nlp', None), \
                patch.object(word_revert, '_model_broken', False), \
                patch.object(word_revert, 'use_api_get_prototype', return_value='run') as fallback:
            self.assertEqual(word_revert.word_revert('running'), 'run')
            self.assertEqual(word_revert.word_revert('runs'), 'runs')
            fake_spacy.load.assert_called_once()
            fallback.assert_called_once_with('running')


if __name__ == '__main__':
    unittest.main()
