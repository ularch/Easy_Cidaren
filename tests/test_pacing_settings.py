import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication
import main
from publicInfo.publicInfo import PublicInfo
from view.setting import Ui_Form


class PacingTests(unittest.TestCase):
    def setUp(self):
        self.worker = main.TaskWorker([])

    def test_wait_uses_configured_range(self):
        with patch.object(main.random, 'uniform', return_value=3.25) as sample, \
                patch.object(main.random, 'random', return_value=0.5), \
                patch.object(main.time, 'sleep') as sleep:
            self.worker._pacing_delay(SimpleNamespace(min_time=2, max_time=6))
            sample.assert_called_once_with(2, 6)
            sleep.assert_called_once_with(3.25)

    def test_occasional_pause_extends_regular_wait(self):
        with patch.object(main.random, 'uniform', side_effect=[1.5, 4.0]), \
                patch.object(main.random, 'random', return_value=0.02), \
                patch.object(main.time, 'sleep') as sleep:
            self.worker._pacing_delay(SimpleNamespace(min_time=1, max_time=2))
            sleep.assert_called_once_with(5.5)

    def test_nonpositive_bounds_still_wait_at_least_one_second(self):
        with patch.object(main.random, 'uniform', return_value=1) as sample, \
                patch.object(main.random, 'random', return_value=0.5), \
                patch.object(main.time, 'sleep') as sleep:
            self.worker._pacing_delay(SimpleNamespace(min_time=0, max_time=0))
            sample.assert_called_once_with(1, 1)
            sleep.assert_called_once_with(1)


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'config/config.json'
        self.path.parent.mkdir()
        self.example = json.loads((Path(__file__).resolve().parents[1] / 'config/config.json').read_text(encoding='utf-8'))

    def load(self, low, high):
        self.path.write_text(json.dumps(dict(self.example, min_time=low, max_time=high)), encoding='utf-8')
        return PublicInfo(self.folder.name)

    def test_zero_legacy_config_uses_default_range(self):
        info = self.load(0, 0)
        self.assertEqual((info.min_time, info.max_time), (1, 2))

    def test_loaded_bounds_are_at_least_one_and_ordered(self):
        for low, high, expected in [(5, 1, (1, 5)), (-3, 5, (1, 5)), (-3, -1, (1, 2)),
                                    (0, 5, (1, 5)), (5, 0, (1, 5)), (1, 1, (1, 1))]:
            with self.subTest(low=low, high=high):
                info = self.load(low, high)
                self.assertEqual((info.min_time, info.max_time), expected)

    def test_saved_bounds_are_normalized_and_persisted(self):
        for low, high, expected in [(0, 0, (1, 2)), (5, 1, (1, 5)), (-3, 5, (1, 5)),
                                    (5, 0, (1, 5)), (1, 1, (1, 1))]:
            with self.subTest(low=low, high=high):
                info = self.load(2, 3)
                info.input_info(low, high, 5, 15, True, 'gzip')
                restored = PublicInfo(self.folder.name)
                self.assertEqual((restored.min_time, restored.max_time), expected)
                stored = json.loads(self.path.read_text(encoding='utf-8'))
                self.assertEqual((stored['min_time'], stored['max_time']), expected)

    def test_settings_inputs_enforce_one_second_and_can_save(self):
        application = QApplication.instance() or QApplication([])
        info = self.load(1, 2)
        form = Ui_Form(info)
        try:
            self.assertEqual(form.min_time.minimum(), 1)
            self.assertEqual(form.max_time.minimum(), 1)
            form.min_time.setValue(0)
            form.max_time.setValue(0)
            self.assertEqual((form.min_time.value(), form.max_time.value()), (1, 1))
            self.assertTrue(form.input())
            restored = PublicInfo(self.folder.name)
            self.assertEqual((restored.min_time, restored.max_time), (1, 1))
        finally:
            form.close()


if __name__ == '__main__':
    unittest.main()
