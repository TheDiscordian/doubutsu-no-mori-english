"""Source-guarded seasonal publication bridge and native helper reference audit."""

import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from check_keyboard_assembly import IMAGE
from notice_seasonal import GUARDS

ROOT = Path(__file__).resolve().parents[1]
START, END, HELPERS_END = 0x800A6384, 0x800A6544, 0x800A6548
SYMBOLS = {'af_notice_seasonal_bridge': START}
MODULE_HASH = '493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6'
REFERENCES = [[CODE_VROM, at-CODE_RAM, kind, target] for at, kind, target in (
    (0x800A64A0, 'branch', 0x800A64B4), (0x800A64BC, 'jump', START),
    (0x800A64D8, 'branch', 0x800A6490), (0x800A64F0, 'branch', 0x800A6500),
    (0x800A64F8, 'branch', 0x800A650C), (0x800A650C, 'jump', START),
    (0x800A66C8, 'jump', 0x800A63F8), (0x800A671C, 'jump', 0x800A6450))]


def call(target): return 0x0C000000 | ((target >> 2) & 0x3FFFFFF)


def scan_references(native):
    """Conservative aligned-word scan of every stored, decompressed DMA file.

    Report direct jumps, literal KSEG pointers, and nearby LUI/ADDIU or ORI
    pairs. These are static reference checks, not a general reachability proof.
    Relative branches are also checked in resident code, where PCs are known.
    """
    result = []
    for entry in by_vrom(native).values():
        if entry.pstart == 0xFFFFFFFF: continue
        data = entry.extract(native)
        words = [v[0] for v in struct.iter_unpack('>I', data[:len(data) & ~3])]
        for index, word in enumerate(words):
            offset, opcode = index*4, word >> 26
            target = None
            if opcode in (2, 3):
                target = 0x80000000 | ((word & 0x3FFFFFF) << 2)
                kind = 'jump'
            elif 0x80000000 <= word < 0xC0000000:
                target = word & ~0x20000000
                kind = 'literal'
            if target is not None and START <= target < HELPERS_END:
                result.append([entry.vstart, offset, kind, target])
            if opcode == 15 and (word & 65535) in (0x800A, 0xA00A):
                register = (word >> 16) & 31
                for after, low in enumerate(words[index+1:index+17], index+1):
                    if (low >> 21) & 31 != register or low >> 26 not in (9, 13): continue
                    value = low & 65535
                    if low >> 26 == 9 and value & 32768: value -= 65536
                    target = ((((word & 65535) << 16)+value) & 0xFFFFFFFF) & ~0x20000000
                    if START <= target < HELPERS_END:
                        result.append([entry.vstart, offset, 'address_pair', target, after*4])
            if entry.vstart == CODE_VROM and opcode in (1, 4, 5, 6, 7, 20, 21, 22, 23):
                displacement = word & 65535
                if displacement & 32768: displacement -= 65536
                target = CODE_RAM+offset+4+displacement*4
                if START <= target < HELPERS_END:
                    result.append([entry.vstart, offset, 'branch', target])
    return result


def source_hashes():
    return {name: sha256((ROOT/name).read_bytes()) for name in
            ('overlays/notice/seasonal_owner.s', 'tools/notice_seasonal_owner.py')}


def expected(loader):
    words = [0x27BDFF10, 0xAFBF00EC, 0x3C084146, 0x35084E53, 0xAFA800D4,
             0x8FA80100, 0xA7A800D8, 0x96480000, 0xA7A800DA, 0xAFA000DC,
             0x240800F3, 0xA3A800DF, 0xAFA000C4, 0xAFA000C8, 0xAFA000CC,
             0xAFA000D0, 0xAFA00010, 0xAFA00014, 0x27A40020, 0x27A500C4,
             0x27A600D4, 0x00003825, call(loader), 0,
             0x10400010, 0x27A80020, 0x02804825, 0x27AA0080,
             0x8D0B0000, 0x25080004, 0xAD2B0000, 0x150AFFFC, 0x25290004,
             call(0x800A5D30), 0x02802025, 0x92280000, 0x96490000,
             0x3C0A8013, 0xA1487919, 0xA549791A, 0x24020001,
             0x8FBF00EC, 0x03E00008, 0x27BD00F0]
    return struct.pack('>44I', *words).ljust(END-START, b'\0')


