"""Connect the complete creature collection to native passport travel."""
import copy
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32,verified_rom
from v3_asset_loader import ROOT,compile_part
from v3_console_disk_install import reservations
from v3_creature_save import DEFINES
from v3_import_storage import jump
from v3_npc_clothing import guard_incoming

RAM,SIZE,STATE=0x80655000,0xC000,0x80655FC0
SOURCES=('tools/v3_creature_travel.py','overlays/v3/creature_travel.c',
    'overlays/v3/creature_travel.ld','overlays/v3/creature_collection.c',
    'tools/v3_creature_fish.py','tools/v3_furniture_pipeline.py',
    'tools/v3_asset_loader.py','tools/v3_room_goods.py')


def install(base,prior,blob,output,core):
    e=copy.deepcopy(prior['equipment_resources']);fish=e['creature_fish'];w=fish['world'];p=w['packet']
    if not e['creature_items'].get('optional_selection') or w.get('creature_travel'):
        raise ValueError('Creature travel requires the selected complete fish category')
    files=by_vrom(base);at=p['blob_offset'];before=bytes(blob[at:at+p['bytes']])
    if (core is None or bytes(core)!=files[CODE_VROM].extract(base) or
            p['ram']!=0x8064A000 or p['bytes']!=0xB000 or at+p['bytes']!=len(blob) or
            sha256(before)!=p['sha256'] or zlib.crc32(before)!=p['crc32']):
        raise ValueError('Creature travel requires the checked current native core and packet tail')
    if (p['ram']+SIZE>0x807DA800 or
            any(a<p['ram']+SIZE and RAM<b for a,b in reservations(prior))):
        raise ValueError('Creature travel overlaps another Expansion Pak reservation')
    stable=e['console_storage']['compiled']['symbols']
    code,compiled=compile_part('creature_travel',output/'creature_travel',
        extra_sources=('overlays/v3/creature_collection.c',),defines=DEFINES+('AF_V3_CREATURE_VISITORS=1',),
        link_symbols={'AF_CREATURE_ITEM_TYPE':e['creature_items']['code']['symbols']['af_v3_creature_item_type'],
            'AF_CREATURE_SAVE_COLLECT':w['save']['codec']['symbols']['af_v3_save_collect_extended'],
            'AF_CREATURE_REQUIRE_STATE':stable['af_v3_require_save_state'],
            'AF_CREATURE_SAVE_HALT':stable['af_v3_save_halt']})
    if len(code)>STATE-RAM:raise ValueError('Creature travel overlaps live visitor state')
    packet=bytearray(before+bytes(SIZE-len(before)));packet[RAM-p['ram']:RAM-p['ram']+len(code)]=code
    packet[-16:]=struct.pack('>4I',*([0xAF465748]*4))
    oldcode=w['compiled'];offset=oldcode['symbols']['af_v3_creature_collected']-p['ram']
    if sha256(before[:oldcode['bytes']])!=oldcode['sha256']:
        raise ValueError('Changed complete installed collection adapter')
    original=before[offset:offset+8];replacement=struct.pack('>2I',jump(compiled['symbols']['af_v3_creature_collected']),0)
    guard_incoming(before,oldcode['bytes'],p['ram'],[(offset,8)])
    packet[offset:offset+8]=replacement
    oldcode['sha256']=sha256(packet[:oldcode['bytes']])

    original_rom=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    native_core=by_vrom(original_rom)[CODE_VROM].extract(original_rom)
    # Check the complete native Pak implementation, including its unused header
    # and tail fields, rather than assuming zero-looking space is available.
    if core[0x80078E90-CODE_RAM:0x8007A0C0-CODE_RAM]!=native_core[0x80078E90-CODE_RAM:0x8007A0C0-CODE_RAM]:
        raise ValueError('Changed native passport allocation/copy/checksum contract')
    if core[0x80116808-CODE_RAM:0x80116810-CODE_RAM]!=struct.pack('>2I',0x1200,0x6700):
        raise ValueError('Changed native Pak note sizes')
    patches=[]
    for address,end,name in ((0x80079080,0x800790C0,'passport_clear'),
            (0x800793B8,0x8007942C,'passport_save'),(0x8007942C,0x800794E4,'passport_load'),
            (0x800B7F48,0x800B7F78,'private_copy')):
        pos=address-CODE_RAM;function=bytes(core[pos:end-CODE_RAM])
        if function!=native_core[pos:end-CODE_RAM]:raise ValueError('Changed native passport/private function')
        guard_incoming(core,len(core),CODE_RAM,[(pos,8)])
        after=struct.pack('>2I',jump(compiled['symbols']['af_v3_creature_'+name]),0)
        core[pos:pos+8]=after
        patches.append(dict(address=address,bytes=end-address,function_sha256=sha256(function),
            before=function[:8].hex(),after=after.hex()))
    next(o for o in w['manager_owners'] if o['name']=='completion')['sha256']=sha256(core)
    blob[at:]=packet;p.update(bytes=SIZE,sha256=sha256(packet),crc32=zlib.crc32(packet))
    w['creature_travel']=dict(format='AFV3-CREATURE-TRAVEL-1',code=compiled,ram=RAM,
        visitor_ram=STATE,visitor_bytes=28,passport_bytes=0x1200,capsule_offset=0x11C0,capsule_bytes=48,
        capsule_version=1,player_identity_bytes=16,profile_bytes=4,collection_bytes=4,
        installed=True,native_execution_tested=False,ordinary_travel_tested=False,
        complete_import_travel_supported=False,
        retained_native_contract_sha256=sha256(native_core[0x80078E90-CODE_RAM:0x8007A0C0-CODE_RAM]),
        patches=patches,collection_redirect=dict(address=p['ram']+offset,before=original.hex(),after=replacement.hex()),
        warning='Added creature records travel only between compatible V3 profiles. V2 and older V3 passport readers do not understand this extension. Other imported catalogue/console travel remains unfinished.')
    e['creature_items']['optional_selection']['controller_pak_collection_installed']=True
    e['creature_items']['remaining']=['added insect field behaviours','other import travel','ordinary gameplay and save/reload']
    fish.update(additional_resident_bytes=0x1000,
        pending=['other import Controller Pak transport','ordinary gameplay and native save/reload'],
        sources={path:sha256((ROOT/path).read_bytes()) for path in (*fish['sources'],*SOURCES)})
    return e,{}
