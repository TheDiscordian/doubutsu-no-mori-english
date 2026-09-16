"""Shared player action tables and relocation-aware native dispatch.

Keep every original action. Reserve the donor's additional action indices with
their actual metadata, but null callbacks until their complete implementations
are installed. This adapter does not enable equipment or new gameplay actions.
"""
import copy
import re
import struct
import zlib

from aflib import by_vrom, sha256, u32
from v3_asset_loader import BLOB, ROOT, compile_part
from v3_equipment_runtime import RAM, SIZE, GUARD, PLAYER_RAM, PLAYER_VROM, PLAYER_RELOC
from v3_furniture_pipeline import Source
from v3_import_storage import END, jump
from v3_npc_draw import relocation_offsets

NATIVE_COUNT, COUNT = 105, 121
CODE_OFFSET, TABLE_OFFSET, MODULE_SIZE = 0x2000, 0x4000, 0x6000
CTOR, CTOR_SLOT, TEXT_SIZE = 0x808DD748, 0x80143900, 0x2AF00
# Source consumer, native consumer, native bound, native table, record width.
# These are engine categories, not individual item definitions.
CATEGORIES = (
    (0x164E9C,0x808B3370,0x808B3388,0x808DDE88,1),
    (0x164EEC,0x808B33B8,0x808B33D0,0x808DDEF4,1),
    (0x165030,0x808B34E8,0x808B3504,0x808DDF60,1),
    (0x1650DC,0x808B3584,0x808B359C,0x808DDFCC,1),
    (0x165124,0x808B35C8,0x808B35D8,0x808DE038,1),
    (0x1651AC,0x808B3648,0x808B3668,0x808DE0A4,1),
    (0x165440,0x808B3960,0x808B397C,0x808DE118,1),
    (0x1655DC,0x808B3A84,0x808B3AB4,0x808DE184,1),
    (0x165664,0x808B3B08,0x808B3B20,0x808DE1F0,1),
    (0x167F84,0x808B63B4,0x808B63C4,0x808DE56C,1),
    (0x167FC0,0x808B63EC,0x808B63FC,0x808DE5D8,1),
    (0x167FFC,0x808B6424,0x808B6434,0x808DE644,1),
    (0x169AC4,0x808B828C,0x808B82B8,0x808DE6F0,1),
    (0x16A170,0x808B8778,0x808B87A0,0x808DE75C,1),
    (0x16A1DC,0x808B87C8,0x808B87D8,0x808DE7C8,1),
    (0x16A5A4,0x808B8B00,0x808B8B24,0x808DE834,1),
    (0x16C7D8,0x808BAC20,0x808BAC70,0x808DF2BC,1),
    (0x16CFFC,0x808BB43C,0x808BB458,0x808DF328,1),
    (0x16EE78,0x808BBDE8,0x808BBE28,0x808DF3A0,1),
    (0x16DB2C,0x808BBF38,0x808BBF6C,0x808DF40C,1),
    (0x16E074,0x808BC308,0x808BC330,0x808DF49C,1),
    (0x16427C,0x808DDBD4,0x808DDBF4,0x808E00E4,1),
    (0x17199C,0x808BE620,0x808BE63C,0x808DF628,4),
    (0x163E98,0x808DD874,0x808DD8B4,0x808DFA54,4),
    (0x164008,0x808DD9B4,0x808DD9D4,0x808DFBF8,4),
    (0x164094,0x808DDA18,0x808DDA58,0x808DFD9C,4),
    (0x1641E8,0x808DDB5C,0x808DDB90,0x808DFF40,4),
)
DISPATCH = ((0x808BE658,2),(0x808DD8D0,2),(0x808DD9F4,2),
            (0x808DDAFC,25),(0x808DDBB0,2))
# This address is also the exclusive end of the PRECEDING eight-float array.
# The spatial-search loop compares its incrementing pointer against this end;
# moving that boundary to the new action table would overrun its stack buffer.
RETAINED_BOUNDARY = (0x808B99D0,0x808B99D8,0x808DF2BC)
SOURCES = ('tools/v3_player_actions.py','tools/v3_furniture_pipeline.py',
           'tools/v3_asset_loader.py','overlays/v3/startup.c',
           'overlays/v3/player_actions.S','overlays/v3/player_actions.ld')


