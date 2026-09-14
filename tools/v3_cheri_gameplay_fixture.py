"""Create a disposable Cheri gameplay seed; never alter the source town or ROM."""
import argparse
import importlib.util
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from apply_translation import write_new
from v3_save_codec import BANK, PAYLOAD, PROFILE, STATE

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = 'd489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60'


def create(source, rom, report):
    if sha256(source) != SOURCE_SHA or len(source) != BANK*2:
        raise ValueError('Game fixture requires the preserved source town')
    if sha256(rom) != report['output_sha256'] or not report.get('villager_rewards'):
        raise ValueError('Game fixture requires the complete current villager foundation')
    files = by_vrom(rom)
    blob = files[0x3F00000].extract(rom)
    state = blob[0x20:0x20+PROFILE]+bytes(STATE-PROFILE)
    if not state[234 >> 3] & (1 << (234 & 7)):
        raise ValueError('Current cartridge lacks Cheri profile support')
    row = next(r for r in report['villager_text']['imports'] if r['actor_id'] == 'E0EA')
    if (not row['initial_defaults_applied'] or row['personality'] != 1
            or report['villager_houses']['installed_villagers'] != ['E0EA']):
        raise ValueError('Cheri gameplay dependencies are incomplete')
    spec = importlib.util.spec_from_file_location('v3_save_reference', ROOT/'tests/test_v3_save_codec.py')
    reference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reference)
    output, changes = bytearray(), []
    # Only this throwaway fixture substitutes a resident. The additive ROM and
    # actual selection code do not replace any original villager identity.
    offset = 0x9F18+3*0x528
    for number in range(2):
        bank = bytearray(source[number*BANK:(number+1)*BANK])
        if bank[4:8] != b'NAFJ' or sum(struct.unpack('>'+str(PAYLOAD//2)+'H', bank[:PAYLOAD])) & 0xFFFF:
            raise ValueError('Invalid original town bank')
        if bank[offset:offset+2] != bytes.fromhex('e004') or bank[offset+11] != 1:
            raise ValueError('Changed known peppy resident fixture slot')
        fields = ((offset, bytes.fromhex('e0ea')), (offset+10, b'\xEA'),
                  (offset+0x4E5, bytes.fromhex(row['saved_default_key'])),
                  (offset+0x520, bytes.fromhex(row['clothing_identity']['native_item_id'])))
        for at, value in fields:
            changes.append({'bank': number, 'offset': at, 'before': bank[at:at+len(value)].hex(), 'after': value.hex()})
            bank[at:at+len(value)] = value
        bank[0xF86C+234//8] |= 1 << (234 & 7)
        output.extend(reference.reference_pack(bank, state))
    return bytes(output), {'source_save_sha256': SOURCE_SHA, 'rom_sha256': sha256(rom),
        'fixture_save_sha256': sha256(output), 'resident_slot': 3, 'actor_id': 'E0EA',
        'field_changes': changes, 'appearance_history_marks_cheri': True,
        'v3_profile_bound': True, 'natural_move_in_tested': False,
        'fixture_only_resident_substitution': True, 'source_save_modified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = ROOT/'local/rc2-save-report-g3O4lU/test.flash'
    image, receipt = create(source.read_bytes(), args.rom.read_bytes(),
                            json.loads((args.rom.parent/'build.json').read_text()))
    rtc = (ROOT/'build/v3-identity-arrival-01/test.rtc').read_bytes()
    if len(rtc) != 32:
        raise ValueError('Invalid retained daytime emulator RTC')
    args.output.mkdir(parents=True, exist_ok=False)
    write_new(args.output/'test.flash', image)
    write_new(args.output/'test.rtc', rtc)
    receipt['rtc_sha256'] = sha256(rtc)
    write_new(args.output/'fixture.json', (json.dumps(receipt, indent=2)+'\n').encode())
    if sha256(source.read_bytes()) != SOURCE_SHA:
        raise ValueError('Source town unexpectedly changed')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__': main()
