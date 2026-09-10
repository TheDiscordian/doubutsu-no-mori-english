"""Install complete address-list names/prompts and bounded English letter defaults."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom, make_ups, apply_ups
from catalogue_names import Image, elf_inventory
from npc_mail_show import relocate_verified_data
from title_start_fix import reconstruct
from toolchain import IMAGE
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '5f777165ad4cf77ad18ccab6c7cf5ab1e73901093e3ffa9a7453911f0e5a4573'
PARTS = {
    'address': {'vrom': 0x792700, 'reloc': 0x794240, 'ram': 0x8088ADB0,
        'new_vrom': 0x3E60000, 'new_reloc': 0x3E68000, 'owner_at': 0x2BB0,
        'sha': '54868e80abb268bf8723a461288234dbb41673a7076fbeb9cf3d52e257e3eae6',
        'reloc_sha': '32cf7ed4611ee5255ea6724d8d2d8273669be6a069df5f0fad6e61e3764f1bf8',
        'imports': {'af_ui_load_name': 0x80196044, 'af_ui_width': 0x8009028C, 'af_ui_draw': 0x80090E98},
        'calls': {0x8088BB60: ('af_ui_prompt_draw', 0x80090E98),
                  0x8088BEFC: ('af_ui_address_draw', 0x80090E98)}},
    'board': {'vrom': 0x3B60000, 'reloc': 0x3B70000, 'ram': 0x80888E90,
        'new_vrom': 0x3B60000, 'new_reloc': 0x3B70000, 'owner_at': 0x2B90,
        'sha': 'a822296dcf2698c7b675444d391082a09ae1ad7a4d2872f5558b88f83991060f',
        'reloc_sha': 'fb7211d00c16410ddca193dd0c616c98cb78b669a40eafcf5fdad9db177b4665',
        'imports': {'af_ui_original_board_init': 0x8088A2D0},
        'calls': {0x8088A750: ('af_ui_board_init', 0x8088A2D0)}},
}
POOL_AT, POOL_BEFORE, POOL_EXTRA = 0x800C4B10, 0x25CE4620, 0x1000


def source_hashes():
    return {str(p.relative_to(ROOT)): sha256(p.read_bytes())
            for p in sorted((ROOT/'overlays/letter_ui').iterdir()) if p.is_file()}


def reference(rel, symbols):
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Changed supplied English letter UI reference')
    for at, value in ((0x7A5E8, b'Choose an addressee.'),
                      (0x7A5FC, b'Your address book is empty!'),
                      (0x7B374, b'To '), (0x7B378, b'from ')):
        if rel[DATA_BASE+at:DATA_BASE+at+len(value)] != value:
            raise ValueError('Changed complete English letter UI wording')


def compile_part(name, base, out):
    spec = PARTS[name]; ram = spec['ram']; files = by_vrom(base)
    old, old_rel = (files[spec[k]].extract(base) for k in ('vrom', 'reloc'))
    if sha256(old) != spec['sha'] or sha256(old_rel) != spec['reloc_sha']:
        raise ValueError('Changed preceding letter UI owner')
    sections = struct.unpack_from('>5I', old_rel)
    if sum(sections[:3]) != len(old): raise ValueError('Changed letter UI native sections')
    prefix = old+bytes(sections[3]); rows = []
    for row in struct.unpack_from('>'+str(sections[4])+'I', old_rel, 20):
        section, kind, at = row >> 30, row >> 24 & 63, row & 0xFFFFFF
        if section not in (1, 2, 3) or kind not in (2, 4, 5, 6): raise ValueError('Unknown letter relocation')
        at += sum(sections[:section-1]); rows.append(0x40000000 | kind << 24 | at)
    original_rows = set(rows)
    for at, (_, target) in spec['calls'].items():
        if struct.unpack_from('>I', old, at-ram)[0] != 0x0C000000 | (target >> 2 & 0x3FFFFFF):
            raise ValueError('Changed letter UI draw/init call')
        if (ram <= target < ram+len(prefix)) != (0x44000000 | (at-ram) in original_rows):
            raise ValueError('Changed letter UI call relocation')
    out.mkdir(parents=True, exist_ok=False)
    (out/'previous.bin').write_bytes(prefix)
    (out/'prefix.s').write_text('.section .native,"ax",@progbits\n.incbin "previous.bin"\n')
    (out/'imports.ld').write_text(''.join(f'{n} = 0x{v:08X};\n' for n, v in spec['imports'].items()))
    (out/'image.ld').write_text(f'''OUTPUT_ARCH(mips)
INCLUDE imports.ld
SECTIONS {{
 . = 0x{ram:08X};
 .text : {{ KEEP(*(.native)) *(.text .text.*) . = ALIGN(16);
           *(.rodata .rodata.* .data .data.*) . = ALIGN(16);
           *(.bss .bss.* COMMON) . = ALIGN(16); }}
 /DISCARD/ : {{ *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }}
}}
''')
    docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}:/source:ro', '-v', f'{out.resolve()}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        r = subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                           capture_output=True, text=True, timeout=60)
        if r.returncode: raise ValueError(r.stdout+r.stderr)
        return r.stdout
    run('gcc', '-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0', '-mno-abicalls',
        '-fno-pic', '-ffreestanding', '-fno-builtin', '-fno-common', '-fno-stack-protector',
        '-fno-merge-constants', '-mno-explicit-relocs', '-mno-split-addresses', '-fstack-usage',
        '-Wall', '-Wextra', '-Werror', '/source/overlays/letter_ui/'+name+'.c', '-o', 'helper.o')
    run('as', '-EB', '-mabi=32', '-march=vr4300', '-o', 'prefix.o', 'prefix.s')
    run('ld', '-EB', '--emit-relocs', '-T', 'image.ld', '-Map=image.map', '-o', 'image.elf', 'prefix.o', 'helper.o')
    if run('nm', '--undefined-only', 'image.elf').strip(): raise ValueError('Unresolved letter UI import')
    defined = {}
    for line in run('nm', '--defined-only', 'image.elf').splitlines():
        f = line.split()
        if len(f) == 3: defined[f[2]] = int(f[0], 16)
    run('objcopy', '-O', 'binary', '-j', '.text', 'image.elf', 'image.bin')
    data = bytearray((out/'image.bin').read_bytes()); touched = set()
    if data[:len(prefix)] != prefix: raise ValueError('Compiled letter UI changes its previous prefix')
    for at, (symbol, _) in spec['calls'].items():
        struct.pack_into('>I', data, at-ram, 0x0C000000 | (defined[symbol] >> 2 & 0x3FFFFFF))
        touched.update(range(at-ram, at-ram+4))
        row = 0x44000000 | (at-ram)
        if row not in original_rows: rows.append(row)
    inventory_text = run('readelf', '-rW', 'image.elf'); inventory = elf_inventory(inventory_text, ram)
    for at, kind, target, symbol in inventory:
        if not len(prefix) <= at <= len(data)-4 or at & 3: raise ValueError('Invalid letter UI suffix relocation')
        if ram <= target < ram+len(data): rows.append(0x40000000 | kind << 24 | at)
        elif spec['imports'].get(symbol) != target or kind != 4: raise ValueError('Unbound letter UI import')
    if len({r & 0xFFFFFF for r in rows}) != len(rows): raise ValueError('Duplicate letter UI relocation')
    size = (24+len(rows)*4+15) & ~15
    relocation = (struct.pack('>5I', len(data), 0, 0, 0, len(rows))+
                  struct.pack('>'+str(len(rows))+'I', *rows)+bytes(size-24-len(rows)*4)+struct.pack('>I', size))
    for base_at in (0x80200010, 0x80370010):
        before = relocate_verified_data(Image(ram, len(prefix), sections), old, old_rel, base_at)
        after = relocate_verified_data(Image(ram, len(data), struct.unpack_from('>5I', relocation)), data, relocation, base_at)
        if any(a != b and at not in touched for at, (a, b) in enumerate(zip(before, after))):
            raise ValueError('Letter UI changes retained code/data at a runtime load address')
    report = {'previous_bytes': len(old), 'previous_resident_bytes': len(prefix), 'bytes': len(data),
              'previous_sha256': sha256(old), 'previous_relocation_sha256': sha256(old_rel),
              'overlay_sha256': sha256(data), 'relocation_sha256': sha256(relocation),
              'symbols': {n: v-ram for n, v in defined.items() if n not in spec['imports']},
              'imports': spec['imports'], 'elf_relocations': inventory, 'touched_offsets': sorted(touched),
              'stack_usage': (out/'helper.su').read_text(), 'relocation_bases': ['80200010', '80370010']}
    (out/'image.bin').write_bytes(data); (out/'relocation.bin').write_bytes(relocation)
    (out/'image.asm').write_text(run('objdump', '-d', 'image.elf'))
    (out/'elf-relocations.txt').write_text(inventory_text)
    (out/'image.json').write_text(json.dumps(report, indent=2)+'\n')
    return bytes(data), relocation, report


def build(native, base, rel, symbols, out):
    verified_rom(native); reference(rel, symbols)
    if sha256(base) != BASE_SHA: raise ValueError('Letter UI requires the checked inventory money predecessor')
    before = source_hashes(); files = by_vrom(base); changes = {}; reports = {}; moves = {}; growth = 0
    owner = bytearray(files[0x7749C0].extract(base)); code = bytearray(files[CODE_VROM].extract(base))
    for name, spec in PARTS.items():
        data, relocation, profile = compile_part(name, base, out/name)
        at = spec['owner_at']; ram = spec['ram']
        if struct.unpack_from('>4I', owner, at) != (spec['vrom'], spec['vrom']+profile['previous_bytes'],
                                                   ram, ram+profile['previous_resident_bytes']):
            raise ValueError('Changed letter UI native allocation owner')
        if len(data) > spec['new_reloc']-spec['new_vrom']: raise ValueError('Letter UI exceeds its new owned slot')
        struct.pack_into('>4I', owner, at, spec['new_vrom'], spec['new_vrom']+len(data), ram, ram+len(data))
        changes[spec['vrom']] = data; changes[spec['reloc']] = relocation; reports[name] = profile
        for old, new in ((spec['vrom'], spec['new_vrom']), (spec['reloc'], spec['new_reloc'])):
            if old != new: moves[old] = new
        growth += ((len(data)+63) & ~63)-((profile['previous_resident_bytes']+63) & ~63)
    if growth > POOL_EXTRA or struct.unpack_from('>I', code, POOL_AT-CODE_RAM)[0] != POOL_BEFORE:
        raise ValueError('Letter UI exceeds its shared pool allocation')
    struct.pack_into('>I', code, POOL_AT-CODE_RAM, POOL_BEFORE+POOL_EXTRA)
    changes[0x7749C0] = bytes(owner); changes[CODE_VROM] = bytes(code)
    image = reconstruct(native, base, changes, resized=tuple(v for s in PARTS.values() for v in (s['vrom'], s['reloc'])), moves=moves)
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image: raise ValueError('Letter UI patch reconstruction failed')
    if source_hashes() != before: raise ValueError('Letter UI sources changed while compiling')
    return image, patch, {'version': 1, 'source_sha256': sha256(native), 'baseline_sha256': BASE_SHA,
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch), 'sources': before,
        'source_rel_sha256': REL_SHA256, 'source_symbols_sha256': SYMBOLS_SHA256,
        'parts': reports, 'vrom_moves': {f'{v:08X}': f'{n:08X}' for v, n in moves.items()},
        'shared_growth_bytes': growth, 'extra_pool_bytes': POOL_EXTRA, 'toolchain_image': IMAGE,
        'rom_bytes': len(image), 'required_ram_bytes': 0x800000, 'save_format_changed': False,
        'custom_letter_text_preserved': True, 'fixed_issues': ['V1-07', 'V1-08', 'V1-10'],
        'hardware_retest': 'pending', 'native_tests': 'pending'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, default=ROOT/'build/v1-inventory-money-fix-01')
    p.add_argument('--output', type=Path, default=ROOT/'build/v1-letter-ui-fix-01'); a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (a.base/'animal-forest-title-preview.z64').read_bytes(),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(), a.output)
    for name, data in {'animal-forest-title-preview.z64': image, 'animal-forest-title-preview.ups': patch,
                       'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        with (a.output/name).open('xb') as target: target.write(data)
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
