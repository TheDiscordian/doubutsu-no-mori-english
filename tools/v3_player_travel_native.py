"""Focused installed player-note execution on an isolated emulated Controller Pak.

This invokes native departure/arrival entries with controlled town identities.
It does not pretend to be a walked station trip or a hardware playthrough.
"""
import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_VROM, CODE_RAM, by_vrom, sha256
from apply_translation import write_new
from v3_player_travel_install import STATE, STATE_BYTES, RECORD_BYTES
from v3_asset_loader import BLOB

PLAYERS, FOREIGN, PASSPORT, PAK = 0x80126EC0, 0x801439A0, 0x80137C40, 0x80137960


def scenario(directory, *, both_note_kinds=False, loaded_world=False, console_visitor_only=False):
    if (both_note_kinds or console_visitor_only) and not loaded_world:
        raise ValueError('Both-note/console-visitor fixture requires a matching-ROM loaded-village checkpoint')
    if both_note_kinds and console_visitor_only:
        raise ValueError('Choose both-note transport or connected console visitor preparation')
    image=(directory/'animal-forest-v3-asset-loader.z64').read_bytes()
    report=json.loads((directory/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed current cartridge')
    e=report['equipment_resources'];t=e['player_travel'];files=by_vrom(image)
    checks=[];proofs=[];symbols=t['compiled']['symbols']
    for name,f in t['compiled']['fragments'].items():
        p=e['diaries']['packets']['ui'] if f['ram']<0x80700000 else e['harvest']['packet']
        at=p['physical']+f['ram']-p['ram']
        size=f['bytes'] if name=='io' else min(symbols[n] for n in
            ('town','selection','arrival','departing','received'))-f['ram']
        # A loaded village has legitimately prepared the bindings/selection
        # after the immutable body; do not compare mutable globals to ROM zeroes.
        checked_size=size if loaded_world else f['bytes']
        checks.append(dict(read=[f'{f["ram"]:08X}',checked_size],
            expect=image[at:at+checked_size].hex()))
        proofs.append(dict(ram=f['ram'],data=image[at:at+size].hex()))
    p=t['state_packet']
    if not loaded_world:
        checks.append(dict(read=[f'{p["ram"]:08X}',p['bytes']],
            expect=image[p['physical']:p['physical']+p['bytes']].hex()))
    core=files[CODE_VROM].extract(image)
    if console_visitor_only:
        # Native startup renews local acquaintance records against the actual
        # residents. Prepare that same consistent host after its controlled ID
        # change, so a later restart does not clean up an impossible fixture.
        first,last=0x800A6E40,0x800A6F48
        body=core[first-CODE_RAM:last-CODE_RAM]
        if sha256(body)!='f238e0e3afa057b613fba69d863b1c5ec842ba49ab694d7bc74c4a038625fb2d':
            raise ValueError('Changed original local-acquaintance renewal routine')
        proofs.append(dict(ram=first,data=body.hex()))
    for h in t['hooks']:
        if CODE_RAM<=h['address']<0x80400000:
            if core[h['address']-CODE_RAM:h['address']-CODE_RAM+8].hex()!=h['after']:
                raise ValueError('Changed installed native hook')
        checks.append(dict(read=[f'{h["address"]:08X}',8],expect=h['after']))
    # These ownership guards border the newly used padding and visitor record.
    for ram,data in ((STATE-16,bytes(16)),
            (0x806A7FF0,bytes.fromhex(e['diaries']['packets']['ui']['guard'])),
            (0x806A8FF0,bytes.fromhex(e['diaries']['packets']['ui']['guard'])),
            (0x807F7B40,bytes.fromhex('41464852')*4)):
        # Title startup has not used a furniture bank yet, so the model pool's
        # lazy guard is still zero. The visitor initializer must not touch it.
        if ram!=STATE-16 or not loaded_world:
            checks.append(dict(read=[f'{ram:08X}',16],expect=data.hex()))
    consumers={h['symbol']:h['address'] for h in t['hooks'] if h.get('owner')}
    if consumers:
        consumers.update(af_carried_record=0x800B88EC,af_carried_owned=0x80469AD4)
        # The public catalogue query is outside the runner's ordinary call
        # range. Authenticate its complete immutable source body, rather than
        # widening that range or trusting whatever happens to be loaded.
        blob=files[BLOB].extract(image);n=report['collection']['code']['bytes']
        proofs.append(dict(ram=0x804699C0,data=blob[0x99C0:0x99C0+n].hex()))
    request=dict(rom_sha256=sha256(image),symbols=symbols,state=t['state_packet'],proofs=proofs,
        consumers=consumers,both_note_kinds=both_note_kinds,
        console_visitor_only=console_visitor_only,
        equipment_resources={'scene_arena':e['scene_arena']})
    actions=[{'wait':2 if loaded_world else 16},*checks,{'save_state':True},
        {'pause_game_thread':True},{'test_v3_player_travel':request}]
    if not console_visitor_only:
        actions += [{'load_state':True},{'wait':1},{'read':['8003CE34',4],'expect':'00000000'}]
    return actions


def exercise(debug, request, record, out):
    s=request['symbols'];read=debug.read_memory
    model_boundary=read(STATE-16,16)
    proofs=[(p['ram'],bytes.fromhex(p['data'])) for p in request['proofs']]
    def call(name,args=(),expected=None):
        address=s[name] if isinstance(name,str) else name
        proof=next((p for p in proofs if p[0]<=address<p[0]+len(p[1])),None)
        r=debug.call(f'{address:08X}',args,verified_code=proof)
        record(r)
        if expected is not None and r['return_value']!=expected:
            record(dict(pak_error=read(PAK+0x70,4).hex(),loaded=read(0x80138E44,4).hex(),
                state_header=read(STATE,16).hex()))
            raise ValueError(f'Installed call {name} returned {r["return_value"]}, expected {expected}')
        return r['return_value']
    def write(address,data):
        debug.write_memory(address,data)
    def check(label,address,expected):
        actual=read(address,len(expected))
        record(dict(player_travel_check=label,passed=actual==expected,address=f'{address:08X}',
            bytes=len(expected),expected_sha256=sha256(expected),actual_sha256=sha256(actual)))
        if actual!=expected:raise ValueError('Installed player-travel mismatch: '+label)
    call('af_v3_travel_prepare',expected=1)
    if request.get('console_visitor_only'):
        # Reuse the loaded town's actual player, pockets, and imported records.
        # Only the host identity is controlled to make the native arrival
        # wrapper choose its genuine foreign-player path; no NES/diary progress
        # is fabricated and the final checkpoint restores the test town.
        check('loaded native home player',0x80136FD8,struct.pack('>I',PLAYERS))
        check('loaded native resident index',0x80136EA3,b'\x00')
        home=read(PLAYERS,4*0xBD0)
        call(0x800B7F78,[PLAYERS],1)
        call(0x8007A070,expected=PAK);call(0x800790C0,[0],1)
        call(0x800793B8,[PLAYERS,0x80130DB8,PAK],1)
        write(PLAYERS,bytes((home[0]^1,)))
        host=read(PLAYERS,4*0xBD0)
        call(0x800A6E40)
        check('native acquaintance renewal retains host player records',PLAYERS,host)
        record(dict(native_host_acquaintance_renewal=True,
            original_startup_routine='800A6E40',controlled_host_identity=True,
            game_code_changed=False))
        call(0x800B8D64,[4,PAK],1)
        check('console visitor has the complete original private record',FOREIGN,home[:0xBD0])
        check('console visitor selected by native arrival',0x80136FD8,struct.pack('>I',FOREIGN))
        check('console visitor retains foreign index',0x80136EA3,b'\x04')
        check('console arrival leaves host residents unchanged',PLAYERS,host)
        check('console visitor cache admitted',STATE,struct.pack('>2I',0x41465431,1))
        check('console visitor storage guard',STATE+16+RECORD_BYTES,
            struct.pack('>4I',*([0xAF54524C]*4)))
        return dict(native_console_visitor_prepared=True,actual_native_arrival=True,
            original_loaded_player_records=True,controlled_host_identity=True,
            ordinary_station_visit_tested=False,requires_checkpoint_restore=True)
    # Construct valid native identities through the real clear routine and the
    # documented PersonalID layout, not the host test's reduced validation stub.
    for slot in range(4):
        p=PLAYERS+slot*0xBD0;call(0x800B7ADC,[p])
        identity=f'Player{slot}'.encode().ljust(12,b' ')+struct.pack('>2H',slot+1,0x3001)
        write(p,identity);call(0x800B7F78,[p],1)
    home=read(PLAYERS,4*0xBD0)
    call(0x8007A070,expected=PAK);call(0x800790C0,[0],1)
    write(0x80136FD8,struct.pack('>I',PLAYERS))
    write(0x80136EA3,b'\x00')
    call(0x800793B8,[PLAYERS,0x80130DB8,PAK],1)
    check('native passport shape remains unchanged',PASSPORT+2,b'AFV3PT')
    # Simulate the host's distinct residents without changing save ownership.
    for slot in range(4):write(PLAYERS+slot*0xBD0,bytes([home[slot*0xBD0]^1]))
    host=read(PLAYERS,4*0xBD0)
    call(0x800B8D64,[4,PAK],1)
    check('arrival binds the exact traveller',FOREIGN,home[:16])
    check('native arrival selects the actual visitor',0x80136FD8,struct.pack('>I',FOREIGN))
    check('native arrival retains foreign player index',0x80136EA3,b'\x04')
    check('host residents unchanged',PLAYERS,host)
    check('full visitor cache admitted',STATE,struct.pack('>2I',0x41465431,1))
    consumers=request.get('consumers',{})
    if consumers:
        # Enter the actual retained public chain, not only the transport API.
        for item in (0x3224,0x34BF,0x2649,0x2749,0x2244,0x2B10,0x2040):
            call(consumers['af_carried_owned'],[FOREIGN,item],0)
            call(consumers['af_carried_record'],[item])
            call(consumers['af_carried_owned'],[FOREIGN,item],1)
        for item in (0x3227,0x3C03,0x30FF,0x2041,0x2042,0x2043):
            call(consumers['af_carried_owned'],[FOREIGN,item],1)
    else:
        call('af_v3_travel_visitor_collect',[FOREIGN,0x3224,1],1)
    call('af_v3_travel_creature_collect',[FOREIGN,0x2328,1],1)
    call('af_v3_travel_visitor_paper',[FOREIGN,1],1)
    # Record-only mutation checks transport; diary UI/NES sessions are separate.
    write(STATE+16+2196+104+17,b'Z');write(STATE+16+564+23,b'\xAE')
    acquired=read(STATE+16,RECORD_BYTES)
    call('af_v3_pak_native_status',[0x8019AE00,0,PAK,0],1)
    check('status never rewinds visitor progress',STATE+16,acquired)
    call(0x800793B8,[FOREIGN,0x80130DB8,PAK],1)
    check('departure never credits host residents',PLAYERS,host)
    write(PLAYERS,home)
    call(0x800B8D64,[0,PAK],1)
    check('native return selects the matching home resident',0x80136FD8,struct.pack('>I',PLAYERS))
    check('native return restores home player index',0x80136EA3,b'\x00')
    check('return restores the current editable visitor record',STATE+16,acquired)
    check('other native private records remain unchanged',PLAYERS+0xBD0,home[0xBD0:])
    call('af_v3_travel_prepare',expected=1)
    # Verify restored diary/console bytes through the actual guarded getters.
    diary=call('af_v3_diary_data');console=call('af_v3_console_player_data')
    if consumers:
        for item in (0x3224,0x34BF,0x2649,0x2749,0x2244,0x2B10,0x2040):
            call(consumers['af_carried_owned'],[PLAYERS,item],1)
    check('returned diary page',diary+16+104+17,b'Z')
    check('returned console progress',console+23,b'\xAE')
    check('visitor storage guard',STATE+16+RECORD_BYTES,struct.pack('>4I',*([0xAF54524C]*4)))
    check('model-pool boundary unchanged',STATE-16,model_boundary)
    out.mkdir(parents=True,exist_ok=False)
    write_new(out/'records.bin',acquired)
    if request.get('both_note_kinds'):
        from pak_mail import PROBE_CODE
        from v3_save_runtime_smoke import diagnostic_arena_checks
        # After returning home, use the original stored-letter writer's first
        # stage. Its next stage saves FlashRAM and is outside this Pak check.
        write(0x80136FD8,struct.pack('>I',PLAYERS))
        write(0x80136EA3,b'\x00')
        size=0x8200
        # Like the existing stored-letter fixture, this check needs a loaded
        # village. The title scene has consumed both its arena and the global
        # heap, so it cannot supply this ordinary native allocation.
        allocation=call(0x8009BFC0,[size])
        arena_checks=diagnostic_arena_checks(request,allocation,size)
        for at,wanted in arena_checks:check('both-note native allocation owner',at,wanted)
        probe,buffer=allocation+16,allocation+0x100
        chip=buffer
        edge=b'V3PK'*4
        guards=(allocation,probe+len(PROBE_CODE),chip+0x8000)
        write(probe,PROBE_CODE)
        for at in guards:write(at,edge)
        write(buffer+0x6700,edge)
        write(buffer,bytes(0x6700))
        call(0x8009C384,[buffer+0x52])
        empty_letter=read(buffer+0x52,0xA4)
        write(buffer+2,b' '*80)
        write(buffer+0x52,empty_letter*160)
        stage=buffer+0x6710
        write(stage,b'\x00')
        call(0x80079D50,[buffer,PAK,stage],0)
        check('original stored-letter writer advances to its save stage',stage,b'\x01')
        backup=read(buffer,0x6700)
        if sum(struct.unpack('>13184H',backup))&65535:
            raise ValueError('Original stored-letter writer produces an invalid checksum')
        write(buffer,b'!'*0x6700)
        call(0x80079EA4,[buffer,PAK],1)
        check('complete stored-letter note after traveller round trip',buffer,backup)
        check('letter read never replaces the returning imported record',STATE+16,acquired)
        call('af_v3_pak_native_status',[0x8019AE00,1,PAK,buffer],1)
        check('stored-letter status retains its complete contents',buffer,backup)
        check('stored-letter status never rewinds imported records',STATE+16,acquired)
        call(0x8007919C,[PAK,0])
        call('af_v3_pak_native_status',[0x8019AE00,0,PAK,0],1)
        check('passport remains readable beside stored letters',PASSPORT+2,b'AFV3PT')
        check('both notes preserve returned ownership and editable records',STATE+16,acquired)
        check('complete stored-letter buffer guard before raw export',buffer+0x6700,edge)
        # Reuse the letter buffer for the larger raw chip only after all letter
        # checks. The complete native note is already retained in host memory.
        result=debug.call(f'{probe:08X}',[chip],verified_code=(probe,PROBE_CODE))
        record(result)
        if result['return_value']!=0:raise ValueError('Native raw Controller Pak export fails')
        exported=read(chip,0x8000)
        write_new(out/'test.pak',exported)
        write_new(out/'backup.bin',backup)
        write_new(out/'passport.bin',read(PASSPORT,0x1200))
        for at in guards:check('both-note fixture allocation guard',at,edge)
        check('other residents retained after both note kinds',PLAYERS+0xBD0,home[0xBD0:])
        check('traveller guard after both note kinds',STATE+16+RECORD_BYTES,
            struct.pack('>4I',*([0xAF54524C]*4)))
        call(0x8009C040,[allocation])
        for at,wanted in arena_checks:check('both-note native allocation owner retained',at,wanted)
        record(dict(both_native_note_kinds='passed',native_raw_pak_sha256=sha256(exported),
            complete_backup_sha256=sha256(backup),backup_bytes=len(backup),
            passport_and_backup_share_one_device=True,raw_export_before_checkpoint_restore=True))
    return dict(installed_native_player_transport=True,emulated_controller_pak_io=True,
        imported_acquisition_and_return=True,diary_ui_played=False,console_game_played=False,
        actual_collection_consumers=bool(consumers),both_native_note_kinds=bool(request.get('both_note_kinds')),
        walked_station_visit=False,hardware_tested=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--both-note-kinds',action='store_true')
    p.add_argument('--loaded-world',action='store_true',help='Use a matching-ROM loaded-village checkpoint')
    p.add_argument('--console-visitor-only',action='store_true',help='Prepare the native visitor for connected console checks')
    args=p.parse_args()
    if (args.both_note_kinds or args.console_visitor_only) and not args.loaded_world:
        p.error('Both-note/console-visitor fixtures require --loaded-world and its matching-ROM checkpoint')
    if args.both_note_kinds and args.console_visitor_only:
        p.error('Choose both-note transport or connected console visitor preparation')
    write_new(args.output,(json.dumps(scenario(args.build,
        both_note_kinds=args.both_note_kinds,loaded_world=args.loaded_world,
        console_visitor_only=args.console_visitor_only),indent=2)+'\n').encode())
