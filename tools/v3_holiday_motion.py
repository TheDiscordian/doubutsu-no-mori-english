"""Connect the holiday actor's shared movement services to the installed registry.

Reuse complete art/cane resources. Actor activation still requires the event,
conversation, and exercise providers; installing these services cannot enable it.
"""
import copy
import json
import struct
import zlib
from aflib import by_vrom,sha256
from apply_translation import write_new
from v3_asset_loader import ROOT,compile_part
from v3_furniture_pipeline import Source
from v3_import_storage import jump
from v3_npc_draw import relocation_offsets
from v3_npc_registry import RAM,SIZE
from v3_keyframes import _animation,CHANNELS
import v3_physical_resources as physical

VROM,RELOC,OWNER=0x8681F0,0x878550,0x809735B0
NATIVE=(
    ('animation',0x809749D0,0x80974CFC,'01311c0c6ff63fa982ad88c237b805e233bbdd250b2b71adea56e601fa80c577'),
    ('wander',0x8097D460,0x8097DBD0,'e8010ff0be18fbfa6e6a58c15414c0bd8ad41edf6117230fcaee23eb1cd3dd6d'),
    ('fatigue',0x8097CBD0,0x8097CC34,'1bd0619fbfdf3edd4d527beec7e6405f3287903bd45c245547491cb31fb619b4'),
    ('mood',0x80974184,0x809741B4,'4bc9c7ab5c4cd6905b51114fb8f6688009dfd1c195d3d1c5653ca9145418f8f3'),
    ('range',0x80976F74,0x8097703C,'439ff1b0e3086fac5d952f75702ce9c03ac1817f8ca43358edfe42f9f2f8d167'),
    ('combine',0x80974FD8,0x809750E0,'3b698d405137135ab6d58a56ace5ed61cb9c7c742161f3d68c80d4adfdf10fe0'),
    ('schedule',0x8097EFAC,0x8097F060,'2c636c780c647ce3627443352b3961d848274364acb8d4516c01de081abb320d'),
)
REFERENCES={
    'local/ac-decomp/src/actor/npc/ac_npc_think_wander.c_inc':'58cf9bff118c7c9f810e626fb03935b0fd2e8f7e5ada632e9d3bbdb07f387353',
    'local/ac-decomp/src/actor/npc/ac_npc_anime.c_inc':'3c7d000ed811480b0e7a1b114a5f032c0fcb071b6dbf19f43a6ac8431e1bb6ce',
    'local/ac-decomp/src/actor/npc/ac_npc_schedule.c_inc':'c8b7eaf020bd4e74d2730bb6e438442269322900bdd21bcd8ebba8340b53cd4f',
    'local/ac-decomp/src/actor/npc/ac_npc_data.c_inc':'be24a91f5c6d9e5d5318e1c24820ed8504571c13117d8c6c5828717d00cf684a',
    'local/ac-decomp/src/game.c':'15bf6436c2c6cfd7263781d2f0044fa29fa8238ee82531522d186b8a6c1d5096',
    'local/ac-decomp/include/game.h':'8ef3ddeee5180c1424bc8f03783cc422c845bce97329d47efa7bad193c7a8cc8',
    'upstream/af/src/code/game.c':'cd4d79562acfe1184e0d250bf0d58447779d287ed9361b9abd6c1975c591357d',
}
SOURCES=('tools/v3_holiday_motion.py','overlays/v3/holiday_motion.h',
    'overlays/v3/holiday_motion.c','overlays/v3/holiday_motion_native.c',
    'overlays/v3/holiday_motion_original.S','overlays/v3/holiday_motion.ld',
    'overlays/v3/holiday_actor.h','overlays/v3/holiday_npc.h','overlays/v3/npc_registry.h',
    'tools/v3_asset_loader.py','tools/v3_furniture_install.py')


