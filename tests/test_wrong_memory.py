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


class MemoryTests(unittest.TestCase):
    def test_context_keeps_blank_positions_and_hyphens(self):
        self.assertNotEqual(wrong_memory._key(73, 'a {} b', '译文'),
                            wrong_memory._key(73, 'a b {}', '译文'))
        self.assertNotEqual(wrong_memory._key(32, '_-_', '译文'),
                            wrong_memory._key(32, '_ _', '译文'))
        self.assertEqual(wrong_memory._key(32, 'Ａ\u00a0 _ ', '译文'),
                         wrong_memory._key(32, 'a _', '译文'))

    def test_roundtrip_overwrites_old_correction(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(wrong_memory, '_mem_path', return_value=str(Path(directory) / 'wrong_memory.json')), \
                patch.object(wrong_memory, '_memory', None):
            wrong_memory.record(73, '{con}', '译文', ['conservation'])
            wrong_memory.record(73, '{con}', '译文', ['construction'])
            wrong_memory.load_memory(force=True)
            self.assertEqual(wrong_memory.lookup(73, '{con}', '译文'), ['construction'])
            self.assertIsNone(wrong_memory.lookup(73, 'fixed {con}', '译文'))

    def test_legacy_memory_requires_matching_full_context(self):
        legacy = {'73|ab|译文': {'mode': 73, 'content': 'a {} b', 'remark': '译文', 'answers': ['word']}}
        with patch.object(wrong_memory, '_memory', legacy):
            self.assertEqual(wrong_memory.lookup(73, 'a {} b', '译文'), ['word'])
            self.assertIsNone(wrong_memory.lookup(73, 'a b {}', '译文'))

    def test_choice_follows_content_after_options_reorder(self):
        with patch.object(answers, 'lookup_wrong', return_value=['正确']):
            self.assertEqual(answers._memory_choice_index(
                question(17, 'question', ['错误', '正确']), 17), 1)

    def test_ambiguous_choice_is_ignored(self):
        with patch.object(answers, 'lookup_wrong', return_value=['正确']):
            self.assertIsNone(answers._memory_choice_index(
                question(17, 'question', ['正确', '正确']), 17))

    def test_sentence_memory_encodes_tag_suffix(self):
        for tag, sub_options, expected in [
            ('1#', [], '1#0'),
            ('1#', [{'content': 'word', 'answer_tag': 2}], '1#2'),
            (2, [], 2),
        ]:
            with self.subTest(tag=tag, sub_options=sub_options), \
                    patch.object(answers, 'lookup_wrong', return_value=['word']):
                info = question(42, 'a {}', [{'content': 'word', 'answer_tag': tag,
                                             'sub_options': sub_options}])
                self.assertEqual(answers.full_sentence(info), expected)

    def test_spelling_correction_precedes_shared_phrase(self):
        info = question(73, '{con}', w_lens=[12])
        with patch.object(answers, 'lookup', return_value=['conservation']), \
                patch.object(answers, 'lookup_wrong', return_value=['construction']):
            self.assertEqual(json.loads(answers.complete_spelling(info)), ['construction'])

    def test_spelling_memory_preserves_order_and_hyphenated_words(self):
        for content, words, lengths in [
            ('{con} {con}', ['construction', 'conservation'], [12, 12]),
            ('{} development', ['low-carbon'], [10]),
            ('{low} development', ['low-carbon'], [10]),
        ]:
            with self.subTest(content=content), \
                    patch.object(answers, 'lookup_wrong', return_value=words):
                info = question(73, content, w_lens=lengths)
                self.assertEqual(json.loads(answers.complete_spelling(info)), words)

    def test_wrong_answer_capture_uses_option_contents(self):
        with patch.object(main_api, 'record_wrong_answer') as record:
            main_api._record_wrong_answer(17, {'content': 'x', 'remark': 'y'},
                                          [1, True, 99], [{'content': 'bad'}, {'content': 'good'}])
            record.assert_called_once_with(17, 'x', 'y', ['good'])


    def test_self_learning_switch_controls_memory_writes(self):
        for enabled in [True, False]:
            info = question(17, 'question', ['wrong', 'correct'])
            info._self_learn_lib = enabled
            info.topic_code = 'current'
            info.right_count = info.wrong_count = 0
            response = Mock(json=lambda: {'data': 'encoded', 'jv': 'known'})
            with self.subTest(enabled=enabled), \
                    patch.object(PublicInfo, 'task_type', 'Test', create=True), \
                    patch.object(main_api.requests, 'rqs2_session', SimpleNamespace(post=Mock())), \
                    patch.object(main_api, 'check_jv_and_retry_post', return_value=response), \
                    patch.object(main_api, 'handle_response'), \
                    patch.object(main_api, 'debase64', return_value={
                        'answer_result': 2, 'answer_corrects': [1], 'topic_code': 'next'}), \
                    patch.object(main_api, 'record_wrong_answer') as record:
                main_api.submit_result(info, 0)
                self.assertEqual(record.call_count, int(enabled))
                self.assertEqual(info.wrong_count, 1)
                self.assertEqual(info.topic_code, 'next')


    def test_memory_location_is_independent_of_working_directory(self):
        expected = Path(wrong_memory.__file__).absolute().parent.parent / 'config/wrong_memory.json'
        with tempfile.TemporaryDirectory() as directory, chdir(directory):
            self.assertEqual(Path(wrong_memory._mem_path()), expected)
            self.assertFalse((Path(directory) / 'config').exists())
