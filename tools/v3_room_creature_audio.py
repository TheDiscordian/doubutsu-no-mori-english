"""Complete shared creature-trigger dependencies, separate from furniture loops."""
import json
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from v3_asset_loader import ROOT
from v3_villager_audio import read_audio_donor


def dependencies(source,image,report,selected=()):
    """Resolve every matching installed rig from its complete source callback."""
    from v3_furniture_rigs import EMBEDDED_CATEGORY
    donor,_=read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    receipts=[];tables=[]
    for name,at,n,digest in (
        ('scheduler',0x80014D18,0x4CC,'b17f70b903cc39ba73660c4df5714c7ee711da12111502c815a75bc85f8982b4'),
        ('sounds',0x800A99F6,34,'f417257fded10dc520e34a2a9e4f882779063fbaae4846459455e1daeb315a7d'),
        ('random_offsets',0x800A9A18,34,'3ba6e7f474dd701f2ad51cb1d241a658ace16e559d8d8f9f8d56a3075c5efc9e')):
        raw=donor.read(at,n)
        if sha256(raw)!=digest:raise ValueError('Changed complete creature sound source: '+name)
        receipts.append(dict(name=name,address=at,bytes=n,sha256=digest))
        if name!='scheduler':tables.append(list(struct.unpack('>17H',raw)))
    sounds,delays=tables;core=by_vrom(image)[CODE_VROM].extract(image)
    native=core[0x800FB744-CODE_RAM:0x800FBA90-CODE_RAM]
    if sha256(native)!='e619a3488a2ee48544f62f67c4d7b448f7625c880c49e3741d150997c9954b31':
        raise ValueError('Changed original native creature scheduler')
    rows=[]
    for rig in report['equipment_resources']['room_rigs']['rows']:
        item=rig['source_item_id']
        if rig.get('mode')!=13 or selected and item not in selected:continue
        profile=source.profile(int(item,16));adapter=profile['callback_adapter']
        sound=adapter.get('level_sound')
        if not sound:continue
        sid=sound['source_sound_id'];index=sid-54
        if (adapter['category']!=EMBEDDED_CATEGORY or not 0<=index<len(sounds)-1 or
                sound['excluded_states']!=[12,13,14,15] or sound['callback_installed']):
            raise ValueError('Unsupported complete embedded creature sound lifecycle')
        rows.append(dict(source_item_id=item,runtime_index=rig['runtime_index'],
            source_sound_id=sid,source_sound_word=sounds[index],random_offset=delays[index],
            source_excluded_states=sound['excluded_states'],native_excluded_states=[5,6,13,15],
            profile_sha256=profile['profile_sha256'],callback=adapter['functions']['move'],
            helper=adapter['helpers']['sAdo_RoomIncectPos']))
    if not rows or selected and set(selected)!={r['source_item_id'] for r in rows}:
        raise ValueError('Creature sound selection lacks complete installed source rigs')
    return json.loads(json.dumps(dict(category='timed-room-creature-triggers',rows=rows,
        source=receipts,source_sounds=sounds,source_random_offsets=delays,
        native_scheduler=dict(address=0x800FB744,bytes=len(native),sha256=sha256(native)),
        native_scheduler_installed=False,callback_installed=False)))
