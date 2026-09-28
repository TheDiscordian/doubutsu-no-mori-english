"""Bind the diary calendar to native dates and credited English event labels."""
import json
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from gamecube import rarc_files
from gc_text import decode_gc,decoder_tables,plain
from textbanks import Bank
from v3_furniture_pipeline import ROOT
from v3_import_catalog import DONOR_FILES,DECODER_SHA
from v3_villager_text import FIRST_SHA

# One calendar entry per actual holiday, not per subordinate sports/crowd actor.
# single identifies the named date of an overnight event (not its spillover).
RULES=(
    ('new-year',14,3,1),('valentine',19,19,1),('white-day',21,23,1),
    ('mother',24,28,1),('father',25,27,1),('cherry',26,12,0),
    ('spring-sports',29,18,1),('children',36,4,1),('summer-fishing',40,20,1),
    ('aerobics',43,16,0),('fireworks',46,11,1),('harvest-moon',50,22,1),
    ('second-moon',54,21,1),('fall-sports',58,1,1),('mushrooms',65,15,0),
    ('halloween',68,13,1),('jingle',74,5,1),('new-year-eve',78,6,1),
    ('autumn-fishing',71,2,1),
)
TABLE_SHA='ce1d33ad17ccce132d32cd5e78a0028d45d4573c142b1912c3bb755554a67876'
NATIVE=(
    (0x800D5E70,936,'f34385a54155a9f7ef740cda4c8583bb76a3c6725c718b1db0b353eb6c164d72','lunar conversion and all helpers'),
    (0x8010EFE0,26,'dd54b33a2f7121c4a4447e79fad419dd021bd750b2533459e9a5df4f66d92ffb','Gregorian month lengths'),
    (0x8010EFFC,858,'12c9e9a4544d5cb3983cd333ee62a6e53852e6477e8f40ca1669bb34f48ce530','complete lunar month table'),
    (0x8010F358,132,'d3eb034302ff466d115a2708e275ca786413507127717e891067a7ef70c3f700','complete lunar leap table'),
    (0x8007DF98,356,'c48ea0d15baa14479345b065ffcc15bc5638229826df3988ac01ceadbac5c5f9','native weekly date decoder'),
    (0x8007F1A8,228,'b085f1b718303bc37aca383e2036e146bfc00364ce35e19d66cd04ce7f81a4f8','native encoded date decoder'),
    (0x8007F374,172,'b6e360a77ae87541fc3d7b4118842e3bc73afd507cc540338a2383c979dfb3f2','player, clock, and birthday readers'),
    (0x8007F988,444,'a361fb2da76a8e4e20a442b307f76a355a9aa668fddeea7e28c34d73266704b9','complete gated event-update caller'),
    (0x800815F0,208,'52d3604a77f595f41ec1c255210b246b791ccdc7180f2f8f0c8d083f4e862ab9','complete live-player predicate'),
)
LABELS={
    'new-year':('string',0x6F8,None), 'valentine':('message',0xB8B,"Valentine's Day"),
    'white-day':('catalogue','message:26F5','White Day'),
    'mother':('string',0x6FF,None), 'father':('string',0x701,None),
    'cherry':('string',0x6FC,None), 'spring-sports':('string',0x6FA,None),
    'children':('catalogue','message:17FB',"Children's Day"),
    'summer-fishing':('string',0x702,None), 'aerobics':('select',0xBD,None),
    'fireworks':('string',0x704,None), 'harvest-moon':('string',0x709,None),
    'second-moon':('catalogue','select:00BF',None), 'fall-sports':('string',0x708,None),
    'mushrooms':('message',0x1813,'mushroom season'), 'halloween':('string',0x70B,None),
    'jingle':('message',0x7AA,'Jingle'), 'new-year-eve':('string',0x713,None),
    'autumn-fishing':('string',0x70E,None), 'birthday':('string',0x714,None),
}


