"""Install complete donor summer conversations and choices with additive IDs."""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import (CODE_RAM,CODE_VROM,DMA_START,DMA_END,by_vrom,sha256,
                   verified_rom,fix_checksum,make_ups,apply_ups)
from apply_translation import write_new
from gc_adapter import remove_redundant_article_suppression
from gc_text import decoder_tables,decode_gc
from runtime_module import module_command_info
from textbanks import Bank
from textcodec import encode,tokenize,LATIN
from textvalidate import expanded_bound
from v3_asset_loader import ROOT,BLOB,MODULE,STARTUP,CONFIG,compile_part
from v3_campsite_calendar import PACKAGE_SIZE
from v3_furniture_art import verify_sources
from v3_import_storage import replace_checked
from v3_villager_art import data_pointers

BASE=ROOT/'build/v3-camper-quest-runtime-02'
BASE_SHA='f0a34dfed22880ac012cae1ebc6be22d0c49cade56c9d4b08a2e24bfc3d0c001'
REPORT_SHA='b1404f8d40ca28d68bda4f4319aa24d250779f432f66d9c3e17265cf4c57f93d'
ABI=79
DONOR_FIRST,DONOR_END,FIRST,CHOICE_FIRST=15930,16183,11754,462
OLD_MESSAGE,MESSAGE,TABLE,CHOICES,CHOICE_TABLE=0x02000000,0x01FA0000,0xCF9000,0x025F0000,0xD06000
PHYSICAL=0x03000000
DONOR_FILES={
    'forest_2nd.arc.unpacked/data/message_data.bin':
        '57e0971900ab944d24beb9b93f800cebda5177ca4200223d75601ef2d2a1d8ce',
    'forest_2nd.arc.unpacked/data/message_data_table.bin':
        'e4962174ef139a28c6d2ff7dc5541ee8ec093944576eb6f0555c3719d0db4a2a',
    'forest_1st.arc.unpacked/data/select_data.bin':
        '31b4cf5c9b4f2b1e2409d290e25aa497f597d5332b918e604d74a6c598d0643f',
    'forest_1st.arc.unpacked/data/select_data_table.bin':
        '43f9895125224bece808445648c24b9d79ddf52dc28bc819fc70a43ef5af0100'}


def donor():
    rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    verify_sources(rel,symbols)
    files={name:(ROOT/'build/gamecube/files'/name).read_bytes() for name in DONOR_FILES}
    if any(sha256(data)!=DONOR_FILES[name] for name,data in files.items()):
        raise ValueError('Changed complete GAFE01-r0 message/choice source')
    messages=Bank('message',0,0,files['forest_2nd.arc.unpacked/data/message_data.bin'],
                  files['forest_2nd.arc.unpacked/data/message_data_table.bin']).entries()
    choices=Bank('select',0,0,files['forest_1st.arc.unpacked/data/select_data.bin'],
                 files['forest_1st.arc.unpacked/data/select_data_table.bin']).entries()
    return messages,choices,decoder_tables(ROOT/'local/ac-decomp/tools/msg_tool.py')


