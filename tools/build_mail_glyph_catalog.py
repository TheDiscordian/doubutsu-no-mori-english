#!/usr/bin/env python3
"""Bundle frozen mail catalogues without replacing old saved-letter identities."""

import argparse
import json
from pathlib import Path

from aflib import sha256, verified_rom
from mail_catalog import VROM,verify_registered
from mail_glyph_codes import CATALOG,VROM as GLYPH_VROM


def bundle(rom,base,glyphs,out):
    rom = verified_rom(rom)
    report = json.loads((base/'catalog.json').read_text())
    original = (base/'catalog.bin').read_bytes()
    actual = verify_registered(original)
    if (actual['catalog'] != 2 or report.get('registered') is not True
            or report.get('source_sha256') != sha256(rom)
            or any(report.get(key) != value for key,value in actual.items())
            or report.get('glyph_catalog') or (base/'glyph-catalog.bin').exists()):
        raise ValueError('Changed original mail catalogue bundle')
    files = {'catalog.bin':original}
    if report.get('fortune_catalog'):
        from fortune_slips import CATALOG_VROM
        fortune = (base/'fortune-catalog.bin').read_bytes()
        expected = {**verify_registered(fortune),'vrom':f'{CATALOG_VROM:08X}'}
        if expected['catalog'] != 3 or report['fortune_catalog'] != expected:
            raise ValueError('Changed frozen fortune catalogue')
        files['fortune-catalog.bin'] = fortune
    elif (base/'fortune-catalog.bin').exists():
        raise ValueError('Untracked fortune catalogue')
    data = (glyphs/'catalog.bin').read_bytes()
    details = verify_registered(data)
    source = json.loads((glyphs/'catalog.json').read_text())
    if (details['catalog'] != CATALOG or source.get('registered') is not True
            or source.get('source_sha256') != sha256(rom)
            or source.get('vrom') != f'{GLYPH_VROM:08X}'
            or any(source.get(key) != value for key,value in details.items())):
        raise ValueError('Changed or unregistered complete glyph catalogue')
    report = {**report,'glyph_catalog':{**details,'vrom':f'{GLYPH_VROM:08X}'}}
    files['glyph-catalog.bin'] = data
    if out.resolve() in (base.resolve(),glyphs.resolve()):
        raise ValueError('Write the combined catalogues into a separate output directory')
    out.mkdir(parents=True,exist_ok=True)
    for name,data in files.items():
        (out/name).write_bytes(data)
    (out/'catalog.json').write_text(json.dumps(report,indent=2)+'\n')
    return {name:sha256(data) for name,data in files.items()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--base',type=Path,default=Path('build/fortune-slip-resources'))
    parser.add_argument('--glyphs',type=Path,default=Path('build/mail-glyph-catalog'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(bundle(args.rom.read_bytes(),args.base,args.glyphs,args.output),indent=2))
