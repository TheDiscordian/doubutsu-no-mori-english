"""Build checked summer-event code for integration, without changing any ROM/site."""
import argparse
import json
from pathlib import Path

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from apply_translation import write_new
from gc_names import rel_sections
from v3_asset_loader import ROOT, compile_part
from v3_furniture_art import verify_sources
from v3_villager_art import data_pointers

SCHEDULE_SHA = 'd449bc06ca8d7378319420f2889186d0833a084df7437cf354299237ec98da83'
NATIVE_CONTRACTS = (
    ('today_directory_initialization', 0x8007E60C, 0x8007E690,
     '19a00dff313ce6d2fc41f325a9321f21b4f8a0f577bf0b9f57b06fd57849b482'),
    ('native_after_day', 0x8007DE2C, 0x8007DF04,
     '0ea5257e91fc2b6a41bbb54b843c0fdbe84f35d4b2d7f9d68c5b1a00aecece5a'),
    ('update_schedule', 0x8007F358, 0x8007F6A0,
     'e78d93bb4578ca8b32feb19328d2aae22586bfdfe1665254eed39577fc7169bb'),
    ('reserve_saved_event', 0x80080080, 0x80080200,
     'e2bb9b6a6cb80e11964b08aa97b462a2294e48c6dcbe0d617c0c8fc85ba21769'),
    ('get_saved_event', 0x8008033C, 0x800804AC,
     'e3f773780ce82da3b43a46975c07e1c0c37815fbc95bca00f3b00ce8869adec3'),
)


def donor_schedule(rel, symbols):
    verify_sources(rel, symbols)
    at = rel_sections(rel)[5][0] + 0x441C
    table = rel[at:at + 0x648]
    row = table[55 * 12:56 * 12]
    if (sha256(table) != SCHEDULE_SHA or row.hex() != '06be004906b8000e00000018'
            or data_pointers(rel, 0x46B0, 12)):
        raise ValueError('Changed donor calendar or summer event row')
    return row


def native_contracts(native):
    verified_rom(native)
    code = by_vrom(native)[CODE_VROM].extract(native)
    result = []
    for name, start, end, expected in NATIVE_CONTRACTS:
        data = code[start - CODE_RAM:end - CODE_RAM]
        if sha256(data) != expected:
            raise ValueError('Changed native event contract: ' + name)
        result.append(dict(name=name, start=start, end=end, sha256=expected))
    return result


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh ignored build directory')
    row = donor_schedule((ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                         (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    contracts = native_contracts((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    output.mkdir(parents=True)
    code, compiled = compile_part('campsite_event', output / 'code')
    write_new(output / 'schedule.bin', row)
    report = dict(build='v3-campsite-event-module', installed=False, code=compiled,
        native_contracts=contracts, donor_row=55, donor_type=24, proposed_native_type=70,
        donor_schedule_sha256=sha256(row), native_event_types=70, native_today_slots=16,
        native_saved_areas=5, native_saved_area_stride=48, native_saved_data_bytes=40,
        native_mask_records=5, native_mask_record_bytes=12,
        native_visitor_animal_bytes=0x528,
        saved_format_changed=False, rom_changed=False, web_patcher_changed=False,
        pending=['extended native event directory and manager binding',
                 'checked resident allocation and startup installation',
                 'visitor Animal/defaults, masked identity readers, and greeting memory',
                 'English conversation flow and selected rewards',
                 'ordinary tent entry, exit, rendering, and persistence'])
    report['source_sha256'] = {name: sha256((ROOT / name).read_bytes()) for name in (
        'overlays/v3/campsite_event.c', 'overlays/v3/campsite_event.h',
        'overlays/v3/campsite_event.ld', 'tools/v3_campsite_event.py')}
    write_new(output / 'event.json', (json.dumps(report, indent=2, sort_keys=True) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2, sort_keys=True))
