"""Native owner/continuation regression with isolated quest and player fixtures.

Runs the real reward, dispatcher, wait, takeout request, message loader, and
normal continuation/closure instructions. It does not animate an ordinary NPC
or walk the tutorial. All temporary singleton pointers require checkpoint restore.
"""
import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from accent_mail_overlays import Overlay
from first_job_progression import ROOT, SPEC, patch
from npc_mail_show import source, relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD
from runtime_module import module_command_info, verify_test_module
from textbanks import Bank, banks
from textcodec import tokenize

WINDOW = 0x80142410
QUEST_VROM, QUEST_RELOC, QUEST_RAM = 0x849B50, 0x84C8A0, 0x80954D80
EDGE = b'FJOB'*4


def word(value):
    return struct.pack('>I', value)


def scenario(native, built, report, *, letters=False):
    if sha256(built) != report['output_sha256']:
        raise ValueError('First-job fixture ROM differs from report')
    verify_test_module(built, report['runtime_module'])
    files, original = by_vrom(built), by_vrom(native)
    before, reloc = source(native, 'first_job')
    if letters and report.get('first_job_progression', {}).get('letter_advice') is not True:
        raise ValueError('Letter-advice fixture requires its installed correction')
    after = patch(native, before, reloc, letter_advice=report.get('first_job_progression', {}).get('letter_advice', False))
    if files[SPEC.vrom].extract(built) != after or files[SPEC.relocation].extract(built) != reloc:
        raise ValueError('First-job fixture requires the installed correction')
    code, native_code = files[CODE_VROM].extract(built), original[CODE_VROM].extract(native)
    guards = {}
    for a, b in ((0x8007B44C, 0x8007B49C), (0x8009D1F0, 0x8009D200),
                 (0x8009DBA4, 0x8009DBB0), (0x8009DD04, 0x8009DDE4),
                 (0x8009E658, 0x8009E6B8), (0x8009E908, 0x8009E94C),
                 (0x800A01C8, 0x800A03B0), (0x800A6978, 0x800A69C8),
                 (0x800AD084, 0x800AD0B8), (0x800B8B08, 0x800B8B8C)):
        data = code[a-CODE_RAM:b-CODE_RAM]
        expected = bytearray(native_code[a-CODE_RAM:b-CODE_RAM])
        if a == 0x8009E658:
            if struct.unpack_from('>I', expected, 0x10)[0] != 0x28A12DE8:
                raise ValueError('Unexpected native message count comparison')
            struct.pack_into('>I', expected, 0x10, 0x28A12DEA)  # Existing two appended general messages.
        if data != expected:
            raise ValueError(f'Changed native first-job dependency {a:08X}')
        guards[f'{a:08X}'] = data.hex()
    quest = files[QUEST_VROM].extract(built)
    # The installed manager may contain unrelated translation hooks. Bind the
    # exact installed image, and independently require these original handlers.
    for a, b in ((0x80955668, 0x8095573C), (0x80955DD8, 0x80955E60), (0x80955F08, 0x80955F38),
                 (0x80956760, 0x809567C0)):
        if quest[a-QUEST_RAM:b-QUEST_RAM] != original[QUEST_VROM].extract(native)[a-QUEST_RAM:b-QUEST_RAM]:
            raise ValueError('Changed native quest dispatch/takeout/wait')
    moved = {int(k, 16): int(v, 16) for k, v in report['vrom_relocations'].items()}
    bank = banks(native)[0]
    entries = Bank('message', 0, 0, files[moved.get(bank.data_vrom, bank.data_vrom)].extract(built),
                   files[moved.get(bank.table_vrom, bank.table_vrom)].extract(built)).entries()
    numbers = (list(range(0x907, 0x913))+[0xA26, 0x2B47] if letters else
               list(range(0x8EF, 0x8FB))+[0x921, 0x2B05, 0x2B06])
    request = {'original_owner': before.hex(), 'owner': after.hex(), 'relocation': reloc.hex(),
               'quest': quest.hex(), 'quest_relocation': files[QUEST_RELOC].extract(built).hex(),
               'messages': {str(n): entries[n].hex() for n in numbers}, 'guards': guards,
               'info': module_command_info(native), 'letters': letters}
    # The IPL bootstrap is loaded from the physical cartridge before main code.
    def bootstrap(at, size):
        offset = at-0x80025C60+0x1060
        data = native[offset:offset+size]
        if built[offset:offset+size] != data:
            raise ValueError('Changed physical native bootstrap dependency')
        return data.hex()
    request['loader'] = bootstrap(0x800262D0, 0xF0)
    if sha256(bytes.fromhex(request['loader'])) != '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Changed native overlay loader')
    request['cache'] = {str(at): bootstrap(at, 0x80) for at in (0x8002FE00, 0x80034CE0)}
    return [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True},
            {'test_first_job_progression': request}, {'load_state': True}, {'resume': True}, {'wait': 2},
            {'read': [f'{GUARD_ADDRESS:08X}', 16], 'expect': word(GUARD_WORD).hex()*4}]


