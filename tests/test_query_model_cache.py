from contextlib import ExitStack
from pathlib import Path
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

    def test_cache_limit_preserves_existing_hits(self):
        with patch.object(main_api, '_WORD_CACHE_LIMIT', 2):
            for word in ['one', 'two', 'three', 'one']:
                main_api.query_word(self.info, word)
            self.assertEqual(self.get.call_count, 3)
            self.assertEqual(len(self.cache), 2)

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
        with patch.object(word_revert, '_nlp', None), \
                patch.object(word_revert.spacy, 'load', return_value=model) as load:
            self.assertEqual(word_revert.word_revert('running'), 'run')
            self.assertEqual(word_revert.word_revert('runs'), 'run')
            load.assert_called_once()

    def test_model_load_failure_can_retry_later(self):
        model = Mock(return_value=[SimpleNamespace(lemma_='run')])
        with patch.object(word_revert, '_nlp', None), \
                patch.object(word_revert.spacy, 'load', side_effect=[RuntimeError('load failed'), model]) as load, \
                patch.object(word_revert, 'use_api_get_prototype', return_value='run') as fallback:
            self.assertEqual(word_revert.word_revert('running'), 'run')
            self.assertEqual(word_revert.word_revert('runs'), 'run')
            self.assertEqual(load.call_count, 2)
            fallback.assert_called_once_with('running')


if __name__ == '__main__':
    unittest.main()
