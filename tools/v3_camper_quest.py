"""Bind summer camper NPC profiles and first/repeat native quest lifecycle."""
import argparse
import copy
import json
from pathlib import Path
import struct
from types import SimpleNamespace
import zlib

from aflib import (DMA_START,DMA_END,by_vrom,sha256,verified_rom,
                   fix_checksum,make_ups,apply_ups)
from apply_translation import write_new
from npc_mail_show import relocate_verified_data
from v3_asset_loader import ROOT,BLOB,MODULE,STARTUP,CONFIG,compile_part
from v3_import_storage import PACKAGE,PACKAGE_RAM,END,replace_checked
from v3_campsite_calendar import PACKAGE_SIZE
from v3_furniture_art import verify_sources

BASE=ROOT/'build/v3-camper-movein-runtime-02'
BASE_SHA='31771d9e0fe23dba25fe1a8643f0124705ea40948b4c060853036fb4e150214f'
REPORT_SHA='d9e18c193d9a3955bc4069fea18913f7ccc083b07211d658918bb8d3de2464b1'
ABI,RAM,LIMIT=78,0x804A2EC0,0x804A2FF0
OWNERS=(
    (0x8681F0,0x878550,0x809735B0,0x80980448,0x80969690,
     '1ef13dcefa632bbd45ea8d062e5261053fa8fb3a0773fca745d273910a56cc93',
     '177536da108299742fb608a2e8d0a26bef9cd2ecf1f4a18e93213f3a01ecee6c'),
    (0x8798C0,0x886FA0,0x80995BF0,0x809A09D0,0x80989060,
     '4ce89a22ffa3d01f7c05598dcf60af78dea7bea846615bde53c6902e9404ad45',
     '5785745510d2f060f83bb9f7ec86dba963185d918e2d7fd4dfa92719b36129b4'),
    (0x849B50,0x84C8A0,0x80954D80,0x809550D8,None,
     '9328e5581784369f0ee8d65c510a06ae5685102c89ad3031fd01f1938a11b572',
     'be7fa75ae8e1b2373f031efdaaee1de4ac9d241459749c7184a9d74848574d70'))
QUEST_BEFORE=bytes.fromhex('961800063401D05E3C1980951701000C240A00018F3971B0'
    '240100012408000417210004240900053C01809510000006A02871A43C018095'
    '10000003A02971A43C018095A02A71A4')
QUEST_RELOCS={0x45000360,0x4600036C,0x45000380,0x46000388,
              0x4500038C,0x46000394,0x45000398,0x4600039C}


def words(*values): return struct.pack('>'+str(len(values))+'I',*values)
def jal(address): return 0x0C000000|(address>>2&0x3FFFFFF)


def patch_owners(base,compiled):
    files=by_vrom(base);changes={};reports=[];symbols=compiled['symbols']
    for vrom,rvrom,ram,hook,bias,source_sha,reloc_sha in OWNERS:
        before,reloc=files[vrom].extract(base),files[rvrom].extract(base)
        if (sha256(before),sha256(reloc))!=(source_sha,reloc_sha):
            raise ValueError('Changed complete native camper quest/NPC owner')
        sections=struct.unpack_from('>5I',reloc);new_sections=sections
        data=bytearray(before);updated=reloc;offset=hook-ram
        if bias is not None:
            # Retain the native HI/LO pair, but produce the relocated row
            # address before calling a helper that handles the added ID.
            old=words(0x85290000|(bias&0xFFFF),0xA7A90056)
            new=words(0x25290000|(bias&0xFFFF),jal(symbols['af_v3_camper_profile']))
            replace_checked(data,offset,old,new)
            if data[offset+8:offset+12]!=words(0x27A40044):
                raise ValueError('Changed NPC profile delay-slot argument')
        else:
            old=QUEST_BEFORE
            new=words(0x96040006,0x3C058095,0x8CA571B0,
                jal(symbols['af_v3_camper_talk_mode']),0,0x3C018095,0xA02271A4)+bytes(44)
            replace_checked(data,offset,old,new)
            rows=list(struct.unpack_from('>'+str(sections[4])+'I',reloc,20))
            removed={r for r in rows if offset<=r&0xFFFFFF<offset+len(old) and r>>30==1}
            if removed!=QUEST_RELOCS: raise ValueError('Changed quest mode relocation inventory')
            kept=[r for r in rows if r not in removed]
            # These pairs are self-contained and cannot change retained HI/LO
            # state. Full relocated-owner comparison below verifies that too.
            added=[0x45000000|offset+4,0x46000000|offset+8,
                   0x45000000|offset+20,0x46000000|offset+24]
            rows=kept+added
            new_sections=(*sections[:4],len(rows))
            updated=words(*new_sections,*rows)
            if len(updated)>len(reloc)-4: raise ValueError('Quest relocations exceed original allocation')
            updated+=bytes(len(reloc)-4-len(updated))+words(len(reloc))
            changes[rvrom]=updated
        spec=SimpleNamespace(ram=ram,resident_bytes=len(before)+sections[3],sections=sections)
        new_spec=SimpleNamespace(ram=ram,resident_bytes=spec.resident_bytes,sections=new_sections)
        constants=() if bias is None else (bias,ram+spec.resident_bytes)
        for at in (0x80204000,0x80308000):
            previous=relocate_verified_data(spec,before,reloc,at,address_constants=constants)
            actual=bytearray(relocate_verified_data(new_spec,data,updated,at,address_constants=constants))
            actual[offset:offset+len(old)]=previous[offset:offset+len(old)]
            if actual!=previous: raise ValueError('Camper route changes unrelated relocated owner bytes')
        changes[vrom]=bytes(data)
        reports.append(dict(vrom=f'{vrom:08X}',relocation_vrom=f'{rvrom:08X}',ram=ram,
            bytes=len(data),sections=new_sections,relocation_bytes=len(updated),
            source_sha256=source_sha,source_relocation_sha256=reloc_sha,
            patched_sha256=sha256(data),relocation_sha256=sha256(updated),
            hook=hook,before=old.hex(),after=new.hex(),address_constants=constants,
            relocation_test_bases=(0x80204000,0x80308000)))
    return changes,reports


