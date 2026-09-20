"""Current native extended save entries, format migration, and player clearing."""
import importlib.util
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_npc_draw_smoke import boot_proofs
from v3_save_clothing import PROFILE, RAM, RUNTIME_BYTES, STATE, VROM
from v3_save_codec import BANK


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['clothing'].get('save_extension'):
        raise ValueError('Clothing save probe requires the current assembled cartridge')
    if report['save_codec']['format_version']==3:
        return reward_exercise(debug,rom,report,record)
    spec = importlib.util.spec_from_file_location('clothing_save_reference',
        Path(__file__).resolve().parents[1]/'tests/test_v3_save_clothing.py')
    reference = importlib.util.module_from_spec(spec); spec.loader.exec_module(reference)
    legacy_bank, state_data = reference.fixture()
    expected_bank = bytes(reference.reference_pack(legacy_bank, state_data))
    profile_data = bytes.fromhex(report['save_runtime']['profile_hex'])
    if profile_data != bytes(state_data[:PROFILE]): raise ValueError('Fixture profile differs from current imports')
    blob = by_vrom(rom)[BLOB].extract(rom)
    proofs, edge = boot_proofs(rom), b'V3SC'*4

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'clothing_save_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected: raise ValueError('Clothing save mismatch: '+label)

    def call(address, args, expected=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM+0x6480,
                            verified_code=proofs.get(address))
        record(result)
        if expected is not None and result['return_value'] != expected & 0xFFFFFFFF:
            raise ValueError('Unexpected clothing-save return value')
        return result['return_value']

    check('complete startup prefix', BLOB_RAM, blob[:0xC000])
    check('separate extended codec loaded completely', RAM, blob[VROM-BLOB:])
    runtime = struct.pack('>4I', 0xAF535633, 0, 0, 0)+profile_data+bytes(640)+bytes.fromhex('AF53C0DE')*4
    check('complete expanded native runtime initialization', 0x8046C000, runtime)
    size = 0x11000
    allocation = call(0x8009BFC0, [size])
    if allocation % 16 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Clothing save fixture allocation failed')
    bank, profile, state, output, bridge = (allocation+x for x in (16, 0x10040, 0x10140, 0x10500, 0x10C00))
    guards = (allocation, bank+BANK, profile+PROFILE, state+STATE, output+STATE,
              allocation+size-16, TEST_STACK-0x800, TEST_STACK+0x40)
    for at in guards: debug.write_memory(at, edge)
    wrappers, entries = bytearray(), {}
    for name in ('check', 'pack', 'collect'):
        entries[name] = bridge+len(wrappers)
        target = report['save_codec']['code']['symbols']['af_v3_save_'+name]
        wrappers.extend(struct.pack('>4I', 0x08000000 | (target >> 2 & 0x3FFFFFF), 0, 0, 0))
    debug.write_memory(bridge, bytes(wrappers))
    call(0x8002FE00, [bridge, len(wrappers)])
    call(0x80034CE0, [bridge, len(wrappers)])
    for address in entries.values(): proofs[address] = (bridge, bytes(wrappers))
    debug.write_memory(bank, bytes(legacy_bank))
    debug.write_memory(profile, profile_data)
    debug.write_memory(state, bytes(state_data))
    call(entries['check'], [bank, BANK, profile, output], 0)
    check('legacy migration initializes all ownership empty', output, profile_data+bytes(640))
    call(entries['pack'], [bank, BANK, state], 1)
    check('complete format-2 bank matches independent encoder', bank, expected_bank)
    call(entries['check'], [bank, BANK, profile, output], 1)
    check('all furniture and clothing ownership restored', output, bytes(state_data))
    missing = bytearray(profile_data); missing[183] = 0
    debug.write_memory(profile, bytes(missing))
    debug.write_memory(output, b'\xA5'*STATE)
    call(entries['check'], [bank, BANK, profile, output], -7)
    check('missing clothing leaves destination intact', output, b'\xA5'*STATE)
    debug.write_memory(profile, profile_data)
    old_bank, old_state = reference.legacy.fixture()
    debug.write_memory(bank, bytes(reference.legacy.reference_pack(old_bank, old_state)))
    call(entries['check'], [bank, BANK, profile, output], 1)
    check('format-1 migration retains furniture and initializes clothing', output,
          profile_data+bytes(old_state[160:])+bytes(128))
    debug.write_memory(state, profile_data+bytes(640))
    for player in range(4):
        call(entries['collect'], [state, player, 0x34BF, 1], 1)
        call(entries['collect'], [state, player, 0x34BC, 0], -7)
    check('clothing ownership never alters furniture rotation bits', state,
          profile_data+bytes(512)+bytes(state_data[PROFILE+512:]))
    call(entries['collect'], [state, 0, 0x3225, 1], 1)
    call(entries['collect'], [state, 0, 0x3227, 0], 1)
    # Exercise the changed native player-clear hook on this disposable machine.
    # The complete emulator checkpoint restores the original private data.
    try:
        debug.write_memory(0x8046C010, bytes(state_data))
        call(0x800B7ADC, [0x80126EC0+3*0xBD0])
        cleared = bytearray(state_data)
        cleared[PROFILE+3*128:PROFILE+4*128] = bytes(128)
        cleared[PROFILE+512+3*32:] = bytes(32)
        check("native player clear removes only that player's furniture and clothing ownership",
              0x8046C000, runtime[:16]+bytes(cleared)+runtime[-16:])
    finally:
        debug.write_memory(0x8046C000, runtime)
    for at in guards: check('fixture guard', at, edge)
    check('expanded runtime restored', 0x8046C000, runtime)
    check('resident prefix intact', BLOB_RAM, blob[:0xC000])
    check('extended codec intact', RAM, blob[VROM-BLOB:])
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, [allocation])
    return {'native_public_save_entries': 3, 'clothing_players': 4,
            'format_1_migration_tested': True, 'format_2_complete_encoding_tested': True,
            'native_player_clear_tested': True, 'runtime_bytes': RUNTIME_BYTES,
            'device_io_performed': False, 'ordinary_clothing_save_reload_tested': False,
            'requires_checkpoint_restore': True}


