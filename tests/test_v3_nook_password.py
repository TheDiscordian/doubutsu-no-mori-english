"""Focused source-stage mechanics; native bindings remain separate evidence."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class NookPasswordTests(unittest.TestCase):
    def test_result_retry_and_animated_single_insertion(self):
        with tempfile.TemporaryDirectory(prefix='v3-nook-password-') as tmp:
            binary=Path(tmp)/'test'
            result=subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-O1','-g',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_nook_password_test.c'),'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            print(result.stdout.strip())


if __name__=='__main__':unittest.main()
