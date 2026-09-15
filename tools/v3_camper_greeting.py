"""Install summer greeting selection and native last-gift quest state."""
import argparse
import copy
import json
from pathlib import Path
import struct
from types import SimpleNamespace
import zlib

from aflib import DMA_START,DMA_END,by_vrom,sha256,verified_rom,fix_checksum,make_ups,apply_ups
from apply_translation import write_new
from catalogue_names import elf_inventory
from gc_names import symbol_data
from npc_mail_show import relocate_verified_data
from v3_asset_loader import ROOT,BLOB,MODULE,STARTUP,CONFIG,compile_part
from v3_import_storage import PACKAGE,PACKAGE_RAM,END,replace_checked
from v3_campsite_calendar import PACKAGE_SIZE
from v3_furniture_art import verify_sources

BASE=ROOT/'build/v3-camper-text-runtime-03'
BASE_SHA='df8161549e9069ee68c34a4fae3cf3200739a40cb3adecef5e31f6a8aebd24e1'
REPORT_SHA='778db38b13be2c71056ea2c50f25a1d7f73209a0e205e3f20bb4fad802984e97'
ABI=80
OLD,OLD_RELOC,VROM,RELOC,RAM,SIZE=0x824500,0x8252E0,0x03A10000,0x03A14000,0x8092CD00,3552
QUEST,QUEST_RELOC,QUEST_RAM=0x849B50,0x84C8A0,0x80954D80
NORMAL,NORMAL_RELOC,NORMAL_RAM=0x03910000,0x03918000,0x8091D7B0
GIFT,LAST_GIFT=0x804A2F30,0x804A1A12
SOURCES={
    OLD:'d4120132f45759dee40d017f4949d67c1aee9cc490a7164a613ffbdf6a1e8f70',
    OLD_RELOC:'b1ca628bd35faef2df87f8dde4e3f7118699d2f76d7bc41b32f2e262d64a7f83',
    QUEST:'48fe55c73b6c9dda8a1aa35020c9496a8f76fe9367ae27983509b763d2fb1b85',
    QUEST_RELOC:'0488d8c93b285bcd03b84105e838bb887878f26acf6670ba8448198162b2c678',
    NORMAL:'2c440b6b17e9138cea2c1171642d4cdebe47eb56a2a7cc4f47cd00255ce21318',
    NORMAL_RELOC:'cafc6c298d54915be15feef31c6661d20cff68e4d3f9817f454991e784ded12e'}
IMPORTS=dict(native_private=0x80136FD8,native_hour=0x80136FBE,camper_last_gift=LAST_GIFT,
    native_looks=0x800AD084,native_first=0x8092CD5C,native_winter=0x8092D808,
    native_ordinary=0x8092D4D0,native_random=0x8002C9AC,native_item_kind=0x80468000)
BEFORE=bytes.fromhex('94f800063401d05e8fa500341701000500e020250c24b602'
                     '00e0202510000004004018250c24b5348fa5003400401825')
DONOR_REPEAT=(16002,16032,16063,16093,16123,16153)

def words(*values):return struct.pack('>'+str(len(values))+'I',*values)
def jal(address):return 0x0C000000|(address>>2&0x3FFFFFF)


def source_owners(base):
    files=by_vrom(base);data={v:files[v].extract(base) for v in SOURCES}
    if any(sha256(data[v])!=digest for v,digest in SOURCES.items()):
        raise ValueError('Changed complete greeting, quest, or normal conversation owner')
    if struct.unpack_from('>5I',data[OLD_RELOC])!=(3264,288,0,0,49):
        raise ValueError('Changed complete native greeting sections')
    rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    verify_sources(rel,symbols);symbols=symbols.decode()
    table=symbol_data(rel,symbols,'msg_table$761')
    if (table!=words(*DONOR_REPEAT) or
            sha256(symbol_data(rel,symbols,'aQMgr_get_hello_msg_no_summercamp'))!=
            '5e2d2688581628dccc2768eeaeccb400a12dca911646abe2295f57766b5af18c'):
        raise ValueError('Changed donor summer greeting selection or full personality table')
    return data


