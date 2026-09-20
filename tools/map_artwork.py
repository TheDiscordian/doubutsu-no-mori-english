"""Port supplied English map heading and acre layout within the native asset file."""
import argparse
import copy
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shlex
import struct
import subprocess

from aflib import by_vrom, sha256, verified_rom, replace_dma, make_ups, apply_ups, u32
from building_artwork import donor_texture_pointers
from check_keyboard_assembly import IMAGE
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256, untile, pack4, model_texture_shape

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '507ddfe5ed585bcd6e20fbab44f7247315339a9c90b66dacec03b1e6b22fbc3a'
VROM = 0xAAD000
NATIVE_SHA = 'f7c6357e60fb53825f58ecf2fc494c34642365bb0225791a07c3fc0024c1f66b'
VERTICES = 0x4B92C0
QUADS = ((0xAB3A90, 0), (0xAB3ED0, 4), (0xAB3F10, 8), (0xAB3B50, 75), (0xAB3E50, 123))


@dataclass(frozen=True)
class Donor:
    gc: int
    gc_model: int
    model_bytes: int = 0x30


DONORS = (Donor(0x4B45C0, 0x4B9AF0), Donor(0x4B7EC0, 0x4B9B20))


def compile_commands(out, source=None, sections=(('acre', 56), ('dash', 48))):
    source = ROOT/'overlays/map/artwork.c' if source is None else source
    out.mkdir(parents=True, exist_ok=True)
    docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
        '-v', f'{ROOT}:/source:ro', '-v', f'{out.resolve()}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                       check=True, capture_output=True, timeout=60)
    run('gcc', '-c', '-EB', '-mabi=32', '-march=vr4300', '-G0', '-mno-abicalls', '-fno-pic',
        '-D_LANGUAGE_C', '-DF3DEX_GBI_2', '-I/source/upstream/af/lib/ultralib/include',
        '/source/'+str(source.relative_to(ROOT)), '-o', 'commands.o')
    result = {}
    for name, expected in sections:
        run('objcopy', '-O', 'binary', '-j', '.'+name, 'commands.o', name+'.bin')
        result[name] = (out/(name+'.bin')).read_bytes()
        if len(result[name]) != expected:
            raise ValueError('Native map command section exceeds its fixed space')
    return result


def compile_commands_batch(out, jobs):
    """Compile checked display-list jobs in one existing toolchain container.

    Each job retains its own object/sections and exact expected lengths. No
    shell data is interpolated without quoting; only the output tree is writable.
    """
    out=out.resolve();seen=set();commands=['set -eu'];targets=[]
    for key,source,sections in jobs:
        if not re.fullmatch(r'[A-Za-z0-9_-]+',key) or key in seen:
            raise ValueError('Invalid or duplicated native command job')
        seen.add(key);source=source.resolve();sections=tuple(sections)
        if not source.is_relative_to(ROOT) or not source.is_file() or not sections:
            raise ValueError('Native command source must be an existing project file')
        names=[name for name,_ in sections]
        if (len(set(names))!=len(names) or any(not re.fullmatch(r'[A-Za-z0-9_]+',name)
                or type(size) is not int or size<=0 or size%8 for name,size in sections)):
            raise ValueError('Invalid native command section contract')
        target=out/key;targets.append((key,target,sections))
        commands.append(shlex.join(['/n64_toolchain/bin/mips64-elf-gcc','-c','-EB','-mabi=32',
            '-march=vr4300','-G0','-mno-abicalls','-fno-pic','-D_LANGUAGE_C','-DF3DEX_GBI_2',
            '-I/source/upstream/af/lib/ultralib/include','/source/'+str(source.relative_to(ROOT)),
            '-o',f'/out/{key}/commands.o']))
        for name,_ in sections:
            commands.append(shlex.join(['/n64_toolchain/bin/mips64-elf-objcopy','-O','binary',
                '-j','.'+name,f'/out/{key}/commands.o',f'/out/{key}/{name}.bin']))
    if not targets:return {}
    for _,target,_ in targets:target.mkdir(parents=True,exist_ok=False)
    subprocess.run(['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint','/bin/sh',IMAGE,
        '-c','\n'.join(commands)],check=True,capture_output=True,timeout=max(60,15*len(targets)))
    result={}
    for key,target,sections in targets:
        result[key]={}
        for name,expected in sections:
            raw=(target/(name+'.bin')).read_bytes()
            if len(raw)!=expected:raise ValueError('Native batch command section differs from its contract')
            result[key][name]=raw
    return result


