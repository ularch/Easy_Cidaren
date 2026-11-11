import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from answer_questions import answer_questions as answers
from api import main_api
import main


class CaseTests(unittest.TestCase):
    def test_word_case_match_avoids_lemmatization(self):
        info = SimpleNamespace(exam={'stem': {'content': '{Insert}'}}, word_list=[])
        info.word_list = ['insert']
        with patch.object(answers, 'query_word') as query, \
                patch.object(answers, 'handle_query_word_mean'), \
                patch.object(answers, 'select_mean', return_value=1), \
                patch.object(answers, 'word_revert') as revert:
            self.assertEqual(answers.word_form_mean(info), 1)
            query.assert_called_once_with(info, 'insert')
            revert.assert_not_called()


    def test_self_built_resolves_case_before_choosing_unit(self):
        info = SimpleNamespace(is_self_built=True, word_list=['insert'],
                               get_book_words_data=[{'list_id': 'unit'}], now_unit='old')
        query = Mock(return_value='result')
        self.assertEqual(main_api.check_is_self_built(query)(info, 'INSERT'), 'result')
        query.assert_called_once_with(info, 'insert')
        self.assertEqual(info.now_unit, 'unit')

    def test_missing_word_or_unit_index_is_a_lookup_error(self):
        for word, rows in [('missing', [{'list_id': 'unit'}]), ('Insert', [])]:
            with self.subTest(word=word, rows=rows):
                info = SimpleNamespace(is_self_built=True, word_list=['insert'],
                                       get_book_words_data=rows, now_unit='old')
                query = Mock()
                with self.assertRaises(LookupError):
                    main_api.check_is_self_built(query)(info, word)
                query.assert_not_called()


class ErrorHandlingTests(unittest.TestCase):
    def setUp(self):
        self.logger = patch.object(main, 'main', SimpleNamespace(logger=Mock()), create=True)
        self.logger.start()
        self.addCleanup(self.logger.stop)
        self.worker = main.TaskWorker([])


    def test_parse_failure_skips_current_question(self):
        with patch.object(main, 'answer', side_effect=LookupError('missing')):
            self.assertIsNone(self.worker._answer_question(SimpleNamespace(), 17))

    def test_successful_answer_is_returned_unchanged(self):
        with patch.object(main, 'answer', return_value=0):
            self.assertEqual(self.worker._answer_question(SimpleNamespace(), 17), 0)

    def test_network_and_service_failures_propagate(self):
        for error in [main.requests.exceptions.ConnectionError('offline'),
                      main_api.SecurityVerifyError('verify'), main_api.ApiResponseError('rejected')]:
            with self.subTest(error=type(error).__name__), \
                    patch.object(main, 'answer', side_effect=error):
                with self.assertRaises(type(error)):
                    self.worker._answer_question(SimpleNamespace(compat_mode=True), 17)

    def test_server_rejection_is_distinct_from_missing_word(self):
        for payload, exception in [
            ({'code': 11003}, main_api.SecurityVerifyError),
            ({'code': 0, 'msg': '加载单词卡片失败，请重新加载'}, LookupError),
            ({'code': 11001, 'msg': 'expired'}, main_api.ApiResponseError),
        ]:
            with self.subTest(payload=payload), self.assertRaises(exception):
                main_api.handle_response(Mock(json=lambda: payload, text='synthetic response'))

    def test_unknown_encoding_exhaustion_is_a_service_error(self):
        response = Mock(json=lambda: {'jv': 'unknown-encoding'})
        for retry in [main_api.check_jv_and_retry_get, main_api.check_jv_and_retry_post]:
            with self.subTest(retry=retry.__name__), patch.object(main_api.time, 'sleep'):
                request = Mock(return_value=response)
                with self.assertRaises(main_api.ApiResponseError):
                    retry(request, 'https://example.invalid')
                self.assertEqual(request.call_count, 5)


if __name__ == '__main__':
    unittest.main()
