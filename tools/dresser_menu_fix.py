"""Keep dresser cancellation last and bind the matching native action index."""
import argparse
import copy
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, verified_rom, fix_checksum, make_ups, apply_ups
from apply_translation import write_new
from textbanks import Bank

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'build/v2-combined-13'
BASE_SHA = 'f96395426808200dc6faaac0386aec9839ddcf3a4251eaaf98f371b8029a5e68'
NAME = 'Animal Forest English V2'
ROOM, ROOM_RAM = 0x82D7F0, 0x80936710
HANDLER, END, DECISION = 0x80939350, 0x809394F4, 0x80939394
HANDLER_SHA = 'e3b84416bedc4e69ea131c369d8db1c434acb48912478627cd18262c9c7bbdd5'
MESSAGE_SHA = 'edc17fef2f501a0fee9634299fde2053047f2ee998cdd94588c335a135568991'
BEFORE = bytes.fromhex('7F17007E000D00E9')
AFTER = bytes.fromhex('7F17007E00E9000D')
SOURCES = ('tools/dresser_menu_fix.py',)


def restore_handler(room):
    """Normalize only the fully checked correction for older owner contracts."""
    if struct.unpack_from('>I',room,DECISION-ROOM_RAM)[0]!=0x24010002:
        raise ValueError('Changed installed dresser cancellation comparison')
    restored=bytearray(room)
    struct.pack_into('>I',restored,DECISION-ROOM_RAM,0x24010001)
    if sha256(restored[HANDLER-ROOM_RAM:END-ROOM_RAM])!=HANDLER_SHA:
        raise ValueError('Changed complete installed dresser action handler')
    return bytes(restored)


def resources(native, base):
    """Resolve banks by original DMA identity, including relocated V3 banks."""
    verified_rom(native)
    original, files = by_vrom(native), by_vrom(base)
    indexed = {entry.index: entry for entry in files.values()}
    data, table = (indexed[original[v].index] for v in (0xBD4000, 0xCF9000))
    bank = Bank('message', data.vstart, table.vstart, data.extract(base), table.extract(base))
    entries = bank.entries()
    if sha256(entries[0xA0B]) != MESSAGE_SHA or entries[0xA0B].count(BEFORE) != 1:
        raise ValueError('Changed or already corrected dresser message')
    room = bytearray(files[ROOM].extract(base))
    span = room[HANDLER-ROOM_RAM:END-ROOM_RAM]
    if sha256(span) != HANDLER_SHA or struct.unpack_from('>I', room, DECISION-ROOM_RAM)[0] != 0x24010001:
        raise ValueError('Changed complete dresser action handler')
    # Only the row-one/row-two labels and matching cancellation comparison move.
    # Take-out stays zero; native B and its closing sound continue selecting last.
    entries[0xA0B] = entries[0xA0B].replace(BEFORE, AFTER)
    changed_data, changed_table = bank.rebuild(entries)
    if changed_table != bank.table or len(changed_data) != len(bank.data):
        raise ValueError('Dresser correction must retain every bank offset and size')
    struct.pack_into('>I', room, DECISION-ROOM_RAM, 0x24010002)
    changes = {data.vstart: changed_data, ROOM: bytes(room)}
    return changes, dict(message='message:0A0B', message_vrom=data.vstart,
        message_sha256=sha256(entries[0xA0B]), menu_ids=[0x7E, 0xE9, 0xD],
        actions=['remove', 'swap', 'cancel'], cancel_index=2,
        native_handler=f'{HANDLER:08X}', instruction=f'{DECISION:08X}',
        saved_format_changed=False, allocation_changed=False,
        changed_resources={f'{v:08X}':sha256(d) for v,d in changes.items()})


def patch(native, base):
    changes, receipt = resources(native, base)
    files = by_vrom(base)
    result = bytearray(base)
    for vrom, data in changes.items():
        entry = files[vrom]
        if entry.pend or entry.size != len(data):
            raise ValueError('Dresser fix requires existing uncompressed allocations')
        result[entry.pstart:entry.pstart+entry.size] = data
    fix_checksum(result)
    installed = by_vrom(result)
    for vrom, entry in files.items():
        if installed[vrom] != entry or installed[vrom].extract(result) != changes.get(vrom, entry.extract(base)):
            raise ValueError('Dresser correction changes an unrelated resource')
    return bytes(result), receipt


def build(output):
    if output.exists() or not output.resolve().is_relative_to(ROOT/'build'):
        raise ValueError('Choose a fresh ignored build directory')
    native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
    base = (BASE/(NAME+'.z64')).read_bytes()
    if sha256(base) != BASE_SHA:
        raise ValueError('V2-14 requires exact V2-13')
    image, receipt = patch(native, base)
    ups = make_ups(native, image)
    if apply_ups(native, ups) != image:
        raise ValueError('Dresser UPS reconstruction failed')
    report = copy.deepcopy(json.loads((BASE/'build.json').read_bytes()))
    report.update(build='V2-14', input_build_sha256=BASE_SHA,
        output_sha256=sha256(image), patch_sha256=sha256(ups), dresser_menu=receipt)
    report['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    output.mkdir(parents=True)
    for suffix, data in (('.z64',image),('.ups',ups)):
        write_new(output/(NAME+suffix), data)
    write_new(output/'build.json', (json.dumps(report,indent=2)+'\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({k:result[k] for k in ('build','output_sha256','patch_sha256','dresser_menu')},indent=2))