def port_quad(old, donor, scale=10):
    if len(old) != 64 or len(donor) != 64:
        raise ValueError('Map quad must have four complete vertices')
    n = list(struct.iter_unpack('>3hH2h4B', old))
    g = list(struct.iter_unpack('>3hH2h4B', donor))
    def corners(vertices):
        xs, ys = sorted({v[0] for v in vertices}), sorted({v[1] for v in vertices})
        if len(xs) != 2 or len(ys) != 2 or len({v[:2] for v in vertices}) != 4:
            raise ValueError('Map geometry is not an axis-aligned quad')
        return {(v[0] == xs[-1], v[1] == ys[-1]): v for v in vertices}
    nc, gc = corners(n), corners(g)
    reverse = {tuple(v): corner for corner, v in nc.items()}
    result = bytearray()
    for vertex in n:
        source = gc[reverse[tuple(vertex)]]
        values = (*[v*scale for v in source[:3]], vertex[3], *source[4:6], *vertex[6:])
        result.extend(struct.pack('>3hH2h4B', *values))
    return bytes(result)


def patch_assets(native, rel, symbols, commands):
    verified_rom(native)
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Unexpected English map source')
    pointers = donor_texture_pointers(rel, DONORS)
    for row, width in zip(DONORS, (64, 32)):
        model = rel[DATA_BASE+row.gc_model:DATA_BASE+row.gc_model+row.model_bytes]
        if model_texture_shape(model) != (width, 16, 4, 0):
            raise ValueError('English map texture shape changed')
    original = by_vrom(native)[VROM].extract(native)
    if sha256(original) != NATIVE_SHA:
        raise ValueError('Unexpected native map asset file')
    owner = by_vrom(native)[0x795350].extract(native)
    for address, expected in ((0x8088F400, 0xC42C00DC), (0x8088F410, 0x0C038107),
                              (0x808900DC, 0x3DCCCCCD)):
        if u32(owner, address-0x8088DBD0) != expected:
            raise ValueError('Native map geometry scale is no longer one tenth')
    if set(commands) != {'acre', 'dash'} or len(commands['acre']) != 56 or len(commands['dash']) != 48:
        raise ValueError('Invalid native map command sections')
    # Complete expected encodings bind the generated native macros to the patch.
    acre = struct.pack('>14I', 0xFD900000, 0x0C00B460, 0xF5900000, 0x07090250,
        0xE6000000, 0, 0xF3000000, 0x0707F400, 0xE7000000, 0,
        0xF5800400, 0x00F90250, 0xF2000000, 0x0007C03C)
    dash = struct.pack('>12I', 0xE7000000, 0, 0xFCFFFFFF, 0xFFFDF6FB,
        0xFA0000FF, 0x553737FF, 0x01004008, 0x0C006F10, 0x06000204, 0x00020604, 0xDF000000, 0)
    if commands != {'acre': acre, 'dash': dash}:
        raise ValueError('Compiled native map commands differ from fixed instruction specification')
    result = bytearray(original)
    changes = []
    def install(address, value):
        start = address-VROM
        if not 0 <= start <= len(result)-len(value):
            raise ValueError('Map artwork exceeds original asset allocation')
        result[start:start+len(value)] = value
        changes.append({'vrom': f'{address:08X}', 'bytes': len(value),
            'native_sha256': sha256(original[start:start+len(value)]), 'output_sha256': sha256(value)})
    for row, destination, width in zip(DONORS, (0xAB4B60, 0xAB8460), (64, 32)):
        donor = rel[DATA_BASE+row.gc:DATA_BASE+row.gc+width*8]
        converted = pack4(untile(donor, width, 16, 4))
        install(destination, converted+bytes(512-len(converted)))
    install(0xAB8260, bytes(512))
    for address, index in QUADS:
        donor = rel[DATA_BASE+VERTICES+index*16:DATA_BASE+VERTICES+(index+4)*16]
        install(address, port_quad(original[address-VROM:address-VROM+64], donor))
    install(0xAB48F8, acre)
    install(0xAB4940, dash+bytes(0x58-len(dash)))
    return bytes(result), {'version': 1, 'source_rel_sha256': REL_SHA256,
        'symbols_sha256': SYMBOLS_SHA256, 'native_asset_sha256': NATIVE_SHA,
        'asset_vrom': f'{VROM:08X}', 'asset_sha256': sha256(result), 'changes': changes,
        'donor_texture_pointers': {f'{k:08X}': f'{v:08X}' for k, v in pointers.items()},
        'command_source_sha256': sha256((ROOT/'overlays/map/artwork.c').read_bytes()),
        'command_sha256': {k: sha256(v) for k, v in commands.items()},
        'coordinate_format': 'Acre / row letter - column number', 'asset_bytes': len(result),
        'cpu_code_changed': False, 'selection_logic_changed': False, 'save_layout_changed': False,
        'status': 'English map art/layout installed; ordinary visual/navigation checks pending'}


