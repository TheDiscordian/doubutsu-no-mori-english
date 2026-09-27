"""Collection drawing/navigation and official catch text for every added creature.

Continue the shared importer in the already loaded world packet. Preserve all
old collection identities, names, message commands, and physical creature art.
"""
import copy
import json
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from apply_translation import write_new
from gc_text import decode_gc
from runtime_module import module_command_info
from textcodec import encode,tokenize
from textvalidate import expanded_bound
from text_provenance import validate
from v3_asset_loader import ROOT,compile_part
from v3_camper_text import donor,extend_bank
from v3_creature_field import table
from v3_creature_items import source_records
from v3_event_text import MESSAGE,TABLE,CHOICES,CHOICE_TABLE,patch_bounds
from v3_import_storage import jump

RAM,DATA,FIRST=0x80654800,0x80654F00,12015
INVENTORY,INVENTORY_RELOC,INVENTORY_RAM=0x785700,0x7898C0,0x8087D480
TAG,TAG_RELOC,TAG_RAM=0x3950000,0x3960000,0x8086F310
SOURCES=('tools/v3_creature_ui.py','overlays/v3/creature_ui.c',
    'overlays/v3/creature_ui.S','overlays/v3/creature_ui.ld',
    'tools/v3_creature_fish.py','tools/v3_furniture_install.py',
    'tools/v3_furniture_pipeline.py','tools/v3_asset_loader.py','tools/v3_event_text.py',
    'translations/provenance.json')


def messages(base,source):
    """Return unchanged official wording and its single-catalogue source credits."""
    functions=[]
    for at,size,digest,name in (
        (0x183854,24,'16fefc9ebc3b6152e3ec2b8dbed71d28615cee1e97a9316eef2b605e176a7dd0',
         'Player_actor_Get_mushi_msg_num'),
        (0x1867C8,24,'394bd751a2a889489723057b86c377f679a700c6ce8005f6875dcfa3412ae410',
         'Player_actor_Get_sakana_msg_num')):
        raw,receipt=source.function(at)
        if len(raw)!=size or sha256(raw)!=digest or receipt['symbol']!=name:
            raise ValueError('Changed complete source catch message selector')
        functions.append(receipt)
    identities,identity_source=source_records(source)
    bank,_,decoder=donor();info=module_command_info(base);extra=[];rows=[];credits=[]
    for ordinal,row in enumerate(identities):
        i=row['source_index'];fish=row['category']=='fish'
        source_id=i+(0x1327 if i<32 else 0x2FA9) if fish else i+(0xA2C if i<32 else 0x2FA1)
        original=bank[source_id];data=encode(decode_gc(original,decoder),info)
        tokens=list(tokenize(data,info));bound=expanded_bound(data,info)
        if (not tokens or tokens[-1].data!=b'\x7f\x01' or bound>1024 or
                sum(t.kind=='cmd' and t.data[1] in (0,1) for t in tokens)!=1 or
                any(t.kind=='cmd' and t.data[1] not in (1,2,3,4,5,0x52,0x53,0x54,0x5A) for t in tokens)):
            raise ValueError('Catch message has an unreviewed command or native overflow')
        target=FIRST+ordinal;extra.append(data)
        rows.append(dict(item_id=row['item_id'],id=target,source_id=source_id,
            bytes=len(data),sha256=sha256(data),source_sha256=sha256(original),expanded_bound=bound))
        credits.append(dict(id=f'message:{target:04X}',native_sha256=None,locales=dict(en=dict(
            credit='official',locator=['tools/v3_creature_ui.py:messages',f'N64/message/{target:04X}'],
            source=dict(source='user-supplied GAFE01 revision 0 disc',reference_id=f'message:{source_id:04X}',
                        reference_sha256=sha256(original)),
            adaptations=['Native encoding; retain official wording, line and page breaks, pauses, colours, and text effects'],
            human_review='not_recorded',encoded_sha256=sha256(data)))))
    return extra,dict(first_id=FIRST,count=len(extra),rows=rows,source_functions=functions,
        source_identities=identity_source,provenance_entries=credits,max_expanded_bytes=max(r['expanded_bound'] for r in rows))


