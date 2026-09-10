"""Append proportional draft layout without changing saved mail/notice capacities."""
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

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '1898c04ffb844f5cd7ccd0199dae9c41c733e63e8accbe128a1a5933b71a0a08'
OWNER = 0x7749C0
POOL_AT, POOL_BEFORE, POOL_EXTRA = 0x800C4B10, 0x25CE3220, 0x1400
COMMON = {'af_mail_next_line': 0x801992A8, 'af_mail_draw': 0x8019923C}
# Entry hooks specify both displaced instructions. Call hooks specify the full
# previous instruction. No branch or relocated address is copied into a stub.
PARTS = {
    'editor': {
        'vrom': 0x03940000, 'reloc': 0x03948000, 'ram': 0x80885140, 'owner_at': 0x2B50,
        'sha256': 'd087dd33e57659e933b88f4d41bbe2a05623a07fb09a41ee7b98737e21f25579',
        'reloc_sha256': '6fc26aa496a5407b0af08239d0cf85c8cb5c602dc269fe85ad54699b8c01597f',
        'imports': {'af_grid_context': 0x80885140+28608, 'af_grid_editor_input': 0x80885140+25136,
                    'af_grid_owned': 0x80885140+24620, 'af_pixel_native_insert': 0x80885DD4,
                    'af_pixel_sound': 0x800D1A9C},
        'entries': {
            0x80885AEC: ('af_pixel_position', (0x8C820024, 0xA4C00000), 'af_pixel_original_position'),
            0x80885F6C: ('af_pixel_up', (0x27BDFFE8, 0xAFBF0014), 'af_pixel_original_up'),
            0x80885FCC: ('af_pixel_down', (0x27BDFFD0, 0xAFB00018), 'af_pixel_original_down')},
        'calls': {0x808868D8: ('af_pixel_grid_input', 0x80885140+25136, True)},
    },
    'letter': {
        'vrom': 0x03B60000, 'reloc': 0x03B70000, 'ram': 0x80888E90, 'owner_at': 0x2B90,
        'imports': {'af_letter_cursor': 0x80888E90+8692, 'af_mail_read_body': 0x80199434,
                    'af_mail_read_footer': 0x80199650},
        'entries': {
            0x80889A9C: ('af_mail_read_body', (0x27BDFF68, 0xF7B40040), None),
            0x808899E4: ('af_mail_read_footer', (0x27BDFFC0, 0x3C013F80), None)},
        'calls': {0x8088A114: ('af_pixel_letter_cursor', 0x80888E90+8692, True)},
    },
    'notice': {
        'vrom': 0x03920000, 'reloc': 0x03928000, 'ram': 0x80894250, 'owner_at': 0x2AD0,
        'imports': {},
        'entries': {0x8089542C: ('af_pixel_notice_body', (0x27BDFF68, 0xAFBE0090), None)},
        'calls': {0x80895850: ('af_pixel_notice_cursor', 0x0320F809, False)},
    },
}


def jump(target, link=False):
    return (0x0C000000 if link else 0x08000000) | (target >> 2 & 0x3FFFFFF)


def sources():
    paths = sorted((ROOT/'overlays/editor_pixels').iterdir())
    paths += [ROOT/'overlays/hboard/editor.h', ROOT/'overlays/keyboard_grid/editor.h',
              ROOT/'overlays/keyboard_grid/core.h', ROOT/'runtime/mail/view.h']
    return {str(p.relative_to(ROOT)): sha256(p.read_bytes()) for p in paths if p.is_file()}


def flat_rows(data, size):
    sections = struct.unpack_from('>5I', data)
    if sections[:4] != (size, 0, 0, 0): raise ValueError('Expected flattened current overlay')
    rows = list(struct.unpack_from('>'+str(sections[4])+'I', data, 20))
    if any(r >> 30 != 1 or r & 0xFFFFFF > size-4 for r in rows):
        raise ValueError('Invalid preceding relocation section/bounds')
    return rows


