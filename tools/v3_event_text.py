"""Additive event dialogue, with every adaptation in the one source catalogue."""
import json
import struct

from aflib import CODE_RAM,DMA_START,DMA_END,by_vrom,sha256,u32
from apply_translation import write_new
from gc_text import decode_gc
from runtime_module import module_command_info
from textcodec import encode,tokenize
from textvalidate import expanded_bound
from v3_asset_loader import ROOT
from v3_camper_text import donor,extend_bank
from text_provenance import validate

FIRST=12007
REWARD_FIRST=FIRST+4
MESSAGE,TABLE,CHOICES,CHOICE_TABLE=0x1FA0000,0xCF9000,0x25F0000,0xD06000
# Only the platform-specific merchandise pages are newly written. Greetings,
# final questions, page boundaries, and branch/timing commands retain the donor.
PAGES=(
    ("Today's hot item{cmd:7F0308}\nis K.K.'s music!{cmd:7F04}\n",
     "You can get one right now\nfor only 980 Bells!{cmd:7F0314}\nA special, one-time bargain!{cmd:7F04}\n"),
    ("I've got a real treat for you\ntoday! {cmd:7F0308}Rare gyroids!{cmd:7F04}\n",
     "Just 1,000 Bells each!{cmd:7F0314}\nA special, one-time bargain!{cmd:7F04}\n"),
    ("Look what I've got for you!{cmd:7F0308}\nFruit from far and wide!{cmd:7F04}\n",
     "Only 1,280 Bells each!{cmd:7F0314}\nA bargain's bargain!{cmd:7F04}\n"))
LABELS=(b'Original wares  ',b'Festival items  ')


def prepare_rewards(base,output,source):
    """Import complete official message records selected by the donor's reward callback."""
    raw,constructor=source.function(0x19861C)
    if (len(raw)!=200 or sha256(raw)!='cd0326d46ea06262ae35f80a6752ae8a1c38de14879fd37f840b51efba211492'
            or constructor['symbol']!='Player_actor_Demo_get_golden_item_demo_ct'):
        raise ValueError('Changed complete reward message constructor')
    ordered=[word&65535 for word in struct.unpack('>50I',raw)
             if word>>16==0x3860 and word&65535>=0x3000]
    if ordered!=[0x306F,0x306D,0x306E,0x3070]:raise ValueError('Changed reward type/message relation')
    files=by_vrom(base);info=module_command_info(base);messages,_,decoder=donor()
    extra=[];rows=[];credits=[]
    for index,source_id in enumerate(sorted(ordered)):
        target=REWARD_FIRST+index;original=messages[source_id]
        data=encode(decode_gc(original,decoder),info);tokens=list(tokenize(data,info))
        if (tokens[-1].data!=b'\x7f\0' or expanded_bound(data,info)>1024
                or any(t.kind=='cmd' and t.data[1] not in (0,2,3,5) for t in tokens)
                or sum(t.kind=='cmd' and t.data[1]==0 for t in tokens)!=1):
            raise ValueError('Reward text has an unreviewed operation or native overflow')
        extra.append(data)
        rows.append(dict(id=target,source_id=source_id,bytes=len(data),sha256=sha256(data),
                         source_sha256=sha256(original),expanded_bound=expanded_bound(data,info)))
        credits.append(dict(id=f'message:{target:04X}',native_sha256=None,locales=dict(en=dict(
            credit='official',locator=['tools/v3_event_text.py:prepare_rewards',f'N64/message/{target:04X}'],
            source=dict(source='user-supplied GAFE01 revision 0 disc',reference_id=f'message:{source_id:04X}',
                        reference_sha256=sha256(original)),
            adaptations=['Lossless native encoding; retain all official wording, pages, colours, and message commands'],
            human_review='not_recorded',encoded_sha256=sha256(data)))))
    catalogue=json.loads((ROOT/'translations/provenance.json').read_bytes());validate(catalogue)
    indexed={r['id']:r for r in catalogue['entries']};missing=[]
    for row in credits:
        if row['id'] not in indexed:missing.append(row)
        elif indexed[row['id']]!=row:raise ValueError('Conflicting reward text provenance: '+row['id'])
    payload,directory=extend_bank(files[MESSAGE].extract(base),files[TABLE].extract(base),extra,REWARD_FIRST)
    resources=[]
    for v,data in ((MESSAGE,payload),(TABLE,directory),(CHOICES,files[CHOICES].extract(base)),
                   (CHOICE_TABLE,files[CHOICE_TABLE].extract(base))):
        filename=f'reward-text-{v:08X}.bin';write_new(output/filename,data)
        resources.append(dict(vrom=v,file=filename,bytes=len(data),sha256=sha256(data),
                              original_sha256=sha256(files[v].extract(base))))
    return dict(first_id=REWARD_FIRST,count=len(extra),rows=rows,source_constructor=constructor,
        type_messages=[REWARD_FIRST+sorted(ordered).index(i) for i in ordered],resources=resources,
        provenance_entries=credits,provenance_missing=missing,
        max_expanded_bytes=max(row['expanded_bound'] for row in rows))