def convert(base):
    messages,choices,tables=donor();info=module_command_info(base)
    # GC adds command 23 as a second pointer to trade 13. Native accepts only
    # 1..22, so retain the operation by selecting its existing handler instead.
    rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    pointers=data_pointers(rel,0x3E464,0x5C,expected_section=1)
    owner=by_vrom(base)[0x03910000].extract(base);ram=0x8091D7B0
    if (len(pointers)!=23 or pointers.get(0x3E494)!=0x124ADC
            or pointers.get(0x3E4BC)!=0x124ADC
            or owner[0x80920DF4-ram:0x80920E3C-ram]!=bytes.fromhex(
                '27bdffe8afbf0014948201ae1840000928410017102000072442ffff00027080'
                '3c198092032ec8218f391cd40320f809000000008fbf001427bd001803e000080000000027bdffe8')
            or owner[0x80921D04-ram:0x80921D08-ram]!=bytes.fromhex('80920c74')
            or owner[0x80920C74-ram:0x80920C94-ram]!=bytes.fromhex(
                '27bdffe8afbf00140c247d16000000008fbf001427bd001803e0000800000000')):
        raise ValueError('Changed donor trade alias or existing native trade-13 handler')
    prepared=[];choice_ids=set();adaptations={}
    for number in range(DONOR_FIRST,DONOR_END):
        text,edits=remove_redundant_article_suppression(decode_gc(messages[number],tables))
        data=encode(text,info);tokens=list(tokenize(data,info))
        if (not tokens or tokens[-1].data not in (b'\x7f\0',b'\x7f\1')
                or sum(t.kind=='cmd' and t.data[1] in (0,1) for t in tokens)!=1
                or any(t.kind!='cmd' and (t.kind!='text' or t.data[0] not in LATIN|{0xCD}) for t in tokens)
                or expanded_bound(data,info)>1024):
            raise ValueError('Summer message has invalid text, termination, or expansion bound')
        for token in tokens:
            if token.kind!='cmd': continue
            op=token.data[1]
            if op==9 and (token.data[:3]!=b'\x7f\x09\0' or
                           int.from_bytes(token.data[3:],'big') not in {*range(1,24),255}):
                raise ValueError('Summer speaker expression is outside the native standing set')
            if op==12:
                kind,value=token.data[2],int.from_bytes(token.data[3:],'big')
                if not (kind==2 and value in (3,12,14,15,17) or kind==3 and 1<=value<=23):
                    raise ValueError('Unreviewed summer quest trade operation')
            if 14<=op<=21:
                targets=struct.unpack('>'+'H'*((len(token.data)-2)//2),token.data[2:])
                if any(not DONOR_FIRST<=n<DONOR_END for n in targets):
                    raise ValueError('Summer dialogue branches outside the complete imported group')
            if 22<=op<=24:
                choice_ids.update(struct.unpack('>'+'H'*((len(token.data)-2)//2),token.data[2:]))
        prepared.append(data);adaptations[number]=edits
    # Reserve a stable row for each donor choice, even where two captions agree.
    # No existing selection or runtime ID depends on the chosen import subset.
    choice_map={number:CHOICE_FIRST+index for index,number in enumerate(sorted(choice_ids))}
    extra_choices=[];choice_report=[]
    for number,target in choice_map.items():
        data=encode(decode_gc(choices[number],tables),info)
        if not 1<=len(data)<=20 or any(c not in LATIN for c in data):
            raise ValueError('Summer choice does not fit the complete native English choice record')
        extra_choices.append(data)
        choice_report.append(dict(donor_id=number,id=target,source_sha256=sha256(choices[number]),
                                  encoded_sha256=sha256(data),bytes=len(data)))
    result=[];rows=[]
    for number,data in zip(range(DONOR_FIRST,DONOR_END),prepared):
        out=bytearray(data);branches=0;selects=0;trade_aliases=0
        for token in tokenize(data,info):
            if token.kind!='cmd': continue
            op=token.data[1]
            if token.data==b'\x7f\x0c\x03\x00\x17':
                out[token.offset+4]=13;trade_aliases+=1
            if 14<=op<=24:
                for at in range(2,len(token.data),2):
                    source=int.from_bytes(token.data[at:at+2],'big')
                    target=FIRST+source-DONOR_FIRST if op<=21 else choice_map[source]
                    struct.pack_into('>H',out,token.offset+at,target)
                    if op<=21: branches+=1
                    else: selects+=1
        out=bytes(out);result.append(out)
        rows.append(dict(donor_id=number,id=FIRST+number-DONOR_FIRST,source_sha256=sha256(messages[number]),
            encoded_sha256=sha256(out),bytes=len(out),expanded_bound=expanded_bound(out,info),
            remapped_message_targets=branches,remapped_choice_targets=selects,
            adaptations=adaptations[number],trade_23_to_13_aliases=trade_aliases))
    if sum(row['trade_23_to_13_aliases'] for row in rows)!=8:
        raise ValueError('Changed complete summer trade-alias coverage')
    return result,extra_choices,dict(donor_sources=DONOR_FILES,messages=rows,choices=choice_report,
        first_id=FIRST,count=len(result),first_choice=CHOICE_FIRST,choice_count=len(extra_choices),
        highest_expanded_bound=max(row['expanded_bound'] for row in rows),
        native_expression_and_trade_operations_retained=True,
        trade_alias=dict(donor=23,native=13,count=8,donor_shared_handler='00124ADC',
                         native_handler='80920C74'),summer_selector_installed=False,
        selected_camping_rewards_installed=False,ordinary_conversations_tested=False)


def extend_bank(data,table,extra,count):
    old=Bank('current',0,0,data,table).entries();end=sum(map(len,old))
    if len(old)!=count or any(data[end:]) or any(table[count*4:]):
        raise ValueError('Changed native bank count or unused tail')
    joined=old+extra;payload=b''.join(joined);result=[];end=0
    for row in joined: end+=len(row);result.append(end)
    directory=struct.pack('>'+str(len(result))+'I',*result)+bytes(16)
    directory+=bytes(-len(directory)%16);payload+=bytes(-len(payload)%16)
    if Bank('extended',0,0,payload,directory).entries()!=joined:
        raise ValueError('Appended bank does not preserve every complete old/new record')
    return payload,directory


def build(output):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):
        raise ValueError('Choose a fresh ignored build directory')
    native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes();verified_rom(native)
    base=(BASE/'animal-forest-v3-asset-loader.z64').read_bytes();raw=(BASE/'build.json').read_bytes()
    if (sha256(base),sha256(raw))!=(BASE_SHA,REPORT_SHA): raise ValueError('Changed complete camper quest base')
    prior,files=json.loads(raw),by_vrom(base)
    messages,choices,text=convert(base)
    data,table=extend_bank(files[OLD_MESSAGE].extract(base),files[TABLE].extract(base),messages,FIRST)
    selects,select_table=extend_bank(files[CHOICES].extract(base),files[CHOICE_TABLE].extract(base),choices,CHOICE_FIRST)
    resources=((OLD_MESSAGE,MESSAGE,data),(TABLE,TABLE,table),
               (CHOICES,CHOICES,selects),(CHOICE_TABLE,CHOICE_TABLE,select_table))
    # Use the free virtual interval after the complete audio-wave resource.
    # Both virtual and physical bounds remain below the native 64-MiB ceiling;
    # do not relax the shared DMA validator. The BLOB and old bytes stay put.
    moving={old for old,_,_ in resources}
    for old,vrom,payload in resources:
        if (vrom+len(payload)>0x04000000 or
                any(vrom<e.vend and e.vstart<vrom+len(payload) for key,e in files.items() if key not in moving)):
            raise ValueError('Expanded text virtual allocation overlaps another resource')
    cursor=PHYSICAL;relocated=[]
    for old,vrom,payload in resources:
        cursor=(cursor+15)&~15
        relocated.append(dict(old_vrom=old,vrom=vrom,bytes=len(payload),physical=cursor,sha256=sha256(payload)))
        cursor+=len(payload)
    if (cursor>len(base) or any(base[PHYSICAL:cursor])
            or any(e.pstart<cursor and PHYSICAL<(e.pend or e.pstart+e.size)
                   for e in files.values() if e.pstart!=0xFFFFFFFF)):
        raise ValueError('Text relocation needs verified unused physical cartridge storage')
    code=bytearray(files[CODE_VROM].extract(base));hooks=[]
    for address,before,after in (
        (0x8009E474,0x3C180200,0x3C1801FA),
        (0x8009E3A4,0x2A012DEA,0x2A010000|(FIRST+len(messages))),
        (0x8009E668,0x28A12DEA,0x28A10000|(FIRST+len(messages))),
        (0x80065544,0x2A0101CE,0x2A010000|(CHOICE_FIRST+len(choices))),
        (0x80065DAC,0x288101CE,0x28810000|(CHOICE_FIRST+len(choices)))):
        old,new=struct.pack('>I',before),struct.pack('>I',after)
        replace_checked(code,address-CODE_RAM,old,new)
        hooks.append(dict(address=address,before=old.hex(),after=new.hex()))
    if code[0x8009E478-CODE_RAM:0x8009E47C-CODE_RAM]!=bytes.fromhex('27180000'):
        raise ValueError('Changed native main-bank low address')
    output.mkdir(parents=True)
    startup,startup_report=compile_part('startup',output/'startup',defines=(
        'AF_V3_BLOB_SIZE=49152',f'AF_V3_ABI={ABI}','AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1','AF_V3_CLOTHING_PROFILE=1','AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1',f'AF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
        'AF_V3_ACCESSORY_VROM=0x02400000','AF_V3_WESTERN_LARGE=1',
        'AF_V3_CAMPSITE=1','AF_V3_CAMPER_CALENDAR=1','AF_V3_CAMPER=1'))
    module=bytearray(files[MODULE].extract(base));blob=bytearray(files[BLOB].extract(base));old=prior['startup']
    if (sha256(module[STARTUP:STARTUP+old['bytes']])!=old['sha256']
            or any(module[STARTUP+old['bytes']:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed startup reservation')
    module[STARTUP:CONFIG]=startup+bytes(CONFIG-STARTUP-len(startup))
    struct.pack_into('>I',blob,4,ABI)
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),ABI)
    image=bytearray(base)
    for vrom,payload in ((BLOB,blob),(MODULE,module),(CODE_VROM,code)):
        entry=files[vrom]
        if entry.pend or len(payload)!=entry.size: raise ValueError('Unexpected current owner resize')
        image[entry.pstart:entry.pstart+len(payload)]=payload
    for (old,vrom,payload),row in zip(resources,relocated):
        image[row['physical']:row['physical']+len(payload)]=payload
        struct.pack_into('>4I',image,DMA_START+files[old].index*16,vrom,vrom+len(payload),row['physical'],0)
    fix_checksum(image);image=bytes(image);installed=by_vrom(image)
    if (len(installed)!=len(files) or image[DMA_END-16:DMA_END]!=bytes(16)
            or any(installed[v]!=files[v] for v in files if v not in moving)):
        raise ValueError('Summer text changes an unrelated DMA identity')
    patch=make_ups(native,image)
    if apply_ups(native,patch)!=image: raise ValueError('Summer text patch reconstruction failed')
    report=copy.deepcopy(prior)
    text.update(resources=relocated,hooks=hooks,message_vrom=MESSAGE,message_table_vrom=TABLE,
        choice_vrom=CHOICES,choice_table_vrom=CHOICE_TABLE,additional_resident_bytes=0,
        additional_heap_bytes=0,saved_format_changed=False,saved_profile_changed=False,web_patcher_enabled=False)
    report.update(build='v3-camper-text',runtime_abi=ABI,input_build_sha256=BASE_SHA,
        output_sha256=sha256(image),patch_sha256=sha256(patch),blob_sha256=sha256(blob),
        startup=startup_report,camper_text=text,native_test='pending complete current text/choice loads')
    report['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in ('tools/v3_camper_text.py',
        'tools/gc_text.py','tools/gc_adapter.py','tools/textcodec.py','tools/textvalidate.py',
        'tools/v3_villager_art.py','local/ac-decomp/tools/msg_tool.py')})
    write_new(output/'animal-forest-v3-asset-loader.z64',image)
    write_new(output/'animal-forest-v3-asset-loader.ups',patch)
    write_new(output/'build.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    report=build(parser.parse_args().output)
    print(json.dumps({key:report[key] for key in ('build','runtime_abi','output_sha256','patch_sha256')},indent=2))