def exercise(debug, request, record):
    read, write = debug.read_memory, debug.write_memory
    assertions = calls = 0

    def check(label, at, expected):
        nonlocal assertions
        actual = read(at, len(expected))
        record({'first_job_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected:
            raise ValueError('First-job native mismatch: '+label)
        assertions += 1

    def call(at, args=(), expected=None, proof=None):
        nonlocal calls
        if str(at) in request['cache']:
            proof = (at, bytes.fromhex(request['cache'][str(at)]))
        result = debug.call(f'{at:08X}', args, verified_code=proof)
        record(result)
        calls += 1
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'First-job return {at:08X}: {result["return_value"]}, expected {expected}')
        return result['return_value']

    for at, data in request['guards'].items():
        check('unchanged native dependency', int(at, 16), bytes.fromhex(data))
    size = 0x7800
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('First-job fixture allocation failed')
    owner, quest, manager, client, animal, pointers, setting, registered, private, message, cursor, orders = (
        allocation+o for o in (0x10, 0xD00, 0x4100, 0x4A00, 0x4B90, 0x4BB0,
                              0x4BE0, 0x4C80, 0x4D00, 0x5900, 0x5D30, 0x5D50))
    write(allocation, bytes(size))
    edges = (allocation, manager-16, client-16, private-16, message-16, message+0x410,
             orders-16, orders+216, allocation+size-16, TEST_STACK-0x800, TEST_STACK+0x30)
    for at in edges:
        write(at, EDGE)
    original_owner, installed_owner, owner_reloc = (bytes.fromhex(request[k]) for k in
                                                   ('original_owner', 'owner', 'relocation'))
    quest_data, quest_reloc = (bytes.fromhex(request[k]) for k in ('quest', 'quest_relocation'))
    quest_spec = Overlay(QUEST_RAM, len(quest_data), struct.unpack_from('>5I', quest_reloc))
    quest_image = relocate_verified_data(quest_spec, quest_data, quest_reloc, quest)
    loader_proof = (0x800262D0, bytes.fromhex(request['loader']))
    for vrom, spec, base, data, reloc in ((SPEC.vrom, SPEC, owner, installed_owner, owner_reloc),
                                       (QUEST_VROM, quest_spec, quest, quest_data, quest_reloc)):
        call(0x800262D0, [vrom, vrom+len(data), spec.ram, spec.ram+spec.resident_bytes,
                         base, base+spec.resident_bytes, len(reloc)], proof=loader_proof)
        check('complete native loaded overlay and BSS', base,
              relocate_verified_data(spec, data, reloc, base))
    quest_proof = (quest, quest_image[:quest_spec.sections[0]])
    old_globals = {at: read(at, n) for at, n in ((WINDOW, 0x330), (0x80136FD8, 4), (0x80104A70, 4))}
    write(0x80136FD8, word(private))
    write(0x80104A70, word(orders))
    entries = {int(n): bytes.fromhex(data) for n, data in request['messages'].items()}
    info = [tuple(v) for v in request['info']]
    expected_orders = bytearray(216)
    for row, slot, value in ((4, 1, 2), (5, 0, 0x1004), (5, 1, 7)):
        struct.pack_into('>H', expected_orders, 16+row*20+slot*2, value)

    def load(number):
        call(0x8009E658, [WINDOW, number], 1)
        check('complete English cartridge record', message,
              struct.pack('>4I', 1, number, len(entries[number]), 0)+entries[number])

    def ending(number):
        commands = [t for t in tokenize(entries[number], info) if t.kind == 'cmd']
        links = [t for t in commands if t.data[1] == 14]
        if len(links) > 1 or commands[-1].data not in (b'\x7f\x00', b'\x7f\x01'):
            raise ValueError('Unexpected first-job fixture message flow')
        for token in links:
            write(cursor, word(token.offset))
            call(0x800A21C0, [WINDOW, cursor], 0)
        end = commands[-1]
        write(WINDOW+0x28C, bytes(4))
        write(cursor, word(end.offset))
        call(0x800A21C0, [WINDOW, cursor], 2)
        check('native end cursor', WINDOW+0x2A0, word(end.offset))
        write(WINDOW+0x2B4, word(2))  # Normal message at its reached ending.
        write(WINDOW+0x2B0, bytes(4))
        return int.from_bytes(links[0].data[2:], 'big') if links else None

    def advance():
        # Use the native forced-advance input to avoid timing a controller press
        # while the graph thread is checkpoint-paused. No return is substituted.
        write(WINDOW+0x2CC, word(1))
        write(WINDOW+0x2D0, bytes(4))
        call(0x800A01C8, [WINDOW, 0])

    completed = []
    letters = request.get('letters', False)
    for fixed, looks in [(False, 4)]+[(True, n) for n in ((2, 4, 5) if letters else range(6))]:
        image = relocate_verified_data(SPEC, installed_owner if fixed else original_owner, owner_reloc, owner)
        write(owner, image)
        call(0x8002FE00, [owner, len(image)])
        call(0x80034CE0, [owner, len(image)])
        proof = (owner, image[:SPEC.sections[0]])
        write(manager, bytes(0x8D0))
        write(client, bytes(0x180))
        write(client+2, b'\x03')
        write(client+0x174, word(animal))
        write(animal, struct.pack('>HH6sBB', 0xE000, 0x1234, b'TOWN  ', 0, looks))
        write(pointers, word(client))
        write(manager+0x178, word(pointers))
        write(manager+0x17C, word(pointers+4))
        write(pointers+4, word(registered))
        write(manager+0x186, bytes((10 if letters else 7,)))
        write(manager+0x1D4, word(3)+struct.pack('>H', 0x1004))
        write(manager+0x1F0, word(setting))  # target + 0x30: set_data_p.
        write(setting, bytes(0x60))
        write(setting+0x14+5*4, word(0x908 if letters else 0x8F0))
        write(registered, b'\x46\x18'+bytes(46))
        write(manager+0x214, word(registered))
        write(manager+0x8B8, word(quest+0x80955F08-QUEST_RAM))
        write(private, bytes(0xBD0))
        write(WINDOW, bytes(0x330))
        write(WINDOW+12, word(message))
        write(orders, bytes(216))
        root = (0x908 if letters else 0x8F0)+looks*2
        call(owner+0x8091D594-SPEC.ram, [manager], proof=proof)
        check('native first handoff request' if not letters else 'letter advice requests no furniture',
              orders, bytes(216) if letters else bytes(expected_orders))
        check('native reward item and inventory slot' if not letters else 'letter advice retains inventory',
              private+0x1A, bytes(2) if letters else b'\x10\x04')
        check('quest progress completed', registered+1, b'\x00')
        check('advice selected for personality', WINDOW+0x2C4, word(root))
        check('owner step after completion', manager+0x186, bytes((11 if fixed else (12 if letters else 7),)))
        inventory_after = read(private, 0xBD0)
        load(root)
        traversed = [root]
        target = ending(root)
        if target is not None:
            write(orders, bytes(216))
            call(quest+0x80956760-QUEST_RAM, [manager], 1, proof=quest_proof)
            call(owner+0x8091D594-SPEC.ram, [manager], proof=proof)
            check('continuation retained' if fixed else 'original next-message overwrite reproduced',
                  WINDOW+0x2C4, word(target if fixed else (0 if letters else root)))
            check('no repeated handoff' if fixed else 'original repeated handoff reproduced',
                  orders, bytes(216) if fixed or letters else bytes(expected_orders))
            if letters and not fixed:
                record({'first_job_original_letter_target_overwritten': True,
                        'expected_target': target, 'actual_target': 0, 'root': root})
                continue
            advance()
            next_number = target if fixed else root
            check('normal transition loads intended full record', message,
                  struct.pack('>4I', 1, next_number, len(entries[next_number]), 0)+entries[next_number])
            traversed.append(next_number)
            if not fixed:
                record({'first_job_original_loop_reproduced': True, 'messages': traversed})
                continue
            ending(target)
        write(orders, bytes(216))
        call(quest+0x80956760-QUEST_RAM, [manager], 0, proof=quest_proof)
        advance()
        check('normal conversation disappearance requested', WINDOW+0x2AC, word(4))
        check('no handoff at final end', orders, bytes(216))
        check('inventory retained after conversation', private, inventory_after)
        check('quest remains completed', registered+1, b'\x00')
        for at in edges:
            check('fixture or stack guard', at, EDGE)
        completed.append({'looks': looks, 'messages': traversed, 'final_disappear_requested': True})
        record({'first_job_corrected_conversation': completed[-1]})
    for at, data in old_globals.items():
        write(at, data)
        check('temporary singleton restored', at, data)
    check('resident guard', GUARD_ADDRESS, word(GUARD_WORD)*4)
    call(0x8009C040, [allocation])
    return {'first_job_original_loop_reproduced': not letters,
            'first_job_original_letter_target_overwritten': letters,
            'first_job_corrected_conversations': completed,
            'native_calls': calls, 'assertions': assertions, 'normal_actor_gameplay': False,
            'requires_checkpoint_restore': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT/'build/v0-first-job-fix-01')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--letters', action='store_true')
    args = parser.parse_args()
    actions = scenario((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (args.build/'animal-forest-halfwidth.z64').read_bytes(), json.loads((args.build/'build.json').read_text()),
        letters=args.letters)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'scenario': str(args.output), 'actions': len(actions),
                      'corrected_personalities': 3 if args.letters else 6, 'letters': args.letters}))


if __name__ == '__main__':
    main()
