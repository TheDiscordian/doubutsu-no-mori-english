"""Connect source-derived equipment ownership through the shared runtime refresh."""
import copy
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from v3_asset_loader import ROOT, compile_part
from v3_furniture_pipeline import Source
from v3_handheld_items import parent_records
from v3_room_aliases import discover
from v3_equipment_runtime import RAM
from v3_player_actions import PARENT_CODE_OFFSET, POCKET_ICON_OFFSET

CODE=0xCA00
SOURCES=('tools/v3_held_collection.py','tools/v3_room_aliases.py',
    'tools/v3_asset_loader.py',
    'tools/v3_handheld_items.py','overlays/v3/held_items.c','overlays/v3/held_items.ld',
    'overlays/v3/held_collection.c','overlays/v3/held_collection.ld',
    'overlays/v3/save_runtime.h','overlays/v3/save_codec.h')


def source_records(source,equipment):
    """Use actual collection conversions and all nine catalogue lists.

    The umbrella page also contains balloons, fans, and pinwheels. Absence
    from mCL_furniture_list alone does not mean an item has no catalogue row.
    """
    aliases=discover(source)
    table,parents=parent_records(source,equipment)
    actual=equipment['parent_readers']
    if (parents['rows']!=actual['rows'] or parents['table_sha256']!=actual['table_sha256']):
        raise ValueError('Changed installed collection parents')
    names=('furniture','wall','carpet','cloth','umbrella','paper','haniwa','fossil','music')
    lists=[]
    info=source.raw('mCL_item_idx_data');base=source.symbol('mCL_item_idx_data')[0]
    if len(info)!=72:raise ValueError('Changed source catalogue category count')
    for i,name in enumerate(names):
        symbol='mCL_furniture_list' if not i else f'mCL_{name}_idx_list'
        raw=source.raw(symbol);width=4 if not i else 2
        values=list(struct.unpack('>'+str(len(raw)//2)+'H',raw))
        indices=values[::2] if not i else values
        pointer=source.relocations.get(base+i*8)
        expected=None if not i else (1,True,5,source.symbol(symbol)[0])
        if (len(raw)%width or len(indices)!=len(set(indices)) or
                info[i*8:i*8+4]!=bytes(4) or pointer!=expected or
                struct.unpack_from('>I',info,i*8+4)[0]!=len(indices)):
            raise ValueError('Changed complete source catalogue list binding')
        lists.append(dict(category=name,category_index=i,symbol=symbol,
            offset=source.symbol(symbol)[0],count=len(indices),sha256=sha256(raw),indices=indices))
    by_parent={a['parent_item_id']:a for a in aliases['rows']}
    rows=[]
    for parent in parents['rows']:
        alias=by_parent[parent['item_id']];item=int(alias['display_item_id'],16)
        index=1024+((item-0x3000)>>2)
        membership=[dict(category=t['category'],category_index=t['category_index'],
            source_symbol=t['symbol'],position=t['indices'].index(index)) for t in lists
            if t['category'] not in ('wall','carpet','paper','music') and index in t['indices']]
        if (alias['context_outputs']['collection_record']!=[parent['display_item_id']] or
                alias['context_outputs']['collection_check']!=[parent['display_item_id']] or
                alias['context_outputs']['room_placement']!=[parent['item_id']] or
                parent['profile_byte']!=32+((item&0xFFF)>>5) or
                parent['profile_mask']!=1<<(((item&0xFFF)>>2)&7) or len(membership)!=1):
            raise ValueError('Unreviewed parent collection or catalogue context')
        rows.append(dict(item_id=parent['item_id'],display_item_id=parent['display_item_id'],
            runtime_index=index,profile_byte=parent['profile_byte'],profile_mask=parent['profile_mask'],
            catalogue=membership[0],room_drop_item_id=parent['item_id']))
    return table,dict(format='AFV3-HELD-COLLECTION-1',rows=rows,
        source_contexts=aliases['contexts'],source_lists=lists,
        source_catalogue_constructor=source.function(0x25BB84)[1],
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()))


def install(base,prior,blob,core,original,output):
    old=prior['equipment_resources'];at=old['blob_offset']
    module=bytearray(blob[at:at+old['bytes']]);parents=old['parent_readers']
    if (old.get('collection') or old['bytes']!=0xD000 or
            not old.get('event_acquisition',{}).get('menu') or sha256(module)!=old['sha256'] or
            any(module[CODE:-16])):
        raise ValueError('Held collection requires checked event-equipped free code space')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    table,receipt=source_records(source,old)
    t=parents['table_offset'];previous=parents['code']
    if (module[t:t+len(table)]!=table or
            sha256(module[PARENT_CODE_OFFSET:PARENT_CODE_OFFSET+previous['bytes']])!=previous['sha256'] or
            any(module[PARENT_CODE_OFFSET+previous['bytes']:POCKET_ICON_OFFSET])):
        raise ValueError('Changed complete held reader reservation')
    # These native pocket functions continue to invoke the public collection
    # entry with original condition handling. No change to delivery/payment.
    native=by_vrom(original)[CODE_VROM].extract(original)
    start,end=0x800B8B08-CODE_RAM,0x800B8BE4-CODE_RAM
    if core[start:end]!=native[start:end]:raise ValueError('Changed native acquisition pair')
    reader,compiled=compile_part('held_items',output/'held_items',
        extra_sources=('overlays/v3/held_icon.S',),defines=tuple(f[2:] for f in previous['flags']
            if f.startswith('-D'))+('AF_V3_HELD_COLLECTION=1',))
    if (len(reader)>POCKET_ICON_OFFSET-PARENT_CODE_OFFSET or
            compiled['symbols']['af_v3_held_item_collection']!=0x804A6600 or
            reader[:previous['bytes']]!=module[PARENT_CODE_OFFSET:PARENT_CODE_OFFSET+previous['bytes']]):
        raise ValueError('Collection identity entry moves existing held readers')
    code,code_report=compile_part('held_collection',output/'held_collection',
        defines=('AF_V3_CLOTHING_PROFILE=1',))
    imports={'af_v3_held_item_collection':compiled['symbols']['af_v3_held_item_collection'],
        'af_v3_prior_catalogue_record':0x80466F00,'af_v3_prior_catalogue_owned':0x80466F10,
        'af_v3_require_save_state':prior['save_runtime']['code']['symbols']['require_state'],
        'af_v3_save_halt':prior['save_runtime']['code']['symbols']['af_v3_save_halt'],
        'af_v3_save_collect':prior['save_codec']['code']['symbols']['af_v3_save_collect']}
    if (len(code)>len(module)-16-CODE or any(code_report['symbols'][k]!=v for k,v in imports.items()) or
            code_report['symbols']['af_v3_held_catalogue_record']!=0x804AFA00 or
            code_report['symbols']['af_v3_held_catalogue_owned']!=0x804AFB00):
        raise ValueError('Changed collection dependency ABI or reservation')
    for hook in prior['clothing']['display']['readers']['collection_hooks']:
        b=hook['bridge']-0x80460000
        if blob[b:b+16].hex()!=hook['bridge_bytes']:
            raise ValueError('Changed original collection bridge')
    module[PARENT_CODE_OFFSET:PARENT_CODE_OFFSET+len(reader)]=reader
    module[CODE:CODE+len(code)]=code
    receipt.update(code=code_report,code_offset=CODE,identity_code=compiled,
        native_acquisition_sha256=sha256(core[start:end]),additional_resident_bytes=0,
        saved_format_changed=False,profile_bits_enabled=0,catalogue_rows_installed=False,
        native_tested=False,ordinary_acquisition_tested=False)
    report=copy.deepcopy(old)
    report['parent_readers'].update(code=compiled,collection_installed=True)
    report['pocket_icons']['code']=compiled
    report.update(collection=receipt,sha256=sha256(module),crc32=zlib.crc32(module))
    blob[at:at+len(module)]=module
    return report,{}