def install(base,helper,compiled):
    symbols=compiled['symbols']
    if (not helper or len(helper)>LIMIT-RAM or len(helper)!=compiled['bytes']
            or sha256(helper)!=compiled['sha256'] or symbols.get('af_v3_camper_profile')!=RAM
            or symbols.get('camper_greeted')!=0x804A1A10
            or not RAM<=symbols.get('af_v3_camper_talk_mode',0)<RAM+len(helper)):
        raise ValueError('Invalid resident camper quest code or state binding')
    files=by_vrom(base);blob=bytearray(files[BLOB].extract(base));at=PACKAGE+RAM-PACKAGE_RAM
    if (any(blob[at:PACKAGE+LIMIT-PACKAGE_RAM])
            or struct.unpack_from('>4I',blob,0xF0)!=(BLOB+PACKAGE,PACKAGE_SIZE,
                zlib.crc32(blob[PACKAGE:PACKAGE+PACKAGE_SIZE]),PACKAGE_RAM)):
        raise ValueError('Changed checked camper reservation or package descriptor')
    changes,owners=patch_owners(base,compiled)
    blob[at:at+len(helper)]=helper
    struct.pack_into('>I',blob,0xF8,zlib.crc32(blob[PACKAGE:PACKAGE+PACKAGE_SIZE]))
    changes[BLOB]=blob
    return changes,dict(code=compiled,owners=owners,npc_profile=0x23,camper_id=0xD08F,
        first_mode=4,repeat_mode=5,session_flag=0x804A1A10,
        session_transition='first summer talk start',additional_resident_bytes=0,
        additional_heap_bytes=0,saved_format_changed=False,saved_profile_changed=False,
        summer_english_message_selection=False,full_npc_construction_tested=False,
        web_patcher_enabled=False)


