"""Shared player tree predicates, with a register-preserving lazy-loading gate.

Reclaim one replaced inline predicate for the gate; actor size, saved data, and
the native target/animation/bee routines remain unchanged. No per-item hooks.
"""
import struct

from aflib import by_vrom,sha256,u32
from v3_import_storage import jump
from v3_player_actions import native_references
from v3_npc_clothing import guard_incoming

RAM,VROM,RELOC=0x808B2D50,0x7AC420,0x7D9BA0
GATE=0x808B6934
# Complete donor function, digest, and matching complete native consumer.
FUNCTIONS=(
    (0x168038,'31376ee3cdc2f227a29478ef4491d90c108d96e628d0c27ef68f965f7f4b6220',0x808B6458,0x808B7CDC),
    (0x16B6A0,'5887dcac121405c2900995729c9b5fb9c73325a92bd1a1e5ffd64b3fd3b992a7',0x808B996C,0x808BA0B0),
    (0x16BF6C,'30c6c062a6af75982f30e5f50e1e93cb61329473c5083b6ebed22adef06f1851',0x808BA388,0x808BA7BC),
    (0x16C9E8,'707a0b353e149ecd4c48947308ab86523e7cd254dc693fbd5f42d358e7381356',0x808BAE38,0x808BAF40),
    (0x17FCBC,'ce386a711cd93f4645d362dad154f7dc13f3f9f27535d1b02c8e15355f812b0b',0x808CA400,0x808CA4C8),
    (0x188498,'8a3c8e17051865dce282727a4070417b948d4331ad9aa91ab2654b28dc915913',0x808D14A8,0x808D1A78),
    (0x188A98,'acd606be19cba1eaa19419aa973bd85ba0337a7047622e5729ecb14e85c4a287',0x808D1AE8,0x808D1F4C),
    (0x190A9C,'7645884f6a3e16b3215579a81d1bddedcdafb00800703f434ff5f370e3c24d01',0x808D8C78,0x808D90B8),
)
# The retained first comparisons also retain their original stores/delay slots.
# start, end, source register, result register, query (solid/shakeable/bee).
PREDICATES=((0x808B68F4,0x808B6C24,3,6,0),
    (0x808B709C,0x808B73CC,2,6,0),(0x808B755C,0x808B788C,2,6,0),
    (0x808B9A6C,0x808B9E50,4,3,0),(0x808BA410,0x808BA6A4,6,2,1),
    (0x808D14F0,0x808D1820,15,2,0),(0x808D1B9C,0x808D1ECC,8,2,0),
    (0x808D8CCC,0x808D8FFC,25,2,0))
BEE_SPANS=((0x808BAE7C,12),(0x808CA444,48),(0x808D9064,36))


def contract(source,base,original,actions):
    files=by_vrom(base);native=by_vrom(original)[VROM].extract(original)
    owner,rel=(files[v].extract(base) for v in (VROM,RELOC))
    if sha256(owner)!=actions['owner_sha256'] or sha256(rel)!=actions['relocation_sha256']:
        raise ValueError('Changed installed player tree consumer')
    sections=struct.unpack_from('>5I',rel)
    _,_,records,locations,_=native_references(owner,rel,expected_sections=sections[:4])
    functions=[]
    for offset,digest,start,end in FUNCTIONS:
        raw,receipt=source.function(offset)
        a,b=start-RAM,end-RAM
        if sha256(raw)!=digest or owner[a:b]!=native[a:b]:
            raise ValueError('Changed complete source/native player tree function')
        functions.append(dict(source=receipt,start=start,end=end,native_sha256=sha256(native[a:b])))
    spans=[(a-RAM,b-a) for a,b,*_ in PREDICATES]+[(a-RAM,n) for a,n in BEE_SPANS]
    # The common-bee delay slot reloads the same real item instead of using t8.
    spans.append((0x808BAE88-RAM,4))
    guard_incoming(owner,sections[0],RAM,spans)
    if any(any(a<=p<a+n for a,n in spans) for p in locations):
        raise ValueError('Unexpected original relocation inside player predicates')
    def ids(a,b):
        return sorted({u32(native,p)&65535 for p in range(a-RAM,b-RAM,4) if u32(native,p)>>26==14})
    solid=ids(0x808B68E4,0x808B6C24);small=ids(0x808B9748,0x808B97E8)
    shakeable=ids(0x808BA400,0x808BA6A4)
    if len(solid)!=60 or len(small)!=10 or set(shakeable)!=set(solid)-set(small):
        raise ValueError('Changed native solid/shakeable tree categories')
    if [v for v in solid if v<0x800]!=[0x5e,0x5f,0x60,0x61,0x69] or any(v>=0x860 for v in solid):
        raise ValueError('Native tree predicates exceed the verified bitmap')
    masks=[[sum(1<<(v-0x800-i*32) for v in values if 0x800+i*32<=v<0x820+i*32)
            for i in range(3)] for values in (solid,small)]
    return dict(functions=functions,vrom=VROM,reloc=RELOC,ram=RAM,sections=sections,
        resident_bytes=sum(sections[:4]),previous_sha256=sha256(owner),previous_reloc_sha256=sha256(rel),
        masks=masks,solid_ids=solid,small_ids=small,shakeable_ids=shakeable,
        spans=spans,gate_ram=GATE),owner,rel,records


