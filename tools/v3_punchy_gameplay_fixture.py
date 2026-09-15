"""Copy the preserved town into an isolated Punchy house/gameplay fixture."""
import argparse
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import struct
import time

from aflib import by_vrom, sha256
from apply_translation import write_new
from v3_asset_loader import BLOB
from v3_cheri_gameplay_fixture import SOURCE_SHA
from v3_save_codec import BANK, PAYLOAD
from v3_save_clothing import PROFILE, STATE

ROOT = Path(__file__).resolve().parents[1]
ANIMAL = 0x9F18 + 3*0x528


def create(source, rom, report):
    if len(source) != 2*BANK or sha256(source) != SOURCE_SHA:
        raise ValueError('Punchy fixture requires the preserved source town')
    if sha256(rom) != report['output_sha256'] or not report['clothing']['punchy_defaults_enabled']:
        raise ValueError('Punchy fixture requires current installed house/default support')
    row = next(r for r in report['villager_text']['imports'] if r['actor_id']=='E0ED')
    profile = bytes.fromhex(report['save_runtime']['profile_hex'])
    if (len(profile)!=PROFILE or not profile[237//8] & (1<<(237&7))
            or not profile[183]&128 or not profile[58]&16
            or row['applied_clothing_id']!='34BF' or row['personality']!=2
            or 'E0ED' not in report['villager_houses']['installed_villagers']
            or by_vrom(rom)[BLOB].extract(rom)[0x20:0x20+PROFILE] != profile):
        raise ValueError('Punchy fixture has incomplete selected dependencies')
    spec = importlib.util.spec_from_file_location('v3_clothing_reference',ROOT/'tests/test_v3_save_clothing.py')
    reference = importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
    state = profile + bytes(STATE-PROFILE)
    output, changes = bytearray(), []
    for number in range(2):
        bank = bytearray(source[number*BANK:(number+1)*BANK])
        if (bank[4:8]!=b'NAFJ' or sum(struct.unpack('>'+str(PAYLOAD//2)+'H',bank[:PAYLOAD]))&65535
                or bank[ANIMAL:ANIMAL+2]!=bytes.fromhex('E004') or bank[ANIMAL+11]!=1):
            raise ValueError('Changed copied-town resident slot or checksum')
        # An existing resident's outdoor house is stored independently of its
        # identity record. Preserve the location and assign the same fixture ID.
        home=bank[ANIMAL+0x4E0:ANIMAL+0x4E5]
        if home!=bytes.fromhex('0004030B07'):
            raise ValueError('Changed copied-town home coordinates')
        _,bx,bz,x,z=home
        house=0x62A8+((bz-1)*5+bx-1)*512+((z-1)*16+x)*2
        if bank[house:house+2]!=bytes.fromhex('5004'):
            raise ValueError('Changed copied-town outdoor house identity')
        # Fixture-only substitution at the existing, navigable acre-4/3 house.
        # The ROM remains additive. At-home state is seeded, not schedule proof.
        edits = ((ANIMAL,bytes.fromhex('E0ED')), (ANIMAL+10,bytes((237,2))),
                 (ANIMAL+0x4E5,bytes.fromhex(row['saved_default_key'])),
                 (ANIMAL+0x520,bytes.fromhex('34BF')), (ANIMAL+0x524,b'\x01'),
                 (house,bytes.fromhex('50ED')))
        for at,value in edits:
            changes.append({'bank':number,'offset':at,'before':bank[at:at+len(value)].hex(),
                            'after':value.hex()})
            bank[at:at+len(value)] = value
        bank[0xF86C+237//8] |= 1<<(237&7)
        output.extend(reference.reference_pack(bank,state))
    return bytes(output), {'source_save_sha256':SOURCE_SHA,'fixture_save_sha256':sha256(output),
        'rom_sha256':sha256(rom),'actor_id':'E0ED','resident_slot':3,'save_format':2,
        'fixture_only_resident_substitution':True,'seeded_at_home':True,
        'matching_outdoor_house_identity':'50ED','house_cell_offset':house,
        'natural_move_in_or_schedule_tested':False,'field_changes':changes,
        'player_pockets_and_other_residents_unchanged':True,'source_save_modified':False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    source = ROOT/'local/rc2-save-report-g3O4lU/test.flash'
    data,receipt = create(source.read_bytes(),args.rom.read_bytes(),
                         json.loads((args.rom.parent/'build.json').read_text()))
    staged = datetime(2026,9,10,12,0)
    bcd = lambda n:(n//10)*16+n%10
    rtc = bytearray(b'\xFF'*32)
    rtc[16:24] = bytes((0,0,0x92,0x10,4,9,0x26,1))
    if rtc[16:24] != bytes((bcd(staged.second),bcd(staged.minute),bcd(staged.hour)|128,
        bcd(staged.day),bcd((staged.weekday()+1)%7),bcd(staged.month),bcd(staged.year%100),1)):
        raise ValueError('Invalid isolated midday RTC')
    rtc[24:] = int(time.time()).to_bytes(8,'big')
    args.output.mkdir(parents=True,exist_ok=False)
    write_new(args.output/'test.flash',data);write_new(args.output/'test.rtc',rtc)
    receipt.update(isolated_clock=staged.isoformat(),rtc_sha256=sha256(rtc))
    write_new(args.output/'fixture.json',(json.dumps(receipt,indent=2)+'\n').encode())
    if sha256(source.read_bytes())!=SOURCE_SHA:raise ValueError('Source town changed')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