def source_tables(source):
    """Resolve complete action tables through their actual donor consumers."""
    spans = {}
    for name,at,n in re.findall(
            r'^(\S+) = \.rodata:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) ',
            source.symbols,re.M):
        spans.setdefault(int(at,16),[]).append((name,int(n,16)))
    result=[]
    for donor,entry,bound,table,width in CATEGORIES:
        raw,receipt=source.function(donor)
        if raw!=source.rel[source.sections[1][0]+donor:source.sections[1][0]+donor+receipt['bytes']]:
            raise ValueError('Action consumer does not match the checked donor')
        targets={r[3] for r in receipt['relocations'].values() if r[:3] in ((6,1,4),(4,1,4))
                 and len(spans.get(r[3],[]))==1 and spans[r[3]][0][1]==COUNT*width}
        if len(targets)!=1:raise ValueError('Missing or ambiguous complete donor action table')
        target=targets.pop();n=COUNT*width;base=source.sections[4][0]+target
        value=source.rel[base:base+n]
        references={k:v for k,v in receipt['relocations'].items() if v[1:]==(1,4,target)}
        if (len(value)!=n or {v[0] for v in references.values()}!={4,6}
                or sum(v[0]==4 for v in references.values())!=sum(v[0]==6 for v in references.values())):
            raise ValueError('Incomplete donor action table address binding')
        pointers={at-target:r for (section,at),r in source.section_relocations.items()
                  if section==4 and target<=at<target+n}
        callbacks={}
        if width==4:
            if any(value) or any(at%4 or row[:3]!=(1,1,1) for at,row in pointers.items()):
                raise ValueError('Invalid or external donor action callback')
            for at,row in pointers.items():
                _,callback=source.function(row[3]);callbacks[at//4]=callback
        elif pointers:
            raise ValueError('Unexpected pointer inside byte action metadata')
        result.append(dict(consumer=receipt,table_symbol=spans[target][0][0],
            source_section=4,source_offset=target,source_bytes=n,source_sha256=sha256(value),
            source_hex=value.hex() if width==1 else None,source_callbacks=callbacks,
            native_entry=entry,native_bound=bound,native_table=table,width=width))
    return result


def native_references(owner,reloc):
    """Resolve all native table references, including multiple low consumers."""
    slots=relocation_offsets(reloc,len(owner));sections=struct.unpack_from('>5I',reloc)
    if sections[:4]!=(TEXT_SIZE,9488,880,0):raise ValueError('Changed complete player owner dimensions')
    rows=list(struct.unpack_from('>'+str(sections[4])+'I',reloc,20))
    high={};groups={};absolute={};locations={}
    for record in rows:
        section,kind,offset=record>>30,record>>24&63,record&0xFFFFFF
        at=sum(sections[:section-1])+offset;word=u32(owner,at);locations[at]=record
        if kind==5:
            if word>>26!=15:raise ValueError('Changed native player high-half relocation')
            high[word>>16&31]=at;groups[at]=[]
        elif kind==6:
            reg=word>>21&31
            if reg not in high:raise ValueError('Unpaired native player table reference')
            hi=high[reg]
            target=((u32(owner,hi)&65535)<<16)+struct.unpack('>h',struct.pack('>H',word&65535))[0]
            groups[hi].append((at,target))
        elif kind==2:absolute[at]=word
    return groups,absolute,rows,locations,slots


def expanded_tables(source,owner,reloc):
    """Build full-capacity tables; unimplemented extra actions cannot dispatch."""
    groups,absolute,rows,locations,slots=native_references(owner,reloc)
    observed={PLAYER_RAM+i for i in range(0,TEXT_SIZE,4)
              if u32(owner,i)>>26 in (10,11) and u32(owner,i)&65535==NATIVE_COUNT}
    if observed!={r[2] for r in CATEGORIES}:
        raise ValueError('Player action bound inventory changed')
    tables=source_tables(source);data=bytearray(struct.pack('>4I',0x41465041,1,COUNT,len(tables)))
    removed=set();patches=[]
    for table in tables:
        target,width=table['native_table'],table['width'];n=NATIVE_COUNT*width
        old=owner[target-PLAYER_RAM:target-PLAYER_RAM+n]
        if len(old)!=n:raise ValueError('Truncated original action table')
        pairs=[]
        for hi,lows in groups.items():
            if any(target<=address<target+n for _,address in lows):
                if any(address!=target for _,address in lows):
                    raise ValueError('Shared unrelated high half or interior action reference')
                for lo,address in lows:
                    if (PLAYER_RAM+hi,PLAYER_RAM+lo,address)==RETAINED_BOUNDARY:
                        if (u32(owner,hi)!=0x3C04808E or u32(owner,lo)!=0x2484F2BC
                                or u32(owner,0x808B99DC-PLAYER_RAM)!=0x2442F29C
                                or u32(owner,0x808B99F8-PLAYER_RAM)!=0x24420004
                                or u32(owner,0x808B9A00-PLAYER_RAM)!=0x0044082B):
                            raise ValueError('Changed spatial-search array-end reference')
                        continue
                    pairs.append((hi,lo))
        if (len(pairs)!=(2 if table['native_entry']==0x808DDA18 else 1)
                or any(target<=v<target+n for v in absolute.values())):
            raise ValueError('Changed complete native action reference inventory')
        data.extend(bytes(-len(data)%4));offset=TABLE_OFFSET+len(data);address=RAM+offset
        if width==1:
            value=old+bytes.fromhex(table['source_hex'])[NATIVE_COUNT:]
        else:
            for at,pointer in enumerate(struct.unpack('>'+str(NATIVE_COUNT)+'I',old)):
                location=target-PLAYER_RAM+4*at
                if pointer:
                    if not PLAYER_RAM<=pointer<PLAYER_RAM+TEXT_SIZE or pointer%4 or location not in slots:
                        raise ValueError('Unrelocated or external original action callback')
                elif location in slots:raise ValueError('Relocated null original action callback')
            value=old+bytes((COUNT-NATIVE_COUNT)*4)
        data.extend(value)
        for hi,lo in pairs:
            for at,part in ((hi,(address+0x8000)>>16),(lo,address&65535)):
                if at in removed:raise ValueError('Overlapping extended action table references')
                before=u32(owner,at);patches.append(dict(offset=at,before=before,after=before&0xFFFF0000|part))
                removed.add(at)
        at=table['native_bound']-PLAYER_RAM;before=u32(owner,at)
        if at in slots:raise ValueError('Relocated action limit instruction')
        patches.append(dict(offset=at,before=before,after=before&0xFFFF0000|COUNT))
        table.update(offset=offset,ram=address,bytes=len(value),sha256=sha256(value),
            native_sha256=sha256(old),references=[(PLAYER_RAM+a,PLAYER_RAM+b) for a,b in pairs])
    if TABLE_OFFSET+len(data)>MODULE_SIZE-16:raise ValueError('Action tables exceed their reservation')
    return data,tables,patches,removed,rows,locations


def install(base,prior,blob,core,original,output):
    old=prior.get('equipment_resources',{})
    if not old.get('kind_readers') or old.get('player_actions') or old.get('bytes')!=SIZE:
        raise ValueError('Action tables require the complete, unextended equipment-kind module')
    at=old['blob_offset'];module=bytearray(blob[at:at+SIZE])
    if sha256(module)!=old['sha256'] or old['ram']!=RAM or old['vrom']!=BLOB+at:
        raise ValueError('Changed installed equipment module')
    if RAM+MODULE_SIZE>prior['furniture']['bank_pool']['start']:
        raise ValueError('Extended equipment code overlaps native furniture model banks')
    files=by_vrom(base);native=by_vrom(original)
    owner=files[PLAYER_VROM].extract(base);reloc=files[PLAYER_RELOC].extract(base)
    native_owner=native[PLAYER_VROM].extract(original);native_reloc=native[PLAYER_RELOC].extract(original)
    if sha256(owner)!=old['player_motion']['owner_sha256'] or reloc!=native_reloc:
        raise ValueError('Changed player owner or original relocations')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    data,tables,patches,removed,rows,locations=expanded_tables(source,native_owner,native_reloc)
    # Compare complete consumers, not just their changed instructions. Current
    # kind/resource adapters live outside these action consumers.
    boundaries=sorted(set(int(a,16) for a in re.findall(r'= 0x([0-9A-Fa-f]+); // type:func',
        (ROOT/'upstream/af/linker_scripts/jp/symbol_addrs_overlays.txt').read_text())))
    for table in tables:
        entry=table['native_entry'];end=min(x for x in boundaries if x>entry)
        a,b=entry-PLAYER_RAM,end-PLAYER_RAM
        if owner[a:b]!=native_owner[a:b]:raise ValueError('Changed complete native action consumer')
        table.update(native_end=end,native_consumer_sha256=sha256(owner[a:b]))
        a=table['native_table']-PLAYER_RAM;n=NATIVE_COUNT*table['width']
        if owner[a:a+n]!=native_owner[a:a+n]:raise ValueError('Changed original action metadata')
    code,compiled=compile_part('player_actions',output/'player_actions',primary_source='overlays/v3/player_actions.S')
    if len(code)>TABLE_OFFSET-CODE_OFFSET:raise ValueError('Player action code exceeds table boundary')
    for entry,register in DISPATCH:
        at=entry-PLAYER_RAM;before=u32(owner,at)
        if before!=register<<21|0xF809 or at in locations:
            raise ValueError('Changed native action indirect call')
        helper='af_v3_player_action_t9' if register==25 else 'af_v3_player_action_v0'
        patches.append(dict(offset=at,before=before,after=jump(compiled['symbols'][helper],link=True)))
    patched=bytearray(owner)
    for row in patches:
        at=row['offset']
        if u32(patched,at)!=row['before']:raise ValueError('Changed native action patch input')
        struct.pack_into('>I',patched,at,row['after'])
    # Remove only table-address relocations; original tables, callback pointers,
    # unrelated constants, and native calls retain their original relocations.
    kept=[record for record in rows if record not in {locations[x] for x in removed}]
    new_reloc=bytearray(reloc);struct.pack_into('>I',new_reloc,16,len(kept))
    new_reloc[20:-4]=struct.pack('>'+str(len(kept))+'I',*kept)+bytes(len(reloc)-24-len(kept)*4)
    module.extend(bytes(MODULE_SIZE-len(module)))
    module[CODE_OFFSET:CODE_OFFSET+len(code)]=code
    module[TABLE_OFFSET:TABLE_OFFSET+len(data)]=data
    struct.pack_into('>4I',module,MODULE_SIZE-16,*([GUARD]*4))
    blob.extend(bytes(-len(blob)%16));position=len(blob);blob.extend(module)
    if BLOB+len(blob)>END:raise ValueError('Extended actions exceed import ROM storage')
    report=copy.deepcopy(old)
    report.update(bytes=MODULE_SIZE,vrom=BLOB+position,blob_offset=position,
        sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=MODULE_SIZE-SIZE)
    report['player_motion']['owner_sha256']=sha256(patched)
    report['player_motion']['reloc_sha256']=sha256(new_reloc)
    report['player_actions']=dict(format='AFV3-PLAYER-ACTION-TABLES-1',
        native_count=NATIVE_COUNT,count=COUNT,tables=tables,code=compiled,
        table_offset=TABLE_OFFSET,table_bytes=len(data),code_offset=CODE_OFFSET,
        patches=sorted(patches,key=lambda r:r['offset']),removed_relocations=len(removed),
        owner_sha256=sha256(patched),relocation_sha256=sha256(new_reloc),
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()),
        disabled_indices=list(range(NATIVE_COUNT,COUNT)),enabled_imported_actions=[],
        constructor_ram=CTOR,constructor_slot=CTOR_SLOT,
        logical_imports_added=0,ordinary_actions_tested=False,fan_action_installed=False)
    return report,{PLAYER_VROM:bytes(patched),PLAYER_RELOC:bytes(new_reloc)}