def compile_part(name, base, out):
    spec = PARTS[name]; ram = spec['ram']; files = by_vrom(base)
    prior = files[spec['vrom']].extract(base); old_rel = files[spec['reloc']].extract(base)
    if ('sha256' in spec and sha256(prior) != spec['sha256'] or
            'reloc_sha256' in spec and sha256(old_rel) != spec['reloc_sha256']):
        raise ValueError('Changed preceding editor image')
    rows = flat_rows(old_rel, len(prior)); original_rows = set(rows)
    imports = dict(COMMON, **spec['imports']); trampolines = []
    for at, (_, words, stub) in spec['entries'].items():
        if struct.unpack_from('>2I', prior, at-ram) != words:
            raise ValueError(f'Changed {name} native entry {at:08X}')
        if any(at-ram <= r & 0xFFFFFF < at-ram+8 for r in rows):
            raise ValueError('Displaced entry contains a relocation')
        if stub:
            imports[stub+'_resume'] = at+8
            trampolines += [f'.globl {stub}', stub+':', *(f'.word 0x{word:08X}' for word in words),
                            f'j {stub}_resume', 'nop']
    for at, (_, old, direct) in spec['calls'].items():
        if struct.unpack_from('>I', prior, at-ram)[0] != (jump(old, True) if direct else old):
            raise ValueError('Changed preceding draft call')
        if direct != (0x44000000 | (at-ram) in original_rows):
            raise ValueError('Changed draft call relocation ownership')
    out.mkdir(parents=True, exist_ok=False)
    (out/'previous.bin').write_bytes(prior)
    (out/'trampolines.s').write_text('\n'.join(trampolines)+'\n')
    (out/'imports.ld').write_text(''.join(f'{key} = 0x{value:08X};\n' for key, value in imports.items()))
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
    common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}:/source:ro', '-v', f'{out.resolve()}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                                capture_output=True, text=True, timeout=60)
        if result.returncode: raise ValueError(result.stdout+result.stderr)
        return result.stdout
    flags = ['-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0', '-mno-abicalls',
             '-fno-pic', '-ffreestanding', '-fno-builtin', '-fno-common', '-fno-stack-protector',
             '-fno-merge-constants', '-mno-explicit-relocs', '-mno-split-addresses', '-fstack-usage',
             '-Wall', '-Wextra', '-Werror']
    for unit in ('layout', name):
        run('gcc', *flags, '/source/overlays/editor_pixels/'+unit+'.c', '-o', unit+'.o')
    run('as', '-EB', '-mabi=32', '-march=vr4300', '-I/out', '-o', 'prefix.o',
        '/source/overlays/editor_pixels/image.s')
    run('ld', '-EB', '--emit-relocs', '-T', 'image.ld', '-Map=image.map', '-o', 'image.elf',
        'prefix.o', 'layout.o', name+'.o')
    if run('nm', '--undefined-only', 'image.elf').strip(): raise ValueError('Unresolved pixel-editor import')
    defined = {}
    for line in run('nm', '--defined-only', 'image.elf').splitlines():
        fields = line.split()
        if len(fields) == 3: defined[fields[2]] = int(fields[0], 16)
    run('objcopy', '-O', 'binary', '-j', '.text', 'image.elf', 'image.bin')
    data = bytearray((out/'image.bin').read_bytes())
    if data[:len(prior)] != prior or len(data) > spec['reloc']-spec['vrom']:
        raise ValueError('Pixel-editor suffix exceeds its owned VROM slot')
    inventory_text = run('readelf', '-rW', 'image.elf')
    inventory = elf_inventory(inventory_text, ram)
    touched = set()
    for at, (symbol, _, _) in spec['entries'].items():
        target = defined[symbol]
        struct.pack_into('>2I', data, at-ram, jump(target), 0); touched.update((at-ram, at-ram+4))
        if ram <= target < ram+len(data): rows.append(0x44000000 | (at-ram))
    for at, (symbol, _, direct) in spec['calls'].items():
        struct.pack_into('>I', data, at-ram, jump(defined[symbol], True)); touched.add(at-ram)
        if not direct: rows.append(0x44000000 | (at-ram))
    for at, kind, target, symbol in inventory:
        if not len(prior) <= at <= len(data)-4 or at & 3 or kind not in (2, 4, 5, 6):
            raise ValueError('Invalid appended pixel-editor relocation')
        if ram <= target < ram+len(data): rows.append(0x40000000 | kind << 24 | at)
        elif imports.get(symbol) != target or kind != 4: raise ValueError('Unbound resident pixel-editor import')
    if len({r & 0xFFFFFF for r in rows}) != len(rows): raise ValueError('Duplicate pixel-editor relocation')
    rel_size = (24+len(rows)*4+15) & ~15
    relocation = (struct.pack('>5I', len(data), 0, 0, 0, len(rows))+
                  struct.pack('>'+str(len(rows))+'I', *rows)+bytes(rel_size-24-len(rows)*4)+
                  struct.pack('>I', rel_size))
    for load_at in (0x80200010, 0x80370010):
        current = relocate_verified_data(Image(ram, len(data), struct.unpack_from('>5I', relocation)),
                                         data, relocation, load_at)
        old = relocate_verified_data(Image(ram, len(prior), struct.unpack_from('>5I', old_rel)),
                                     prior, old_rel, load_at)
        for at in range(0, len(prior), 4):
            if at not in touched and current[at:at+4] != old[at:at+4]:
                raise ValueError('Pixel-editor relocation changes retained native code/data')
    report = {'bytes': len(data), 'previous_bytes': len(prior), 'previous_sha256': sha256(prior),
              'previous_reloc_sha256': sha256(old_rel), 'overlay_sha256': sha256(data),
              'suffix_sha256': sha256(data[len(prior):]), 'relocation_sha256': sha256(relocation),
              'symbols': {key: value-ram for key, value in defined.items() if key not in imports},
              'imports': imports, 'elf_relocations': inventory,
              'touched_offsets': sorted(touched), 'relocation_bases': ['80200010', '80370010'],
              'stack_usage': {unit: (out/(unit+'.su')).read_text() for unit in ('layout', name)}}
    (out/'image.bin').write_bytes(data); (out/'relocation.bin').write_bytes(relocation)
    (out/'image.asm').write_text(run('objdump', '-d', 'image.elf'))
    (out/'elf-relocations.txt').write_text(inventory_text)
    (out/'image.json').write_text(json.dumps(report, indent=2)+'\n')
    return bytes(data), relocation, report