def verify_code(code):
    for lo, hi, digest in GUARDS + ((0x800A5CB0, 0x800A5DF4,
                                   '030e2ba9743dd8a9eae35b31fb62496f26a6d152e79374cd5c2c6a56cc356f70'),):
        if sha256(code[lo-CODE_RAM:hi-CODE_RAM]) != digest:
            raise ValueError('Changed native seasonal schedule, calendar fields, or reclaimed helpers')


def validate(data, report, module):
    loader = int(module['symbols']['af_npc_mail_load'], 16)
    if (loader != 0x80197BB4 or module['module_sha256'] != MODULE_HASH
            or report.get('version') != 1 or report.get('module_sha256') != MODULE_HASH
            or report.get('loader_ram') != loader or report.get('symbols') != SYMBOLS
            or report.get('sources') != source_hashes() or report.get('sha256') != sha256(data)
            or report.get('native_references') != REFERENCES
            or data != expected(loader)):
        raise ValueError('Changed native seasonal publication bridge')


def patch(code, data, report, module):
    verify_code(code)
    validate(data, report, module)
    output = bytearray(code)
    output[START-CODE_RAM:END-CODE_RAM] = data
    edits = {0x800A66C4: 0, 0x800A66C8: 0, 0x800A66CC: 0, 0x800A671C: 0,
             0x800A6778: call(START), 0x800A6780: 0x10400018, 0x800A6784: 0}
    for at, word in edits.items(): struct.pack_into('>I', output, at-CODE_RAM, word)
    return bytes(output)


def build(native, module, out):
    native = verified_rom(native)
    verify_code(by_vrom(native)[CODE_VROM].extract(native))
    references = scan_references(native)
    if references != REFERENCES:
        raise ValueError('Unaccounted reference to reclaimed seasonal helpers')
    out.mkdir(parents=True, exist_ok=True)
    loader = int(module['symbols']['af_npc_mail_load'], 16)
    common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}:/source:ro', '-v', f'{out}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                                capture_output=True, text=True, timeout=60)
        if result.returncode: raise ValueError(result.stdout+result.stderr)
        return result.stdout
    run('as', '-EB', '-mabi=32', '-march=vr4300', '-o', 'owner.o', '/source/overlays/notice/seasonal_owner.s')
    run('ld', '-EB', '-Ttext', f'0x{START:X}', '-e', 'af_notice_seasonal_bridge',
        f'--defsym=af_npc_mail_load=0x{loader:X}', '-o', 'owner.elf', 'owner.o')
    if run('nm', '--undefined-only', 'owner.elf').strip(): raise ValueError('Unresolved seasonal owner import')
    run('objcopy', '-O', 'binary', '-j', '.text', 'owner.elf', 'owner.bin')
    data = (out/'owner.bin').read_bytes()
    symbols = {}
    for line in run('nm', '--defined-only', 'owner.elf').splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2] in SYMBOLS: symbols[parts[2]] = int(parts[0], 16)
    report = {'version': 1, 'sha256': sha256(data), 'sources': source_hashes(), 'symbols': symbols,
              'loader_ram': loader, 'module_sha256': module['module_sha256'], 'toolchain_image': IMAGE,
              'native_references': references}
    (out/'owner.asm').write_text(run('objdump', '-d', 'owner.elf'))
    validate(data, report, module)
    (out/'owner.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--module', type=Path, default=ROOT/'build/notice-seasonal-runtime/module.json')
    parser.add_argument('--output', type=Path, default=ROOT/'build/noticeboard-seasonal/owner')
    parser.add_argument('--audit-only', action='store_true')
    args = parser.parse_args()
    native = verified_rom(args.rom.read_bytes())
    result = scan_references(native) if args.audit_only else build(native, json.loads(args.module.read_text()), args.output.resolve())
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
