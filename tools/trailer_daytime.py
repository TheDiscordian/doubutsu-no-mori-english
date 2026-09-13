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
    parser.add_argument('--clock',type=datetime.fromisoformat,
                        default=datetime(2026,9,11,11,0,0),
                        help='Disposable emulator clock, ISO local date and time')
    args=parser.parse_args();out=args.output.resolve()
    if not out.is_relative_to(ROOT/'build'):raise ValueError('Stage only in ignored build/')
    staged=args.clock
    if staged.tzinfo is not None or not 1900 <= staged.year <= 2099:
        raise ValueError('Use a local emulator clock between 1900 and 2099')
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('Unexpected seed save')
    out.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(SOURCE,out/'test.flash')
    # Ares RTC layout: local/ares/ares/n64/cartridge/rtc.cpp, RTC::load/save.
    # This is a separate emulator clock, not the host clock or a user save edit.
    def bcd(value):return (value//10)*16+value%10
    rtc=bytearray(b'\xff'*32)
    rtc[16:24]=bytes([bcd(staged.second),bcd(staged.minute),bcd(staged.hour)|0x80,
                     bcd(staged.day),bcd((staged.weekday()+1)%7),bcd(staged.month),
                     bcd(staged.year%100),bcd(staged.year//100-19)])
    rtc[24:32]=int(time.time()).to_bytes(8,'big')
    (out/'test.rtc').write_bytes(rtc)
    (out/'staging.json').write_text(json.dumps({'save_sha256':SOURCE_SHA,
        'isolated_clock':staged.isoformat(),'host_clock_changed':False,'save_content_changed':False,
        'purpose':'Isolated gameplay on a disposable copy'},indent=2)+'\n')
    print(out)

if __name__=='__main__':main()