def build(output):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):
        raise ValueError('Choose a fresh ignored build directory')
    native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes();verified_rom(native)
    base=(BASE/'animal-forest-v3-asset-loader.z64').read_bytes();raw=(BASE/'build.json').read_bytes()
    if (sha256(base),sha256(raw))!=(BASE_SHA,REPORT_SHA): raise ValueError('Changed camper move-in base')
    verify_sources((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                   (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    prior,files=json.loads(raw),by_vrom(base);output.mkdir(parents=True)
    helper,compiled=compile_part('camper_quest',output/'camper_quest',
                                 primary_source='overlays/v3/camper_quest.S')
    changes,quest=install(base,helper,compiled);blob=changes[BLOB]
    # The modified quest relocation file is compressed in its original slot.
    # Keep its virtual identity and runtime size, storing an uncompressed copy
    # in the checked trailing ROM resource as other current owners already do.
    moves=[];old_bytes=len(blob)
    for vrom in tuple(changes):
        if not files[vrom].pend: continue
        data=changes.pop(vrom)
        if vrom!=0x84C8A0 or len(data)!=files[vrom].size:
            raise ValueError('Unexpected compressed quest resource')
        blob.extend(bytes(-len(blob)%16));offset=len(blob);blob.extend(data)
        moves.append(dict(vrom=vrom,bytes=len(data),blob_offset=offset,
                          physical=files[BLOB].pstart+offset,sha256=sha256(data)))
    start,end=files[BLOB].pstart+old_bytes,files[BLOB].pstart+len(blob)
    if (BLOB+len(blob)>END or end>len(base) or any(base[start:end])
            or any(e.pstart<end and start<(e.pend or e.pstart+e.size)
                   for v,e in files.items() if v!=BLOB and e.pstart!=0xFFFFFFFF)
            or any(e.vstart<BLOB+len(blob) and BLOB+old_bytes<e.vend
                   for v,e in files.items() if v!=BLOB)):
        raise ValueError('Quest relocation append overlaps a live resource')
    startup,startup_report=compile_part('startup',output/'startup',defines=(
        'AF_V3_BLOB_SIZE=49152',f'AF_V3_ABI={ABI}','AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1','AF_V3_CLOTHING_PROFILE=1','AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1',f'AF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
        'AF_V3_ACCESSORY_VROM=0x02400000','AF_V3_WESTERN_LARGE=1',
        'AF_V3_CAMPSITE=1','AF_V3_CAMPER_CALENDAR=1','AF_V3_CAMPER=1'))
    module=bytearray(files[MODULE].extract(base));old=prior['startup']
    if (sha256(module[STARTUP:STARTUP+old['bytes']])!=old['sha256']
            or any(module[STARTUP+old['bytes']:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed startup or insufficient reservation')
    module[STARTUP:CONFIG]=startup+bytes(CONFIG-STARTUP-len(startup))
    struct.pack_into('>I',blob,4,ABI)
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),ABI)
    changes[MODULE]=module;image=bytearray(base)
    for vrom,data in changes.items():
        entry=files[vrom]
        if entry.pend or vrom!=BLOB and len(data)!=entry.size:
            raise ValueError('Camper quest changes a runtime allocation')
        image[entry.pstart:entry.pstart+len(data)]=data
    struct.pack_into('>I',image,DMA_START+files[BLOB].index*16+4,BLOB+len(blob))
    for move in moves:
        struct.pack_into('>2I',image,DMA_START+files[move['vrom']].index*16+8,move['physical'],0)
    fix_checksum(image);image=bytes(image)
    installed=by_vrom(image)
    if (set(installed)!=set(files) or image[DMA_END-16:DMA_END]!=bytes(16)
            or any(installed[v]!=files[v] for v in files if v not in (BLOB,0x84C8A0))):
        raise ValueError('Camper quest changes an unrelated DMA identity')
    patch=make_ups(native,image)
    if apply_ups(native,patch)!=image: raise ValueError('Camper quest patch reconstruction failed')
    report=copy.deepcopy(prior)
    report.update(build='v3-camper-quest',runtime_abi=ABI,input_build_sha256=BASE_SHA,
        output_sha256=sha256(image),patch_sha256=sha256(patch),blob_sha256=sha256(blob),
        blob_bytes=len(blob),blob_file_bytes=len(blob),startup=startup_report,camper_quest=quest,
        native_test='pending current NPC-profile/quest execution')
    quest['resource_moves']=moves
    for value in report.values():
        if isinstance(value,dict) and 'package_sha256' in value:
            value['package_sha256']=sha256(blob[PACKAGE:PACKAGE+PACKAGE_SIZE])
    report['import_storage']['remaining_bytes']=END-BLOB-len(blob)
    for row in report['npc_draw']['owners']:
        current=next((o for o in quest['owners'] if o['vrom']==row['vrom']),None)
        if current:
            row.update(patched_sha256=current['patched_sha256'],relocation_sha256=current['relocation_sha256'])
    source_names=('tools/v3_camper_quest.py','tools/v3_asset_loader.py',
                  'overlays/v3/camper_quest.S','overlays/v3/camper_quest.ld')
    report['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in source_names})
    write_new(output/'animal-forest-v3-asset-loader.z64',image)
    write_new(output/'animal-forest-v3-asset-loader.ups',patch)
    write_new(output/'build.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    report=build(parser.parse_args().output)
    print(json.dumps({key:report[key] for key in ('build','runtime_abi','output_sha256','patch_sha256')},indent=2))
