#!/usr/bin/env python3
"""Build an isolated cartridge test for complete mail glyphs and old catalogues.

The fixture is deliberately not named as a translation build or release ROM.
It exercises resources/readers, not normal native letter creation or delivery.
"""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from aflib import by_vrom,replace_dma,sha256,verified_rom
from audit_mail_templates import template_fields
from extended_font_cartridge import install as install_font
from extended_font_cartridge_scenario import scenario as font_scenario
from font import make_halfwidth
from mail_catalog import install as install_catalog,parse,templates
from mail_catalog_test_scenario import scenario as catalog_scenario,WORK,OUTPUT
from mail_format import format_letter
from mail_glyph_codes import ADVANCES
from mail_record import Field,Record
from mail_view_patch import install as install_reader
from runtime_module import add_runtime_module,verify_test_module
from topic_gap_test_scenario import combine_checkpoints

ROOT = Path(__file__).resolve().parents[1]


def case(data,kind,ids,capital=False):
    catalog = parse(data)[0]
    record = Record(catalog,kind,ids,(),capital)
    parts = templates(data,record)
    fields = set().union(*(template_fields(p,extended_glyphs=catalog==4) for p in parts.parts))
    record = replace(record,fields=tuple((i,Field(b'x'*16,4)) for i in sorted(fields)))
    format_letter(record,parts)
    return str(ids),record,parts,None


def build(native,module_dir,catalog_dir,font_dir,out):
    native = verified_rom(native)
    replacements,_ = make_halfwidth(native)
    additions,module = add_runtime_module(native,replacements,module_dir)
    install_reader(native,replacements,additions,module,snapshots=True)
    catalogue = install_catalog(native,additions,module,catalog_dir,glyph_font=font_dir)
    if not catalogue.get('glyph_catalog') or not catalogue.get('fortune_catalog'):
        raise ValueError('Glyph compatibility batch requires catalogues two, three, and four')
    font = install_font(native,replacements,additions,module,font_dir)
    if font['blob_sha256'] != catalogue['glyph_font_sha256']:
        raise ValueError('Glyph fixture must contain the exact approved font')
    rom = replace_dma(native,replacements,additions=additions)
    verify_test_module(rom,module)
    data = additions[0x030A0000];banks = parse(data)[1]
    numbers = [i for i in range(982) if any(b'\x80' in banks[name][i] for name in ('super','mail','ps'))]
    cases = [case(data,0,(i,),capital) for i in numbers for capital in (False,True)]
    cases += [case(data,1,(77,)*5,capital) for capital in (False,True)]
    old = [case(additions[0x03000000],0,(0xFD,),capital) for capital in (False,True)]
    fortune = [case(additions[0x03050000],0,(i,),capital) for i in (114,115,116) for capital in (False,True)]
    glyph_actions = catalog_scenario(rom,module,cases,catalog_id=4)
    # Direct native layout verifies odd widths and a pair held for the next line.
    extra = []
    for code,width in ADVANCES.items():
        pair = bytes((0x80,code))
        for text,expected in ((pair+b'\xcd',(3,2,width,1)),
                              (b'a'*31+pair,(33,33,186+width,0) if width<=6 else (31,31,186,0))):
            extra += [{'write':[f'{WORK:08X}',text.hex()]},
                      {'call':{'address':module['symbols']['af_mail_next_line'],
                               'arguments':[OUTPUT,WORK,len(text)],'expect_return':1}},
                      {'read':[f'{OUTPUT:08X}',16],'expect':struct.pack('>4I',*expected).hex()}]
    restore = next(i for i,a in enumerate(glyph_actions) if 'load_state' in a)
    glyph_actions[restore:restore] = extra
    actions = combine_checkpoints([
        [{'wait':8}]+font_scenario(rom,module),glyph_actions,
        catalog_scenario(rom,module,old),catalog_scenario(rom,module,fortune,catalog_id=3)])
    report = {'rom_sha256':sha256(rom),'module':module,'catalogues':catalogue,'font':font,
              'complete_glyph_letters':len(cases),'old_catalogue_letters':len(old)+len(fortune),
              'native_line_cases':28,'native_font_draws':44,'native_cursor_cases':17,
              'scope':'Isolated cartridge reader/drawing fixture; no native creator, delivery, save round trip, or release claim'}
    out.mkdir(parents=True,exist_ok=True)
    (out/'mail-glyph-test.z64').write_bytes(rom)
    (out/'fixture.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'scenario.json').write_text(json.dumps(actions,indent=2)+'\n')
    return {k:v for k,v in report.items() if k not in ('module','catalogues','font')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--module',type=Path,default=ROOT/'build/mail-glyph-runtime')
    parser.add_argument('--catalogues',type=Path,default=ROOT/'build/mail-glyph-resources')
    parser.add_argument('--font',type=Path,default=ROOT/'build/mail-font-cartridge')
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.rom.read_bytes(),args.module,args.catalogues,args.font,args.output),indent=2))
