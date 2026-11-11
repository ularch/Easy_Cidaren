from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from api.main_api import TaskWordMappingError, check_is_self_built


def task(words, rows, is_self_built=True):
    return SimpleNamespace(is_self_built=is_self_built, word_list=words,
                           get_book_words_data=rows, now_unit='old_unit')


class SelfBuiltWordMappingTests(unittest.TestCase):
    def test_case_insensitive_match_selects_corresponding_unit(self):
        info = task(['other', 'insert'], [{'list_id': 'other_unit'}, {'list_id': 'unit'}])
        query = Mock(return_value='result')
        self.assertEqual(check_is_self_built(query)(info, 'Insert'), 'result')
        query.assert_called_once_with(info, 'insert')
        self.assertEqual(info.now_unit, 'unit')

    def test_exact_spelling_takes_priority(self):
        info = task(['insert', 'Insert'], [{'list_id': 'lower'}, {'list_id': 'exact'}])
        query = Mock()
        check_is_self_built(query)(info, 'Insert')
        query.assert_called_once_with(info, 'Insert')
        self.assertEqual(info.now_unit, 'exact')

    def test_missing_word_raises_specific_mapping_error(self):
        info = task(['insert'], [{'list_id': 'unit'}])
        query = Mock()
        with self.assertRaises(TaskWordMappingError):
            check_is_self_built(query)(info, 'missing')
        query.assert_not_called()
        self.assertEqual(info.now_unit, 'old_unit')

    def test_missing_metadata_index_raises_specific_mapping_error(self):
        info = task(['insert'], [])
        query = Mock()
        with self.assertRaises(TaskWordMappingError):
            check_is_self_built(query)(info, 'INSERT')
        query.assert_not_called()
        self.assertEqual(info.now_unit, 'old_unit')

    def test_ordinary_task_keeps_original_word_and_unit(self):
        info = task([], [], is_self_built=False)
        query = Mock(return_value='result')
        self.assertEqual(check_is_self_built(query)(info, 'Insert'), 'result')
        query.assert_called_once_with(info, 'Insert')
        self.assertEqual(info.now_unit, 'old_unit')

    def test_unrelated_query_errors_are_not_converted(self):
        for error in [TypeError('bad type'), AttributeError('bad attribute'),
                      KeyError('missing key'), IndexError('bad index')]:
            with self.subTest(error=type(error).__name__):
                info = task(['insert'], [{'list_id': 'unit'}])
                query = Mock(side_effect=error)
                with self.assertRaises(type(error)) as captured:
                    check_is_self_built(query)(info, 'Insert')
                self.assertIs(captured.exception, error)

    def test_malformed_unit_metadata_keeps_its_key_error(self):
        info = task(['insert'], [{}])
        query = Mock()
        with self.assertRaises(KeyError):
            check_is_self_built(query)(info, 'insert')
        query.assert_not_called()


if __name__ == '__main__':
    unittest.main()
