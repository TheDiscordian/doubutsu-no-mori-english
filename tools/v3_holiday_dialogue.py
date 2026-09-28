"""Connect the entire official holiday/vacation/exercise dialogue group.

Use the ordinary text-bank installer and existing NPC packet. No holiday-specific
installer, new actor allocation, or selectable unfinished reward is introduced.
"""
import copy
import json
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from apply_translation import write_new
from gc_adapter import remove_redundant_article_suppression
from gc_text import decode_gc
from runtime_module import module_command_info
from textbanks import Bank
from textcodec import encode,tokenize,LATIN
from textvalidate import expanded_bound
from text_provenance import validate
from v3_asset_loader import ROOT,compile_part
from v3_camper_text import donor,extend_bank,DONOR_FILES
from v3_event_text import MESSAGE,TABLE,CHOICE_TABLE,patch_bounds
from v3_holiday_talk import discover
from v3_npc_registry import RAM,SIZE
import v3_physical_resources as physical

FIRST,CHOICE_FIRST=12033,511
RANGES=((0x3280,0x339B),(0x33F4,0x3416),(0x3422,0x3440))
# The 28 ten-message event groups plus complete vacation/card conversations.
# The message branches additionally reach three records between events/Harvest.
ROOTS=(*range(0x3280,0x338E),*range(0x3391,0x339B),
       *range(0x33F4,0x3416),*range(0x3422,0x3440))
EVENT_STRINGS=(0,14,8,3,11,7,24,4,2,5,6,9,10,1,18,12,13,17,20,21,16,19,22,25,15,26,27,23,28)
STRING_FILES={
    'string_data.bin':'1ca41141a2265ddd0b3bee22868f27fe3cd980f2caeb948e1d00e7910e0533cf',
    'string_data_table.bin':'1b61ef035cd276a575169a7473f62a8cd9b1b788abd713bbd972c016487079df'}
NATIVE=(
    (0x8009D1F0,0x8009D200,'e4e54e5f3fc74caca37c6c0fdda0b5684e6e68d753495d23a868e75faf6af1f3'),
    (0x800950D8,0x800950E4,'02beba1edc3bcdcf1d3f1671d5a9cdba53e4dff74ce5a531121057dcb5d6849c'),
    (0x800A08F8,0x800A09A4,'2d25364fec4cb2c9e13a641a1e84201192a743366c3a286b00f694e6ff804446'),
    (0x8009E908,0x8009E94C,'ff7ab67f35cac9085f90c93232cc8942e01bcd1cbc8a5b6c4a90d633b25180e3'),
    (0x8009DBA4,0x8009DBB0,'0aabf3753523c2378aee478773f4b5ce1941af7943ea67feeb34618204628be4'),
    (0x8009DD64,0x8009DDB8,'d4fac744ee1c7055d4ec11accc6fa6de69b9afbb0737072786481fbe4e73316f'),
    (0x800A0A60,0x800A0B54,'796387edb07b63e3c28df81b607f58fcbde755805eb45fbaf1b7ac0709917f4a'),
    (0x8007B44C,0x8007B4E0,'a90f0c04b98f851a7b164e133d2518e71f95da9eea0694e8225c589015d93df0'),
    (0x8007B5C0,0x8007B5D0,'7606d76a6583171277e0c539cd054fb2619b85f9b90d95161eaffc7af5e4b9cf'),
    (0x8007B908,0x8007B928,'823596d2749bb1d34e0929278ccb81d696f2b4f702867a18713d54a4d277fb43'),
    (0x8007BA1C,0x8007BA3C,'bd5507bbe1c2ffa1f97c85c54720ce40fa3007cdfb7052a0732b79470972693a'),
    (0x8007CF34,0x8007D0E0,'7f201cc11bf87b348aee851aa4ccde5694205fa18f40677d181831a459b35cf4'),
)
SOURCES=('tools/v3_holiday_dialogue.py','overlays/v3/holiday_dialogue.c',
    'overlays/v3/holiday_dialogue.h','overlays/v3/holiday_dialogue_native.c',
    'overlays/v3/holiday_dialogue.ld','overlays/v3/holiday_npc.c','overlays/v3/holiday_npc.h',
    'tools/v3_asset_loader.py','tools/v3_furniture_install.py','tools/v3_holiday_motion.py',
    'tools/v3_event_text.py','translations/provenance.json')


