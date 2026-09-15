"""Connect the tent's verified native footstep sound and room-light parameters."""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import (CODE_RAM, CODE_VROM, DMA_START, DMA_END, by_vrom, sha256,
                   verified_rom, fix_checksum, make_ups, apply_ups)
from apply_translation import write_new
from gc_names import symbol_data
from v3_asset_loader import ROOT, BLOB, MODULE, STARTUP, CONFIG, compile_part
from v3_furniture_art import verify_sources
from v3_import_storage import PACKAGE, PACKAGE_RAM, replace_checked
from v3_campsite_calendar import PACKAGE_SIZE
from v3_villager_audio import (GC_SECTIONS, NATIVE_HEADERS, NATIVE_FILES,
    DOL_SHA, AUDIO_SHA, read_audio_donor, header_entry, resource, span, instrument)

BASE = ROOT/'build/v3-camper-trade-runtime-02'
BASE_SHA = 'd01afeb17c4c0a306e892037808268b675f8f02179dba7dd2261b397f03f55a9'
REPORT_SHA = '9aa0289d9cc46fe9eb75ddfaa3d61de6bce085ceed96e651102a9c9ec0d0d56e'
ABI, RAM, LIMIT = 82, 0x804A2F54, 0x804A2FF0
IMPORTS = dict(native_scene=0x80126EB4, native_field_draw=0x80136EA2,
               native_floor_body=0x800BEECC, native_point_body=0x80096D68)


def words(*values): return struct.pack('>'+str(len(values))+'I', *values)
def jump(target): return 0x08000000 | (target >> 2 & 0x3FFFFFF)


def verify_donor(native, dol, audio):
    """Compare actual complete audio dependencies, not coincident numeric IDs."""
    verified_rom(native)
    if sha256(dol.data) != DOL_SHA or sha256(audio) != AUDIO_SHA:
        raise ValueError('Unverified campsite audio donor')
    files = by_vrom(native); code = files[CODE_VROM].extract(native)
    def nr(at, size): return span(code, at-CODE_RAM, size)
    native_table = nr(0x80113A64, 73*2); donor_table = dol.read(0x800A9938, 95*2)
    if (sha256(native_table) != '4b0c696020afdc533cfb4a6b3e799b5f297900fbc4f979e1e59671d69410b6be'
            or sha256(donor_table) != '104e7f8b0fac4806301b2366491aefc715f6d6ecf39d731a7a8ae1d98c38f8ef'
            or struct.unpack_from('>H', native_table, 68*2)[0] != 32
            or struct.unpack_from('>H', donor_table, 85*2)[0] != 32):
        raise ValueError('Changed tent/native floor sound mapping')
    ns = {k: files[v].extract(native) for k,v in NATIVE_FILES.items()}
    gs = {k: span(audio, *struct.unpack_from('>II', header_entry(dol.read, 0x800CE450, i)))
          for i,k in enumerate(('seq', 'bank', 'wave'))}
    sounds = []
    for label,read,headers,sources,sequence,mapping in (
        ('GAFE01-r0', dol.read, GC_SECTIONS, gs, 242, 0x800CE490),
        ('N64-Japan', nr, NATIVE_HEADERS, ns, 199, 0x80115D80)):
        data,_ = resource(read, headers, sources, 'seq', sequence)
        table = struct.unpack_from('>H', data, 0x18E)[0]
        at = struct.unpack_from('>H', data, table+6*2)[0]
        program = span(data, at, 11)
        if (program[:4] != bytes.fromhex('EB021888') or program[6:] != bytes.fromhex('FF67146EFF')
                or struct.unpack_from('>H', program, 4)[0] != at+7):
            raise ValueError('Changed complete tent footstep program')
        off = struct.unpack('>H', read(mapping+sequence*2, 2))[0]
        banks = read(mapping+off, 5)
        if banks[0] != 4: raise ValueError('Changed native audio font-selector mapping')
        # Native EB selector 2 indexes the reverse four-font map at byte 2.
        bank,entry = resource(read, headers, sources, 'bank', banks[2])
        wave,_ = resource(read, headers, sources, 'wave', entry[10])
        sound = instrument(bank, wave, 24, entry[12], extended=True)
        sounds.append(dict(source=label, sequence=sequence, program_offset=at,
            program_sha256=sha256(program), bank=banks[2], wave=entry[10], instrument=24,
            complete_instrument=sound))
    if sounds[0]['complete_instrument'] != sounds[1]['complete_instrument']:
        raise ValueError('Tent sound does not match the complete native instrument/sample')
    rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    verify_sources(rel, symbols)
    bindings = {name:sha256(symbol_data(rel, symbols.decode(), name)) for name in
                ('mRmTp_GetFloorIdx', 'mEnv_GetNowRoomPointLightInfo')}
    return dict(donor_dol_sha256=DOL_SHA, donor_audio_sha256=AUDIO_SHA,
        bindings=bindings, donor_floor_index=85, native_audio_floor_index=68,
        sound_id=0x306, sounds=sounds, new_audio_bytes=0,
        point_position=[120,80,120], point_rgb=[235,190,185], point_power=6000,
        point_is_flame=False)


