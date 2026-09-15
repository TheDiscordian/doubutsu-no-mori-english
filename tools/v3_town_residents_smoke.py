"""Combined current native roster selection, resident construction, and schedules."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK
from v3_asset_loader import BLOB,BLOB_RAM
from v3_villager_selection_smoke import permutation


def exercise(debug,rom_path,record,tail_only=False):
    path=Path(rom_path);rom=path.read_bytes();report=json.loads((path.parent/'build.json').read_text())
    if sha256(rom)!=report['output_sha256'] or report.get('runtime_abi')!=57:
        raise ValueError('Town check requires the current complete-roster cartridge')
    files=by_vrom(rom);blob=files[BLOB].extract(rom);code=files[CODE_VROM].extract(rom)
    prefix=blob[:0xC000];package=blob[0x70000:0x7F000]
    rows={int(r['actor_id'],16)&255:r for r in report['villager_text']['imports']}
    native_looks=code[0x8010AF58-CODE_RAM:0x8010AF58-CODE_RAM+216]
    growth=files[0xE0D000].extract(rom)
    flags,modes,profile=0x80461E60,0x80461F60,0x80460020
    live,history,schedules,seconds=0x80130DB8,0x8013670C,0x80137444,0x80136FB8

    def check(label,address,expected):
        actual=debug.read_memory(address,len(expected))
        record({'town_check':label,'address':f'{address:08X}','bytes':len(expected),
                'assertion':'passed' if actual==expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(actual)})
        if actual!=expected:raise ValueError('Native town mismatch: '+label)

    def call(address,args=(),expected=None):
        result=debug.call(f'{address:08X}',list(args),return_address=MODULE_RAM+0x6480)
        record(result)
        if expected is not None and result['return_value']!=expected:
            raise ValueError(f'Unexpected town return at {address:08X}: {result["return_value"]} != {expected}')
        return result['return_value']

    check('complete startup prefix',BLOB_RAM,prefix)
    check('complete shared package including town predicate',0x80473000,package)
    size=0x6000;allocation=call(0x8009BFC0,[size]);population=allocation+16
    if allocation%16 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-size:
        raise ValueError('Town fixture allocation failed')
    edge=b'V3TW'*4
    guards=(allocation,population+15*0x528,allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    saved={at:debug.read_memory(at,size) for at,size in ((live,15*0x528),(history,32),
        (flags,20),(modes,20),(profile,192),(0x80464700,32),(0x80464800,238*4),
        (0x8003C590,4),(0x800419F0,4),(schedules,15*16),(seconds,4))}
    state=debug.read_memory(0x8046C000,864)
    try:
        debug.write_memory(live,bytes(15*0x528));debug.write_memory(history,bytes(32))
        maelle=rows[218];personality=maelle['personality']
        if not tail_only:
            for looks in range(6):
                wanted=native_looks.count(looks)+sum(r['personality']==looks for r in rows.values())
                call(0x800AA3A4,[looks],wanted)
            wanted=native_looks.count(personality)+sum(r['personality']==personality for r in rows.values())
            for address,value in ((flags,b'\0'),(modes,b'\0'),
                                  (profile+27,bytes((saved[profile][27]&~4,)))):
                original=debug.read_memory(address,1);debug.write_memory(address,value)
                call(0x800AA3A4,[personality],wanted-1)
                debug.write_memory(address,original)
        # One unseen identity forces the ordinary grow path without changing RNG.
        unseen=bytearray(b'\xFF'*32);unseen[27]&=~4
        debug.write_memory(history,unseen)
        if not tail_only:
            call(0x800AD6D4,[personality],218)
            check('fixed Maelle candidate identity',0x80464700,bytes(27)+b'\4'+bytes(4))
            call(0x800AA49C)
            check('unseen islander prevents premature history reset',history,unseen)
        # Free slots require FF home coordinates, not zero-filled records.
        call(0x800A7A9C,[live,15])
        call(0x800AD954,[personality],0)
        check('native grow constructs full islander identity',live,bytes.fromhex('E0DA'))
        check('native grow retains personality',live+11,bytes((personality,)))
        check('native grow installs actual red aloha shirt',live+0x520,bytes.fromhex('341A'))
        check('native grow installs full catchphrase reference',live+0x4E5,bytes.fromhex(maelle['saved_default_key']))
        check('native grow marks new arrival',live+0x525,b'\1')
        call(0x800AD6D4,[personality],0xFFFFFFFF)
        debug.write_memory(history,b'\xFF'*32);call(0x800AA49C)
        check('history reset retains imported resident',history,bytes(27)+b'\4'+bytes(4))
        debug.write_memory(live,bytes(15*0x528))

        def expected_population(seed,enabled):
            identities=list(range(216))+(list(rows) if enabled else [])
            table=permutation(seed,len(identities));result=[];used=set()
            for n in table:
                idx=identities[n]
                if idx<216 and growth[idx]:continue
                looks=native_looks[idx] if idx<216 else rows[idx]['personality']
                if looks not in used:
                    result.append(idx);used.add(looks)
                    if len(result)==6:break
            return table,result

        seed=next(n for n in range(1,1001) if 218 in expected_population(n,True)[1])
        for enabled,test_seed in ((False,1),(True,seed)):
            debug.write_memory(flags,bytes((enabled,))*20)
            debug.write_memory(history,bytes(32));debug.write_memory(population,bytes(15*0x528))
            debug.write_memory(0x8003C590,struct.pack('>I',test_seed))
            table,wanted_ids=expected_population(test_seed,enabled)
            call(0x800AA51C,[population,6,int(enabled)])
            check('retained native shuffle for selected roster',0x80464800,struct.pack('>'+str(len(table))+'I',*table))
            data=debug.read_memory(population,15*0x528)
            observed=[struct.unpack_from('>H',data,i*0x528)[0] for i in range(6)]
            wanted_ids=[0xE000+n for n in wanted_ids]
            record({'town_initial_population':[f'{n:04X}' for n in observed],
                    'expected':[f'{n:04X}' for n in wanted_ids],'seed':test_seed,
                    'imports_enabled':enabled,'assertion':'passed' if observed==wanted_ids else 'failed'})
            if observed!=wanted_ids or {data[i*0x528+11] for i in range(6)}!=set(range(6)):
                raise ValueError('Town initial population changed native personality/RNG rules')
            check('unused population slots retained',population+6*0x528,bytes(9*0x528))

        # One real islander per personality, using the unmodified native manager.
        representatives=(220,224,223,221,219,218)
        debug.write_memory(schedules,bytes(15*16));debug.write_memory(population,bytes(15*0x528))
        tables=[]
        for i,idx in enumerate(representatives):
            animal=population+i*0x528
            if rows[idx]['personality']!=i:raise ValueError('Changed representative personality')
            call(0x800AD8C4,[animal,idx]);call(0x800AEB50,[animal])
            table=struct.unpack_from('>I',code,0x8010BB10-CODE_RAM+i*4)[0]
            check('native schedule chosen from donor personality',schedules+i*16,struct.pack('>2I',animal,table))
            count,entries=struct.unpack_from('>2I',code,table-CODE_RAM)
            tables.append([struct.unpack_from('>2I',code,entries-CODE_RAM+j*8) for j in range(count)])
        for hour in (4,12,20):
            debug.write_memory(seconds,struct.pack('>I',hour*3600));call(0x800AEC74)
            for i,entries in enumerate(tables):
                kind=next(kind for kind,end in entries if hour*3600<end)
                check('personality schedule at '+str(hour),schedules+i*16+8,bytes((kind,0,kind,0))+bytes(4))
        debug.write_memory(schedules+9,b'\3');debug.write_memory(schedules+12,struct.pack('>I',2))
        call(0x800AEC74)
        check('existing timed event override retained',schedules+8,bytes((3,3,1,0))+struct.pack('>I',1))
        call(0x800AEBC8)
        check('existing forced outdoors retained',schedules+8,b'\0')
        call(0x800AEB9C,[population]);check('departing resident schedule released',schedules,bytes(4))
        check('unused schedule slots retained',schedules+6*16,bytes(9*16))
    finally:
        for at,data in saved.items():debug.write_memory(at,data)
    for at in guards:check('fixture and stack guard',at,edge)
    check('complete prefix restored',BLOB_RAM,prefix)
    check('shared package immutable',0x80473000,package)
    check('saved extension retained',0x8046C000,state)
    check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread',0x8003CE34,bytes(4))
    call(0x8009C040,[allocation])
    return {'native_roster_size':236,'selection_tail_only':tail_only,
            'native_initial_populations':2,'native_resident_construction':1,
            'personality_schedules':6,'schedule_times':3,'ordinary_gameplay_or_save_reload':False,
            'saved_data_written':False,'requires_checkpoint_restore':True}
