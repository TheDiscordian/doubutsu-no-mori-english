"""Verify normal boot loads complete paged glyphs without damaging save code."""
import argparse
import json
from pathlib import Path
import struct

from aflib import sha256
from apply_translation import write_new
from v3_asset_loader import ROOT
from v3_furniture_install import inputs
from v3_nook_font import check_pixel_layout


def scenario(lock):
    image,report=inputs(lock)
    e=report['equipment_resources'];font=e['passwords']['nook']['font']
    if not font.get('pixel_pages'):
        raise ValueError('Native font check requires the current repaired pages')
    check_pixel_layout(report,font)
    packet=font['physical_resource']
    raw=image[packet['physical']:packet['physical']+packet['bytes']]
    if sha256(raw)!=packet['sha256']:
        raise ValueError('Changed complete source glyph artwork')
    actions=json.loads((ROOT/'tests/scenarios/v3_import_pipeline_boot.json').read_bytes())
    at=actions.index({'key':'Return','duration':0.12})
    checks=[dict(read=['80199F04',4],expect='80450010'),
        dict(read=[f'{0x80450010+font["symbols"]["af_np_pixels"]:08X}',4],
            expect=f'{font["pixels_ram"]:08X}')]
    for page in font['pixel_pages']:
        first,n=page['source_offset'],page['bytes']
        checks.append(dict(read=[f'{page["ram"]:08X}',n],expect=raw[first:first+n].hex()))
        for guard in ('front_guard','end_guard'):
            checks.append(dict(read=[f'{page[guard]:08X}',16],
                expect=(struct.pack('>I',page['guard_value'])*4).hex()))
    bank=e['bank'];owner=bank['packet'];code=bank['code']
    start=owner['physical']+bank['ram']-owner['ram']
    checks.append(dict(read=[f'{bank["ram"]:08X}',code['bytes']],
        expect=image[start:start+code['bytes']].hex()))
    # Exercise both boot/title and the following ordinary menu transition.
    actions[at:at]=checks
    actions.extend(checks)
    return actions


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-lock',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    actions=scenario(args.base_lock)
    write_new(args.output,(json.dumps(actions,indent=2)+'\n').encode())
    print(json.dumps(dict(actions=len(actions),output=str(args.output))))