def install(native, base, helper, compiled):
    files = by_vrom(base); original = by_vrom(native)[CODE_VROM].extract(native)
    blob = bytearray(files[BLOB].extract(base)); code = bytearray(files[CODE_VROM].extract(base))
    at = PACKAGE+RAM-PACKAGE_RAM; end = PACKAGE+LIMIT-PACKAGE_RAM
    if (not helper or len(helper)>LIMIT-RAM or len(helper)!=compiled['bytes']
            or sha256(helper)!=compiled['sha256'] or any(blob[at:end])
            or any(compiled['symbols'].get(n)!=a for n,a in IMPORTS.items())
            or blob[end:end+16]!=words(*([0xAFACC0DE]*4))):
        raise ValueError('Changed environment bindings, unused reservation, or package guard')
    hooks = []
    for begin,finish,name in ((0x800BEEC4,0x800BEFCC,'af_v3_campsite_floor'),
                              (0x80096D60,0x80096F5C,'af_v3_campsite_point_info')):
        offset = begin-CODE_RAM; target = compiled['symbols'][name]
        if not RAM<=target<RAM+len(helper) or code[offset:finish-CODE_RAM]!=original[offset:finish-CODE_RAM]:
            raise ValueError('Changed complete native environment getter')
        before = bytes(code[offset:offset+8]); after = words(jump(target),0)
        replace_checked(code,offset,before,after)
        hooks.append(dict(address=begin,before=before.hex(),after=after.hex(),symbol=name))
    # Keep every existing audio entry and consumer unchanged.
    for begin,finish in ((0x800F9064,0x800F91E0),(0x80113A64,0x80113AF6)):
        if code[begin-CODE_RAM:finish-CODE_RAM]!=original[begin-CODE_RAM:finish-CODE_RAM]:
            raise ValueError('Changed native floor sound consumer or table')
    blob[at:at+len(helper)] = helper
    struct.pack_into('>I',blob,0xF8,zlib.crc32(blob[PACKAGE:PACKAGE+PACKAGE_SIZE]))
    return blob,code,hooks


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'): raise ValueError('Choose fresh ignored output')
    native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(); verified_rom(native)
    base = (BASE/'animal-forest-v3-asset-loader.z64').read_bytes(); raw = (BASE/'build.json').read_bytes()
    if (sha256(base),sha256(raw)) != (BASE_SHA,REPORT_SHA): raise ValueError('Changed complete trade base')
    dol,audio = read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    donor = verify_donor(native,dol,audio); prior,files = json.loads(raw),by_vrom(base)
    output.mkdir(parents=True)
    helper,compiled = compile_part('campsite_environment',output/'environment',
                                  primary_source='overlays/v3/campsite_environment.S')
    blob,code,hooks = install(native,base,helper,compiled)
    startup,startup_report = compile_part('startup',output/'startup',defines=(
        'AF_V3_BLOB_SIZE=49152',f'AF_V3_ABI={ABI}','AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1','AF_V3_CLOTHING_PROFILE=1','AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1',f'AF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
        'AF_V3_ACCESSORY_VROM=0x02400000','AF_V3_WESTERN_LARGE=1',
        'AF_V3_CAMPSITE=1','AF_V3_CAMPER_CALENDAR=1','AF_V3_CAMPER=1'))
    module = bytearray(files[MODULE].extract(base)); old = prior['startup']
    if (sha256(module[STARTUP:STARTUP+old['bytes']])!=old['sha256']
            or any(module[STARTUP+old['bytes']:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed startup reservation')
    module[STARTUP:CONFIG] = startup+bytes(CONFIG-STARTUP-len(startup))
    struct.pack_into('>I',blob,4,ABI)
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),ABI)
    image = bytearray(base)
    for vrom,data in ((BLOB,blob),(MODULE,module),(CODE_VROM,code)):
        e = files[vrom]
        if e.pend or len(data)!=e.size: raise ValueError('Environment changes an allocation')
        image[e.pstart:e.pstart+len(data)] = data
    fix_checksum(image); image = bytes(image)
    if image[DMA_START:DMA_END]!=base[DMA_START:DMA_END]: raise ValueError('Environment changes DMA directory')
    patch = make_ups(native,image)
    if apply_ups(native,patch)!=image: raise ValueError('Environment patch reconstruction failed')
    report = copy.deepcopy(prior)
    report.update(build='v3-campsite-environment',runtime_abi=ABI,input_build_sha256=BASE_SHA,
        output_sha256=sha256(image),patch_sha256=sha256(patch),blob_sha256=sha256(blob),
        startup=startup_report,campsite_environment=dict(code=compiled,donor=donor,hooks=hooks,
            additional_resident_bytes=0,additional_heap_bytes=0,saved_format_changed=False,
            saved_profile_changed=False,floor_sound_installed=True,point_parameters_installed=True,
            timed_lamp_installed=False,ordinary_scene_tested=False,web_patcher_enabled=False),
        native_test='pending current floor and room-light execution')
    names = ('tools/v3_campsite_environment.py','tools/v3_asset_loader.py',
             'overlays/v3/campsite_environment.S','overlays/v3/campsite_environment.ld')
    report['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in names})
    write_new(output/'animal-forest-v3-asset-loader.z64',image)
    write_new(output/'animal-forest-v3-asset-loader.ups',patch)
    write_new(output/'build.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path,required=True)
    report=build(parser.parse_args().output)
    print(json.dumps({k:report[k] for k in ('build','runtime_abi','output_sha256','patch_sha256')},indent=2))
