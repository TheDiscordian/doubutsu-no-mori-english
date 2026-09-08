#!/usr/bin/env python3
"""Build native tests that require the startup-loaded cartridge glyph image."""

import argparse
import json
from pathlib import Path

from aflib import CODE_VROM,by_vrom,verified_rom
from extended_font_cartridge import VROM
from font import WIDTH_TABLE,FONT_VROM
from runtime_module import verify_test_module,module_command_info
from textcodec import encode,decode
from message_alias_test_scenario import scenario as text_scenario
from topic_gap_test_scenario import combine_checkpoints

IDS = ['message:'+n for n in '04D2 04FA 08A2 08A6 0A15 0E2A'.split()]


def scenario(rom,module):
    verify_test_module(rom,module)
    approval=module.get('extended_font')
    if not approval: raise ValueError('Cartridge font test requires its complete installed resource')
    files=by_vrom(rom);blob=files[VROM].extract(rom);size=approval['configuration'][2]
    request={'image':blob[:size].hex(),'relocations':blob[size:].hex(),'font':approval['font'],'module':module,
             'native_font':files[FONT_VROM].extract(rom)[0x128:0x6128].hex(),
             'cuts':files[CODE_VROM].extract(rom)[WIDTH_TABLE:WIDTH_TABLE+256].hex()}
    return [{'save_state':True},{'pause_game_thread':True},{'test_extended_font_cartridge':request},
            {'load_state':True},{'resume':True},{'wait':2}]


def dialogue_scenario(rom,module,source,edits):
    info=module_command_info(verified_rom(source))
    # The generic cartridge-load fixture takes the lossless native notation.
    # This changes notation only; it compares every actual installed byte.
    selected=[{**edit,'translation':decode(encode(edit['translation'],info,extended_glyphs=True),info)}
              for edit in edits if edit['id'] in IDS]
    font=[{'wait':8}]+scenario(rom,module)
    text=text_scenario(rom,selected,info,message_ids=IDS)
    return combine_checkpoints([font,text])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True);parser.add_argument('--module',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--translations',type=Path)
    parser.add_argument('--source-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    args=parser.parse_args();rom=args.rom.read_bytes();module=json.loads(args.module.read_text())
    actions=(dialogue_scenario(rom,module,args.source_rom.read_bytes(),json.loads(args.translations.read_text()))
             if args.translations else scenario(rom,module))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'cartridge_draws':26,'native_cursor_cases':8,
                      'cartridge_messages':IDS if args.translations else []}))