def build(native, base, out):
    verified_rom(native)
    if sha256(base) != BASE_SHA: raise ValueError('Pixel editor requires the corrected title baseline')
    from runtime_module import MODULE_VROM, verify_test_module
    module = json.loads((ROOT/'build/civic-interior-artwork-01/build.json').read_text())['runtime_module']
    verify_test_module(base, module)
    for symbol, address in dict(COMMON, af_mail_read_body=0x80199434, af_mail_read_footer=0x80199650).items():
        if int(module['symbols'][symbol], 16) != address: raise ValueError('Changed resident layout import')
    before = sources(); files = by_vrom(base); changes = {}; reports = {}; growth = 0
    owner = bytearray(files[OWNER].extract(base)); code = bytearray(files[CODE_VROM].extract(base))
    for name, spec in PARTS.items():
        data, rel, report = compile_part(name, base, out/name)
        old_size = files[spec['vrom']].size; at = spec['owner_at']
        if struct.unpack_from('>4I', owner, at) != (spec['vrom'], spec['vrom']+old_size,
                                                   spec['ram'], spec['ram']+old_size):
            raise ValueError('Changed pixel-editor allocation owner')
        struct.pack_into('>4I', owner, at, spec['vrom'], spec['vrom']+len(data), spec['ram'], spec['ram']+len(data))
        growth += ((len(data)+63) & ~63)-((old_size+63) & ~63)
        changes[spec['vrom']] = data; changes[spec['reloc']] = rel; reports[name] = report
    if growth > POOL_EXTRA or struct.unpack_from('>I', code, POOL_AT-CODE_RAM)[0] != POOL_BEFORE:
        raise ValueError('Pixel-editor growth exceeds its shared pool reservation')
    struct.pack_into('>I', code, POOL_AT-CODE_RAM, POOL_BEFORE+POOL_EXTRA)
    changes[OWNER] = bytes(owner); changes[CODE_VROM] = bytes(code)
    resized = tuple(v for s in PARTS.values() for v in (s['vrom'], s['reloc']))
    image = reconstruct(native, base, changes, resized=resized)
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image: raise ValueError('Pixel-editor patch does not reconstruct cartridge')
    if before != sources(): raise ValueError('Pixel-editor sources changed while compiling')
    report = {'version': 1, 'baseline_sha256': BASE_SHA, 'output_sha256': sha256(image),
              'patch_sha256': sha256(patch), 'source_sha256': sha256(native), 'sources': before,
              'parts': reports, 'shared_growth_bytes': growth, 'extra_pool_bytes': POOL_EXTRA,
              'module_sha256': sha256(files[MODULE_VROM].extract(base)), 'toolchain_image': IMAGE,
              'rom_bytes': len(image), 'required_ram_bytes': 0x800000, 'saved_body_bytes': 96,
              'save_format_changed': False, 'hardware_retest': 'pending',
              'status': 'Compiled and installed candidate; focused editor execution checks pending'}
    return image, patch, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/v1-editor-pixel-fix-01')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (ROOT/'build/v1-playtest-fixes-01/animal-forest-title-preview.z64').read_bytes(), args.output)
    for name, data in {'animal-forest-title-preview.z64': image, 'animal-forest-title-preview.ups': patch,
                       'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target: target.write(data)
    print(json.dumps({key: report[key] for key in ('output_sha256', 'patch_sha256', 'shared_growth_bytes', 'status')}, indent=2))


if __name__ == '__main__': main()
