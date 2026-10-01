"""Complete shared creature-trigger dependencies, separate from furniture loops."""
import json
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from v3_asset_loader import ROOT
from v3_villager_audio import read_audio_donor

TABLE=0x804B1F40
COUNT=17
DELAY=TABLE+COUNT*2
END=DELAY+COUNT*2
SCHEDULER=0x800FB744
SCHEDULER_BYTES=0x34C
SCHEDULER_SHA='e619a3488a2ee48544f62f67c4d7b448f7625c880c49e3741d150997c9954b31'
NATIVE_HELPER_SHA='ca7337575386faba579568df6e8e59f37eaf035d512a523984f109f01d853bbf'


def required_words(contract):
    # Retain the complete scheduler category, including source entries whose
    # room displays do not currently have an additional callback.
    return contract['source_sounds'][11:-1]


def scheduler_hooks():
    return tuple(dict(address=at,before=before,after=after) for at,before,after in (
        (0x800FB800,0x3C108011,0x3C100000|((TABLE+0x8000)>>16)),
        (0x800FB804,0x26103AFC,0x26100000|(TABLE&65535)),
        (0x800FB81C,0x3C0A8011,0x3C0A0000|((DELAY+0x8000)>>16)),
        (0x800FB828,0x254A3B14,0x254A0000|(DELAY&65535)),
        (0x800FB8F4,0x2841000C,0x28410000|COUNT),
        (0x800FB9A4,0x3C108011,0x3C100000|((TABLE+0x8000)>>16)),
        (0x800FB9AC,0x26103AFC,0x26100000|(TABLE&65535)),
        (0x800FB9D4,0x3C0C8011,0x3C0C0000|((DELAY+0x8000)>>16)),
        (0x800FB9DC,0x958C3B14,0x958C0000|(DELAY&65535))))


def checked_scheduler(core,installed=None):
    raw=bytearray(core[SCHEDULER-CODE_RAM:SCHEDULER-CODE_RAM+SCHEDULER_BYTES])
    if installed and installed.get('native_scheduler_installed'):
        if installed.get('scheduler_hooks')!=list(scheduler_hooks()):
            raise ValueError('Changed creature scheduler hook receipt')
        for hook in scheduler_hooks():
            at=hook['address']-SCHEDULER
            if struct.unpack_from('>I',raw,at)[0]!=hook['after']:
                raise ValueError('Changed installed creature scheduler instruction')
            struct.pack_into('>I',raw,at,hook['before'])
    if sha256(raw)!=SCHEDULER_SHA:
        raise ValueError('Changed complete native creature scheduler')
    # The positioned helper consumes (instance, index, world position), and
    # retains the native audio-coordinate calculation before dispatch.
    helper=core[0x800D24EC-CODE_RAM:0x800D252C-CODE_RAM]
    if sha256(helper)!=NATIVE_HELPER_SHA:
        raise ValueError('Changed complete native creature positioning helper')
    return dict(address=SCHEDULER,bytes=len(raw),sha256=sha256(raw))


def table_bytes(audio,core):
    source=audio['source'];words=source['source_sounds'];delays=source['source_random_offsets']
    if (len(words)!=COUNT or len(delays)!=COUNT or words[-1] or delays[-1] or
            struct.pack('>12H',*words[:11],0)!=core[0x80113AFC-CODE_RAM:0x80113B14-CODE_RAM] or
            struct.pack('>12H',*delays[:11],0)!=core[0x80113B14-CODE_RAM:0x80113B2C-CODE_RAM]):
        raise ValueError('Creature tables change an existing native sound or delay')
    programs={p['source_sound_word']:p for p in audio['programs']}
    if not set(required_words(source))<=set(programs):
        raise ValueError('Complete creature scheduler programs are not installed')
    mapped=words[:11]+[programs[word]['native_sound_word'] for word in words[11:-1]]+[0]
    if any(word>>8!=5 or word&0x80 for word in mapped[:-1]):
        raise ValueError('Invalid native creature trigger group or index')
    return struct.pack('>34H',*mapped,*delays)