def layout(base,source,text):
    files=by_vrom(base);inv=files[INVENTORY].extract(base);receipts=[];lists=[]
    for at,name,native_at in ((523976,'mIV_fish_collect_list',0x808812C0),
                             (524016,'mIV_insect_collect_list',0x808812E0)):
        raw,receipt=table(source,at,40,name);receipts.append(receipt)
        if sorted(raw)!=list(range(40)) or raw[:32]!=inv[native_at-INVENTORY_RAM:native_at-INVENTORY_RAM+32]:
            raise ValueError('Changed complete donor/native collection order')
        lists.append(raw)
    # Keep the N64 herabuna in its original slot. Brook trout is an addition,
    # not a replacement for that fish despite sharing source index one.
    fish=lists[0]+bytes([40]);insects=lists[1]
    y,receipt=table(source,533752,10,'mTG_collect_line_pos');receipts.append(receipt)
    if struct.unpack('>5h',y)!=(42,18,-6,-30,-54):raise ValueError('Changed source five-row layout')
    x=tuple(range(-90,79,21))
    result=bytearray(0xF0);struct.pack_into('>4I',result,0,0x41464355,1,45,17)
    result[0x10:0x10+45]=fish+bytes([255])*(45-len(fish))
    result[0x40:0x40+45]=insects+bytes([255])*(45-len(insects))
    struct.pack_into('>9h',result,0x70,*x);result[0x84:0x8E]=y
    struct.pack_into('>17H',result,0x90,*(r['id'] for r in text['rows']))
    return bytes(result),dict(ram=DATA,bytes=len(result),sha256=sha256(result),columns=9,rows=5,
        fish=list(fish),insects=list(insects),empty_index=255,x=list(x),y=list(struct.unpack('>5h',y)),
        source_tables=receipts,icon_scale=0.875,
        adaptation='Retain native fish identities and add brook trout; fit nine columns inside the original horizontal range')


