"""Regresiones para no mezclar intentos ni convertir una marca en éxito físico."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('h1', Path(__file__).with_name('analizar-registro.py'))
h1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h1)
NOTIFY = '[10.000000@2] meson_wdt c11098d0.watchdog: reboot_notify: disable watchdog (event = 1)\n'


class EvidenceTests(unittest.TestCase):
    def test_kernel_duration_and_declared_attempt(self):
        r = h1.analyze((NOTIFY + '[527.240000@0] sdio: cmd:53\n').encode(), 'pstore', 'previo-04')
        self.assertEqual(r['seconds_logged_after_single_notifier'], 517.24)
        self.assertFalse(r['attempt_verified_by_parser'])
        self.assertEqual(r['attempt_declared'], 'previo-04')

    def test_no_notifier_is_not_a_failure_diagnosis(self):
        r = h1.analyze(b'[11.000000@0] sdio: cmd:53\n', 'pstore', 'no-atribuido')
        self.assertIsNone(r['seconds_logged_after_single_notifier'])
        self.assertNotIn('diagnosis', r)

    def test_reset_disables_duration(self):
        r = h1.analyze((NOTIFY + '[1.000000@0] sdio: cmd:53\n').encode(), 'pstore', 'oem-07')
        self.assertIsNone(r['seconds_logged_after_single_notifier'])
        self.assertEqual(r['kernel_time_regressions_at_lines'], [2])

    def test_new_boot_without_visible_reset_disables_duration(self):
        r = h1.analyze((NOTIFY + '[11.000000@0] Linux version 4.9.113\n').encode(), 'pstore', 'oem-07')
        self.assertIsNone(r['seconds_logged_after_single_notifier'])

    def test_two_cycles_are_not_combined(self):
        r = h1.analyze((NOTIFY + NOTIFY.replace('10.000', '20.000')).encode(), 'pstore', 'previo-04')
        self.assertIsNone(r['seconds_logged_after_single_notifier'])

    def test_event_zero_does_not_match_restart(self):
        r = h1.analyze(NOTIFY.replace('event = 1', 'event = 0').encode(), 'pstore', 'previo-04')
        self.assertNotIn('kernel_reboot_notifier', r['marker_counts'])

    def test_logcat_records_stages_but_no_return_inference(self):
        r = h1.analyze(b'01-01 01:00:00 I ShutdownThread: Shutting down activity manager...\n01-01 01:00:01 I ShutdownThread: Calling uncrypt and monitoring the progress...\n', 'logcat', 'oem-07')
        self.assertIn('activity_manager_enter', r['marker_counts'])
        self.assertIn('uncrypt_enter', r['marker_counts'])
        self.assertIsNone(r['seconds_logged_after_single_notifier'])
        self.assertNotIn('uncrypt_completed', r['marker_counts'])

    def test_raw_content_never_exported(self):
        r = h1.analyze(b'PRIVATE_TEXT_NOT_TO_EXPORT\nI ShutdownThread: Rebooting, reason: PRIVATE_REASON\n', 'logcat', 'no-atribuido')
        self.assertNotIn('PRIVATE_', str(r))

    def test_reject_binary_invalid_utf8_empty_and_oversized(self):
        for data in (b'', b'abc\0def', b'\xff', b'x' * (h1.MAX_BYTES + 1)):
            with self.subTest(size=len(data)):
                with self.assertRaises((ValueError, UnicodeDecodeError)):
                    h1.analyze(data, 'pstore', 'oem-07')

    def test_restart_message_is_not_physical_reset(self):
        r = h1.analyze(b'[20.000000@0] Restarting system with command recovery\n', 'pstore', 'oem-07')
        self.assertEqual(r['marker_counts']['kernel_restart_message'], 1)
        self.assertNotIn('physical_reset', r)
        self.assertNotIn('installed', r)


if __name__ == '__main__':
    unittest.main()