def install_scheduler(equipment,core,previous=None):
    """Bind complete resources and native timing in the ordinary sound stage."""
    audio=equipment['creature_audio']
    checked_scheduler(core,previous or audio)
    data=table_bytes(audio,core)
    for hook in scheduler_hooks():
        struct.pack_into('>I',core,hook['address']-CODE_RAM,hook['after'])
    audio.update(native_scheduler_installed=True,callback_installed=True,
        scheduler_hooks=list(scheduler_hooks()),table=dict(ram=TABLE,delay_ram=DELAY,
            count=COUNT,bytes=len(data),hex=data.hex(),sha256=sha256(data)),
        helper=dict(address=0x800D24EC,bytes=64,sha256=NATIVE_HELPER_SHA),
        table_published=bool(previous and previous.get('table_published')),
        additional_resident_bytes=0,saved_format_changed=False,
        timing='native room-audio phase and per-instance randomized countdown')
    callbacks={r['source_item_id']:r for r in audio['source']['rows']}
    for rig in equipment['room_rigs']['rows']:
        if rig.get('mode')!=13:continue
        callback=callbacks.get(rig['source_item_id'])
        if callback:
            if callback['runtime_index']!=rig['runtime_index']:
                raise ValueError('Creature sound changes its native display identity')
            rig['last']=callback['source_sound_id']
            rig['pending_dependencies']=[p for p in rig['pending_dependencies']
                if p!='complete room-creature sound engine and programs']


def checked_binding(source,image,report):
    """Check scheduler, resident arrays, rig fields, and complete sound resources."""
    from v3_asset_loader import BLOB
    from v3_equipment_runtime import RAM
    from v3_sound_programs import installed_resource
    files=by_vrom(image);core=files[CODE_VROM].extract(image)
    equipment=report['equipment_resources'];audio=equipment.get('creature_audio',{})
    if not audio.get('native_scheduler_installed'):return False
    contract=dependencies(source,image,report,[r['source_item_id'] for r in audio['source']['rows']])
    if (contract!=audio['source'] or not audio.get('callback_installed') or not audio.get('table_published') or
            audio.get('helper')!=dict(address=0x800D24EC,bytes=64,sha256=NATIVE_HELPER_SHA)):
        raise ValueError('Changed complete installed creature sound source')
    data=table_bytes(audio,core);blob=files[BLOB].extract(image)
    at=equipment['blob_offset']+TABLE-RAM
    expected=dict(ram=TABLE,delay_ram=DELAY,count=COUNT,bytes=len(data),hex=data.hex(),sha256=sha256(data))
    table=audio['table']
    # The installed receipt also retains the compiler's digest. It is not an
    # additional array field; authenticate it without rejecting the current
    # unchanged native table because that provenance key is present.
    if ({k:v for k,v in table.items() if k!='compiled_sha256'}!=expected or
            table.get('compiled_sha256',expected['sha256'])!=expected['sha256'] or
            blob[at:at+len(data)]!=data):
        raise ValueError('Changed startup-loaded creature sound arrays')
    sequence,_,_=installed_resource(image,core,'seq',199)
    table=struct.unpack_from('>H',sequence,0x192)[0]
    for program in audio['programs']:
        at,n=program['offset'],program['bytes'];index=program['native_sound_word']&255
        if (struct.unpack_from('>H',sequence,table+index*2)[0]!=at or
                sha256(sequence[at:at+n])!=program['sha256']):
            raise ValueError('Changed complete creature trigger program/dispatch')
    callbacks={r['source_item_id']:r['source_sound_id'] for r in contract['rows']}
    for rig in equipment['room_rigs']['rows']:
        if rig.get('mode')==13 and rig['last']!=callbacks.get(rig['source_item_id'],0):
            raise ValueError('Changed complete creature callback membership')
    if '-DAF_V3_ROOM_CREATURE_SOUND' not in equipment['room_rigs']['code']['flags']:
        raise ValueError('Creature sound callback is not compiled')
    return True


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
    native=checked_scheduler(core,report['equipment_resources'].get('creature_audio'))
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
        native_scheduler=native,
        native_scheduler_installed=False,callback_installed=False)))
