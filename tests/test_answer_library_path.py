from contextlib import chdir
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from util import answer_lib


class AnswerLibraryPathTests(unittest.TestCase):
    def test_source_path_is_independent_of_working_directory(self):
        expected = Path(answer_lib.__file__).absolute().parent.parent / 'config/answer_lib.json'
        with tempfile.TemporaryDirectory() as other, chdir(other):
            self.assertEqual(Path(answer_lib._lib_path()), expected)

    def test_read_and_write_use_module_directory(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as other:
            root = Path(directory)
            config = root / 'config'
            config.mkdir()
            data = {'测试释义': ['original phrase'], '_word_answers': {'测试释义': ['original']}}
            (config / 'answer_lib.json').write_text(json.dumps(data), encoding='utf-8')
            unrelated_config = Path(other) / 'config'
            unrelated_config.mkdir()
            unrelated = unrelated_config / 'answer_lib.json'
            unrelated_data = {'测试释义': ['unrelated phrase']}
            unrelated.write_text(json.dumps(unrelated_data), encoding='utf-8')
            with patch.object(answer_lib, '__file__', str(root / 'util/answer_lib.py')), \
                    patch.object(answer_lib, '_lib', None), chdir(other):
                self.assertEqual(answer_lib.lookup('测试释义'), ['original phrase'])
                self.assertEqual(answer_lib.lookup_word('测试释义'), ['original'])
                answer_lib.add_answer('测试释义', ['test phrase'])
                answer_lib.add_word_answer('测试释义', ['test'])
            stored = json.loads((root / 'config/answer_lib.json').read_text(encoding='utf-8'))
            self.assertEqual(stored['测试释义'], ['original phrase', 'test phrase'])
            self.assertEqual(stored['_word_answers']['测试释义'], ['original', 'test'])
            self.assertEqual(json.loads(unrelated.read_text(encoding='utf-8')), unrelated_data)

    def test_loading_missing_library_does_not_create_directory(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as other:
            root = Path(directory)
            with patch.object(answer_lib, '__file__', str(root / 'util/answer_lib.py')), \
                    patch.object(answer_lib, '_lib', None), chdir(other):
                self.assertEqual(Path(answer_lib._lib_path()), root / 'config/answer_lib.json')
                self.assertIsNone(answer_lib.lookup('测试释义'))
                self.assertFalse((root / 'config').exists())
                self.assertFalse((Path(other) / 'config').exists())


if __name__ == '__main__':
    unittest.main()