def install(base,prior,blob,output,core):
    from v3_creature_fish import rewrite,WORLD_RAM
    from v3_equipment_runtime import PLAYER_VROM,PLAYER_RELOC,PLAYER_RAM
    from v3_furniture_pipeline import Source
    from player_item_names import BRIDGE,BRIDGE_END,bridge_body,call_body,CALLS
    e=copy.deepcopy(prior['equipment_resources']);fish=e['creature_fish'];world=fish['world']
    if not world.get('pocket_icons') or world.get('collection_ui_installed'):
        raise ValueError('Collection UI requires installed catches/icons and an unfinished UI')
    files=by_vrom(base)
    if core is None or bytes(core)!=files[CODE_VROM].extract(base):
        raise ValueError('Creature text requires the unchanged checked native core')
    p=world['packet'];at=p['blob_offset'];packet=bytearray(blob[at:at+p['bytes']])
    if (p['ram']!=WORLD_RAM or p['bytes']!=0xB000 or sha256(packet)!=p['sha256'] or
            zlib.crc32(packet)!=p['crc32'] or any(packet[RAM-WORLD_RAM:DATA-WORLD_RAM+0xF0])):
        raise ValueError('Creature UI would replace occupied or changed resident bytes')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    identities,_=source_records(source)
    if identities!=e['creature_items']['rows']:raise ValueError('Changed installed creature identities')
    extra,text=messages(base,source)
    catalogue=json.loads((ROOT/'translations/provenance.json').read_bytes());validate(catalogue)
    indexed={r['id']:r for r in catalogue['entries']}
    if any(indexed.get(r['id'])!=r for r in text['provenance_entries']):
        raise ValueError('Official creature messages need their exact single-catalogue credits')
    data,grid=layout(base,source,text)
    code,compiled=compile_part('creature_ui',output/'creature_ui',
        extra_sources=('overlays/v3/creature_ui.S',),link_symbols={
            'AF_CREATURE_COLLECTED':world['compiled']['symbols']['af_v3_creature_collected'],
            'AF_CREATURE_ITEM_TYPE':e['creature_items']['code']['symbols']['af_v3_creature_item_type']})
    if len(code)>DATA-RAM:raise ValueError('Creature UI code overlaps complete identity data')
    packet[RAM-WORLD_RAM:RAM-WORLD_RAM+len(code)]=code
    packet[DATA-WORLD_RAM:DATA-WORLD_RAM+len(data)]=data
    symbols=compiled['symbols'];owners=[];changes={}

    def patch(name,vrom,reloc_vrom,ram,windows,functions):
        raw=files[vrom].extract(base);reloc=files[reloc_vrom].extract(base)
        for address,size,digest in functions:
            if sha256(raw[address-ram:address-ram+size])!=digest:
                raise ValueError('Changed complete native collection/message consumer')
        data,fixed,receipt=rewrite(raw,reloc,ram,{},windows)
        receipt.update(name=name,vrom=vrom,reloc=reloc_vrom,ram=ram,
            original_sha256=sha256(raw),original_reloc_sha256=sha256(reloc),
            functions=[dict(address=a,bytes=n,sha256=d) for a,n,d in functions])
        owners.append(receipt);changes[vrom]=data;changes[reloc_vrom]=fixed
        return receipt

    inv=patch('collection_inventory',INVENTORY,INVENTORY_RELOC,INVENTORY_RAM,[
        (0x8087D480,(0x27BDFFE8,0xAFBF0014),(jump(symbols['af_v3_creature_grid_item']),0)),
        (0x808807C8,(0x3C013F80,),(0x3C013F60,)),
        (0x808807D0,(0x24130020,),(0x2413002D,))],[
        (0x8087D480,156,'84bf15d7474074ebf7b376e8dceeaf2892ed869c264c4a7ca64f2c5f9136de60'),
        (0x8088078C,240,'c20ca5d40b7422a28277f3f7329a2015a4c60bc97e02546c5d148d678838585c')])
    if (inv['original_sha256']!=e['inventory_preview']['owner_sha256'] or
            inv['original_reloc_sha256']!=e['inventory_preview']['relocation_sha256']):
        raise ValueError('Changed complete installed inventory consumer')
    e['inventory_preview'].update(owner_sha256=inv['sha256'],relocation_sha256=inv['reloc_sha256'])
    patch('collection_navigation',TAG,TAG_RELOC,TAG_RAM,[
        (0x80878A54,(0x00080004,0x80878948,0x808789AC),(0x00090005,DATA+0x70,DATA+0x84)),
        (0x8087499C,(0xACC30038,),(0xACC80038,))],[
        (0x80874680,240,'dea9cbeb19e99e9028cacc31d5b89e4e6bdc5e919e67c00ed10f47d8502437b6'),
        (0x808748B0,620,'717780b8840670f46d0c57da355c45156b2563554733691c9f35f4fa7203babd'),
        (0x80874B1C,368,'062f1f42cce2bdccdeb6bc6c29125a8f42b1e882a08310f0cd4232376182e0db')])
    player=files[PLAYER_VROM].extract(base)
    if core[BRIDGE-CODE_RAM:BRIDGE_END-CODE_RAM]!=bridge_body():
        raise ValueError('Changed complete native full-name bridge')
    for kind in ('fish','insect'):
        pos=CALLS[kind][0]-PLAYER_RAM
        if player[pos:pos+28]!=call_body(kind):raise ValueError('Changed last-catch full-name reader')
    windows=[]
    for address,name in ((0x808CF9D8,'fish'),(0x808CD070,'insect')):
        windows.append((address,(0x0C01ED70,0x00A02025),
            (jump(symbols[f'af_v3_creature_{name}_message_call'],link=True),0x00A02025)))
    changed=patch('catch_messages',PLAYER_VROM,PLAYER_RELOC,PLAYER_RAM,windows,[
        (0x808CF92C,288,'ebf9a052dfd5d297a010896523ca318a71580de3893c52aa513e8c2c4b2e3455'),
        (0x808CCFDC,328,'3f1b6ee97c2c670c122c0afcb6a88dc005d66cecb3f706e8fca8972e19b9f7aa')])
    old=next(o for o in world['manager_owners'] if o['name']=='player_catches')
    if changed['original_sha256']!=old['sha256'] or changed['original_reloc_sha256']!=old['reloc_sha256']:
        raise ValueError('Changed complete installed catch owner')
    old.update(sha256=changed['sha256'],reloc_sha256=changed['reloc_sha256'])
    payload,directory=extend_bank(files[MESSAGE].extract(base),files[TABLE].extract(base),extra,FIRST)
    resources=[];choices=prior['import_storage']['choice_vrom'];text['choice_vrom']=choices
    for v,data in ((MESSAGE,payload),(TABLE,directory),(choices,files[choices].extract(base)),
                   (CHOICE_TABLE,files[CHOICE_TABLE].extract(base))):
        filename=f'creature-text-{v:08X}.bin';write_new(output/filename,data)
        resources.append(dict(vrom=v,file=filename,bytes=len(data),sha256=sha256(data),
                              original_sha256=sha256(files[v].extract(base))))
    text['resources']=resources;core_before=sha256(core)
    bounds=patch_bounds(core,FIRST,len(extra))
    owners.append(dict(name='message_bounds',vrom=CODE_VROM,ram=CODE_RAM,
        original_sha256=core_before,sha256=sha256(core),patches=bounds))
    next(o for o in world['manager_owners'] if o['name']=='completion')['sha256']=sha256(core)
    blob[at:at+p['bytes']]=packet;p.update(sha256=sha256(packet),crc32=zlib.crc32(packet))
    world.update(collection_ui_installed=True,ui=dict(code=compiled,code_ram=RAM,grid=grid,
        owners=owners,text=text,native_execution_tested=False,additional_resident_bytes=0))
    fish.update(additional_resident_bytes=0,sources={path:sha256((ROOT/path).read_bytes())
        for path in (*fish['sources'],*SOURCES)},pending=['behaviour-choice composition',
            'Controller Pak collection transport','ordinary gameplay'])
    return e,changes


def finish(image,base,prior,output,equipment):
    old=prior['equipment_resources']['creature_fish'].get('world',{}).get('ui')
    current=equipment['creature_fish'].get('world',{}).get('ui')
    if current and not old:
        from v3_event_text import install as install_text
        return install_text(image,base,output,current['text'],relocate=True,
            physical_resources=prior.get('physical_resources',()),
            reserved_end=prior.get('resource_capacity',{}).get('reserved_physical_end',0))
    return image