def labels():
    entries={r['id']:r for r in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
    banks={}
    for archive,digest,names in (('forest_1st.arc',FIRST_SHA,('string','select')),
            ('forest_2nd.arc',DONOR_FILES['forest_2nd.arc'][1],('message',))):
        raw=(ROOT/'build/gamecube/files'/archive).read_bytes()
        if sha256(raw)!=digest:raise ValueError('Changed complete donor text archive: '+archive)
        members=dict(rarc_files(raw))
        for name in names:
            banks[name]=Bank(name,0,0,members[f'data/{name}_data.bin'],members[f'data/{name}_data_table.bin']).entries()
    decoder=ROOT/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes())!=DECODER_SHA:raise ValueError('Changed official text decoder')
    tables=decoder_tables(decoder);result=[]
    for key,(bank,index,excerpt) in LABELS.items():
        if bank=='catalogue':
            source=entries[index]['locales']['en'];text=source['text'];credit=source['credit']
            digest=source['encoded_sha256'];ref=index
        else:
            raw=banks[bank][index];text=plain(decode_gc(raw,tables));credit='official'
            digest=sha256(raw);ref=f'{bank}:{index:04X}'
        if excerpt is not None:
            if excerpt not in text:raise ValueError('Absent source event name: '+key)
            text=excerpt
        # Headline capitalization is recorded as an adaptation, not new wording.
        if key=='mushrooms':text=text[0].upper()+text[1:]
        encoded=text.encode('ascii')
        if not 1<=len(encoded)<=48 or any(b<32 or b>=127 for b in encoded):
            raise ValueError('Invalid calendar label: '+key)
        result.append(dict(key=key,text=text,credit=credit,reference_id=ref,
            reference_sha256=digest,encoded_sha256=sha256(encoded),
            source_kind='catalogue' if bank=='catalogue' else 'GAFE01-r0',excerpt=excerpt))
    return result


def prepare(image):
    core=by_vrom(image)[CODE_VROM].extract(image)
    for address,size,digest,name in NATIVE:
        if sha256(core[address-CODE_RAM:address-CODE_RAM+size])!=digest:
            raise ValueError('Changed native diary calendar dependency: '+name)
    schedule=core[0x80104B60-CODE_RAM:0x80104F2C-CODE_RAM]
    if sha256(schedule)!=TABLE_SHA:raise ValueError('Changed complete native event master')
    rows=list(struct.iter_unpack('>3I',schedule));names=labels()
    entries={r['id']:r for r in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
    generated=['#include "diary_events.h"\nconst AFDiaryEventRule af_diary_event_rules[]={\n']
    for key,row,event,single in RULES:
        if rows[row][2]!=event:raise ValueError('Changed calendar event identity: '+key)
        generated.append(f'    {{{row},{event},{single},0}},\n')
    generated.append('};\nconst AFDiaryEventLabel af_diary_event_labels[]={\n')
    for item in names:
        key='v3/diary/event/'+item['key'];entry=entries[key]['locales']['en']
        if (entry['text']!=item['text'] or entry['credit']!=item['credit'] or
                entry['encoded_sha256']!=item['encoded_sha256'] or
                entry['source']['reference_id']!=item['reference_id'] or
                entry['source']['reference_sha256']!=item['reference_sha256']):
            raise ValueError('Changed diary event provenance: '+key)
        generated.append(f'    {{(const unsigned char *){json.dumps(item["text"])},{len(item["text"])} }},\n')
    generated.append('};\n')
    return ''.join(generated).encode(),dict(native_schedule_ram=0x80104B60,
        native_schedule_sha256=TABLE_SHA,rules=[dict(key=k,row=r,native_event=t,single=bool(s),
            start=rows[r][0],end=rows[r][1]) for k,r,t,s in RULES],labels=names,
        native_consumers=[dict(address=a,bytes=n,sha256=d,purpose=p) for a,n,d,p in NATIVE],
        calendar_uses_native_dates=True,participation_callers_installed=False)