def prepare(base,output):
    files=by_vrom(base);info=module_command_info(base);messages,_,decoder=donor()
    originals=[];rows=[]
    for i,pages in enumerate(PAGES):
        donor_id=0x1758+i;text=decode_gc(messages[donor_id],decoder)
        parts=text.split('{cmd:7F02}')
        if len(parts)!=4:raise ValueError('Changed donor stall page boundaries')
        data=encode('{cmd:7F02}'.join((parts[0],*pages,parts[3])),info)
        originals.append(data)
        rows.append(dict(id=f'message:{FIRST+i:04X}',native_sha256=None,locales=dict(en=dict(
            credit='assistant',locator=['tools/v3_event_text.py:PAGES',f'N64/message/{FIRST+i:04X}'],
            source=dict(source='Project adaptation for original N64 merchandise',
                native_reference_id=f'message:{donor_id:04X}',
                official_reference=dict(source='user-supplied GAFE01 revision 0 disc',
                    reference_id=f'message:{donor_id:04X}',reference_sha256=sha256(messages[donor_id])),
                human_translation_search='The official donor and supplied AFProjectDistro both describe different merchandise'),
            authored_fragments=list(pages),adaptations=['Retain official greeting, final question, branches, and unaffected timing; correct native goods and prices'],
            human_review='not_recorded',encoded_sha256=sha256(data)))))
    donor_id=0x175C;donor_text=decode_gc(messages[donor_id],decoder)
    phrase="What'll it be?"
    if donor_text.count(phrase)!=1:raise ValueError('Changed official stall menu question')
    prompt=encode(donor_text[donor_text.index(phrase):],info);originals.append(prompt)
    rows.append(dict(id=f'message:{FIRST+3:04X}',native_sha256=None,locales=dict(en=dict(
        credit='official',locator=['tools/v3_event_text.py:prepare',f'N64/message/{FIRST+3:04X}'],
        source=dict(source='user-supplied GAFE01 revision 0 disc',reference_id='message:175C',
                    reference_sha256=sha256(messages[donor_id])),
        adaptations=['Use the complete final question and command suffix for the additive stock-route menu'],
        human_review='not_recorded',encoded_sha256=sha256(prompt)))))
    for role,label in zip(('original','imported'),LABELS):
        rows.append(dict(id='ui/stall/route-'+role,native_sha256=None,locales=dict(en=dict(
            credit='assistant',locator=['overlays/v3/event_menu.c:routes'],
            source='Project-authored option for the added stock-route menu; no counterpart in the unmodified games',
            text=label.decode(),human_review='not_recorded',encoded_sha256=sha256(label)))))
    for data in originals:
        tokens=list(tokenize(data,info))
        if (tokens[-1].data!=b'\x7f\x01' or expanded_bound(data,info)>1024 or
                sum(t.kind=='cmd' and t.data[1] in (0,1) for t in tokens)!=1):
            raise ValueError('Event message violates native buffer/termination bounds')
    catalogue=json.loads((ROOT/'translations/provenance.json').read_bytes());validate(catalogue)
    indexed={r['id']:r for r in catalogue['entries']}
    missing=[]
    for row in rows:
        if row['id'] not in indexed:missing.append(row)
        elif indexed[row['id']]!=row:raise ValueError('Conflicting event text provenance: '+row['id'])
    # Original copyrighted messages remain in ignored resources, not source.
    payload,directory=extend_bank(files[MESSAGE].extract(base),files[TABLE].extract(base),originals,FIRST)
    resources=[]
    for v,data in ((MESSAGE,payload),(TABLE,directory),(CHOICES,files[CHOICES].extract(base)),
                   (CHOICE_TABLE,files[CHOICE_TABLE].extract(base))):
        filename=f'event-text-{v:08X}.bin';write_new(output/filename,data)
        resources.append(dict(vrom=v,file=filename,bytes=len(data),sha256=sha256(data),
                              original_sha256=sha256(files[v].extract(base))))
    return dict(first_id=FIRST,count=len(originals),menu_id=FIRST+3,
        resources=resources,provenance_entries=rows,provenance_missing=missing,
        max_expanded_bytes=max(expanded_bound(d,info) for d in originals))