def install(base,suffix,compiled,gift,gift_report):
    sources=source_owners(base);symbols=compiled['symbols'];old=sources[OLD]
    if (len(suffix)!=compiled['bytes'] or sha256(suffix)!=compiled['sha256'] or len(suffix)%16
            or any(symbols.get(name)!=address for name,address in IMPORTS.items())
            or gift_report['symbols'].get('af_v3_camper_gift')!=GIFT
            or gift_report['symbols'].get('camper_last_gift')!=LAST_GIFT
            or gift_report['symbols'].get('native_clear')!=0x8002F4C0
            or len(gift)!=gift_report['bytes'] or sha256(gift)!=gift_report['sha256']
            or not 0<len(gift)<=0x804A2FF0-GIFT
            or not GIFT<=gift_report['symbols'].get('af_v3_camper_gift_reset',0)<GIFT+len(gift)):
        raise ValueError('Changed summer code or native imports')
    data=bytearray(old+suffix);at=0xC58
    dispatch=words(0x8FA50034,0x00E02025,jal(symbols['af_v3_camper_greeting']),0,0x00401825)+bytes(28)
    replace_checked(data,at,BEFORE,dispatch)
    rows=[];removed=[]
    # Flatten the original data section into the extended file. Existing bytes
    # and linked addresses stay fixed; section-2 relocation offsets become
    # absolute section-1 offsets before appending the compiled suffix records.
    for (row,) in struct.iter_unpack('>I',sources[OLD_RELOC][20:20+49*4]):
        section,kind,pos=row>>30,row>>24&63,row&0xFFFFFF
        if section not in (1,2):raise ValueError('Unexpected greeting relocation section')
        absolute=pos+(3264 if section==2 else 0)
        if at<=absolute<at+len(BEFORE):removed.append(row)
        else:rows.append(0x40000000|kind<<24|absolute)
    if removed!=[0x44000C6C,0x44000C7C]:raise ValueError('Changed native greeting dispatch relocations')
    rows.append(0x44000C60)
    for pos,kind,target,name in elf_inventory(compiled['elf_relocations'],ram=RAM):
        if not SIZE<=pos<=len(data)-4 or pos&3:raise ValueError('Greeting suffix relocation outside owner')
        if RAM<=target<RAM+len(data):rows.append(0x40000000|kind<<24|pos)
        elif IMPORTS.get(name)!=target or kind not in (2,4,5,6):
            raise ValueError('Unknown external greeting reference')
    if len({r&0xFFFFFF for r in rows})!=len(rows):raise ValueError('Duplicate greeting relocations')
    length=(24+len(rows)*4+15)&~15
    sections=(len(data),0,0,0,len(rows))
    relocation=words(*sections,*rows)+bytes(length-24-len(rows)*4)+words(length)
    if len(data)+length>0x8800 or VROM+len(data)>RELOC:
        raise ValueError('Summer greetings exceed existing conversation buffer or virtual reservation')
    for address in (0x80204000,0x80308000):
        previous=relocate_verified_data(SimpleNamespace(ram=RAM,resident_bytes=SIZE,
            sections=(3264,288,0,0,49)),old,sources[OLD_RELOC],address)
        current=bytearray(relocate_verified_data(SimpleNamespace(ram=RAM,resident_bytes=len(data),
            sections=sections),data,relocation,address))
        current[at:at+len(BEFORE)]=previous[at:at+len(BEFORE)]
        if current[:SIZE]!=previous:raise ValueError('Summer suffix changes unrelated relocated greeting bytes')
    changes={VROM:bytes(data),RELOC:relocation};hooks=[]
    quest=bytearray(sources[QUEST]);normal=bytearray(sources[NORMAL])
    def patch(owner,ram,address,before,after):
        replace_checked(owner,address-ram,words(before),words(after))
        hooks.append(dict(vrom=QUEST if owner is quest else NORMAL,ram=ram,address=address,before=before,after=after))
    end=RAM+len(data)
    for address,before,after in (
        (0x80954EA0,0x3C040082,0x3C040000|VROM>>16),
        (0x80954EA4,0x3C050082,0x3C050000|(VROM+len(data)+0x8000)>>16),
        (0x80954EB0,0x3C078093,0x3C070000|(end+0x8000)>>16),
        (0x80954EB8,0x24E7DAE0,0x24E70000|end&65535),
        (0x80954EC8,0x24A552E0,0x24A50000|(VROM+len(data))&65535),
        (0x80954ECC,0x24844500,0x24840000|VROM&65535),
        (0x80957040,0x0C00BD30,jal(gift_report['symbols']['af_v3_camper_gift_reset']))):
        patch(quest,QUEST_RAM,address,before,after)
    for address in (0x8091F56C,0x80920AB8):
        patch(normal,NORMAL_RAM,address,0x0320F809,jal(GIFT))
        if normal[address-NORMAL_RAM+4:address-NORMAL_RAM+8]!=words(0xA61801D8):
            raise ValueError('Changed original full gift store delay slot')
    # All changed manager/normal windows are constants or resident calls; their
    # native relocations must remain absent, including the reset's delay slot.
    for v,rv,ram,owner in ((QUEST,QUEST_RELOC,QUEST_RAM,quest),(NORMAL,NORMAL_RELOC,NORMAL_RAM,normal)):
        rel=sources[rv];sect=struct.unpack_from('>5I',rel)
        changed={h['address']-ram for h in hooks if h['vrom']==v}
        if any(r>>30==1 and r&0xFFFFFF in changed for (r,) in struct.iter_unpack('>I',rel[20:20+sect[4]*4])):
            raise ValueError('Changed native window unexpectedly requires relocation')
        for address in (0x80204000,0x80308000):
            spec=SimpleNamespace(ram=ram,resident_bytes=len(owner)+sect[3],sections=sect)
            before=relocate_verified_data(spec,sources[v],rel,address)
            current=bytearray(relocate_verified_data(spec,owner,rel,address))
            for pos in changed:current[pos:pos+4]=before[pos:pos+4]
            if current!=before:raise ValueError('Summer change escapes declared native owner windows')
        changes[v]=bytes(owner)
    return changes,dict(code=compiled,gift_code=gift_report,bytes=len(data),sections=sections,
        relocation_bytes=len(relocation),relocation_sha256=sha256(relocation),sha256=sha256(data),
        vrom=VROM,relocation_vrom=RELOC,ram=RAM,dispatch=RAM+at,
        dispatch_before=BEFORE.hex(),dispatch_after=dispatch.hex(),
        hooks=hooks,donor_repeat_messages=DONOR_REPEAT,repeat_messages=[n-4176 for n in DONOR_REPEAT],
        original_bytes=SIZE,on_demand_growth=len(data)-SIZE,shared_buffer_bytes=0x8800,
        last_gift_address=LAST_GIFT,last_gift_reset='quest manager construction',
        saved_format_changed=False,saved_profile_changed=False,additional_resident_bytes=0,
        additional_heap_bytes=0,summer_selection_installed=True,last_gift_tracking_installed=True,
        selected_rewards_installed=False,ordinary_conversations_tested=False,web_patcher_enabled=False)


