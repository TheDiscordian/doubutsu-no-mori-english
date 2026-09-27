"""Complete controller capacity for both native and donor insect populations.

The native setup, graphics transfer, movement, and drawing paths retain their
implementations. Extend their common allocation/loop bounds together, and replace
the clip's two-slot creator only after the complete runtime is loaded.
"""
import struct

from aflib import by_vrom,sha256,u32
from v3_player_actions import native_references

VROM,RELOC,RAM=0x8DEEC0,0x8E0870,0x80A10210
PATCHES=(
    (0x80A10248,0xACCE08F4,0xACCE17F4,'constructor bank field'),
    (0x80A1027C,0x24040003,0x24040009,'destructor program slots'),
    (0x80A10330,0x24062400,0x24066C00,'graphics bank allocation'),
    (0x80A10348,0xAF0F08F4,0xAF0F17F4,'allocated bank field'),
    (0x80A10420,0x24140003,0x24140009,'graphics reload slots'),
    (0x80A10424,0x8C4E08F4,0x8C4E17F4,'graphics reload bank field'),
    (0x80A10640,0x8C6A08F4,0x8C6A17F4,'creation bank field'),
    (0x80A11224,0x24010003,0x24010009,'movement slots'),
    (0x80A1163C,0x24010003,0x24010009,'drawing slots'),
    (0x80A116A0,0x000008F8,0x000017F8,'controller allocation'),
)
FUNCTIONS=(
    (0x80A10210,0x80A102B8,'ceceb00fbf78bfb02831e6f0073c38b968e03dac21b2a17c02a0f7cadbd835aa'),
    (0x80A10314,0x80A1035C,'3dba520579fd44fdfa4fa75be6986ec6dab98a9f07a3a59fe69598400ceec3fb'),
    (0x80A103F8,0x80A10494,'2258c389d364e3f23852fdf4f1f34d1cb07f8cd45b41f8e797b338d5dd1a2925'),
    (0x80A104F8,0x80A109A4,'b19ac265df1c87244508eabc07974581978bbb84211410c82c95097f5f74f29a'),
    (0x80A109A4,0x80A10A20,'4f35865f52f005590547cd72d90c665a1ae9dc63b5c9bebf131faee8f9255ccf'),
    (0x80A1102C,0x80A11264,'a32b9642d869accdfeca58522825f5d58c816b319572e4cb8b1482b2f1076c54'),
    (0x80A114A8,0x80A11684,'759c6745ebaf309e3ed8f8bd33984a09813184ddf23f7865f1b281134e6b8bdf'),
)


def contract(image,source):
    files=by_vrom(image);owner=files[VROM].extract(image);rel=files[RELOC].extract(image)
    sections=struct.unpack_from('>5I',rel)
    groups,_,_,locations,_=native_references(owner,rel,expected_sections=sections[:4])
    functions=[]
    for start,end,digest in FUNCTIONS:
        if sha256(owner[start-RAM:end-RAM])!=digest:
            raise ValueError('Changed complete native insect population consumer')
        functions.append(dict(address=start,end=end,sha256=digest))
    patches=[]
    for address,before,after,purpose in PATCHES:
        if u32(owner,address-RAM)!=before or address-RAM in locations:
            raise ValueError('Changed or relocated native insect population word')
        patches.append(dict(address=address,before=before,after=after,purpose=purpose))
    # Native free-slot lookup is called only by the old make function; that
    # function's sole address reference is the clip assignment replaced at bind.
    callers=[]
    for target,expected_calls,expected_refs in (
            (0x80A104F8,[0x80A108C0],[]),
            (0x80A108AC,[],[(0x80A109BC,0x80A109C4)]),
            (0x80A10558,[0x80A1096C],[])):
        calls=[RAM+at for at in range(0,sections[0],4) if u32(owner,at)>>26 in (2,3)
               and ((u32(owner,at)&0x3FFFFFF)*4|(RAM&0xF0000000))==target]
        refs=[(RAM+hi,RAM+lo) for hi,lows in groups.items() for lo,value in lows if value==target]
        if calls!=expected_calls or refs!=expected_refs:
            raise ValueError('Unaccounted native insect creation consumer')
        callers.append(dict(target=target,calls=calls,address_references=refs))
    donor=[]
    for name in ('aINS_actor_ct','aINS_actor_dt','aINS_actor_move','aINS_actor_draw',
                 'aINS_searchRegistSpace','aINS_make_insect','aINS_make_actor',
                 'aINS_init_dma_and_clip_area'):
        addresses=[at for at,names in source.functions.items() if any(n==name for n,_ in names)]
        if len(addresses)!=1:raise ValueError('Missing donor population function: '+name)
        donor.append(source.function(addresses[0])[1])
    return dict(owner_vrom=VROM,reloc_vrom=RELOC,owner_ram=RAM,
        owner_sha256=sha256(owner),reloc_sha256=sha256(rel),native_functions=functions,
        patches=patches,creation_consumers=callers,source_functions=donor,
        original_slots=3,slots=9,wild_slots={'N64':2,'GameCube':8},release_slot=8,
        slot_bytes=0x280,controller_bytes=0x17F8,graphics_bytes=0x6C00,
        program_bytes_per_slot=0x1C00,retained_native_programs=3,
        resident_program_buffer_bytes=6*0x1C00,
        additional_scene_bytes=(0x17F8-0x8F8)+(0x6C00-0x2400),
        setup_address=0x80A10558,setup_return_delta=0x2FC,
        native_spacing_square=40,donor_spacing_exclusion=False,
        installed=False,native_execution_tested=False)


def install(image,prepared,changes=None):
    """Compose with controller hooks, retaining all other code and relocations."""
    files=by_vrom(image);original=files[VROM].extract(image);rel=files[RELOC].extract(image)
    if sha256(original)!=prepared['owner_sha256'] or sha256(rel)!=prepared['reloc_sha256']:
        raise ValueError('Changed prepared insect population owner')
    changed=dict(changes or {});owner=bytearray(changed.get(VROM,original))
    if len(owner)!=len(original) or prepared['patches']!=[
            dict(address=a,before=b,after=c,purpose=p) for a,b,c,p in PATCHES]:
        raise ValueError('Changed insect population contract')
    for patch in prepared['patches']:
        at=patch['address']-RAM
        if u32(owner,at)!=patch['before']:raise ValueError('Overlapping insect population patch')
        struct.pack_into('>I',owner,at,patch['after'])
    changed[VROM]=bytes(owner)
    return changed,dict(prepared,runtime_installation_required=True)