def patch_bounds(core,first=FIRST,count=4):
    patches=[]
    for address,opcode in ((0x8009E3A4,0x2A010000),(0x8009E668,0x28A10000)):
        at=address-CODE_RAM;before=opcode|first;after=opcode|(first+count)
        if u32(core,at)!=before:raise ValueError('Changed complete message reader bound')
        struct.pack_into('>I',core,at,after);patches.append(dict(address=address,before=before,after=after))
    return patches


def install(image,base,output,text):
    """Repack the existing four-file text region, never grow the import blob."""
    files=by_vrom(base);rows=text['resources'];moving={r['vrom'] for r in rows}
    ordered=sorted(rows,key=lambda r:files[r['vrom']].pstart)
    start=files[ordered[0]['vrom']].pstart;cursor=start;loaded={};placements=[]
    if moving!={MESSAGE,TABLE,CHOICES,CHOICE_TABLE} or start!=0x3000000:
        raise ValueError('Changed event text region ownership')
    for row in ordered:
        v=row['vrom'];entry=files[v];data=(output/row['file']).read_bytes()
        if (entry.pend or sha256(entry.extract(base))!=row['original_sha256'] or
                sha256(data)!=row['sha256'] or len(data)!=row['bytes'] or len(data)%16):
            raise ValueError('Changed event text resource')
        if any(v<e.vend and e.vstart<v+len(data) for key,e in files.items() if key not in moving):
            raise ValueError('Expanded event text virtual range overlaps another resource')
        loaded[v]=data;placements.append(dict(vrom=v,bytes=len(data),physical=cursor,sha256=sha256(data)))
        cursor+=len(data)
    if any(a['vrom']<b['vrom']+b['bytes'] and b['vrom']<a['vrom']+a['bytes']
           for i,a in enumerate(placements) for b in placements[i+1:]):
        raise ValueError('Expanded text resources overlap each other virtually')
    old_end=max(files[v].pstart+files[v].size for v in moving)
    if (cursor>len(image) or cursor<old_end or any(base[old_end:cursor]) or
            any(e.pstart<cursor and start<(e.pend or e.pstart+e.size) for v,e in files.items()
                if v not in moving and e.pstart!=0xFFFFFFFF)):
        raise ValueError('Event text physical growth overlaps another resource')
    # Every overwritten pre-existing byte belongs to one of these four files.
    covered=start
    for row in ordered:
        e=files[row['vrom']]
        if e.pstart!=covered:raise ValueError('Text region has undeclared gaps/owners')
        if image[e.pstart:e.pstart+e.size]!=e.extract(base):
            raise ValueError('Text region already modified by another adapter')
        covered+=e.size
    before=bytes(image[DMA_START:DMA_END]);expected=bytearray(before)
    for row in placements:
        v=row['vrom'];at=DMA_START+files[v].index*16
        value=(v,v+row['bytes'],row['physical'],0)
        struct.pack_into('>4I',image,at,*value);struct.pack_into('>4I',expected,at-DMA_START,*value)
        image[row['physical']:row['physical']+row['bytes']]=loaded[v]
    if image[DMA_START:DMA_END]!=expected:raise ValueError('Undeclared event text directory change')
    text['placements']=placements
    return image
