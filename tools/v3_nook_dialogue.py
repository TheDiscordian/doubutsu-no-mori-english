"""Complete official Nook code-entry/result text, with native menu routing."""
import copy
import json
import struct

from aflib import by_vrom,sha256
from gc_adapter import remove_redundant_article_suppression
from gc_text import decode_gc
from runtime_module import module_command_info
from textbanks import Bank
from textcodec import LATIN,GLYPHS,encode,tokenize
from textvalidate import expanded_bound
from v3_asset_loader import ROOT
from v3_camper_text import donor,extend_bank,DONOR_FILES
from v3_event_text import MESSAGE,TABLE,CHOICE_TABLE
from v3_holiday_dialogue import credit
from v3_nook_font import assets
from extended_glyphs import ACCENT_GLYPHS
from v3_password_policy import REFERENCES

HEADER_SHA='69ad7b5e183c2ead62f7b8d13cbc19490f0e9a259c4dc7d5c54706f913aa6e50'
ROOTS=tuple(range(0x3E07,0x3E17))
RESULTS=(0x3E0B,0x3E0D,0x3E0E,0x3E0F,0x3E10,0x3E11,0x3E12,0x3E14,0x3E16,0x3E0C)
ROOT_MENU=bytes.fromhex('7f18000a01c40009000b')


