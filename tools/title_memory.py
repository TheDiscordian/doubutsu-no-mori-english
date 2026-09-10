"""Title-only Expansion Pak reservation; all ordinary allocations remain native."""
import os
from pathlib import Path
import struct
import subprocess
import tempfile

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from check_keyboard_assembly import IMAGE

ROOT = Path(__file__).resolve().parents[1]
BOOT, BOOT_RAM = 0x1060, 0x80025C60
HELPER, HELPER_END, CALL = 0x800D6600, 0x800D66D0, 0x80057A10
BASE, LIMIT, GUARD = 0x80400010, 0x80450000, 0xAF54C0DE
SOURCE = 'overlays/title/allocation.s'
WARNING_SOURCE = 'overlays/title/allocation_warning.s'


def compile_helper(*, warning=False):
    with tempfile.TemporaryDirectory(prefix='af-title-memory-') as directory:
        output = Path(directory)
        docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
                  '-v', f'{ROOT}:/source:ro', '-v', f'{output}:/out', '-w', '/out', '--entrypoint']
        def run(tool, *args):
            subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                           check=True, capture_output=True, timeout=60)
        source = WARNING_SOURCE if warning else SOURCE
        run('as', '-EB', '-mabi=32', '-march=vr4300', '/source/'+source, '-o', 'memory.o')
        run('ld', '-EB', '-Ttext', f'0x{HELPER:X}', '-e', 'af_title_allocate', '-o', 'memory.elf', 'memory.o')
        run('objcopy', '-O', 'binary', '-j', '.text', 'memory.elf', 'memory.bin')
        result = (output/'memory.bin').read_bytes()
    if len(result) > HELPER_END-HELPER or len(result) & 3:
        raise ValueError('Title allocator exceeds the verified unused bootstrap tail')
    return result


def install(native, base, code, size, *, warning=False):
    if size & 15 or not 0 < size <= LIMIT-BASE-16:
        raise ValueError('Title image exceeds its dedicated Expansion Pak reservation')
    native_files, files = by_vrom(native), by_vrom(base)
    original = native_files[CODE_VROM].extract(native)
    if (sha256(original[0x800578E0-CODE_RAM:0x80057940-CODE_RAM])
            != '6f975d4f06b43143adb1cd0ed21677684b2384cfcbc5e80e020944599a7f3883'
            or code[0x800578E0-CODE_RAM:0x80057940-CODE_RAM]
            != original[0x800578E0-CODE_RAM:0x80057940-CODE_RAM]
            or code[HELPER-CODE_RAM:HELPER_END-CODE_RAM] != bytes(HELPER_END-HELPER)
            or struct.unpack_from('>I', code, CALL-CODE_RAM)[0] != 0x0C015E38):
        raise ValueError('Changed title allocation call, ordinary allocator, or bootstrap tail')
    # Normal/free paths and the fixed 80400000 heap ceiling remain executable as before.
    for start, end in ((0x800577F8, 0x80057848), (0x800D94F0, 0x800D9514)):
        if code[start-CODE_RAM:end-CODE_RAM] != original[start-CODE_RAM:end-CODE_RAM]:
            raise ValueError('Changed native title release or fixed game-heap ceiling')
    boot = bytearray(files[BOOT].extract(base))
    at = 0x80025D08-BOOT_RAM
    if boot[at:at+4] != bytes.fromhex('ac380318'):
        raise ValueError('Changed native forced-four-MiB boot store')
    # IPL3 already supplies detected RAM size. Do not manufacture eight MiB.
    boot[at:at+4] = bytes(4)
    helper = compile_helper(warning=warning)
    code[HELPER-CODE_RAM:HELPER-CODE_RAM+len(helper)] = helper
    struct.pack_into('>I', code, CALL-CODE_RAM, 0x0C000000 | ((HELPER >> 2) & 0x3FFFFFF))
    return bytes(boot), {'required_ram_bytes': 0x800000, 'base': BASE, 'limit': LIMIT,
                        'guard': GUARD, 'helper': HELPER, 'helper_bytes': len(helper),
                        'helper_sha256': sha256(helper), 'source_sha256': sha256((ROOT/(WARNING_SOURCE if warning else SOURCE)).read_bytes()),
                        'ordinary_heap_end': 0x80400000, 'title_alloc_type': 1,
                        'missing_expansion_pak': ('English power-off/install instruction screen; caller stopped without an exception'
                            if warning else 'Title allocation refused; this preview requires eight MiB')}
