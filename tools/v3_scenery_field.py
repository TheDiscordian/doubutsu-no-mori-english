"""Shared field/insect consumers; retain native layout, scheduling, and species."""
import struct
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from v3_import_storage import jump
from v3_npc_clothing import guard_incoming
from v3_player_actions import native_references

RAM,VROM,RELOC=0x8092A030,0x821B40,0x8240D0
SCAN,GATE,MATCH=0x8092A258,0x8092A278,0x8092A88C
NATIVE=((SCAN,0x8092A328,'18ac7773049e0d494c8fea9af75abd41922e9c009b48547bcc5553570dd7f37b'),
    (0x8092A76C,0x8092AB8C,'2b32068017a8485cb1da0eddf789401e7b1825becff4eed3e45ffab927c23af4'),
    (0x8092AB8C,0x8092AE10,'0b8b9ab1d3eb013eac482d99638c344587242fe65d6c37f95f03badd8ba5ed59'))
DONOR=((0x7DE98,'14de1a74aba0aebaa04c32f1be1200149e28f1bcbb293a3b42895281cad4a872'),
    (0x12B590,'d6a411333584c2e70d126caa01850a899d3103561308943aad87e8c6f145b58d'),
    (0x12BE14,'4ad86dea8a1728f22369b4ea512534c8a8ef4815ce10f81bf0358fa9f740b56f'))


def contract(source,base,original):
    files=by_vrom(base);retail=by_vrom(original)
    data,rel=(files[v].extract(base) for v in (VROM,RELOC));core=files[CODE_VROM].extract(base)
    if data!=retail[VROM].extract(original) or rel!=retail[RELOC].extract(original):
        raise ValueError('Changed complete native insect owner')
    sources=[]
    for offset,digest in DONOR:
        raw,receipt=source.function(offset)
        if sha256(raw)!=digest:raise ValueError('Changed complete source field/insect consumer')
        sources.append(receipt)
    functions=[]
    for start,end,digest in NATIVE:
        if sha256(data[start-RAM:end-RAM])!=digest:raise ValueError('Changed complete native insect consumer')
        functions.append(dict(start=start,end=end,sha256=digest))
    sections=struct.unpack_from('>5I',rel)
    if sections!=(4080,5536,0,784,259):raise ValueError('Changed insect owner dimensions')
    _,_,records,locations,_=native_references(data,rel,expected_sections=sections[:4])
    spans=[(SCAN-RAM,0xD0),(MATCH-RAM,32)]
    guard_incoming(data,sections[0],RAM,spans)
    if any(any(a<=p<a+n for a,n in spans) for p in locations):raise ValueError('Unexpected insect query relocation')
    if struct.unpack_from('>12H',data,0x8092C5A8-RAM)!=(0x804,0x845,0,0,0,0,0x804,0x84D,0,0,0,0):
        raise ValueError('Changed native insect habitat range table')
    if [p for p in range(0,sections[0],4) if u32(data,p)==jump(SCAN,link=True)]!=[0x8092ACBC-RAM]:
        raise ValueError('Changed complete insect scan call inventory')
    a,b=0x800C3398-CODE_RAM,0x800C33CC-CODE_RAM
    if (sha256(core[a:b])!='a9c3135018c2522d8ad42c514b2697cb6a12196698201bcac0e6a7c5887bbba8'
            or core[a:b]!=retail[CODE_VROM].extract(original)[a:b]):
        raise ValueError('Changed native tree clearing consumer')
    guard_incoming(core,len(core),CODE_RAM,[(a,12)])
    callers=[p+CODE_RAM for p in range(0,len(core),4) if u32(core,p)==jump(0x800C3398,link=True)]
    if callers!=[0x800C33EC,0x800C3494,0x800C34A0,0x800C34AC,0x800C34B8]:
        raise ValueError('Changed native edge/entrance clearing callers')
    return dict(sources=sources,functions=functions,sections=sections,resident_bytes=sum(sections[:4]),
        ram=RAM,vrom=VROM,reloc=RELOC,previous_sha256=sha256(data),previous_reloc_sha256=sha256(rel),
        clear_entry=0x800C3398,clear_sha256=sha256(core[a:b]),clear_callers=callers,
        native_entrance_cells=[7,8,23,24],spans=spans),data,rel,records


def dispatch(target,bootstrap):
    return (0x3C190000|((target+0x8000)>>16),jump(bootstrap),0x27390000|(target&65535))


def install(evidence,owner,rel,records,core,bootstrap,symbols):
    data=bytearray(owner);relocation=bytearray(rel);shared=bootstrap['symbols']['af_v3_tree_query_dispatch']
    def write(at,words):struct.pack_into('>'+str(len(words))+'I',data,at-RAM,*words)
    data[SCAN-RAM:SCAN-RAM+0xD0]=bytes(0xD0)
    write(SCAN,dispatch(symbols['af_v3_tree_insect_scan'],shared))
    target=symbols['af_v3_tree_insect_match']
    # Preserve the caller's live height and constant-four registers. Callee-saved
    # integer/FPU registers retain their ordinary o32 ABI; HI/LO are redefined
    # by the original coordinate multiply after this predicate.
    gate=(0x27BDFFE0,0xAFBF0018,0xAFA30010,0xAFA50014,0x96C40000,0x97A50092,0x97A60096,
          0x3C190000|((target+0x8000)>>16),jump(shared,link=True),0x27390000|(target&65535),
          0x8FA30010,0x8FA50014,0x8FBF0018,0x03E00008,0x27BD0020)
    write(GATE,gate)
    branch=0x10400000|((0x8092A9A4-(MATCH+8)-4)//4&65535)
    write(MATCH,(jump(GATE,link=True),0,branch,0,0,0,0,0))
    added=[0x44000000|(MATCH-RAM)];updated=[*records,*added]
    if 24+4*len(updated)>len(relocation) or set(records)&set(added):
        raise ValueError('Insect query relocation exceeds existing padding')
    struct.pack_into('>I',relocation,16,len(updated))
    relocation[20:-4]=struct.pack('>'+str(len(updated))+'I',*updated)+bytes(len(relocation)-24-4*len(updated))
    at=evidence['clear_entry']-CODE_RAM;before=bytes(core[at:at+12])
    after=struct.pack('>3I',*dispatch(symbols['af_v3_tree_clear'],shared));core[at:at+12]=after
    patches=[dict(offset=p,before=u32(owner,p),after=u32(data,p)) for p in range(0,len(data),4) if u32(owner,p)!=u32(data,p)]
    receipt=dict(evidence,sha256=sha256(data),reloc_sha256=sha256(relocation),patches=patches,
        gate_ram=GATE,gate_bytes=len(gate)*4,added_relocations=added,
        core_hooks=[dict(offset=at,before=before.hex(),after=after.hex())],additional_resident_bytes=0,
        additional_scene_resident_bytes=0,ordinary_gameplay_tested=False,native_test='pending')
    return {VROM:bytes(data),RELOC:bytes(relocation)},receipt
