"""Install complete existing native NPC controllers under additive identities.

Controller records bind verified complete images, relocations, profiles, and
event remaps. The shared registry, pool, art, identity readers, spawn paths, and
startup are installed together. Existing native actors are never replaced.
"""
import copy
import json
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from apply_translation import write_new
from fortune_actor import ActorImage
from gc_text import decoder_tables,decode_gc
from npc_mail_show import relocate_verified_data
from runtime_module import module_command_info
from textbanks import Bank
from textcodec import encode,LATIN
from text_provenance import validate
from v3_asset_loader import ROOT,MODULE,MODULE_RAM
from v3_console_disk_install import reservations
from v3_furniture_pipeline import Source
from v3_holiday_dialogue import STRING_FILES
from v3_import_storage import jump
from v3_npc_registry import RAM,SIZE,TABLE,refresh_renderer
from v3_registry import SPECIAL_NPCS
import v3_physical_resources as physical

IDENTITIES=0xA400
BRIDGES=0xA4A0
PROVIDERS={
    # The complete English actor already owns transactional fortune generation,
    # interrupted-payment recovery, and save/destroy refund. Clone that current
    # implementation, not an obsolete Japanese overlay or a new letter engine.
    'english-fortune':dict(donor_name=0xD03D,donor_profile=0x84,
        vrom=0x03600000,relocation=0x03608000,ram=0x809E5740,bytes=8048,
        sections=(6944,0,1104,0,77),actor_bytes=2400,profile=0xB20,
        sha256='296988c24fa2ec610e93dcd0c941add0e968c386b2184853da230076ef9fc338',
        relocation_sha256='a17f3346fb9e6f43af816a0fd96415785922a44f05e243579be63ff6872f7ff6',
        notifications=[dict(offset=0x15C,before=0x0C02052E,argument_offset=0x158,
                            argument=0x24040003,donor_event=1)]),
}
SOURCES=('tools/v3_npc_native.py','tools/v3_npc_registry.py','tools/v3_registry.py',
    'tools/v3_room_goods.py','tools/v3_furniture_install.py','tools/npc_mail_show.py',
    'overlays/v3/npc_identity.c','overlays/v3/npc_identity.h','overlays/v3/npc_identity_spawn.S',
    'translations/provenance.json')


def identities(base,members):
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    raw=source.raw('l_sp_actor_name')
    if len(raw)!=1008:raise ValueError('Changed complete special-character identity directory')
    directory=ROOT/'build/gamecube/files/forest_1st.arc.unpacked/data'
    banks={name:(directory/name).read_bytes() for name in STRING_FILES}
    if any(sha256(banks[n])!=digest for n,digest in STRING_FILES.items()):
        raise ValueError('Changed official special-character name bank')
    strings=Bank('string',0,0,banks['string_data.bin'],banks['string_data_table.bin']).entries()
    decoder=decoder_tables(ROOT/'local/ac-decomp/tools/msg_tool.py');info=module_command_info(base)
    catalogue=json.loads((ROOT/'translations/provenance.json').read_bytes());validate(catalogue)
    credits={r['id']:r for r in catalogue['entries']}
    data=bytearray(struct.pack('>4I',0x41464E49,1,len(members),16));rows=[]
    for identity,r in sorted(members.items()):
        found=[(sex,index,sound) for name,sex,index,sound in struct.iter_unpack('>HHII',raw) if name==r['donor_name']]
        if len(found)!=1:raise ValueError('Missing or ambiguous donor character identity')
        sex,index,sound=found[0];original=strings[index];text=decode_gc(original,decoder);encoded=encode(text,info)
        if not 1<=len(encoded)<=8 or any(c not in LATIN for c in encoded) or sex>2 or sound>4:
            raise ValueError('Invalid complete special-character name or speech identity')
        encoded=encoded.ljust(8,b' ');credit=credits.get(identity+'/name',{}).get('locales',{}).get('en',{})
        if (credit.get('credit')!='official' or credit.get('encoded_sha256')!=sha256(encoded) or
                credit.get('source',{}).get('reference_id')!=f'string:{index:04X}' or
                credit.get('source',{}).get('reference_sha256')!=sha256(original)):
            raise ValueError('Missing official character-name provenance: '+identity)
        data.extend(struct.pack('>HHI8s',r['name'],sex,sound,encoded))
        rows.append(dict(identity=identity,name=r['name'],donor_name=r['donor_name'],sex=sex,
            sound_spec=sound,string_id=index,text=text,source_sha256=sha256(original),encoded_sha256=sha256(encoded)))
    if len(data)>144:raise ValueError('Special-character identity directory exceeds its reservation')
    return bytes(data),rows


