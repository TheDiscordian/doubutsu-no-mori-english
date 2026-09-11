"""Stage an isolated daytime RTC beside an unchanged copy of the supplied save."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import time

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'local/rc2-save-report-g3O4lU/test.flash'
SOURCE_SHA='d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve()
    if not out.is_relative_to(ROOT/'build'):raise ValueError('Stage only in ignored build/')
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('Unexpected seed save')
    out.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(SOURCE,out/'test.flash')
    # Ares RTC layout: local/ares/ares/n64/cartridge/rtc.cpp, RTC::load/save.
    # This is a separate emulator clock, not the host clock or a user save edit.
    staged=datetime(2026,9,11,11,0,0)
    def bcd(value):return (value//10)*16+value%10
    rtc=bytearray(b'\xff'*32)
    rtc[16:24]=bytes([bcd(staged.second),bcd(staged.minute),bcd(staged.hour)|0x80,
                     bcd(staged.day),bcd((staged.weekday()+1)%7),bcd(staged.month),0x26,0x01])
    rtc[24:32]=int(time.time()).to_bytes(8,'big')
    (out/'test.rtc').write_bytes(rtc)
    (out/'staging.json').write_text(json.dumps({'save_sha256':SOURCE_SHA,
        'isolated_clock':staged.isoformat(),'host_clock_changed':False,'save_content_changed':False,
        'purpose':'Daytime trailer footage on a disposable copy'},indent=2)+'\n')
    print(out)

if __name__=='__main__':main()