def build(output):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):raise ValueError('Choose fresh ignored build directory')
    native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes();verified_rom(native)
    base=(BASE/'animal-forest-v3-asset-loader.z64').read_bytes();raw=(BASE/'build.json').read_bytes()
    if (sha256(base),sha256(raw))!=(BASE_SHA,REPORT_SHA):raise ValueError('Changed complete summer text base')
    prior,files=json.loads(raw),by_vrom(base);source_owners(base);output.mkdir(parents=True)
    suffix,compiled=compile_part('camper_greeting',output/'greeting')
    gift,gift_report=compile_part('camper_gift',output/'gift',primary_source='overlays/v3/camper_gift.S')
    changes,greeting=install(base,suffix,compiled,gift,gift_report)
    blob=bytearray(files[BLOB].extract(base));pos=PACKAGE+GIFT-PACKAGE_RAM;state=PACKAGE+LAST_GIFT-PACKAGE_RAM
    if (any(blob[pos:PACKAGE+0x804A2FF0-PACKAGE_RAM]) or any(blob[state:state+2])
            or struct.unpack_from('>4I',blob,0xF0)!=(BLOB+PACKAGE,PACKAGE_SIZE,
                zlib.crc32(blob[PACKAGE:PACKAGE+PACKAGE_SIZE]),PACKAGE_RAM)):
        raise ValueError('Changed complete package, gift reservation, or unused state')
    blob[pos:pos+len(gift)]=gift;struct.pack_into('>I',blob,0xF8,zlib.crc32(blob[PACKAGE:PACKAGE+PACKAGE_SIZE]))
    moves=[];old_size=len(blob)
    for old,vrom in ((OLD,VROM),(OLD_RELOC,RELOC)):
        payload=changes.pop(vrom);blob.extend(bytes(-len(blob)%16));pos=len(blob);blob.extend(payload)
        moves.append(dict(old_vrom=old,vrom=vrom,bytes=len(payload),physical=files[BLOB].pstart+pos,
                          blob_offset=pos,sha256=sha256(payload)))
        if any(vrom<e.vend and e.vstart<vrom+len(payload) for e in files.values()):
            raise ValueError('New greeting virtual identity overlaps an existing resource')
    start,end=files[BLOB].pstart+old_size,files[BLOB].pstart+len(blob)
    if (BLOB+len(blob)>END or end>len(base) or any(base[start:end])
            or any(e.pstart<end and start<(e.pend or e.pstart+e.size) for v,e in files.items()
                   if v!=BLOB and e.pstart!=0xFFFFFFFF)
            or any(e.vstart<BLOB+len(blob) and BLOB+old_size<e.vend for v,e in files.items() if v!=BLOB)):
        raise ValueError('Greeting resource append overlaps used cartridge storage')
    startup,startup_report=compile_part('startup',output/'startup',defines=(
        'AF_V3_BLOB_SIZE=49152',f'AF_V3_ABI={ABI}','AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1','AF_V3_CLOTHING_PROFILE=1','AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1',f'AF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
        'AF_V3_ACCESSORY_VROM=0x02400000','AF_V3_WESTERN_LARGE=1',
        'AF_V3_CAMPSITE=1','AF_V3_CAMPER_CALENDAR=1','AF_V3_CAMPER=1'))
    module=bytearray(files[MODULE].extract(base));old=prior['startup']
    if (sha256(module[STARTUP:STARTUP+old['bytes']])!=old['sha256']
            or any(module[STARTUP+old['bytes']:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed startup reservation')
    module[STARTUP:CONFIG]=startup+bytes(CONFIG-STARTUP-len(startup));struct.pack_into('>I',blob,4,ABI)
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),ABI)
    changes.update({BLOB:blob,MODULE:module});image=bytearray(base)
    for vrom,payload in changes.items():
        e=files[vrom]
        if e.pend or vrom!=BLOB and len(payload)!=e.size:raise ValueError('Unexpected owner allocation change')
        image[e.pstart:e.pstart+len(payload)]=payload
    struct.pack_into('>I',image,DMA_START+files[BLOB].index*16+4,BLOB+len(blob))
    for row in moves:
        struct.pack_into('>4I',image,DMA_START+files[row['old_vrom']].index*16,
                         row['vrom'],row['vrom']+row['bytes'],row['physical'],0)
    fix_checksum(image);image=bytes(image);installed=by_vrom(image)
    if (set(installed)!=(set(files)-{OLD,OLD_RELOC})|{VROM,RELOC}
            or image[DMA_END-16:DMA_END]!=bytes(16)
            or any(installed[v]!=files[v] for v in files if v not in (OLD,OLD_RELOC,BLOB))):
        raise ValueError('Summer greetings change unrelated DMA metadata')
    patch=make_ups(native,image)
    if apply_ups(native,patch)!=image:raise ValueError('Summer greeting patch reconstruction failed')
    report=copy.deepcopy(prior);greeting['moves']=moves
    report.update(build='v3-camper-greeting',runtime_abi=ABI,input_build_sha256=BASE_SHA,
        output_sha256=sha256(image),patch_sha256=sha256(patch),blob_sha256=sha256(blob),
        blob_bytes=len(blob),blob_file_bytes=len(blob),startup=startup_report,camper_greeting=greeting,
        native_test='pending current summer greeting and last-gift native execution')
    report['camper_text']['summer_selector_installed']=True
    report['camper_quest']['summer_english_message_selection']=True
    for row in report['camper_quest']['owners']:
        if int(row['vrom'],16)==QUEST:row['patched_sha256']=sha256(installed[QUEST].extract(image))
    report['import_storage']['remaining_bytes']=END-BLOB-len(blob)
    for section in report.values():
        if isinstance(section,dict) and 'package_sha256' in section:
            section['package_sha256']=sha256(blob[PACKAGE:PACKAGE+PACKAGE_SIZE])
    names=('tools/v3_camper_greeting.py','tools/v3_asset_loader.py','overlays/v3/camper_greeting.c',
           'overlays/v3/camper_greeting.ld','overlays/v3/camper_gift.S','overlays/v3/camper_gift.ld')
    report['sources'].update({name:sha256((ROOT/name).read_bytes()) for name in names})
    write_new(output/'animal-forest-v3-asset-loader.z64',image)
    write_new(output/'animal-forest-v3-asset-loader.ups',patch)
    write_new(output/'build.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    report=build(parser.parse_args().output)
    print(json.dumps({key:report[key] for key in ('build','runtime_abi','output_sha256','patch_sha256')},indent=2))