def reward_exercise(debug,rom,report,record):
    """Format-aware shared persistence probe using the actual loaded cartridge."""
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from tests.test_v3_save_rewards import fixture,reference_pack
    from tests import test_v3_save_clothing as clothing
    from tests import test_v3_save_codec as legacy
    receipt=report['equipment_resources']['player_actions']['reward_state']
    blob=by_vrom(rom)[BLOB].extract(rom);proofs=boot_proofs(rom);assertions=0
    profile_data=bytes.fromhex(report['save_runtime']['profile_hex'])
    legacy_bank,state_data=fixture(profile_data);expected_bank=reference_pack(legacy_bank,state_data)
    size,working=receipt['runtime_bytes'],receipt['working_state_bytes'];edge=b'V3RW'*4
    if (size,working)!=(912,880):raise ValueError('Changed shared reward-state layout')
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(reward_save_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',observed_sha256=sha256(actual),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Reward save mismatch: '+label)
        assertions+=1
    def call(at,args=(),want=None):
        nonlocal assertions
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proofs.get(at))
        if want is not None:
            result['assertion']='passed' if result['return_value']==want&0xFFFFFFFF else 'failed'
        record(result)
        if want is not None:
            if result['return_value']!=want&0xFFFFFFFF:raise ValueError('Unexpected reward save return')
            assertions+=1
        return result['return_value']
    check('complete startup-loaded prefix',BLOB_RAM,blob[:0xC000])
    at=receipt['resource_vrom']-BLOB;extra=blob[at:at+receipt['resource_bytes']]
    check('complete active extra-code package',RAM,extra)
    check('expanded save-state guard',receipt['guard_ram'],bytes.fromhex('AF53C0DE')*4)
    saved={at:debug.read_memory(at,n) for at,n in ((0x8046C000,size),(0x80126EA0,0xF980),
        (0x80136FD8,4),(0x80123E10,0x154))}
    allocation=call(0x8009BFC0,[0x13000])
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-0x13000:
        raise ValueError('Reward save allocation failed')
    bank,profile,state,out,bridge,actor=(allocation+x for x in (16,0x10040,0x10140,0x10500,0x10C00,0x11000))
    guards=(allocation,bank+BANK,profile+192,state+working,out+working,actor-16,
        actor+0x1400,allocation+0x13000-16,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    targets={name:report['save_codec']['code']['symbols']['af_v3_save_'+name] for name in ('check','pack','collect')}
    targets.update(flag=receipt['code']['symbols']['af_v3_reward_flag'],settle=receipt['code']['symbols']['af_v3_reward_settle'])
    targets.update({name:report['save_runtime']['code']['symbols']['af_v3_save_'+name] for name in ('reset','commit')})
    wrappers=bytearray();entries={}
    for name,target in targets.items():
        entries[name]=bridge+len(wrappers)
        wrappers.extend(struct.pack('>4I',0x08000000|(target>>2&0x3FFFFFF),0,0,0))
    debug.write_memory(bridge,wrappers);call(0x8002FE00,[bridge,len(wrappers)]);call(0x80034CE0,[bridge,len(wrappers)])
    for address in entries.values():proofs[address]=(bridge,bytes(wrappers))
    try:
        debug.write_memory(profile,profile_data);debug.write_memory(state,state_data)
        for version,data,want in ((0,legacy_bank,profile_data+bytes(688)),
                (2,clothing.reference_pack(legacy_bank,state_data[:832]),state_data[:832]+bytes(48))):
            debug.write_memory(bank,data);call(entries['check'],[bank,BANK,profile,out],int(version!=0))
            check(f'format-{version} migration clears only new flags',out,want)
        old,old_state=legacy.fixture();debug.write_memory(bank,legacy.reference_pack(old,old_state))
        call(entries['check'],[bank,BANK,profile,out],1)
        check('format-1 migration preserves original ownership',out,profile_data+old_state[160:]+bytes(176))
        debug.write_memory(bank,legacy_bank);call(entries['pack'],[bank,BANK,state],1)
        check('complete format-3 bank matches independent encoder',bank,expected_bank)
        call(entries['check'],[bank,BANK,profile,out],1);check('complete four-player flags decoded',out,state_data)
        damaged=bytearray(expected_bank);damaged[legacy.PAYLOAD+0x369]=1;legacy.seal_extension(damaged)
        debug.write_memory(bank,damaged);debug.write_memory(out,b'\xA5'*working)
        call(entries['check'],[bank,BANK,profile,out],-9);check('invalid flags leave destination intact',out,b'\xA5'*working)
        debug.write_memory(bank,expected_bank)
        call(entries['reset'],[],1);call(entries['commit'],[bank,0x80126EA0,0xF980])
        check('native commit restores extended working state',0x8046C010,state_data)
        check('native commit retains full original payload',0x80126EA0,expected_bank[:0xF980])
        expected=bytearray(state_data)
        for player in range(4):
            call(entries['flag'],[player,0,31,0],int(player==3))
            typ=(player+1)%4;call(entries['flag'],[player,1,typ,1],1)
            expected[832+player*12+8]|=1<<typ
        check('event and celebration flags remain independent',0x8046C010,expected)
        debug.write_memory(actor,bytes(0x1400));debug.write_memory(actor+0xD18,bytes(4))
        debug.write_memory(0x80136FD8,struct.pack('>I',0x80126EC0+2*0xBD0))
        call(0x8005EB74,[0x80123E10]);call(0x8005DC9C,[73,0x168])
        call(entries['settle'],[actor,0]);expected[832+2*12+8]|=1
        check('real settlement records only the active celebration',0x8046C010,expected)
        check('real settlement stops the native fanfare',0x80123E10+14,struct.pack('>H',1))
        call(0x800B7ADC,[0x80126EC0+3*0xBD0])
        expected[192+3*128:192+4*128]=bytes(128)
        expected[192+512+3*32:832]=bytes(32);expected[832+3*12:880]=bytes(12)
        check('native player deletion clears only its catalogues and flags',0x8046C010,expected)
        check('expanded state guard survives commit and deletion',receipt['guard_ram'],bytes.fromhex('AF53C0DE')*4)
        for at in guards:check('reward save fixture guard',at,edge)
        check('resident prefix unchanged',BLOB_RAM,blob[:0xC000]);check('extra code unchanged',RAM,extra)
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        for at,data in saved.items():debug.write_memory(at,data)
        call(0x8009C040,[allocation])
    for at,data in saved.items():check('live state restored',at,data)
    return dict(native_reward_save=True,assertions=assertions,format_1_2_and_legacy_migration=True,
        complete_format_3_encoding=True,native_commit_and_player_clear=True,native_settlement=True,
        runtime_bytes=size,working_bytes=working,test_only_jump_wrappers=True,
        device_io_performed=False,ordinary_save_restart_tested=False,hardware_tested=False,
        requires_checkpoint_restore=True)
