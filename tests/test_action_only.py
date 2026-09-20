"""Host-side regressions; Android commands are never executed."""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def function(source, name):
    return re.search(r'^' + name + r'\(\) [({]\n.*?^[)}]$', source, re.M | re.S)[0]


class ActionOnlyTests(unittest.TestCase):
    def shell(self, code, directory):
        return subprocess.run(['/bin/sh', '-c', code], cwd=directory,
                              capture_output=True, text=True)

    def test_module_allowlist(self):
        expected = {'action.sh', 'customize.sh', 'service.sh', 'uninstall.sh',
                    'module.prop', 'META-INF/com/google/android/update-binary',
                    'META-INF/com/google/android/updater-script'}
        expected |= {'Yuri/' + f for f in ['kill_google_process.sh', 'target_txt.sh',
                     'security_patch.sh', 'boot_hash.sh', 'yuri_keybox.sh', 'pif.sh']}
        actual = {str(p.relative_to(ROOT / 'Module'))
                  for p in (ROOT / 'Module').rglob('*') if p.is_file()}
        self.assertEqual(actual, expected)
        self.assertNotIn('updateJson=', (ROOT / 'Module/module.prop').read_text())

    def test_download_preserves_status_and_path(self):
        for file in ['Module/customize.sh', 'Module/Yuri/yuri_keybox.sh']:
            download = function((ROOT / file).read_text(), 'download')
            for backend in ['curl', 'wget']:
                with self.subTest(file=file, backend=backend), tempfile.TemporaryDirectory() as tmp:
                    mock = 'curl() { return 23; }'
                    if backend == 'wget':
                        mock = 'command() { return 1; }; busybox() { return 23; }'
                    result = self.shell(mock + '\n' + download + '\n' +
                        'old_path=$PATH; download https://example.invalid/key; result=$?; '
                        '[ "$PATH" = "$old_path" ] || exit 99; exit "$result"', tmp)
                    self.assertEqual(result.returncode, 23, result.stderr)
            self.assertIn('-fLsS', download)
            self.assertNotIn('--no-check-certificate', download)

    def test_failed_fetch_never_replaces_keybox_or_backup(self):
        for file in ['Module/customize.sh', 'Module/Yuri/yuri_keybox.sh']:
            source = (ROOT / file).read_text()
            for body in ['printf partial; return 22', 'return 0',
                         "printf '%s' '%%%'; return 0"]:
                with self.subTest(file=file, response=body), tempfile.TemporaryDirectory() as tmp:
                    p = Path(tmp)
                    (p / 'keybox.xml').write_text('original')
                    (p / 'keybox.xml.bak').write_text('older backup')
                    code = '''TARGET_FILE=keybox.xml
BACKUP_FILE=keybox.xml.bak
REMOTE_FILE=keybox
DECODE_FILE=keybox_decode
REMOTE_URL=https://example.invalid/key
ui_print() { :; }
log_message() { :; }
# BSD and Android base64 differ in positional file handling.
base64() { command base64 -d < "$2"; }
'''
                    code += 'download() { ' + body + '; }\n'
                    code += function(source, 'get_keybox') + '\n'
                    code += function(source, 'update_keybox') + '\nupdate_keybox'
                    result = self.shell(code, tmp)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual((p / 'keybox.xml').read_text(), 'original')
                    self.assertEqual((p / 'keybox.xml.bak').read_text(), 'older backup')
                    self.assertFalse((p / 'keybox_decode').exists())

    def test_successful_fetch_backs_up_then_replaces(self):
        for file in ['Module/customize.sh', 'Module/Yuri/yuri_keybox.sh']:
            with self.subTest(file=file), tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp)
                (p / 'keybox.xml').write_text('original')
                source = (ROOT / file).read_text()
                code = '''TARGET_FILE=keybox.xml
BACKUP_FILE=keybox.xml.bak
REMOTE_FILE=keybox
DECODE_FILE=keybox_decode
REMOTE_URL=https://example.invalid/key
ui_print() { :; }
log_message() { :; }
# BSD and Android base64 differ in positional file handling.
base64() { command base64 -d < "$2"; }
download() { printf bmV3; }
'''
                code += function(source, 'get_keybox') + '\n'
                code += function(source, 'update_keybox') + '\nupdate_keybox'
                result = self.shell(code, tmp)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((p / 'keybox.xml').read_text(), 'new')
                self.assertEqual((p / 'keybox.xml.bak').read_text(), 'original')

    def test_broken_tee_uses_generation_mode(self):
        source = (ROOT / 'Module/Yuri/target_txt.sh').read_text()
        for status in ['true', 'false', None]:
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp)
                if status is not None:
                    (p / 'tee_status').write_text('teeBroken=' + status + '\n')
                safe = source.replace('/data/adb/tricky_store/target.txt', str(p / 'target.txt'))
                safe = safe.replace('/data/adb/tricky_store/tee_status', str(p / 'tee_status'))
                mock = 'pm() { case "$3" in -3) echo package:example.user;; -s) echo package:example.system;; esac; }\n'
                result = self.shell(mock + safe, tmp)
                self.assertEqual(result.returncode, 0, result.stderr)
                lines = (p / 'target.txt').read_text().splitlines()
                suffix = '!' if status == 'true' else ''
                self.assertIn('example.user' + suffix, lines)
                self.assertIn('example.system' + suffix, lines)
                self.assertNotIn('example.user?', lines)


if __name__ == '__main__':
    unittest.main()
