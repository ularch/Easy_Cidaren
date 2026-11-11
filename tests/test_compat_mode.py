import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from answer_questions import answer_questions as answers
import main
from api.main_api import TaskWordMappingError
from publicInfo.publicInfo import PublicInfo


def question(mode, content, options=(), remark='释义', **extra):
    return SimpleNamespace(
        exam={'topic_mode': mode, 'stem': {'content': content, 'remark': remark},
              'options': [o if isinstance(o, dict) else {'content': o} for o in options], **extra},
        word_list=[], word_dict={},
    )


class CompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.logger = patch.object(main, 'main', SimpleNamespace(logger=Mock()), create=True)
        self.logger.start()
        self.addCleanup(self.logger.stop)
        self.worker = main.TaskWorker([])


    def test_parse_failure_guesses_when_enabled(self):
        with patch.object(main, 'answer', side_effect=TaskWordMappingError('missing')), \
                patch.object(main, 'guess_answer', return_value=0):
            self.assertEqual(self.worker._answer_question(SimpleNamespace(compat_mode=True), 17), 0)

    def test_parse_failure_skips_when_disabled(self):
        with patch.object(main, 'answer', side_effect=ValueError('bad')), \
                patch.object(main, 'guess_answer') as guess:
            self.assertIsNone(self.worker._answer_question(SimpleNamespace(compat_mode=False), 17))
            guess.assert_not_called()

    def test_guess_sentence_and_spelling_formats(self):
        info = question(42, '{}', [{'content': 'word', 'answer_tag': '1#',
                                    'sub_options': [{'content': 'words', 'answer_tag': 2}]}])
        self.assertEqual(answers.guess_answer(info, 42), '1#2')
        info = question(73, '{ze}-{wa}', w_lens=[4, 5])
        info.word_list = ['zero', 'waste']
        self.assertEqual(json.loads(answers.guess_answer(info, 73)), ['zero', 'waste'])
        self.assertIsNone(answers.guess_answer(info, 999))

    def test_unavailable_guess_skips_question(self):
        with patch.object(main, 'answer', side_effect=ValueError('bad')), \
                patch.object(main, 'guess_answer', return_value=None):
            self.assertIsNone(self.worker._answer_question(SimpleNamespace(compat_mode=True), 999))

    def test_guess_failure_does_not_escape(self):
        for exam in [None, {}, {'options': 123}]:
            with self.subTest(exam=exam):
                self.assertIsNone(answers.guess_answer(SimpleNamespace(exam=exam), 17))

    def test_choice_pairing_and_phrase_formats(self):
        info = question(17, 'question', ['one', 'two'])
        self.assertIn(answers.guess_answer(info, 17), [0, 1])
        info = question(31, '', ['one', 'two'])
        info.exam['stem']['remark'] = [{'relation': 'first'}, {'relation': 'second'}]
        result = answers.guess_answer(info, 31)
        self.assertEqual(set(result), {'first', 'second'})
        self.assertEqual(set(result.values()), {0, 1})
        info = question(32, '_ _', ['one', 'two'])
        self.assertEqual(answers.guess_answer(info, 32), 'one,two')

    def test_word_completion_preserves_prefix_and_length(self):
        info = question(51, '', w_tip='ze', w_lens=[4])
        info.word_list = ['zero', 'waste']
        self.assertEqual(answers.guess_answer(info, 51), 'zero')
        info.word_list = []
        self.assertEqual(answers.guess_answer(info, 51), 'zeaa')

    def test_legacy_config_enables_compatibility_and_persists_changes(self):
        config = json.loads((Path(__file__).resolve().parents[1] / 'config/config.json').read_text(encoding='utf-8'))
        config.pop('compat_mode', None)
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory, 'config')
            config_path.mkdir()
            target = config_path / 'config.json'
            target.write_text(json.dumps(config), encoding='utf-8')
            info = PublicInfo(directory)
            self.assertTrue(info.compat_mode)
            info.input_info(2, 3, 5, 15, True, 'gzip', compat_mode=False)
            self.assertFalse(PublicInfo(directory).compat_mode)
            self.assertFalse(json.loads(target.read_text(encoding='utf-8'))['compat_mode'])


if __name__ == '__main__':
    unittest.main()
