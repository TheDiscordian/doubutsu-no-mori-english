#!/usr/bin/env python3
"""Source-bound complete song-title caller and insertion acceptance batch."""
import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
import credits_strings as c
from extended_items import COUNTS, VROM
from song_item_names import verify_installation
from textbanks import banks


def scenario(native, built, report):
    if sha256(built) != report['output_sha256']:
        raise ValueError('Changed complete song-name ROM')
    verify_installation(native, built, report)
    files = by_vrom(built)
    items = files[VROM].extract(built)
    start = 32+sum(COUNTS[:10])*16
    names = [items[start+i*16:start+(i+1)*16].hex() for i in range(55)]
    original = next(b for b in banks(native) if b.name == 'item_2A')
    short = files[0x010F4000].extract(built)[original.data_offset:original.data_offset+550]
    loader_at = 0x1060+0x800262D0-0x80025C60
    loader = native[loader_at:loader_at+0xF0]
    if sha256(loader) != '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Changed native overlay loader')
    metadata = bytearray(c.METADATA_BYTES)
    struct.pack_into('>I', metadata, 12, c.RAM+c.RESIDENT_BYTES)
    code = files[CODE_VROM].extract(built)
    if code[c.METADATA-CODE_RAM:c.METADATA-CODE_RAM+32] != metadata:
        raise ValueError('Changed song actor ownership metadata')
    request = {'module':report['runtime_module'], 'names':names, 'short_names':short.hex(),
               'actor':files[c.VROM].extract(built).hex(), 'relocation':files[c.RELOCATION].extract(built).hex(),
               'loader':loader.hex(), 'metadata':metadata.hex()}
    return [{'wait':8}, {'save_state':True}, {'pause_game_thread':True}, {'test_song_item_names':request},
            {'load_state':True}, {'resume':True}, {'wait':2}, {'read':['8019B000',4], 'expect':'00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom', type=Path, default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build', type=Path, default=Path('build/song-names-pilot'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--resume-checkpoint', action='store_true', help='Load an isolated matching-ROM checkpoint before the batch')
    args = parser.parse_args()
    actions = scenario(verified_rom(args.native_rom.read_bytes()),
                       (args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()))
    if args.resume_checkpoint:
        actions = [{'wait':3}, {'load_state':True}, {'resume':True}]+actions
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'complete_song_fields_and_insertions':55, 'output':str(args.output)}))


if __name__ == '__main__':
    main()