def contract(base,source):
    files=by_vrom(base);owner=files[VROM].extract(base)
    for path,digest in REFERENCES.items():
        if sha256((ROOT/path).read_bytes())!=digest:raise ValueError('Changed holiday movement reference: '+path)
    for name,start,end,digest in NATIVE:
        if sha256(owner[start-OWNER:end-OWNER])!=digest:raise ValueError('Changed native holiday movement: '+name)
    # Identical arm/mouth selection tables: subtype three is only boolean here.
    parts=[]
    for i,ptr in enumerate(struct.unpack_from('>4I',owner,0x80982994-OWNER)):
        expected=bytearray(27)
        if i&2:expected[18:22]=bytes([1]*4)
        if i&1:expected[23:25]=bytes([2]*2)
        if owner[ptr-OWNER:ptr-OWNER+27]!=expected:raise ValueError('Changed complete native NPC joint selection')
        parts.append(dict(address=ptr,sha256=sha256(expected)))
    # Check all arrays and all control fields, not an animation-index coincidence.
    motions=[]
    for index,name in ((5,'wait1'),(67,'clap1')):
        donor=source.names['cKF_ba_r_npc_1_'+name][0][0]
        desc=_animation(source,donor,joints=26,record_bytes=64)
        ptr,bank=struct.unpack_from('>2I',owner,0x80981974-OWNER+index*8)
        address=0xE0E000+(ptr&0xFFFFFF)
        entry=next(e for e in files.values() if e.vstart<=address<e.vend)
        data=entry.extract(base);at=address-entry.vstart
        if data[at+16:at+64]!=source.data[donor+16:donor+64]:raise ValueError('Different native motion controls: '+name)
        for j,label in enumerate(CHANNELS):
            r=desc['arrays'][label];p=struct.unpack_from('>I',data,at+j*4)[0]
            begin=0xE0E000+(p&0xFFFFFF)-entry.vstart
            if p>>24!=6 or not r or begin<0 or sha256(data[begin:begin+r['bytes']])!=r['source_sha256']:
                raise ValueError('Different complete native motion: '+name+'/'+label)
        motions.append(dict(name=name,index=index,bank=bank,donor=desc,native_vrom=address))
    return dict(native=[dict(name=n,start=a,end=b,sha256=s) for n,a,b,s in NATIVE],
        references=REFERENCES,parts=parts,reused_motions=motions,
        walk_probability=[6,10],native_schedule=4,native_think=1,
        source_update_ticks=1,native_normal_update_ticks=2,native_tick_address=0x80145048,
        callback_cadence='once per native world update; timed waits consume elapsed 60 Hz ticks')


def patch(base,symbols):
    files=by_vrom(base);data=bytearray(files[VROM].extract(base));rel=files[RELOC].extract(base)
    slots=relocation_offsets(rel,len(data));head=list(struct.unpack_from('>5I',rel))
    rows=list(struct.unpack_from('>'+str(head[4])+'I',rel,20));removed=[];hooks=[]
    for address,before,symbol,kind in (
        (0x809749D0,bytes.fromhex('27bdffb0afb0002c'),'af_holiday_motion_animation','entry'),
        (0x8097DB14,bytes.fromhex('0c25f63200000000'),'af_holiday_motion_decide','call'),
        (0x80983598,bytes.fromhex('8097db60'),'af_holiday_motion_wander_init','pointer')):
        at=address-OWNER;target=symbols[symbol]
        if not RAM+0x2000<=target<RAM+0xA000 or target&3 or data[at:at+len(before)]!=before:
            raise ValueError('Changed native motion hook or target')
        if kind=='entry':
            if {at,at+4}&slots:raise ValueError('Animation trampoline prologue needs relocation')
            after=struct.pack('>2I',jump(target),0)
        else:
            # Only the exact native call/table-pointer relocation is removed.
            matches=[]
            for row in rows:
                section=row>>30;offset=row&0xFFFFFF
                start=(0,head[0],head[0]+head[1])[section-1]
                if start+offset==at:matches.append(row)
            if len(matches)!=1 or matches[0]>>24&63!=(4 if kind=='call' else 2):
                raise ValueError('Missing exact native motion relocation')
            rows.remove(matches[0]);removed.append(matches[0])
            after=struct.pack('>I',jump(target,link=True) if kind=='call' else target)+before[4:]
        data[at:at+len(after)]=after
        hooks.append(dict(address=address,before=before.hex(),after=after.hex(),symbol=symbol,kind=kind))
    head[4]=len(rows)
    reloc=(struct.pack('>5I',*head)+struct.pack('>'+str(len(rows))+'I',*rows)).ljust(len(rel)-4,b'\0')+rel[-4:]
    if relocation_offsets(reloc,len(data))!=slots-{h['address']-OWNER for h in hooks if h['kind']!='entry'}:
        raise ValueError('Unexpected native motion relocation change')
    return {VROM:bytes(data),RELOC:reloc},dict(hooks=hooks,removed_relocations=removed,
        owner_sha256=sha256(data),relocation_sha256=sha256(reloc))


