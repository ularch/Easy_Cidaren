from contextlib import chdir
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from answer_questions import answer_questions as answers
from api import main_api
from publicInfo.publicInfo import PublicInfo
from util import wrong_memory


def question(mode, content, options=(), remark='释义', **extra):
    return SimpleNamespace(
        exam={'topic_mode': mode, 'stem': {'content': content, 'remark': remark},
              'options': [o if isinstance(o, dict) else {'content': o} for o in options], **extra},
        word_list=[], word_dict={},
    )


class PhraseTests(unittest.TestCase):
    def test_rejects_excess_candidates(self):
        info = question(32, '_ _', ['one', 'two', 'three'])
        self.assertIsNone(answers._build_phrase_answer(info, 'one two three'))

    def test_rejects_incomplete_candidates(self):
        info = question(32, '_ _', ['one', 'two'])
        self.assertIsNone(answers._build_phrase_answer(info, 'one missing'))

    def test_normalized_options_and_slash_alternative(self):
        info = question(32, '_ _', ['ＧＯ\u00a0', 'Home', 'at'])
        self.assertEqual(answers._build_phrase_answer(info, 'go in/at'), 'ＧＯ,at')

    def test_hyphen_slots(self):
        for template, options, expected in [
            ('_-_ development', ['low', 'carbon'], 'low,carbon'),
            ('_ development', ['low-carbon'], 'low-carbon'),
        ]:
            with self.subTest(template=template):
                self.assertEqual(answers._build_phrase_answer(
                    question(32, template, options), 'low-carbon development'), expected)

    def test_multiword_option_is_one_slot(self):
        info = question(32, '_', ['a very long multiword option'])
        self.assertEqual(answers._build_phrase_answer(info, 'a very long multiword option'),
                         'a very long multiword option')

    def test_tries_later_phrase_after_invalid_candidate(self):
        info = question(32, '_ _', ['one', 'two', 'three'])
        self.assertEqual(answers._best_phrase_answer(info, ['one two three', 'one two']), 'one,two')
