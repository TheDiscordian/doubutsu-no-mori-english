#!/usr/bin/env python3
"""Load the corrected creator from cartridge and execute its native word guard."""

import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, verified_rom
from flash_mail import SAVE_RAM, SAVE_BYTES
from npc_mail_capture import RAM, WORD_HASH, DESIGN_WORD_HASH, relocate, word_guard_offset
from npc_mail_loader import VROM, verify_configuration
from runtime_layout import MODULE_RAM, MODULE_VROM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD
from runtime_module import verify_test_module

ROOT = Path(__file__).resolve().parents[1]
EDGE = b'HERA'*4
BOOT_HELPERS = ((0x80026B44, 0x80026BC0), (0x8002B9C0, 0x8002BC00),
                (0x8002FE00, 0x8002FE74), (0x80034CE0, 0x80034D54))


def scenario(native, built, report):
    native = verified_rom(native)
    if sha256(built) != report['output_sha256'] or sha256(native) != report['source_sha256']:
        raise ValueError('Changed native-species test ROM')
    module, files = report['runtime_module'], by_vrom(built)
    verify_test_module(built, module)
    blob = files[VROM].extract(built)
    verify_configuration(files[MODULE_VROM].extract(built), blob, module)
    approval = module['npc_mail_loader']['overlay']
    if approval['word_sha256'] != DESIGN_WORD_HASH:
        raise ValueError('Native-species probe requires the corrected word profile')
    guards = {}
    for start, end in BOOT_HELPERS:
        at = 0x1060+start-0x80025C60
        expected = native[at:at+end-start]
        if built[at:at+end-start] != expected:
            raise ValueError('Changed original DMA/relocation/cache helper')
        guards[f'{start:08X}'] = expected.hex()
    request = {'module': module, 'blob': blob.hex(), 'guards': guards}
    return [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True},
            {'test_native_species_words': request}, {'load_state': True}, {'resume': True},
            {'wait': 2}, {'read': ['8019B200', 12], 'expect': bytes(12).hex()}]


def exercise(debug, request, record):
    read = debug.read_memory
    def write(at, data):
        debug.write_memory(at, data)
        record({'species_fixture_write': f'{at:08X}', 'bytes': len(data), 'sha256': sha256(data)})
    def check(label, at, expected):
        actual = read(at, len(expected))
        record({'species_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected: raise ValueError('Native species check failed: '+label)
    def call(at, args=(), expected=None, proof=None):
        result = debug.call(f'{at:08X}', list(args), verified_code=proof); record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Native species call {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    module, blob = request['module'], bytes.fromhex(request['blob'])
    verify_configuration(read(MODULE_RAM, RESERVATION), blob, module)
    approval = module['npc_mail_loader']['overlay']
    if approval['word_sha256'] != DESIGN_WORD_HASH: raise ValueError('Wrong native species word profile')
    n = approval['bytes']; data, reloc = blob[:n], blob[n:]
    symbols = approval['symbols']; text = struct.unpack_from('>I', reloc)[0]
    def boot(at, args, expected=None):
        proof = (at, bytes.fromhex(request['guards'][f'{at:08X}']))
        return call(at, args, expected, proof)
    def heap():
        call(0x8009C0C0, [0x8019B200, 0x8019B204, 0x8019B208])
        return read(0x8019B200, 12)
    saved = read(SAVE_RAM, SAVE_BYTES)
    session = int(module['symbols']['af_npc_mail_session'], 16)
    check('no active letter session', session, bytes(4))
    initial_heap = heap()
    size = (len(blob)+0x110+15) & ~15
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Native species fixture allocation failed')
    base = allocation+16
    descriptor, output = base+len(blob)+16, base+len(blob)+64
    guards = (allocation, base+len(blob), descriptor+16, output-16, output+32,
              allocation+size-16, TEST_STACK-0x1000, TEST_STACK+0x30)
    for at in guards: write(at, EDGE)
    write(descriptor, b'?'*12); write(output, b'!'*32)
    # Only expectations live in the request; executable/resource bytes reach
    # the allocation exclusively through the game's own cartridge DMA.
    boot(0x80026B44, [base, VROM, len(blob)], 0)
    check('complete cartridge image and relocations', base, blob)
    boot(0x8002B9C0, [base, base+n, RAM])
    boot(0x8002FE00, [base, n]); boot(0x80034CE0, [base, n])
    loaded = relocate(data, reloc, base, approval['imports'].values())
    check('complete native relocation agrees with independent model', base, loaded)
    def native(name, args, expected):
        return call(base+symbols[name], args, expected, (base, loaded[:text]))
    words, aliases = base+symbols['af_npc_word_data'], base+symbols['af_npc_alias_data']
    arguments = [descriptor, words, 11328, aliases, 6368]
    native('af_npc_mail_sources_init', arguments, 1)
    expected_descriptor = struct.pack('>3I', words, aliases, 0x41464353)
    check('corrected profile publishes complete descriptor', descriptor, expected_descriptor)
    native('af_npc_mail_source_word', [output+1, descriptor, 6, 0x21A], 1)
    check('complete herabuna field with unaligned edge guards', output,
          b'!\x10\0herabuna        '+b'!'*13)
    # The exact old resource digest must not validate the corrected words.
    digest_at = word_guard_offset(data, symbols, text)
    write(base+digest_at, bytes.fromhex(WORD_HASH))
    native('af_npc_mail_sources_init', arguments, 0)
    check('wrong profile retains prior descriptor', descriptor, expected_descriptor)
    write(base+digest_at, loaded[digest_at:digest_at+32])
    tail = words+11327; original_tail = read(tail, 1)
    write(tail, bytes((original_tail[0] ^ 1,)))
    native('af_npc_mail_sources_init', arguments, 0)
    check('damaged words retain prior descriptor', descriptor, expected_descriptor)
    write(tail, original_tail)
    native('af_npc_mail_sources_init', arguments, 1)
    check('restored profile recovers', descriptor, expected_descriptor)
    check('complete creator and resources restored', base, loaded)
    check('relocation records unchanged', base+n, reloc)
    check('entire save unchanged', SAVE_RAM, saved)
    check('no leaked letter session', session, bytes(4))
    for at in guards: check('allocation or stack guard', at, EDGE)
    check('resident guard', GUARD_ADDRESS, struct.pack('>4I', *([GUARD_WORD]*4)))
    call(0x8009C040, [allocation])
    if heap() != initial_heap: raise ValueError('Native species fixture did not release its complete allocation')
    record({'species_heap_restored': True})
    return {'native_species_cartridge_words': True, 'cartridge_dma_and_relocation': True,
            'creator_code_uploaded': False, 'complete_letter_delivery_tested': False,
            'requires_checkpoint_restore': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT/'build/design-items-pilot')
    parser.add_argument('--output', type=Path, default=ROOT/'build/design-species-scenario.json')
    args = parser.parse_args()
    plan = scenario((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                    (args.build/'animal-forest-halfwidth.z64').read_bytes(),
                    json.loads((args.build/'build.json').read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2)+'\n')
    print(json.dumps({'actions': len(plan), 'save_io': False, 'code_upload': False}))


if __name__ == '__main__': main()
