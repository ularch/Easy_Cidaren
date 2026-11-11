from types import SimpleNamespace
import unittest
from unittest.mock import patch

from util import select_mean


class ContextDiagnosticTests(unittest.TestCase):
    def test_context_score_does_not_override_meaning_match(self):
        info = SimpleNamespace(word_list=[], word_means=['正确释义'],
                               exam={'stem': {'remark': '干扰释义'},
                                     'options': [{'content': '干扰释义'}, {'content': '正确释义'}]})
        with patch.object(select_mean.select_module, 'logger') as logger:
            self.assertEqual(select_mean.select_mean(info), 1)
            self.assertTrue(any(str(call.args[0]).startswith('上下文评分(影子)')
                                for call in logger.info.call_args_list))

    def test_word_diagnostics_preserve_source_option_index(self):
        info = SimpleNamespace(word_list=['target'],
                               exam={'stem': {'remark': 'other meaning'},
                                     'options': [{'content': 'other'}, {'content': 'target'}]})

        def query(public_info, word):
            public_info.word_means = ['correct meaning' if word == 'target' else 'other meaning']

        with patch.object(select_mean, 'query_word', side_effect=query), \
                patch.object(select_mean, 'handle_query_word_mean'), \
                patch.object(select_mean.select_module, 'logger') as logger:
            self.assertEqual(select_mean.select_match_word(info, 'correct meaning'), 1)
            self.assertTrue(any(str(call.args[0]).startswith('上下文评分(影子)')
                                for call in logger.info.call_args_list))

    def test_missing_remark_keeps_answer_without_context_scores(self):
        info = SimpleNamespace(word_list=[], word_means=['正确释义'],
                               exam={'stem': {}, 'options': [{'content': '错误'}, {'content': '正确释义'}]})
        with patch.object(select_mean.select_module, 'logger') as logger:
            self.assertEqual(select_mean.select_mean(info), 1)
            self.assertFalse(any(str(call.args[0]).startswith('上下文评分(影子)')
                                 for call in logger.info.call_args_list))
