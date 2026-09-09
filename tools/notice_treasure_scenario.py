#!/usr/bin/env python3
"""Bind a native treasure scheduler/transaction batch to the installed ROM."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from extended_items import COUNTS, WIDTH
from mail_catalog import parse
from mail_record import Field, Record
from notice_record import pack
from notice_treasure import IDS, fields_for, body
from notice_overlay import ROOT, verify_installation
from notice_treasure_owner import RANGES
from npc_mail_capture import ALIAS_HASH
from npc_mail_names import unpack_aliases

GUARDS = (
    (0x80087C40, 0x80087CD0, '8b5f63f0bed63440c5c35bb0964ee825c6b27dad5808a11af2cdecd39f56fe0a'),
    (0x80087E58, 0x80087ED0, '59741ea172eba5132f44779ad54cb68c8dc158268dfeecb43bd451bf76e4bc5c'),
    (0x80088160, 0x800882B0, 'f0cb5f524d97ea061fbe0a6af50f3e5653b60f82cf0325b2c2dd7a1e262c9dad'),
    (0x8008883C, 0x8008891C, '22bde75dee9aa225d178f10695b1aacbb742d11464284216c8f23c8360b8068d'),
    (0x80089440, 0x80089698, '9cf81cf3de63fe20e1a4f3c7063884da92f9c4394694361fd45bb57b781d0237'),
    (0x8008E9C4, 0x8008EA5C, 'efa3a088c06e570e7222e6d1eb6a9a17abdd6ec8438e9f1a6421f98bb79adc43'),
    (0x800A3B84, 0x800A3C1C, '01fa2419478fa45916b102363c782da949ae41a4e103ea4cd47a603ee53e7f98'),
    (0x80072828, 0x800728B4, '62a3054d17237b287d575fbf437583303fd72e2c3a10a9d07488ad212123f57e'),
    (0x800D5090, 0x800D5104, '13eddae8f09af413d1f819760c3c16b2efc4fe65b44fa6774b3d73a9d7e106fd'),
    (0x800A69C8, 0x800A6A04, 'be76eaf78940b50346a5f1bbd72f61338bd0edd7fdd525208b5b219b2e0d0752'),
    (0x80094E38, 0x80094E78, 'fde84d9b42c5e4d88001b28e75fabefd0d2094010dfe6aa01e1177a27bd45731'),
    (0x8009BFC0, 0x8009C108, '6713e8391c869fd384c16e0811ebc1001c7a5c31d56c12d76889f12b3e05e4de'),
    (0x8010436C, 0x801043D0, '662268e1eaf934680eab60158b5c163d3410842dc00270b9a6ddc35c5950ff93'),
    (0x801165C0, 0x801166BC, '437f3883987376d2ce1926b8f318f0b109b38c5f15f5bafdee3fb836ce06d53f'),
    (0x801172A0, 0x801172AC, 'fea6e28ec3e47db1c6ded1650d2e7f5c54940c9b41254401569bca49cde66036'),
)
SEEDS = (10, 0, 11)


def rng(seed, count=6):
    values = []
    for _ in range(count):
        seed = (seed*0x19660D+0x3C6EF35F) & 0xFFFFFFFF
        values.append((seed >> 9)/2**23)
    return seed, values


def scenario(native, built, report, *, skip_complete=0, reader_only=False):
    if type(skip_complete) is not int or not 0 <= skip_complete <= 72:
        raise ValueError('Invalid completed treasure case count')
    if type(reader_only) is not bool: raise ValueError('Invalid treasure reader selection')
    if sha256(built) != report['output_sha256']: raise ValueError('Changed treasure test ROM')
    verify_installation(built, native, report['runtime_module'], report['noticeboard'])
    if not report['noticeboard'].get('treasure_owner'): raise ValueError('Treasure owner is not installed')
    files = by_vrom(built)
    source = by_vrom(native)[CODE_VROM].extract(native)
    code = files[CODE_VROM].extract(built)
    guards = {}
    for lo, hi, digest in GUARDS:
        expected = source[lo-CODE_RAM:hi-CODE_RAM]
        if sha256(expected) != digest or code[lo-CODE_RAM:hi-CODE_RAM] != expected:
            raise ValueError('Changed native treasure test dependency')
        guards[f'{lo:08X}'] = expected.hex()
    for lo, hi, _ in RANGES: guards[f'{lo:08X}'] = code[lo-CODE_RAM:hi-CODE_RAM].hex()
    module = report['runtime_module']
    overlay = module['npc_mail_loader']['overlay']
    offset = overlay['symbols']['af_npc_alias_data']
    aliases = unpack_aliases(files[0x03200000].extract(built)[offset:offset+6368], ALIAS_HASH)
    npc = next(r for r in aliases if len(r.name.rstrip(b' ')) == 8)
    catalog = parse(files[0x030A0000].extract(built))[1]
    items = files[0x02A00000].extract(built)
    at = 32+(sum(COUNTS[:-1])+(0x11FC & 4095))*WIDTH
    item_name = items[at:at+WIDTH]
    if len(item_name.rstrip(b' ')) <= 10: raise ValueError('Treasure test needs a complete wide item name')
    cases = []
    for number in IDS:
        for capital in (0, 1):
            for item in (0x2512, 0x11FC):
                seed = SEEDS[(number-0x1F0) % 3]
                final, random = rng(seed)
                if not (random[0] < 0.4 and random[1] < 1/3 and int(random[5]*3) == (number-0x1F0) % 3):
                    raise ValueError('Treasure seed no longer selects the original template')
                samples = {1: Field(npc.name), 2: Field(b'pitfall         ' if item == 0x2512 else item_name, 1),
                           3: Field(b'1'), 4: Field(b'1'), 5: Field(b'Town  ')}
                value = Record(4, 0, (number,), tuple((i, samples[i]) for i in fields_for(number)), bool(capital))
                cases.append({'template': number, 'capital': capital, 'item': item, 'seed': seed,
                              'rng_final': final, 'hole': (len(cases)//2) % 25, 'unit': (len(cases)*13) % 256,
                              'animal': struct.pack('>HH6sBB', 0xE000+npc.npc_index, 0x1234,
                                                    b'Town  ', npc.npc_index, (number-0x1F0)//3).hex(),
                              'wire': pack(value).hex(), 'body': body(value, catalog).hex()})
    if reader_only:
        from notice_reader_scenario import scenario as reader_scenario
        actions = reader_scenario(native, built, report, skip_initial=8)
        request = actions[3]['test_notice_reader']
        request.update(cases=cases, skip_initial=skip_complete, treasure_only=True)
        return actions
    holes = list(struct.unpack_from('>25I', code, 0x8010436C-CODE_RAM))
    request = {'module': module, 'cases': cases, 'skip_complete': skip_complete, 'guards': guards,
               'hole_profiles': holes, 'empty_rtc': code[0x80117AE0-CODE_RAM:0x80117AE8-CODE_RAM].hex()}
    return [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True},
            {'test_notice_treasure': request}, {'load_state': True}, {'resume': True},
            {'wait': 2}, {'read': ['8019B000', 4], 'expect': '00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT/'build/notice-treasure-pilot')
    parser.add_argument('--output', type=Path, default=ROOT/'build/noticeboard-treasure/native-scenario.json')
    parser.add_argument('--skip-complete', type=int, default=0)
    parser.add_argument('--reader-only', action='store_true',
                        help='Read complete treasure pages without replaying creation or initial-post cases')
    args = parser.parse_args()
    actions = scenario((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                       (args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()), skip_complete=args.skip_complete,
                       reader_only=args.reader_only)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({('reader_cases' if args.reader_only else 'creation_cases'): 72-args.skip_complete,
                      'save_io': False, 'hardware_verified': False}))


if __name__ == '__main__': main()
