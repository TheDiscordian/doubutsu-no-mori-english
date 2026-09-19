"""Correct both museum letter-header displays on the preserved V2-11 cartridge."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom, make_ups, apply_ups
from catalogue_names import Image
from letter_ui_fix import compile_part
import letter_names as names
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, MODULE_VROM
from title_start_fix import reconstruct
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256
from toolchain import IMAGE

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507'
BOARD_SHA = '3eb4eb3515a215546bba2266be869ab15ac0d39077e51b93a2602957d6bde2c9'
REL_SHA = '6fb268be5e51c282e4118ebbea3a5e05922a69fe7a21610e3d2c644526dcc1f9'
MODULE_SHA = 'd47d95442b75edddef43d6d6005bbb0dcba256ae3be326b9d804b1ce6059a1ff'
NAME_ENTRY, GATE = 0x801984D0, MODULE_RAM+0x90
SOURCES = ('tools/v2_museum_header_fix.py', 'overlays/letter_names/names.c',
           'overlays/letter_names/museum_reader.s', 'runtime/mail/reader.c')


def jump(at):
    return 0x08000000 | (at >> 2 & 0x3FFFFFF)


def compile_gate(out):
    out.mkdir(parents=True, exist_ok=False)
    docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}:/source:ro', '-v', f'{out.resolve()}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        return subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                              check=True, capture_output=True, text=True, timeout=60).stdout
    run('as', '-EB', '-mabi=32', '-march=vr4300', '-o', 'gate.o',
        '/source/overlays/letter_names/museum_reader.s')
    run('ld', '-EB', '-Ttext', hex(GATE), '-e', 'af_museum_reader_name', '-o', 'gate.elf', 'gate.o')
    if run('nm', '--undefined-only', 'gate.elf').strip():
        raise ValueError('Unresolved museum reader symbol')
    run('objcopy', '-O', 'binary', '-j', '.text', 'gate.elf', 'gate.bin')
    code = (out/'gate.bin').read_bytes()
    # Independently bind the ABI, exact six bounded stores, and displaced entry.
    words = [0x90A80010, 0x24090002, 0x11090004, 0, 0x27BDFFE0,
             jump(NAME_ENTRY+8), 0xAFB20018]
    for offset, char in enumerate(b'Museum'):
        words.extend((0x24080000 | char, 0xA0880000 | offset))
    words.extend((0x03E00008, 0x24020006))
    expected = struct.pack('>'+str(len(words))+'I', *words)
    if len(code) > 0x70 or code[:len(expected)] != expected or any(code[len(expected):]):
        raise ValueError('Museum reader differs from the checked bounded instructions')
    (out/'gate.asm').write_text(run('objdump', '-d', 'gate.elf'))
    return code


def patch_module(module, gate):
    if sha256(module) != MODULE_SHA or any(module[0x88:0x100]):
        raise ValueError('Changed V2 module or occupied descriptor padding')
    at = NAME_ENTRY-MODULE_RAM
    if struct.unpack_from('>2I', module, at) != (0x27BDFFE0, 0xAFB20018):
        raise ValueError('Changed reader entry')
    if not 84 <= len(gate) <= 0x70:
        raise ValueError('Museum reader exceeds descriptor padding')
    output = bytearray(module)
    output[0x90:0x90+len(gate)] = gate
    struct.pack_into('>2I', output, at, jump(GATE), 0)
    return bytes(output)


def build(native, base, out):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Museum header correction requires exact V2-11')
    sources = {p: sha256((ROOT/p).read_bytes()) for p in SOURCES}
    donor = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    if (sha256(donor) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256
            or donor[DATA_BASE+0xCD80:DATA_BASE+0xCD88] != b'Museum  '):
        raise ValueError('Changed official museum display-name reference')
    files = by_vrom(base)
    old, old_rel = (files[v].extract(base) for v in (names.NEW_VROM, names.NEW_RELOC))
    spec = {'vrom': names.NEW_VROM, 'reloc': names.NEW_RELOC, 'ram': names.RAM,
            'sha': BOARD_SHA, 'reloc_sha': REL_SHA, 'imports': names.IMPORTS, 'calls': {}}
    data, relocation, profile = compile_part('museum_header', base, out/'board', spec=spec,
        source='/source/overlays/letter_names/names.c', flags=('-DAF_MUSEUM_HEADER',))
    data = bytearray(data)
    at = names.HEADER-names.RAM
    if struct.unpack_from('>2I', old, at) != (jump(names.RAM+7828), 0):
        raise ValueError('Changed installed editor header entry')
    target = names.RAM+profile['symbols']['af_letter_header']
    struct.pack_into('>I', data, at, jump(target))
    # The entry already has an internal J relocation; retain that exact row.
    rows = struct.unpack_from('>'+str(struct.unpack_from('>I', relocation, 16)[0])+'I', relocation, 20)
    if rows.count(0x44000000 | at) != 1:
        raise ValueError('Missing museum header entry relocation')
    data = bytes(data)
    for location in (0x80200010, 0x80378010):
        before = relocate_verified_data(Image(names.RAM, len(old), struct.unpack_from('>5I', old_rel)), old, old_rel, location)
        after = relocate_verified_data(Image(names.RAM, len(data), struct.unpack_from('>5I', relocation)), data, relocation, location)
        if (before[:at] != after[:at] or before[at+4:] != after[at+4:len(old)]
                or struct.unpack_from('>I', after, at)[0] != jump(location+profile['symbols']['af_letter_header'])):
            raise ValueError('Museum fix changes retained board code after relocation')
    growth = ((len(data)+63)&~63)-((len(old)+63)&~63)
    # Letter UI reserves 4096 bytes and consumes 1536. Its board remains 10992
    # bytes in V2-11; V2-08's address fix retains its rounded allocation.
    # Subsequent keyboard builds own their separate 8192-byte reservation.
    if len(old) != 10992 or not 0 < growth <= 4096-1536:
        raise ValueError('Museum header exceeds the existing letter-UI reservation')
    if struct.unpack_from('>I', files[CODE_VROM].extract(base), 0x800C4B10-CODE_RAM)[0] != 0x25CE7620:
        raise ValueError('Changed V2 shared submenu reservation')
    owner = bytearray(files[names.OWNER].extract(base))
    if struct.unpack_from('>4I', owner, names.OWNER_AT) != (names.NEW_VROM, names.NEW_VROM+len(old), names.RAM, names.RAM+len(old)):
        raise ValueError('Changed board allocation owner')
    struct.pack_into('>4I', owner, names.OWNER_AT, names.NEW_VROM, names.NEW_VROM+len(data), names.RAM, names.RAM+len(data))
    gate = compile_gate(out/'reader')
    module = patch_module(files[MODULE_VROM].extract(base), gate)
    changes = {names.NEW_VROM: data, names.NEW_RELOC: relocation, names.OWNER: bytes(owner), MODULE_VROM: module}
    image = reconstruct(native, base, changes, resized=(names.NEW_VROM, names.NEW_RELOC))
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image or sources != {p: sha256((ROOT/p).read_bytes()) for p in SOURCES}:
        raise ValueError('Museum header patch reconstruction or source consistency failed')
    profile.update(overlay_sha256=sha256(data), touched_offsets=list(range(at, at+4)))
    return image, patch, {'build': 'V2-12', 'baseline_sha256': BASE_SHA, 'source_sha256': sha256(native),
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch), 'sources': sources,
        'board': profile, 'board_growth_bytes': growth, 'additional_pool_bytes': 0,
        'reader_gate': f'{GATE:08X}', 'reader_gate_bytes': len(gate), 'reader_gate_sha256': sha256(gate),
        'reader_entry': f'{NAME_ENTRY:08X}', 'resident_addresses_unchanged': True,
        'save_format_changed': False, 'delivery_code_changed': False, 'ups_roundtrip': True,
        'required_ram_bytes': 0x800000, 'toolchain_image': IMAGE,
        'official_reference': 'GAFE01_00 foresta.rel .data+0000CD80: Museum',
        'native_validation': 'pending', 'hardware_validation': 'pending',
        'changed_resources': {f'{v:08X}': sha256(d) for v, d in changes.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/v2-museum-header-12-final')
    args = parser.parse_args(); out = args.output.resolve()
    if not out.is_relative_to(ROOT/'build') or out.exists():
        raise ValueError('Choose a fresh ignored build directory')
    out.mkdir(parents=True)
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes(), out)
    for name, raw in {'Animal Forest English V2.z64': image, 'Animal Forest English V2.ups': patch,
                      'build.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        with (out/name).open('xb') as stream: stream.write(raw)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