def prepare(image,prior,source,out):
    reference=ROOT/'local/ac-decomp'
    for name,digest in (('src/actor/npc/ac_npc_shop_common.c',REFERENCES['src/actor/npc/ac_npc_shop_common.c']),
            ('include/ac_npc_shop_common.h',HEADER_SHA)):
        if sha256((reference/name).read_bytes())!=digest:
            raise ValueError('Changed complete Nook code conversation source')
    # Two-byte tags are admitted only with exact extracted source pixels and
    # registered font entries. The connected installer binds this font owner.
    _,glyphs=assets(source)
    if [(r['code'],r['encoding']) for r in glyphs if r['code'] in (0xD1,0xD4)]!=[(0xD1,'80D1'),(0xD4,'80D4')]:
        raise ValueError('Missing complete code/card glyph conversion')
    files=by_vrom(image);cv=prior['import_storage']['choice_vrom']
    mb,tb,cb,ct=(files[v].extract(image) for v in (MESSAGE,TABLE,cv,CHOICE_TABLE))
    old_messages=Bank('messages',0,0,mb,tb).entries()
    old_choices=Bank('choices',0,0,cb,ct).entries()
    first,choice_first=len(old_messages),len(old_choices)
    messages,choices,decoder=donor();info=module_command_info(image)
    mapping={n:first+i for i,n in enumerate(ROOTS)}
    selected=(3,9,11,0x24D)
    choice_map={n:choice_first+i for i,n in enumerate(selected)}
    new_choices=[];credits=[];choice_rows=[]
    for n,target in choice_map.items():
        data=encode(decode_gc(choices[n],decoder),info)
        if not 1<=len(data)<=20 or any(c not in LATIN for c in data):
            raise ValueError('Official Nook choice exceeds its native English field')
        new_choices.append(data)
        row=credit(f'select:{target:04X}',f'select:{n:04X}',choices[n],data,
            ['Native encoding; unchanged official caption'])
        row['locales']['en']['locator'][0]='tools/v3_nook_dialogue.py:prepare';credits.append(row)
        choice_rows.append(dict(donor_id=n,id=target,sha256=sha256(data)))
    # Native Nook already uses four entries, in this order. Keep every existing
    # action; the fourth entry reaches the code/leave sub-menu. No fifth-entry
    # assumption or removal of turnip prices is made.
    native_root=struct.pack('>BB4H',0x7F,0x18,9,10,452,choice_map[9])
    extra=[];rows=[]
    allowed={0,1,2,3,4,9,13,22,24,25,26,42,43,47,51,52,53,80,85,94,114,115,117}
    for n in ROOTS:
        text,article=remove_redundant_article_suppression(decode_gc(messages[n],decoder))
        text=text.replace('⚷','{glyph:80D4}')
        data=encode(text,info);out_data=bytearray();changes=[]
        if n==0x3E07:
            # There is no native "Hear code"/house option in this route. Keep
            # the entire official question, and offer its implemented code
            # entry and ordinary exit rather than exposing unfinished actions.
            old=bytes.fromhex('7f18024e024c024d003d')
            if data.count(old)!=1:raise ValueError('Changed official other-things submenu')
            data=data.replace(old,struct.pack('>BB2H',0x7F,0x16,choice_map[0x24D],choice_map[11]))
            changes.append('Use the official Say code and Never mind captions for the native code/exit submenu')
        for t in tokenize(data,info):
            value=t.data
            if t.kind=='cmd':
                if value==ROOT_MENU:
                    value=native_root
                    changes.append('Retain native turnip-price, selling, catalogue, and other-things action order')
                elif value==bytes.fromhex('7f160003000b'):
                    value=struct.pack('>BB2H',0x7F,0x16,choice_map[3],choice_map[11])
                elif 14<=value[1]<=24:
                    if n!=0x3E07:raise ValueError('Unreviewed Nook message branch or choice')
                if value[1] not in allowed:raise ValueError(f'Unreviewed Nook command {value.hex()}')
                if value[1]==9:
                    index,order=value[2],int.from_bytes(value[3:],'big')
                    if not (index==0 and order in (*range(1,24),255) or index==1 and order==2 or index==9 and order==1):
                        raise ValueError('Unreviewed Nook demo order')
            elif t.kind=='glyph':
                if value!=b'\x80\xD4':raise ValueError('Unregistered Nook literal glyph')
            elif t.kind!='text' or value[0] not in LATIN|{0xCD}:
                raise ValueError('Unrepresentable Nook text character')
            out_data.extend(value)
        data=bytes(out_data);tokens=list(tokenize(data,info))
        # Mask the one reviewed glyph only for the shared conservative bound.
        # Its encoded length is unchanged, and code-row insertion is <=28,
        # less than that helper's existing 32-byte insertion allowance.
        bound=expanded_bound(data.replace(b'\x80\xD4',b'  '),info)
        if (not tokens or tokens[-1].data not in (b'\x7f\0',b'\x7f\1') or
                sum(t.kind=='cmd' and t.data[1] in (0,1) for t in tokens)!=1 or bound>1024):
            raise ValueError('Nook message exceeds its complete buffer or termination contract')
        extra.append(data)
        adaptations=['Native encoding; preserve official wording, pages, pauses, and orders',
            'Map the official card glyph to its separately registered source-pixel font cell',*changes]
        if article:adaptations.append('Remove redundant article-suppression flags before native item insertion')
        row=credit(f'message:{mapping[n]:04X}',f'message:{n:04X}',messages[n],data,adaptations)
        row['locales']['en']['locator'][0]='tools/v3_nook_dialogue.py:prepare';credits.append(row)
        rows.append(dict(donor_id=n,id=mapping[n],bytes=len(data),sha256=sha256(data),
            expanded_bound=bound,source_sha256=sha256(messages[n])))
    new_messages=list(old_messages);root_edits=[]
    catalogue={r['id']:r for r in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
    for n in (0x1092,0x10AC):
        expected=bytes.fromhex('7f180009000a01c4000b')
        if new_messages[n].count(expected)!=1:raise ValueError('Changed native Nook question choices')
        new_messages[n]=new_messages[n].replace(expected,native_root)
        root_edits.append(dict(id=n,before_sha256=sha256(old_messages[n]),sha256=sha256(new_messages[n])))
        key=f'message:{n:04X}'
        if key not in catalogue:raise ValueError('Missing native Nook root-message authorship')
        attribution=copy.deepcopy(catalogue[key]);locale=attribution['locales']['en']
        if locale['encoded_sha256']!=sha256(old_messages[n]):
            raise ValueError('Native Nook root credit does not match the complete installed text')
        locale['encoded_sha256']=sha256(new_messages[n])
        locale.setdefault('adaptations',[]).append('Retain native turnip-price, selling, and catalogue actions; route the fourth official caption to Other things')
        credits.append(attribution)
    def rebuild(entries):
        ends=[];end=0
        for data in entries:end+=len(data);ends.append(end)
        payload=b''.join(entries);table=struct.pack('>'+str(len(ends))+'I',*ends)+bytes(16)
        return payload+bytes(-len(payload)%16),table+bytes(-len(table)%16)
    new_m,new_t=rebuild(new_messages+extra)
    new_c,new_ct=extend_bank(cb,ct,new_choices,choice_first)
    resources=[];out.mkdir(parents=True,exist_ok=False)
    for name,v,data,old in (('messages.bin',MESSAGE,new_m,mb),('message-table.bin',TABLE,new_t,tb),
            ('choices.bin',cv,new_c,cb),('choice-table.bin',CHOICE_TABLE,new_ct,ct)):
        (out/name).write_bytes(data)
        resources.append(dict(file=name,vrom=v,bytes=len(data),sha256=sha256(data),previous_sha256=sha256(old)))
    # Native names contain six one-byte characters. Translate all six and pad
    # the complete donor field to eight; never read two bytes of the next field.
    donor_codes={}
    for i,c in enumerate(decoder['CHAR_MAP']):donor_codes.setdefault(c,[]).append(i)
    native_to_donor=[]
    donor_to_native=[]
    from textcodec import ENCODE
    extended={r['code'] for r in glyphs}
    for n in range(256):
        candidates=donor_codes.get(GLYPHS.get(n),[])
        native_to_donor.append(candidates[0] if len(candidates)==1 else 0xFFFF)
        c=decoder['CHAR_MAP'][n]
        donor_to_native.append(bytes((ENCODE[c],)) if c in ENCODE else
            bytes((0x80,n)) if n in extended else b'')
    report=dict(format='AFV3-NOOK-DIALOGUE-1',first_id=first,count=len(extra),first_choice=choice_first,
        choice_count=len(new_choices),mapping=mapping,result_messages=[mapping[n] for n in RESULTS],
        messages=rows,choices=choice_rows,root_edits=root_edits,resources=resources,
        source_banks=DONOR_FILES,provenance_entries=credits,
        max_expanded_bytes=max(r['expanded_bound'] for r in rows),
        native_to_donor=native_to_donor,donor_to_native=[v.hex() for v in donor_to_native],
        native_extended_name_codes=sorted(extended),
        native_name_bytes=6,donor_name_bytes=8,code_string_bytes=14,maximum_code_expansion=28,
        installed=False,native_execution_tested=False,ordinary_gameplay_tested=False)
    (out/'dialogue.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report
