"""Install format-4 surface profiles/ownership while retaining stable save APIs."""
import copy
import struct
import zlib

from aflib import CODE_RAM,sha256
from v3_asset_loader import ROOT,BLOB,compile_part
from v3_import_storage import jump
from v3_save_clothing import DEFINES as CODEC_DEFINES
from v3_surface_items import RAM,TABLE,BOOT,BOOT_END

SIZE,STATE_BYTES,WORKING_BYTES=0x4000,1232,1200
DEFINES=('AF_V3_CLOTHING_PROFILE=1','AF_V3_REWARD_PROFILE=1','AF_V3_SURFACE_PROFILE=1')
SOURCES=('tools/v3_surface_save.py','overlays/v3/surface_save.c','overlays/v3/surface_save.ld',
    'overlays/v3/surface_codec.ld','overlays/v3/surface_save_runtime.ld',
    'overlays/v3/save_codec.c','overlays/v3/save_codec.h','overlays/v3/save_runtime.c',
    'overlays/v3/save_runtime.h','overlays/v3/surface_bootstrap.c',
    'overlays/v3/surface_bootstrap.ld','tools/v3_display_aliases.py','tools/v3_optional_composition.py')


def words(*v):return struct.pack('>'+str(len(v))+'I',*v)


def install(prior,blob,core,output):
    surface=copy.deepcopy(prior['room_surfaces']);items=surface['items']
    if not surface.get('application') or surface.get('save'):
        raise ValueError('Surface saves require installed room application and no prior format-4 stage')
    if (prior['save_codec']['format_version']!=3 or prior['save_runtime']['state_bytes']!=912
            or prior['save_runtime']['guard_ram']!=0x8046C380 or items['bytes']!=0x1000
            or RAM+SIZE>0x80500000 or 0x8046C000+STATE_BYTES>0x8046D000):
        raise ValueError('Changed surface state or resident memory bounds')
    at=items['blob_offset'];packet=bytearray(blob[at:at+items['bytes']])
    if (at+len(packet)!=len(blob) or sha256(packet)!=items['sha256'] or
            zlib.crc32(packet)!=items['crc32'] or any(packet[TABLE+items['table_bytes']:-16]) or
            packet[-16:]!=bytes.fromhex('AF5351DE')*4):
        raise ValueError('Surface growth requires checked complete packet at reusable resource tail')
    equipment=copy.deepcopy(prior['equipment_resources']);ea=equipment['blob_offset']
    ep=bytearray(blob[ea:ea+equipment['bytes']]);ba=BOOT-equipment['ram'];be=BOOT_END-equipment['ram']
    boot_old=items['bootstrap']['code']
    if (sha256(ep)!=equipment['sha256'] or zlib.crc32(ep)!=equipment['crc32'] or
            sha256(ep[ba:ba+boot_old['bytes']])!=boot_old['sha256'] or any(ep[ba+boot_old['bytes']:be])):
        raise ValueError('Changed complete startup bootstrap/equipment packet')
    saved=copy.deepcopy(prior['save_runtime']);old=saved['code'];old_at=0x9200
    before=bytes(blob[old_at:old_at+old['bytes']])
    if sha256(before)!=old['sha256']:raise ValueError('Changed complete stable save runtime')
    for p in saved['patches']:
        off=p['address']-CODE_RAM;value=bytes.fromhex(p['after'])
        if core[off:off+len(value)]!=value:raise ValueError('Changed native save route')
    reward=equipment['player_actions']['reward_state'];helper=reward['code']
    if sha256(blob[0xB408:0xB408+helper['bytes']])!=helper['sha256']:
        raise ValueError('Changed complete retained reward validator/clear chain')
    clothing=copy.deepcopy(prior['clothing']);old_codec=clothing['save_extension']['active_codec_code']
    vrom,n,crc,dest=struct.unpack_from('>4I',blob,0xE0);extra=blob[vrom-BLOB:vrom-BLOB+n]
    if (dest!=0x8046D000 or sha256(extra)!=prior['tent_lamp']['extra_sha256'] or
            zlib.crc32(extra)!=crc or sha256(extra[:old_codec['bytes']])!=old_codec['sha256']):
        raise ValueError('Changed complete active codec/item/lamp resource')
    h,hc=compile_part('surface_save',output/'surface_save',defines=DEFINES)
    c,cc=compile_part('surface_codec',output/'surface_codec',primary_source='overlays/v3/save_codec.c',
        defines=CODEC_DEFINES+DEFINES[1:]+('AF_V3_EXTERNAL_REWARD_VALIDATOR=1',))
    r,rc=compile_part('surface_save_runtime',output/'surface_save_runtime',
        primary_source='overlays/v3/save_runtime.c',defines=DEFINES)
    expected=dict(af_v3_require_save_state=old['symbols']['require_state'],
        af_v3_save_halt=old['symbols']['af_v3_save_halt'],af_v3_save_collect=0x8046B9C4,
        af_surface_prior_clear=helper['symbols']['af_v3_reward_player_clear'])
    if (any(hc['symbols'].get(k)!=v for k,v in expected.items()) or
            hc['symbols']['af_v3_surface_profile_byte']!=0x804BC900 or
            cc['symbols']['af_v3_surface_profile_byte']!=0x804BC900 or
            rc['symbols']['af_v3_surface_profile_byte']!=0x804BC900 or
            cc['symbols']['af_v3_reward_data_valid']!=helper['symbols']['af_v3_reward_data_valid']):
        raise ValueError('Surface save dependency mismatch')
    packet.extend(bytes(SIZE-len(packet)))
    for offset,data,limit in ((0x900,h,0xFF0),(0x1000,c,0x2000),(0x2000,r,SIZE-16)):
        if offset+len(data)>limit or any(packet[offset:limit]):raise ValueError('Surface code overlaps owned storage')
        packet[offset:offset+len(data)]=data
    packet[-16:]=bytes.fromhex('AF5351DE')*4
    dispatch=[]
    for name,address in old['symbols'].items():
        if not 0x80469200<=address<0x80469200+old['bytes']:continue
        target=rc['symbols'][name];off=address-0x80460000
        if not 0x804BE000<=target<0x804BE000+len(r):raise ValueError('Save entry target outside compiled image')
        original=bytes(blob[off:off+8]);after=words(jump(target),0);blob[off:off+8]=after
        dispatch.append(dict(name=name,address=address,target=target,before=original.hex(),after=after.hex()))
    saved['code']=dict(old,format='AFV3-SAVE-STABLE-ENTRY-DISPATCH-1',compiled_sha256=old['sha256'],
        sha256=sha256(blob[old_at:old_at+old['bytes']]),dispatch=dispatch)
    entries=[]
    for name,row in zip(('check','pack','collect'),clothing['save_extension']['public_entries']):
        off=int(row['entry'],16)-0x80460000;before=bytes.fromhex(row['after'])
        if blob[off:off+8]!=before:raise ValueError('Changed stable codec entry')
        target=cc['symbols']['af_v3_save_'+name+'_extended'];after=words(jump(target),0)
        blob[off:off+8]=after;entries.append(dict(row,before=before.hex(),after=after.hex(),target=f'{target:08X}'))
    display=clothing['display']['readers'];dc=display['code']
    if sha256(blob[0x6C00:0x6C00+dc['bytes']])!=dc['sha256']:
        raise ValueError('Changed complete predecessor collection/display chain')
    hooks=[]
    for row,kind in zip(display['collection_hooks'],('record','owned')):
        off=row['entry']-0x80460000;before=bytes.fromhex(row['after'])
        if blob[off:off+8]!=before or hc['symbols']['af_surface_prior_'+kind]!=row['target']:
            raise ValueError('Changed surface collection predecessor')
        target=hc['symbols']['af_v3_surface_'+kind];after=words(jump(target),0);blob[off:off+8]=after
        hooks.append(dict(address=row['entry'],before=before.hex(),after=after.hex()))
        row.update(surface_prior_target=row['target'],surface_outer_target=target,target=target,after=after.hex())
    clear=0x800B7ADC-CODE_RAM;before=words(jump(expected['af_surface_prior_clear']),0)
    if core[clear:clear+8]!=before:raise ValueError('Changed native reward/player clear entry')
    after=words(jump(hc['symbols']['af_v3_surface_player_clear']),0);core[clear:clear+8]=after
    hooks.append(dict(address=0x800B7ADC,before=before.hex(),after=after.hex()))
    blob[at:]=packet;crc=zlib.crc32(packet)
    boot,bc=compile_part('surface_bootstrap',output/'surface_bootstrap',defines=(
        f'AF_SURFACE_ITEMS_VROM=0x{items["vrom"]:X}u',f'AF_SURFACE_ITEMS_CRC=0x{crc:X}u',
        f'AF_SURFACE_ITEMS_BYTES=0x{SIZE:X}u'))
    if len(boot)>be-ba:raise ValueError('Surface save bootstrap exceeds checked equipment gap')
    ep[ba:be]=boot+bytes(be-ba-len(boot));blob[ea:ea+len(ep)]=ep
    items.update(bytes=SIZE,crc32=crc,sha256=sha256(packet),additional_resident_bytes=SIZE-0x1000)
    items['bootstrap']['code']=bc
    equipment.update(sha256=sha256(ep),crc32=zlib.crc32(ep),surface_bootstrap=items['bootstrap'])
    saved.update(state_bytes=STATE_BYTES,guard_ram=0x8046C4C0,
        surface_profile_bytes=64,surface_catalogue_bytes=256,surface_runtime_code=rc,
        native_save_reload_tested=False)
    save_codec=copy.deepcopy(prior['save_codec'])
    save_codec.update(format_version=4,registry_version=3,work_state_bytes=WORKING_BYTES,
        active_codec_code=cc,extended_entry_dispatch='clothing.save_extension.public_entries')
    clothing['save_extension'].update(format_version=4,registry_version=3,
        working_state_bytes=WORKING_BYTES,runtime_bytes=STATE_BYTES,public_entries=entries,
        retained_codec_code=old_codec,active_codec_code=cc,active_codec_ram=0x804BD000,
        active_codec_resource='room_surfaces.items',legacy_formats_read=['NAFJ','AFS3-v1','AFS3-v2','AFS3-v3'])
    surface['additional_resident_bytes']+=SIZE-0x1000
    surface['save']=dict(format='AFV3-SURFACE-SAVE-1',format_version=4,registry_version=3,
        profile_bytes=64,ownership_bytes=256,working_offset=880,capsule_offset=0x390,
        state_bytes=STATE_BYTES,working_bytes=WORKING_BYTES,guard_ram=0x8046C4C0,
        helpers=hc,codec=cc,runtime=rc,stable_runtime_dispatch=dispatch,codec_entries=entries,
        collection_hooks=hooks,older_v3_reads_new_saves=False,ordinary_persistence_tested=False,
        native_execution_tested=False,surface_options_enabled=False)
    surface['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    warning=('Format-4 V3 saves require this or a newer compatible build. Valid older V3 saves migrate '
        'with surface ownership clear; equal or larger import profiles remain required. Older format-1/2/3 '
        'V3 builds and V2 cannot load these saves. Preserve backups. Ordinary cross-version gameplay reload '
        'is not newly verified.')
    return {},dict(room_surfaces=surface,equipment_resources=equipment,save_runtime=saved,
        save_codec=save_codec,clothing=clothing,expansion_state_range=['8046C000','8046C4D0'],
        saved_format_changed=True,save_warning=warning)