def install(base,prior,blob,core,output):
    del blob,core
    equipment=copy.deepcopy(prior['equipment_resources']);npc=equipment['npc_extra']
    if not npc['installed'] or npc.get('motion'):raise ValueError('NPC motion needs the installed registry without duplicate services')
    physical.verify(base,prior['physical_resources'])
    packet=npc['packet'];data=bytearray(base[packet['physical']:packet['physical']+SIZE])
    if len(data)!=SIZE or sha256(data)!=packet['sha256'] or any(data[0x2000:0xA000]):
        raise ValueError('Changed NPC packet or occupied actor code')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    description=contract(base,source)
    cane=npc['record']['cane']
    if sha256(data[cane['offset']:cane['offset']+cane['bytes']])!=cane['sha256']:
        raise ValueError('Changed complete resident cane motion')
    bindings=dict(af_v3_npc_extra_owned=npc['code']['symbols']['af_v3_npc_extra_owned'],
        af_holiday_cane=cane['header'],af_holiday_keyframe_init=0x80052584,
        af_holiday_unit=0x800885A8,af_holiday_block=0x80088710,
        af_holiday_random_native=0x8002C9AC,af_holiday_sound_native=0x800D1D08)
    directory=output/'holiday-motion'
    code,compiled=compile_part('holiday_motion',directory/'code',link_symbols=bindings,
        extra_sources=('overlays/v3/holiday_motion_native.c','overlays/v3/holiday_motion_original.S'))
    data[0x2000:0x2000+len(code)]=code
    changed,hooks=patch(base,compiled['symbols'])
    # Replace the existing fixed-size packet only in the new cartridge. Every
    # resource, registry byte, pool guard, and actor flag outside code is retained.
    replacement=next(copy.deepcopy(r) for r in prior['physical_resources'] if r['id']==packet['id'])
    replacement['sha256']=sha256(data)
    records=[replacement if r['id']==replacement['id'] else copy.deepcopy(r) for r in prior['physical_resources']]
    npc['packet'].update(sha256=sha256(data),crc32=zlib.crc32(data))
    npc['record']['cane']['runtime_bound']=True
    npc['motion']=dict(format='AFV3-HOLIDAY-MOTION-1',contract=description,code=compiled,
        bindings=bindings,**hooks,installed=True,actor_provider_bindings_pending=True,
        native_execution_verified=False,previous_packet_sha256=prior['equipment_resources']['npc_extra']['packet']['sha256'],
        retained_registry_and_resources=True,additional_resident_bytes=0)
    npc['pending']=['Event owner and actor providers','English messages and demo transport','Separate exercise/card route']
    npc['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    write_new(directory/'motion.json',(json.dumps(npc['motion'],indent=2)+'\n').encode())
    write_new(directory/'packet.bin',data)
    return equipment,changed,dict(physical_resources=records),[(dict(replacement,
        previous_sha256=prior['equipment_resources']['npc_extra']['packet']['sha256']),bytes(data))]