def build(native, base, report, rel, symbols, commands):
    if sha256(base) != BASE_SHA or report.get('output_sha256') != BASE_SHA:
        raise ValueError('Map artwork requires complete shop-artwork/hardware-fix baseline')
    changed, profile = patch_assets(native, rel, symbols, commands)
    files = by_vrom(base)
    if sha256(files[VROM].extract(base)) != NATIVE_SHA:
        raise ValueError('Installed map assets already have unrelated changes')
    moved = {int(k, 16): int(v, 16) for k, v in report['vrom_relocations'].items()}
    replacements = {int(v, 16): files[moved.get(int(v, 16), int(v, 16))].extract(base)
                    for v in report['replacement_files']}
    additions = {int(v, 16): files[int(v, 16)].extract(base) for v in report['added_files']}
    if VROM in moved or VROM in additions:
        raise ValueError('Map asset ownership changed')
    replacements[VROM] = changed
    image = replace_dma(native, replacements, moved, additions)
    installed = by_vrom(image)
    if set(installed) != set(files) or len(image) != len(base):
        raise ValueError('Map artwork alters cartridge size or DMA identities')
    for vrom, entry in files.items():
        actual, expected = installed[vrom].extract(image), changed if vrom == VROM else entry.extract(base)
        if vrom == 0x19D40:
            actual, expected = actual[:16], expected[:16]
        if actual != expected or installed[vrom].index != entry.index:
            raise ValueError(f'Map artwork loses prior resource {vrom:08X}')
    ups = make_ups(native, image)
    if apply_ups(native, ups) != image:
        raise ValueError('Map artwork UPS reconstruction failed')
    result = copy.deepcopy(report)
    result.update(output_sha256=sha256(image), patch_sha256=sha256(ups),
        replacement_files=[f'{v:08X}' for v in sorted(replacements)], map_artwork=profile,
        release_status='English map/shop artwork candidate; ordinary visual/hardware checks pending')
    return image, ups, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/map-artwork-01')
    parser.add_argument('--commands', type=Path, default=ROOT/'build/map-artwork-commands')
    args = parser.parse_args()
    commands = compile_commands(args.commands)
    baseline = ROOT/'build/shop-artwork-02'
    image, ups, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (baseline/'animal-forest-halfwidth.z64').read_bytes(), json.loads((baseline/'build.json').read_text()),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(), commands)
    args.output.mkdir(parents=True, exist_ok=False)
    for name, value in {'animal-forest-halfwidth.z64': image, 'animal-forest-halfwidth.ups': ups,
        'build.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target:
            target.write(value)
    print(json.dumps({'output': str(args.output), 'sha256': report['output_sha256'], 'map_artwork': report['map_artwork']}))


if __name__ == '__main__':
    main()
