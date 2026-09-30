"""Install exclusive gameplay reuse of the complete title-only RAM reservation."""
import copy
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from apply_translation import write_new
from v3_asset_loader import ROOT, compile_part
from v3_import_storage import jump
from v3_private_save_bank import refresh_aliases

PLAY, RELOC, PLAY_RAM = 0x741FB0, 0x743950, 0x80802AE0
PLAY_SHA = '3c4572ab97426819a058758b98056c5b18bca2792fd454206a1409e9f6300bf1'
RELOC_SHA = '5ebbcf8973ded2b2dd5d0b8764ace09c7cf1396d6b5517f42b5de060149e4b2d'
CODE = 0x804F3280
SOURCES = ('tools/v3_scene_arena.py', 'overlays/v3/scene_arena.c',
           'overlays/v3/scene_arena.ld', 'tools/v3_furniture_install.py',
           'tools/v3_asset_loader.py', 'upstream/af/include/m_scene_table.h')


def install(base, prior, blob, core, module, output):
    del blob, module
    e=copy.deepcopy(prior['equipment_resources']); files=by_vrom(base)
    if e.get('scene_arena') or not e.get('private_save_bank',{}).get('installed'):
        raise ValueError('Scene repair requires the installed complete private save bank')
    play=bytearray(files[PLAY].extract(base)); reloc=files[RELOC].extract(base)
    if sha256(play)!=PLAY_SHA or sha256(reloc)!=RELOC_SHA or files[PLAY].pend:
        raise ValueError('Changed complete native play lifecycle or relocation')
    # Authenticate the exclusive title allocation and the complete native
    # segmented-arena API; do not extend the fixed ordinary main heap.
    if (bytes(core[0x801021F0-CODE_RAM:0x80102210-CODE_RAM]) != bytes.fromhex(
            '03c0000003c475e080a9fc7080ae72500000000080aa1f400000000000010000') or
            sha256(core[0x800D6600-CODE_RAM:0x800D66D0-CODE_RAM]) !=
            'ec21919b043c7d38702855d20000dc755aa13104e398afceb611b141a5332906'):
        raise ValueError('Changed exclusive title workspace owner')
    boot=files[0x1060].extract(base)
    if sha256(boot[0x7000:0x70A0])!='d02911cd7fcfb538994bc500b663cc5cc4f8a2482b3da61d8d4c21b24f2d7dde':
        raise ValueError('Changed complete native arena block-registration API')
    old=copy.deepcopy(e['console_storage']['packet'])
    raw=bytearray(base[old['physical']:old['physical']+old['bytes']])
    bank=e['private_save_bank']
    if (sha256(raw)!=old['sha256'] or old['ram']!=0x804DE200 or
            old['ram']+len(raw)!=0x804F4980 or
            bank['code']['ram']+bank['code']['bytes']>CODE):
        raise ValueError('Changed checked startup packet or private save code extent')
    code,compiled=compile_part('scene_arena',output/'scene_arena',link_symbols={
        'af_scene_native_init':0x8009C11C, 'af_scene_native_cleanup':0x8009C16C,
        'af_scene_native_add':0x8002CC60,
        'af_v3_save_halt':prior['save_runtime']['code']['symbols']['af_v3_save_halt']})
    at=CODE-old['ram']
    if any(raw[at:at+len(code)]) or CODE+len(code)>0x804F4900 or any(raw[0x804F4900-old['ram']:]):
        raise ValueError('Scene code overlaps retained startup data')
    raw[at:at+len(code)]=code
    patches=[]
    relocation_entries=struct.unpack_from('>'+str(u32(reloc,16))+'I',reloc,20)
    for address,before,name in ((0x808034BC,0x0C027047,'af_v3_scene_init'),
                                (0x808032DC,0x0C02705B,'af_v3_scene_cleanup')):
        offset=address-PLAY_RAM
        if u32(play,offset)!=before or any((r&0xFFFFFF)==offset for r in relocation_entries):
            raise ValueError('Changed native scene call or external-call relocation')
        after=jump(compiled['symbols'][name],link=True)
        struct.pack_into('>I',play,offset,after)
        patches.append(dict(address=address,before=before,after=after,delay_slot=u32(play,offset+4)))
    replacement=dict(old,sha256=sha256(raw),crc32=zlib.crc32(raw))
    refresh_aliases(e,old,replacement)
    records=copy.deepcopy(prior['physical_resources'])
    record=next(r for r in records if r['id']==old['id']); record['sha256']=replacement['sha256']
    report=dict(format='AFV3-SCENE-TITLE-WORKSPACE-1',installed=True,
        code=dict(compiled,ram=CODE),packet=replacement,
        workspace=dict(ram=0x80400000,end=0x80450000,bytes=0x50000,
            front_guard=0x80400000,end_guard=0x8044FFF0,sentinel=0x80400010,
            free_block=0x80400030,free_payload_bytes=0x4FFB0),
        ownership='Ordinary town/room scenes only, after title release and before native scene cleanup',
        borrowed_state=dict(ram=0x804F4900,bytes=4),
        gameplay_scenes=[6,7,9,12,14,17,18,20,21,22,23,24,25,29,31],
        title_loaded_pointer=0x80102200,native_main_heap_end=0x80400000,
        native_arena_functions_retained=True,allocated_cross_block_sentinel=True,
        play_sha256=sha256(play),previous_play_sha256=PLAY_SHA,relocation_sha256=RELOC_SHA,
        patches=patches,artwork_changed=False,saved_format_changed=False,
        native_execution_verified=False,sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    e['scene_arena']=report
    write_new(output/'scene_arena/installed.bin',code)
    return e,{PLAY:bytes(play)},{'physical_resources':records},[
        (dict(record,previous_sha256=old['sha256']),bytes(raw))]
