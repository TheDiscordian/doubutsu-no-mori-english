"""Official bank text with additive IDs and retained native mail/Pak actions."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256
from apply_translation import write_new
from gc_adapter import remove_redundant_article_suppression
from gc_text import decode_gc
from runtime_module import module_command_info
from textbanks import Bank
from textcodec import encode,tokenize,LATIN
from textvalidate import expanded_bound
from v3_asset_loader import ROOT
from v3_camper_text import donor,extend_bank,DONOR_FILES
from v3_event_text import MESSAGE,TABLE,CHOICE_TABLE
from v3_holiday_dialogue import credit
from v3_post_office import REFERENCES

ROOTS=(0x8CF,0x8D0,0x8D1,0x8D2,0x8DD,0x8DE,0x8DF,0x8E0,
       0x2DE0,0x2DE1,0x2DE2,0x2DE3,0x3BAE,0x3BAF)
CHOICES=(0x5B,0x1D5,0x9D,0x15)
# These destinations already have ordinary N64 actions. In particular, the
# donor Memory Card menu is not the native Controller Pak letter-save menu.
NATIVE_DESTINATIONS=(0x8AF,0x8B0,0x8B5,0x8B6,0x1BE7,0x1BE8,0x8B3,0x8B4)
NATIVE_TEXT={
    0x8AF:'569a5d15ec6aca66415dd13a1a61bca5fffcff582eceb3135bbdf97831ff10d9',
    0x8B0:'ec4df0ed3310b1ad5bd22c66343e53cca2ae2480608059bbd3be158ebed075a6',
    0x8B5:'3e1b19e0b71b7d4735b7d949b2812fc0a7dd59ca2160bcb93adeaca4111dc749',
    0x8B6:'1c84160baa0e78fd20ed7a2e4c6587444f1eac6edf72c6bef3d8dbccc480a3f8',
    0x1BE7:'f473d4f750e9d0411b0d4443102266c65e1f1b95617e85e8882d55494d42c5b0',
    0x1BE8:'729fad2259c5b19c3e5fc29a28684645bb99214ba8ff6a63c96985b4dfa94129',
    0x8B3:'48a8d5e7aa00ca74449152ba2ef75bf629d3395440e49fd85b066f499be447f9',
    0x8B4:'89aea7cd91302fd16458a4af143d77e64f151ed7ac3a9df0f1be009d2ad5c182',
}
FIRST,CHOICE_FIRST=13234,544


def prepare(image,prior,out):
    for path in ('src/actor/npc/ac_npc_post_girl.c','src/actor/npc/ac_npc_post_girl.c_inc'):
        if sha256((ROOT/'local/ac-decomp'/path).read_bytes())!=REFERENCES[path]:
            raise ValueError('Changed complete bank conversation source')
    files=by_vrom(image);cv=prior['import_storage']['choice_vrom']
    mb,tb,cb,ct=(files[v].extract(image) for v in (MESSAGE,TABLE,cv,CHOICE_TABLE))
    old_messages=Bank('messages',0,0,mb,tb).entries()
    old_choices=Bank('choices',0,0,cb,ct).entries()
    if (len(old_messages),len(old_choices))!=(FIRST,CHOICE_FIRST):
        raise ValueError('Changed additive bank dialogue IDs; review the current complete bank first')
    if any(sha256(old_messages[n])!=digest for n,digest in NATIVE_TEXT.items()):
        raise ValueError('Changed native mail/Pak dialogue destination')
    messages,choices,decoder=donor();info=module_command_info(image)
    mapping={n:FIRST+i for i,n in enumerate(ROOTS)}
    choice_map={n:CHOICE_FIRST+i for i,n in enumerate(CHOICES)}
    targets={**{n:n for n in NATIVE_DESTINATIONS},**mapping}
    extra=[];selects=[];rows=[];choice_rows=[];credits=[];branches=set();orders=set()
    allowed={0,1,2,3,4,5,9,13,15,16,17,18,24,25,39,81,94}
    def attribution(kind,n,target,original,data,adaptations):
        row=credit(f'{kind}:{target:04X}',f'{kind}:{n:04X}',original,data,adaptations)
        row['locales']['en']['locator'][0]='tools/v3_bank_dialogue.py:prepare'
        credits.append(row)
    for n in ROOTS:
        text,article=remove_redundant_article_suppression(decode_gc(messages[n],decoder))
        data=encode(text,info);out_data=bytearray(data);tokens=list(tokenize(data,info))
        if (not tokens or tokens[-1].data not in (b'\x7f\0',b'\x7f\1') or
            sum(t.kind=='cmd' and t.data[1] in (0,1) for t in tokens)!=1 or
            any(t.kind!='cmd' and (t.kind!='text' or t.data[0] not in LATIN|{0xCD}) for t in tokens) or
            expanded_bound(data,info)>1024):
            raise ValueError(f'Invalid complete bank message: {n:04X}')
        for t in tokens:
            if t.kind!='cmd':continue
            op=t.data[1]
            if op not in allowed:raise ValueError('Unreviewed bank command: '+t.data.hex())
            if op==9:
                order=(t.data[2],int.from_bytes(t.data[3:],'big'))
                if not (order[0]==0 and order[1] in {*range(1,24),255} or order==(9,1)):
                    raise ValueError('Unreviewed bank demo order')
                orders.add(order)
            if 15<=op<=18 or op==24:
                refs=choice_map if op==24 else targets
                for at in range(2,len(t.data),2):
                    target=int.from_bytes(t.data[at:at+2],'big')
                    if target not in refs:raise ValueError('Bank branch escapes its reviewed native/source actions')
                    struct.pack_into('>H',out_data,t.offset+at,refs[target])
                    if op!=24:branches.add(target)
        data=bytes(out_data);extra.append(data)
        adaptations=['Native encoding; preserve official wording, line/page breaks, pauses, and demo orders',
            'Use additive bank messages and choices; retain ordinary N64 send-letter, Controller Pak save-letter, and exit destinations']
        if article:adaptations.append('Remove redundant article-suppression flags before native insertion')
        attribution('message',n,mapping[n],messages[n],data,adaptations)
        rows.append(dict(donor_id=n,id=mapping[n],source_sha256=sha256(messages[n]),
            sha256=sha256(data),bytes=len(data),expanded_bound=expanded_bound(data,info)))
    if branches!=set(NATIVE_DESTINATIONS)|{0x2DE0,0x2DE1}:
        raise ValueError('Changed complete bank greeting/continuation branch set')
    for n,target in choice_map.items():
        data=encode(decode_gc(choices[n],decoder),info)
        if not 1<=len(data)<=20 or any(c not in LATIN for c in data):
            raise ValueError('Official bank choice exceeds its native field')
        selects.append(data)
        attribution('select',n,target,choices[n],data,['Native encoding; unchanged official caption'])
        choice_rows.append(dict(donor_id=n,id=target,source_sha256=sha256(choices[n]),sha256=sha256(data),bytes=len(data)))
    new_m,new_t=extend_bank(mb,tb,extra,FIRST)
    new_c,new_ct=extend_bank(cb,ct,selects,CHOICE_FIRST)
    resources=[];out=Path(out).resolve()
    if not out.is_relative_to(ROOT/'build'):raise ValueError('Use an ignored bank dialogue directory')
    out.mkdir(parents=True,exist_ok=False)
    for name,v,data,old in (('messages.bin',MESSAGE,new_m,mb),('message-table.bin',TABLE,new_t,tb),
            ('choices.bin',cv,new_c,cb),('choice-table.bin',CHOICE_TABLE,new_ct,ct)):
        write_new(out/name,data)
        resources.append(dict(file=name,vrom=v,bytes=len(data),sha256=sha256(data),previous_sha256=sha256(old)))
    # Each direction maps only these owned messages. Existing source
    # destinations stay native, preserving message-number comparisons in both
    # the bank controller and the ordinary Pelly letter/Pak controllers.
    source='#include "bank_dialogue.h"\nstatic const unsigned short ids[][2]={\n'
    source+=''.join(f' {{0x{n:04X},0x{target:04X}}},\n' for n,target in mapping.items())+'};\n'
    source+='''static int translate(int n,int reverse) {
    for(unsigned int i=0;i<sizeof(ids)/sizeof(*ids);i++)
        if(n==ids[i][reverse])return ids[i][!reverse];
    return n;
}
int af_bank_pelly_message_map(int n) {return translate(n,0);}
int af_bank_pelly_message_unmap(int n) {return translate(n,1);}
'''
    write_new(out/'bank-dialogue.c',source.encode())
    report=dict(format='AFV3-BANK-DIALOGUE-1',first_id=FIRST,count=len(extra),first_choice=CHOICE_FIRST,
        choice_count=len(selects),mapping=mapping,choice_mapping=choice_map,messages=rows,choices=choice_rows,
        native_destinations=[dict(id=n,bytes=len(old_messages[n]),sha256=sha256(old_messages[n])) for n in NATIVE_DESTINATIONS],
        npc_orders=sorted(orders),max_expanded_bytes=max(r['expanded_bound'] for r in rows),
        source_banks=DONOR_FILES,resources=resources,provenance_entries=credits,
        generated_sha256=sha256(source.encode()),installed=False,ordinary_gameplay_tested=False)
    write_new(out/'dialogue.json',(json.dumps(report,indent=2,ensure_ascii=False)+'\n').encode())
    return report


def main():
    from v3_furniture_install import inputs
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-lock',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();image,prior=inputs(args.base_lock)
    r=prepare(image,prior,args.output)
    print(json.dumps({k:r[k] for k in ('first_id','count','first_choice','choice_count','max_expanded_bytes','installed')}))


if __name__=='__main__':main()
