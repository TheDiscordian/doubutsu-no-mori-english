"""Checked shared water/mud consumers for the complete insect category."""
import struct

from aflib import by_vrom,sha256
from v3_import_storage import jump
from v3_npc_clothing import guard_incoming
from v3_player_actions import native_references

OWNERS=(
    (69,0x927440,0x927860,0x80A671A0,
     '4c7ca9815ec0c5640b83826f01bd704923aad459f4a4f76e6b3faea28c7d7b9d',
     '84dd6aa15a89641b838f35d361a45d96c9792162136b8da059ffd74e4e8cfe9f'),
    (70,0x927910,0x928170,0x80A67670,
     '81edf3700ff7d62a8bd3148609f897a7bb52be7534a465d58a3998b6488d316c',
     '8cef31ab3b6036300c4e83751bbe7a47e971c8309c27230fef5942ff19afd253'),
    (85,0x8EED90,0x8EF400,0x80A272F0,
     'c7435068ea531fe26dc205a1c7ab67c74818a125a8aefd524bbdcd540c4a5b3b',
     'd5db030085f119e6b0d075f99b68e07853d5446b04976ee316bfcdc240a69380'))


def contract(image,prior,source):
    files=by_vrom(image);controller=prior['equipment_resources']['room_rigs']['effects']['controller']
    data=files[controller['vrom']].extract(image)
    if sha256(data)!=controller['sha256']:raise ValueError('Changed effect controller')
    table=controller['tables'][0]
    if table['stride']!=20 or sha256(data[table['offset']:table['offset']+table['bytes']])!=table['sha256']:
        raise ValueError('Changed live effect descriptor table')
    rows=[];functions=[];profiles=[]
    # Local eTM_* symbols also name an unrelated effect. Resolve callbacks
    # through each actual profile's relocations, never an ambiguous short name.
    for name in ('iam_ef_turi_hamon','iam_ef_turi_mizu','iam_ef_dig_mud'):
        at,size=source.symbol(name);raw=source.raw(name)
        if size!=24 or raw[:16]!=bytes(16):raise ValueError('Changed donor field effect profile')
        addresses=[]
        for offset in range(0,16,4):
            ref=source.section_relocations.get((5,at+offset))
            if ref is None or ref[:3]!=(1,1,1):raise ValueError('Unbound source effect callback')
            addresses.append(ref[3]);functions.append(source.function(ref[3])[1])
        profiles.append(dict(symbol=name,offset=at,sha256=sha256(raw),callbacks=addresses))
    addresses=[a for a,names in source.functions.items() if any(n=='eTM_CallEffect' for n,_ in names)]
    if len(addresses)!=1:raise ValueError('Missing complete donor water subeffects')
    functions.append(source.function(addresses[0])[1])
    for index,vrom,reloc,ram,digest,rel_digest in OWNERS:
        owner=files[vrom].extract(image);rel=files[reloc].extract(image)
        if sha256(owner)!=digest or sha256(rel)!=rel_digest:
            raise ValueError('Changed complete native field effect')
        desc=struct.unpack_from('>5I',data,table['offset']+20*index)
        if desc[:3]!=(vrom,reloc,ram):raise ValueError('Changed native field effect identity')
        rows.append(dict(type=index,vrom=vrom,reloc=reloc,ram=ram,sha256=digest,
            reloc_sha256=rel_digest,descriptor=list(desc),
            functions=list(struct.unpack_from('>4I',owner,desc[4]-ram))))
    mud=rows[-1];owner=files[mud['vrom']].extract(image);rel=files[mud['reloc']].extract(image)
    at=0x80A2736C-mud['ram'];sections=struct.unpack_from('>4I',rel)
    _,_,_,locations,_=native_references(owner,rel,expected_sections=sections)
    guard_incoming(owner,sections[0],mud['ram'],[(at,4)])
    if owner[at:at+8]!=bytes.fromhex('0320F80900000000') or at in locations:
        raise ValueError('Changed native mud constructor dispatch')
    return dict(native=rows,source_functions=functions,source_profiles=profiles,clip=0x80136F3C,
        source_mud_type=84,native_mud_type=85,small_mud_flag=0x4000,small_scale=0.005,
        mud_hook=dict(vrom=mud['vrom'],address=0x80A2736C,offset=at,
            before='0320f809',symbol='af_insect_mud_create'),
        source_ticks_per_native_update=2,native_water_and_mud_timing_retained=True,
        additional_effect_slots=0,installed=False)


def install(image,symbols,prepared):
    files=by_vrom(image);mud=prepared['native'][-1];hook=prepared['mud_hook']
    owner=bytearray(files[mud['vrom']].extract(image));rel=files[mud['reloc']].extract(image)
    if sha256(owner)!=mud['sha256'] or sha256(rel)!=mud['reloc_sha256']:
        raise ValueError('Changed prepared mud owner')
    target=symbols[hook['symbol']]
    if target&3 or not 0x80000000<=target<0x80800000:
        raise ValueError('Mud bridge is not resident executable RAM')
    at=hook['offset']
    if owner[at:at+4]!=bytes.fromhex(hook['before']):raise ValueError('Changed mud constructor call')
    after=struct.pack('>I',jump(target,link=True));owner[at:at+4]=after
    return {mud['vrom']:bytes(owner)},dict(hook,target=target,after=after.hex())
