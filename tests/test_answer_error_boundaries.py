import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from answer_questions import answer_questions as answers
from api import main_api
import main


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
                      main_api.SecurityVerifyError('verify'), main_api.ApiResponseError('rejected'), main_api.TaskNotEffectiveError('not ready')]:
            with self.subTest(error=type(error).__name__), \
                    patch.object(main, 'answer', side_effect=error):
                with self.assertRaises(type(error)):
                    self.worker._answer_question(SimpleNamespace(compat_mode=True), 17)

    def test_server_rejection_is_distinct_from_missing_word(self):
        for payload, exception in [
            ({'code': 11003}, main_api.SecurityVerifyError),
            ({'code': 20005, 'msg': 'not ready'}, main_api.TaskNotEffectiveError),
            ({'code': 120, 'msg': 'card error'}, main_api.WordCardDataError),
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