def credit(identity,source_id,original,data,adaptations):
    return dict(id=identity,native_sha256=None,locales=dict(en=dict(credit='official',
        locator=['tools/v3_holiday_dialogue.py:convert',identity],
        source=dict(source='user-supplied GAFE01 revision 0 disc',reference_id=source_id,
                    reference_sha256=sha256(original)),adaptations=adaptations,
        human_review='not_recorded',encoded_sha256=sha256(data))))


def convert(base):
    messages,choices,decoder=donor();info=module_command_info(base)
    ready={};edits={};dashes={};pending=set(ROOTS);selects=set();orders=set()
    allowed={0,1,2,3,4,9,13,14,15,16,20,22,25,26,36,37,47,49,50}
    while pending:
        number=min(pending);pending.remove(number)
        if not 0<=number<len(messages):raise ValueError('Holiday branch escapes the donor bank')
        text,edits[number]=remove_redundant_article_suppression(decode_gc(messages[number],decoder))
        dashes[number]=text.count('ー');text=text.replace('ー','-')
        data=encode(text,info);tokens=list(tokenize(data,info))
        if (not tokens or tokens[-1].data not in (b'\x7f\0',b'\x7f\1') or
                sum(t.kind=='cmd' and t.data[1] in (0,1) for t in tokens)!=1 or
                any(t.kind!='cmd' and (t.kind!='text' or t.data[0] not in LATIN|{0xCD}) for t in tokens) or
                any(t.kind=='cmd' and t.data[1] not in allowed for t in tokens) or expanded_bound(data,info)>1024):
            raise ValueError(f'Invalid holiday text, operation, termination, or buffer bound: {number:04X}')
        ready[number]=data
        for t in tokens:
            if t.kind!='cmd':continue
            op=t.data[1]
            if op==9:
                index,value=t.data[2],int.from_bytes(t.data[3:],'big')
                if not (index==0 and value in {*range(1,24),255} or index==1 and value in (2,10,14) or index==9 and value==1):
                    raise ValueError('Unknown holiday NPC demo order')
                orders.add((index,value))
            if 14<=op<=24:
                targets=struct.unpack('>'+'H'*((len(t.data)-2)//2),t.data[2:])
                if op<=21:pending.update(n for n in targets if n not in ready)
                else:selects.update(targets)
    expected=[n for a,b in RANGES for n in range(a,b)]
    if sorted(ready)!=expected or sorted(selects)!=[0x35,0x44,0x4D,0x17F]:
        raise ValueError('Changed complete holiday dialogue/choice closure')
    mapping={n:FIRST+i for i,n in enumerate(expected)}
    choice_map={n:CHOICE_FIRST+i for i,n in enumerate(sorted(selects))}
    extra=[];new_choices=[];rows=[];choice_rows=[];credits=[]
    for n in expected:
        data=ready[n];out=bytearray(data);branches=select_count=0
        for t in tokenize(data,info):
            if t.kind=='cmd' and 14<=t.data[1]<=24:
                refs=mapping if t.data[1]<=21 else choice_map
                for at in range(2,len(t.data),2):
                    target=refs[int.from_bytes(t.data[at:at+2],'big')]
                    struct.pack_into('>H',out,t.offset+at,target)
                    if t.data[1]<=21:branches+=1
                    else:select_count+=1
        out=bytes(out);extra.append(out)
        adaptations=['Native encoding; retain official wording, line/page breaks, pauses, and demo orders',
                     'Remap all message branches and choices to stable additive native IDs']
        if edits[n]:adaptations.append('Remove redundant GameCube article-suppression flags; native insertions do not add articles')
        if dashes[n]:adaptations.append('Map the donor horizontal dash to the native halfwidth Latin hyphen')
        credits.append(credit(f'message:{mapping[n]:04X}',f'message:{n:04X}',messages[n],out,adaptations))
        rows.append(dict(donor_id=n,id=mapping[n],source_sha256=sha256(messages[n]),sha256=sha256(out),
            bytes=len(out),expanded_bound=expanded_bound(out,info),branches=branches,choices=select_count,
            article_adaptations=edits[n],dash_adaptations=dashes[n]))
    for n,target in choice_map.items():
        data=encode(decode_gc(choices[n],decoder),info)
        if not 1<=len(data)<=20 or any(c not in LATIN for c in data):raise ValueError('Invalid holiday choice')
        new_choices.append(data)
        credits.append(credit(f'select:{target:04X}',f'select:{n:04X}',choices[n],data,['Native encoding; unchanged official choice']))
        choice_rows.append(dict(donor_id=n,id=target,sha256=sha256(data),bytes=len(data)))
    directory=ROOT/'build/gamecube/files/forest_1st.arc.unpacked/data'
    strings={n:(directory/n).read_bytes() for n in STRING_FILES}
    if any(sha256(data)!=STRING_FILES[n] for n,data in strings.items()):raise ValueError('Changed complete donor string banks')
    bank=Bank('strings',0,0,strings['string_data.bin'],strings['string_data_table.bin']).entries()
    ranges=[dict(first=a,end=b,target=mapping[a]) for a,b in RANGES]
    packet=bytearray(struct.pack('>3I',0x41464844,1,3))
    for r in ranges:packet.extend(struct.pack('>3I',r['first'],r['end'],r['target']))
    fields=[]
    for kind,ids,width in (('day',range(0x64E,0x66D),4),('event',(0x6F8+i for i in EVENT_STRINGS),16)):
        for i,n in enumerate(ids):
            data=encode(decode_gc(bank[n],decoder),info)
            if not 1<=len(data)<=width or any(c not in LATIN for c in data):raise ValueError('Incomplete holiday field')
            data=data.ljust(width,b' ');packet.extend(data)
            identity=f'v3/holiday/{kind}/{i:02d}'
            credits.append(credit(identity,f'string:{n:04X}',bank[n],data,
                ['Native encoding and field padding; unchanged official wording']))
            fields.append(dict(id=identity,source_id=n,bytes=width,sha256=sha256(data)))
    packet.extend(bytes(-len(packet)%16))
    return extra,new_choices,bytes(packet),dict(first_id=FIRST,count=len(extra),first_choice=CHOICE_FIRST,
        choice_count=len(new_choices),ranges=ranges,rows=rows,choices=choice_rows,fields=fields,
        roots=list(ROOTS),branch_added=sorted(set(expected)-set(ROOTS)),npc_orders=sorted(orders),
        max_expanded_bytes=max(r['expanded_bound'] for r in rows),provenance_entries=credits,
        source_banks={**DONOR_FILES,**STRING_FILES})


def check_provenance(text):
    catalogue=json.loads((ROOT/'translations/provenance.json').read_bytes());validate(catalogue)
    indexed={r['id']:r for r in catalogue['entries']}
    if any(indexed.get(r['id'])!=r for r in text['provenance_entries']):
        raise ValueError('Holiday dialogue needs exact credits in the single provenance catalogue')


def install(base,prior,blob,core,output):
    if prior['equipment_resources']['npc_extra'].get('dialogue'):
        from v3_holiday_world import install as install_world
        return install_world(base,prior,blob,core,output)
    del blob
    from v3_furniture_pipeline import Source
    e=copy.deepcopy(prior['equipment_resources']);npc=e['npc_extra'];packet=npc['packet']
    if not npc.get('motion') or npc.get('dialogue'):raise ValueError('Holiday dialogue requires installed motion and no duplicate dialogue')
    physical.verify(base,prior['physical_resources']);files=by_vrom(base)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    contract=discover(source)
    if (sha256((ROOT/'local/ac-decomp/src/game/m_soncho.c').read_bytes())!='86925ff50163654cf795045563d93fa9da6859e81c6c5cf5d4e42fcc9bf8bf11' or
            source.raw('chg_string_idx$607')!=struct.pack('>29I',*EVENT_STRINGS)):
        raise ValueError('Changed complete holiday/card selector or event-name relation')
    for a,b,digest in NATIVE:
        if sha256(core[a-CODE_RAM:b-CODE_RAM])!=digest:raise ValueError(f'Changed holiday message transport {a:08X}')
    hook=next(h for h in e['diary_items']['hooks'] if h['kind']=='name')
    if hook['address']!=0x801969C8 or files[0x2800000].extract(base)[0x801969C8-0x801948E0:0x801969D0-0x801948E0]!=bytes.fromhex(hook['after']):
        raise ValueError('Holiday item names need the complete selected-category reader')
    messages,choices,fields,text=convert(base);check_provenance(text)
    text['choice_vrom']=prior['import_storage']['choice_vrom']
    directory=output/'holiday-dialogue';directory.mkdir()
    text['hooks']=patch_bounds(core,FIRST,len(messages))
    for a,op in ((0x80065544,0x2A010000),(0x80065DAC,0x28810000)):
        if u32(core,a-CODE_RAM)!=op|CHOICE_FIRST:raise ValueError('Changed shared choice bound')
        struct.pack_into('>I',core,a-CODE_RAM,op|(CHOICE_FIRST+len(choices)))
        text['hooks'].append(dict(address=a,before=op|CHOICE_FIRST,after=op|(CHOICE_FIRST+len(choices))))
    new_messages,new_table=extend_bank(files[MESSAGE].extract(base),files[TABLE].extract(base),messages,FIRST)
    cv=text['choice_vrom']
    new_choices,new_choice_table=extend_bank(files[cv].extract(base),files[CHOICE_TABLE].extract(base),choices,CHOICE_FIRST)
    text['resources']=[]
    for v,data in ((MESSAGE,new_messages),(TABLE,new_table),(cv,new_choices),(CHOICE_TABLE,new_choice_table)):
        filename=f'holiday-dialogue/text-{v:08X}.bin';write_new(output/filename,data)
        text['resources'].append(dict(vrom=v,file=filename,bytes=len(data),sha256=sha256(data),
            original_sha256=sha256(files[v].extract(base))))
    code,compiled=compile_part('holiday_dialogue',directory/'code',
        extra_sources=('overlays/v3/holiday_dialogue_native.c',))
    data=bytearray(base[packet['physical']:packet['physical']+SIZE])
    if sha256(data)!=packet['sha256'] or any(data[0x2800:0x4000]):raise ValueError('Changed NPC dialogue reservation')
    data[0x2800:0x2800+len(code)]=code;data[0x3800:0x3800+len(fields)]=fields
    replacement=next(copy.deepcopy(r) for r in prior['physical_resources'] if r['id']==packet['id'])
    replacement['sha256']=sha256(data)
    records=[replacement if r['id']==replacement['id'] else copy.deepcopy(r) for r in prior['physical_resources']]
    previous=packet['sha256'];packet.update(sha256=sha256(data),crc32=zlib.crc32(data))
    npc['dialogue']=dict(format='AFV3-HOLIDAY-DIALOGUE-1',text=text,code=compiled,contract=contract,
        fields=dict(ram=RAM+0x3800,bytes=len(fields),sha256=sha256(fields)),installed=True,
        native_transport=[dict(start=a,end=b,sha256=s) for a,b,s in NATIVE],
        native_execution_verified=False,actor_active=False,additional_resident_bytes=0)
    npc['pending']=['Event owner, live world/reward bindings, and cleanup','Separate exercise/card route',
                    'Connected native diary gameplay/save verification']
    npc['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    write_new(directory/'dialogue.json',(json.dumps(npc['dialogue'],indent=2)+'\n').encode())
    write_new(directory/'packet.bin',data)
    return e,{},dict(physical_resources=records),[(dict(replacement,previous_sha256=previous),bytes(data))]


def finish(image,base,prior,output,equipment):
    from v3_event_text import install as install_text
    npc=equipment['npc_extra'];old=prior['equipment_resources']['npc_extra']
    if npc.get('dialogue') and not old.get('dialogue'):
        return install_text(image,base,output,npc['dialogue']['text'],relocate=True,
            physical_resources=prior['physical_resources'],
            reserved_end=prior.get('resource_capacity',{}).get('reserved_physical_end',0))
    return image