def gate(load,query):
    """Preserve every live caller register, HI/LO, and floating-point state.

    The jal delay slot is an inert `ori zero,zero,metadata`. Reading that word
    gives source/result registers and query kind without clobbering a register.
    Saved register slots are indexed by architectural register number.
    """
    regs=(*range(1,16),24,25,31)
    words=[0x27BDFF00]  # 256-byte aligned frame; 16-byte outgoing argument area.
    words += [0xAFA00000|r<<16|(16+4*r) for r in regs]
    words += [0x00004010,0xAFA80090,0x00004812,0xAFA90094,0x444AF800,0xAFAA0098]
    words += [0xF7A00000|r<<16|(160+4*r) for r in range(0,20,2)]
    words += [jump(load,link=True),0,0x1040000B,0]
    # Recover the metadata after lazy loading, then call the shared query.
    words += [0x8FA8008C,0x8D09FFFC,0x312A001F,0x000A5080,0x015D5021,
              0x8D440010,0x00092A82,0x30A5003F,jump(query,link=True),0,
              0x8FA8008C,0x8D09FFFC,0x000948C2,0x3129007C,0x013D4821,0xAD220010]
    words += [0x8FA80090,0x01000011,0x8FA90094,0x01200013]
    words += [0xD7A00000|r<<16|(160+4*r) for r in range(0,20,2)]
    words += [0x8FAA0098,0x44CAF800]
    words += [0x8FA00000|r<<16|(16+4*r) for r in regs]
    words += [0x03E00008,0x27BD0100]
    data=struct.pack('>'+str(len(words))+'I',*words)
    if GATE+len(data)>PREDICATES[0][1]:raise ValueError('Player gate exceeds replaced predicate')
    return data


def descriptor(source,result,query):
    if source not in (*range(1,16),24,25) or result not in (*range(1,16),24,25) or query not in range(3):
        raise ValueError('Unsupported inline query ABI')
    return 0x34000000|source|(result<<5)|(query<<10)


def install(evidence,owner,rel,records,bootstrap,symbols):
    data=bytearray(owner);removed=set();added=[]
    def write(address,words):
        struct.pack_into('>'+str(len(words))+'I',data,address-RAM,*words)
    def branch(at,target,reg,nonzero=False):
        return (0x14000000 if nonzero else 0x10000000)|reg<<21|((target-at-4)//4&65535)
    for a,b,src,dst,kind in PREDICATES:
        data[a-RAM:b-RAM]=bytes(b-a)
        write(a,[jump(GATE,link=True),descriptor(src,dst,kind),branch(a+8,b,0),0])
        added.append(0x44000000|(a-RAM))
    # Common bee release: keep clip/null/coordinate checks and the actual ID.
    write(0x808BAE7C,[jump(GATE,link=True),descriptor(5,2,2),branch(0x808BAE84,0x808BAF2C,2),0x97A4003E])
    # Cut count is saved before the query; the native callback keeps all args.
    write(0x808CA444,[0xAFA20034,0x97A40042,jump(GATE,link=True),descriptor(4,2,2),
        branch(0x808CA454,0x808CA47C,2,True),0x3C0E8013,0x8DCE6F20,0x8FA50044,
        0x8DD90038,0x27A70028,0x0320F809,0x8FA60048])
    # Keep the original null-callback return, five-frame bee timer, and drop.
    write(0x808D9064,[branch(0x808D9064,0x808D90A8,3),0x27A70034,
        jump(GATE,link=True),descriptor(8,2,2),branch(0x808D9074,0x808D9090,2,True),
        0x97A40042,0x8FA5004C,0x0060F809,0x8FA60048])
    added += [0x44000000|(a-RAM) for a in (0x808BAE7C,0x808CA44C,0x808D906C)]
    code=gate(bootstrap['symbols']['load'],symbols['af_v3_tree_player_query'])
    data[GATE-RAM:GATE-RAM+len(code)]=code
    if set(records)&set(added):raise ValueError('Duplicate player query relocation')
    # The loader caches HI16 values by register. Preserve the original order;
    # sorting by relocation type would pair many LO16 sites with the wrong HI16.
    updated=[v for v in records if v not in removed]+added
    # This relocation owner has retained padding; no section/actor growth.
    relocation=bytearray(rel)
    if 24+len(updated)*4>len(relocation):raise ValueError('Player query relocations exceed existing owner')
    struct.pack_into('>I',relocation,16,len(updated))
    relocation[20:-4]=struct.pack('>'+str(len(updated))+'I',*updated)+bytes(len(relocation)-24-4*len(updated))
    patches=[dict(offset=p,before=u32(owner,p),after=u32(data,p)) for p in range(0,len(data),4)
             if u32(owner,p)!=u32(data,p)]
    receipt=dict(evidence,sha256=sha256(data),reloc_sha256=sha256(relocation),patches=patches,
        added_relocations=added,removed_relocations=sorted(removed),gate_bytes=len(code),gate_sha256=sha256(code),
        calls=[dict(address=a,source=src,result=dst,query=kind) for a,b,src,dst,kind in PREDICATES]+
            [dict(address=a,source=src,result=2,query=2) for a,src in ((0x808BAE7C,5),(0x808CA44C,4),(0x808D906C,8))],
        additional_resident_bytes=0,additional_scene_resident_bytes=0,ordinary_gameplay_tested=False,native_test='pending')
    return bytes(data),bytes(relocation),receipt