def install_batch(base,prior,output,batch,manifest,*,core,module):
    if not isinstance(core,bytearray) or not isinstance(module,bytearray):
        raise ValueError('Native character readers require the shared mutable core/module')
    equipment=copy.deepcopy(prior['equipment_resources']);npc=equipment['npc_extra'];events=npc['events']
    if npc.get('native_batches') or not batch.get('records'):
        raise ValueError('Expected a new complete native-controller batch')
    old_packet=copy.deepcopy(events['sky']['packet']);prefix=base[old_packet['physical']:old_packet['physical']+old_packet['bytes']]
    packet=npc['packet'];original=base[packet['physical']:packet['physical']+packet['bytes']]
    data=bytearray(original);files=by_vrom(base)
    if (sha256(prefix)!=old_packet['sha256'] or events['participants']['packet']!=old_packet or
            len(data)!=SIZE or sha256(data)!=packet['sha256']):
        raise ValueError('Changed complete shared character packets')
    magic,version,count,stride=struct.unpack_from('>4I',data,TABLE)
    if (magic,version,stride)!=(0x41464E58,1,44) or not 0<count<8:
        raise ValueError('Changed complete shared character registry')
    members={npc['record']['identity']['identity']:npc['record']['identity']} if 'identity' in npc['record']['identity'] else {
        'GAFE01-r0/npc/ev-soncho2':npc['record']['identity']}
    members.update({k:v['identity'] for k,v in npc.get('prepared_characters',{}).items() if v['actor_installed']})
    if len(members)!=count or any(struct.unpack_from('>I',data,TABLE+20+i*44)[0] for i in range(count)):
        raise ValueError('Cannot extend active or mismatched unfinished special-character registry')
    work=output/'npc-native';work.mkdir();appended=bytearray();installed=[]
    start=old_packet['ram']+old_packet['bytes']
    notify=events['native_directory']['code']['symbols']['af_holiday_native_notify']
    for row in batch['records']:
        identity=row['identity'];provider=PROVIDERS.get(row['provider']);member=npc['prepared_characters'].get(identity)
        slots=row['slots']
        if (not provider or not member or member['actor_installed'] or member['identity']!=SPECIAL_NPCS[identity] or
                type(slots) is not int or not 1<=slots<=16 or count>=8 or identity in members):
            raise ValueError('Unknown, duplicate, or unprepared complete native character')
        r=member['identity']
        if (r['donor_name'],r['donor_profile'])!=(provider['donor_name'],provider['donor_profile']):
            raise ValueError('Native controller does not belong to this donor character')
        raw=files[provider['vrom']].extract(base);reloc=files[provider['relocation']].extract(base)
        if (len(raw)!=provider['bytes'] or sha256(raw)!=provider['sha256'] or
                sha256(reloc)!=provider['relocation_sha256'] or struct.unpack_from('>5I',reloc)!=provider['sections']):
            raise ValueError('Changed complete native character implementation or relocation')
        address=start+len(appended)
        spec=ActorImage(provider['ram'],len(raw)+provider['sections'][3],provider['sections'])
        image=bytearray(relocate_verified_data(spec,raw,reloc,address,memory_end=0x80800000))
        at=provider['profile'];fields=struct.unpack_from('>HHIHH6I',image,at)
        if fields[:6]!=(r['donor_profile'],3<<8,0,r['donor_name'],3,provider['actor_bytes']):
            raise ValueError('Changed complete native character profile')
        struct.pack_into('>H',image,at,r['profile']);struct.pack_into('>H',image,at+8,r['name'])
        notifications=[]
        for call in provider['notifications']:
            pos=call['offset'];arg=call['argument_offset']
            if struct.unpack_from('>I',image,pos)[0]!=call['before'] or struct.unpack_from('>I',image,arg)[0]!=call['argument']:
                raise ValueError('Changed native character event-notification caller')
            struct.pack_into('>I',image,pos,jump(notify,link=True))
            struct.pack_into('>I',image,arg,0x24040000|call['donor_event'])
            notifications.append(dict(call,target=notify))
        appended.extend(image);appended.extend(bytes(-len(appended)%16))
        descriptor=start+len(appended);draw=descriptor+32;stream=draw+112;area=stream+48
        slot_stride=(provider['actor_bytes']+15&~15)+32
        chunk=bytearray(192+slots*slot_stride)
        struct.pack_into('>8I',chunk,0,0,0,0,0,0,address+at,0,0)
        chunk[32:132]=bytes.fromhex(member['draw_hex']);chunk[144:180]=bytes.fromhex(member['stream_hex'])
        for i in range(slots):
            pos=192+i*slot_stride
            struct.pack_into('>4I',chunk,pos,0x41464E53,0,r['name'],r['profile'])
            struct.pack_into('>4I',chunk,pos+slot_stride-16,*([0x4E504347]*4))
        offset=TABLE+16+count*44
        if any(data[offset:offset+44]):raise ValueError('Native character overwrites an existing registry row')
        struct.pack_into('>HH9I2H',data,offset,r['name'],r['profile'],0,provider['actor_bytes'],slots,slot_stride,
            area,descriptor,draw,stream,member['voice'],r['model_bank'],r['texture_bank'])
        appended.extend(chunk);members[identity]=r;count+=1
        member.update(actor_installed=True,active=False,descriptor=descriptor,profile=address+at,
            actor_bytes=provider['actor_bytes'],slots=slots,slot_stride=slot_stride,pool_ram=area,
            flags_offset=offset+4,callback_family=row['provider'])
        installed.append(dict(identity=identity,provider=row['provider'],source=provider,ram=address,
            bytes=len(image),sha256=sha256(image),callbacks=list(fields[6:]),notifications=notifications,
            profile=address+at,descriptor=descriptor,pool_ram=area,pool_bytes=slots*slot_stride))
    struct.pack_into('>I',data,TABLE+8,count)
    identity_data,identity_rows=identities(base,members)
    if any(data[IDENTITIES:BRIDGES+32]):raise ValueError('Character name/bridge reservation is occupied')
    data[IDENTITIES:IDENTITIES+len(identity_data)]=identity_data
    changes={};hooks=[];links=dict(npc['code']['link_symbols']);text=prior['villager_text']['code']['symbols']
    links.update(af_npc_identities=RAM+IDENTITIES,
        af_npc_previous_name=text['af_v3_load_name'],af_npc_previous_actor_name=text['af_v3_actor_name'],
        af_npc_previous_sex=RAM+BRIDGES,af_npc_previous_sound=RAM+BRIDGES+16,
        af_npc_previous_spawn=events['participants']['code']['symbols']['af_hp_spawn_profile'])
    native_core=files[CODE_VROM].extract(base)
    for entry,end,offset,digest in (
        (0x800AD0B8,0x800AD104,BRIDGES,'901dd7b2cda5bfc681b6c8b196308ee4bd5295070f06dd64e459e31cff354c1a'),
        (0x800AD1E0,0x800AD22C,BRIDGES+16,'58806559c1c7d63b510c8a722962da4aa921eef715f213637cfb6572b5734e76')):
        original_entry=native_core[entry-CODE_RAM:entry-CODE_RAM+8]
        if sha256(native_core[entry-CODE_RAM:end-CODE_RAM])!=digest or original_entry!=bytes.fromhex('afa400003084ffff'):
            raise ValueError('Changed native special-character identity reader')
        data[offset:offset+16]=original_entry+struct.pack('>2I',jump(entry+8),0)
    # Recompile the existing registry code plus shared identity readers. Existing
    # public exports keep their addresses; native draw hooks rebind together.
    fresh=refresh_renderer(npc,original,work/'code',base,changes,
        extra_sources=('overlays/v3/npc_identity.c','overlays/v3/npc_identity_spawn.S'),link_symbols=links)
    data[:0x2000]=fresh[:0x2000];symbols=npc['code']['symbols']
    def hook(vrom,ram,entry,before,target):
        owner=core if vrom==CODE_VROM else module if vrom==MODULE else bytearray(changes.get(vrom,files[vrom].extract(base)))
        off=entry-ram
        if owner[off:off+len(before)]!=before:raise ValueError(f'Changed shared character reader {entry:08X}')
        after=struct.pack('>2I',jump(symbols[target]),0) if len(before)==8 else struct.pack('>I',jump(symbols[target],link=True))
        owner[off:off+len(before)]=after
        if vrom not in (CODE_VROM,MODULE):changes[vrom]=bytes(owner)
        hooks.append(dict(vrom=vrom,ram=ram,address=entry,before=before.hex(),after=after.hex(),helper=target))
    for entry,old,target in ((0x80196044,text['af_v3_load_name'],'af_npc_identity_name'),
                            (0x80195D20,text['af_v3_actor_name'],'af_npc_identity_actor_name')):
        hook(MODULE,MODULE_RAM,entry,struct.pack('>2I',jump(old),0),target)
    for entry,target in ((0x800AD0B8,'af_npc_identity_sex'),(0x800AD1E0,'af_npc_identity_sound')):
        hook(CODE_VROM,CODE_RAM,entry,bytes.fromhex('afa400003084ffff'),target)
    previous_hooks=npc.get('variants',{}).get('spawn_hooks',events['participants']['installed_hooks'])
    for h in previous_hooks:
        if h.get('replacement') not in ('af_npc_variant_spawn','af_hp_spawn_profile'):continue
        hook(h['vrom'],h['ram'],h['address'],bytes.fromhex(h['after']),'af_npc_identity_spawn')
    if sum(h['helper']=='af_npc_identity_spawn' for h in hooks)!=2:
        raise ValueError('Both native NPC-controller spawn readers must be bound')
    appended.extend(b'AFNN'*4);end=start+len(appended)
    if end>0x807DA800 or any(a<end and start<b for a,b in reservations(prior)):
        raise ValueError('Complete native character batch overlaps existing memory')
    combined=prefix+appended;records=copy.deepcopy(prior['physical_resources'])
    write=physical.grow_backwards(base,records,old_packet['id'],combined)
    record={k:write[k] for k in ('id','physical','bytes','sha256')}
    records=[record if r['id']==old_packet['id'] else r for r in records]
    new=dict(record,ram=old_packet['ram'],crc32=zlib.crc32(combined),storage='physical-ROM')
    events['sky']['packet']=copy.deepcopy(new);events['participants']['packet']=copy.deepcopy(new)
    packet.update(sha256=sha256(data),crc32=zlib.crc32(data))
    registry_record=next(r for r in records if r['id']==packet['id']);registry_record['sha256']=sha256(data)
    npc['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    receipt=dict(format=batch['format'],manifest_sha256=sha256(manifest),installed=True,
        ram=start,bytes=len(appended),sha256=sha256(appended),guard='AFNN',controllers=installed,
        identities=identity_rows,identity_ram=RAM+IDENTITIES,hooks=hooks,preserved_packet=old_packet,
        additional_resident_bytes=len(appended),actor_admission_changed=False,saved_format_changed=False,
        native_execution_verified=False)
    npc['native_batches']=[receipt]
    write_new(work/'installed.json',(json.dumps(receipt,indent=2)+'\n').encode())
    write_new(work/'packet.bin',combined);write_new(work/'registry.bin',data)
    return equipment,changes,dict(physical_resources=records),[(write,combined),
        (dict(registry_record,previous_sha256=sha256(original)),bytes(data))]
