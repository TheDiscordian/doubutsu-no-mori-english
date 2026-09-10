"""Bounded host/sanitizer checks of the same birthday renderer compiled for N64."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class BirthdayDrawTests(unittest.TestCase):
    def test_same_renderer_complete_text_date_colours_and_read_only_state(self):
        with tempfile.TemporaryDirectory(prefix='af-birthday-draw-') as directory:
            out=Path(directory)/'check'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                str(ROOT/'tests/birthday_draw_check.c'),str(ROOT/'overlays/birthday/draw.c'),
                '-o',str(out)],check=True,capture_output=True,text=True,timeout=30)
            result=subprocess.run([str(out)],check=True,capture_output=True,text=True,timeout=15)
            self.assertIn('42 read-only layouts',result.stdout)


if __name__=='__main__':unittest.main()
