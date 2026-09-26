"""Complete direct-model interaction categories, independent of item identity."""
import copy
import json
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32

CATEGORY = 'static-interaction'
MAGIC = 0x41464931
SOURCES = ('tools/v3_furniture_static.py', 'overlays/v3/room_static.c',
           'overlays/v3/room_static.h')


def discover(source, receipt):
    """Recognise complete wallet and town-melody callback implementations."""
    raw, actual = source.function(receipt['offset'])
    if receipt != actual:
        raise ValueError('Changed complete static interaction callback')
    module = u32(source.rel, 0)
    effect_forms={
        (240,'0c0117d9e794873683e9d49315f75a8d9545650b74c92c529aaa4e112a3e8ebb'):(3,'steam'),
        (336,'e8f6300c4ea1572cef467be6954a08c7d0c240471e0711f2a09343ba453a5181'):(4,'projectile'),
    }
    effect=effect_forms.get((len(raw),sha256(raw)))
    if effect:
        from v3_room_particles import source_contract
        mode,kind=effect;contract=source_contract(source)
        result=dict(category=CATEGORY,mode=mode,parameter=9 if mode==3 else 0,
            effects=[kind],effect_source=contract,excluded_states=[13,14,15,12],runtime_installed=False)
        if mode==3:
            result['level_sound']=dict(category='periodic-effect-loop',source_sound_id=0x55,
                switch_clicks=[],excluded_states=[13,14,15,12],source_period=16,native_period=8,
                height=30.0,spread=9,source_effect=113,callback=actual)
        else:
            result.update(trigger=dict(sound_word=contract['projectile_source_sound']),
                switch_test='equals-one',contact_directions=[0,2],angle_offset=0x124)
        return result
    # Unknown callbacks must remain eligible for artwork preparation. Only
    # recognised complete instruction shapes enter an implemented category.
    normalized=bytearray(raw)
    if len(raw)==104:
        for at in (0x1E,0x22,0x3E):normalized[at:at+2]=bytes(2)
        struct.pack_into('>I',normalized,0x40,u32(raw,0x40)&0xFC000003)
        if sha256(normalized)!='3fe73234191a5ef87631d9447b6046a416bb0ad58891190e2de2f1b36f5408b9':return None
    if len(raw)==68:
        for at in (0x0A,0x0E,0x2A):normalized[at:at+2]=bytes(2)
        if sha256(normalized)!='9010131508b15e0d650e1be7a24b4c7a8407b5ebfc3a8e254aca2ed4feb67c74':return None
    if len(raw) == 104:
        sound = struct.unpack_from('>H', raw, 0x3E)[0]
        helpers = source.checked_callback_code(receipt, 104,
            '3fe73234191a5ef87631d9447b6046a416bb0ad58891190e2de2f1b36f5408b9',
            {0x1E: (6,module,6,48192), 0x22: (4,module,6,48192)},
            {0x40: (0x2BDDE8,'sAdo_OngenTrgStart')}, 'wallet interaction', {0x3E:sound})
        helper = helpers['sAdo_OngenTrgStart']
        if (helper['sha256'] != '4fdc889bb1697c19c8f386d72b80585ea07706d9f26b328389766bec96f0f989' or
                helper['relocations'] != {48:(10,0,4,0x8001383C)}):
            raise ValueError('Changed complete positioned wallet sound helper')
        return dict(category=CATEGORY, mode=1, parameter=1, helpers=helpers,
            trigger=dict(sound_word=sound), source_wallet_offset=0x8C,
            native_wallet_offset=0x38, switch_test='nonzero', excluded_states=[],
            runtime_installed=False)
    if len(raw) == 68:
        instrument = struct.unpack_from('>H', raw, 0x2A)[0]
        if instrument >= 16:
            raise ValueError('Town-melody selector exceeds complete source table')
        source.checked_callback_code(receipt, 68,
            '9010131508b15e0d650e1be7a24b4c7a8407b5ebfc3a8e254aca2ed4feb67c74',
            {0x0A:(6,module,6,48192), 0x0E:(4,module,6,48192)}, {},
            'town-melody interaction', {0x2A:instrument})
        helpers = {}
        for at, name, digest in (
            (0x1075D0,'aMR_SoundMelody','5ca68df8368ce50fa525b9152ef81372ddf14e943b7123324f8035fafb252c88'),
            (0x76638,'mRmTp_GetMelodyData','4e0d0c82b70486ea1cf76f73112b19abe42018409528dd83dece64dee0b5a18e'),
            (0x2BDF58,'sAdo_FurnitureInst','95915c9fa3cef31d5a06d031b4f1e3c7719b2e3184bf81107172d3ecaf9b8fea'),
            (0x2BE590,'sAdo_FurnitureInstPos','10dd6bcb370cf240643649dea818045a2fbe2f38e64c43af30600d772e8258d4')):
            _, helper = source.function(at)
            if helper['symbol'] != name or helper['sha256'] != digest:
                raise ValueError('Changed complete town-melody helper: '+name)
            helpers[name] = helper
        return dict(category=CATEGORY, mode=2, parameter=instrument, helpers=helpers,
            room_clip_offset=0x64, switch_test='nonzero', excluded_states=[],
            position_updated_without_press=True, runtime_installed=False)
    return None


def native_contract(image):
    files = by_vrom(image)
    core = files[CODE_VROM].extract(image)
    room = files[0x82D7F0].extract(image)
    rows = []
    for name, raw, ram, first, end, digest in (
        ('private_wallet_initialization',core,CODE_RAM,0x800C37BC,0x800C3970,
         'e361f7c11c84b077b270384908ab83616f75dc58873759edf11a15e257e708ab'),
        ('room_clip_registration',room,0x80936710,0x80939050,0x8093919C,
         '829a1b5c83b3284fe2e0174932f22be1ad56e184b4540017259fe6b229ed381a'),
        ('room_melody_dispatch',room,0x80936710,0x8093B418,0x8093B498,
         '71d6f4a977c46a2d084a7a0115bb80c73ec76d77c565457ab8792f90a94a973b'),
        ('town_melody_data',core,CODE_RAM,0x800BF26C,0x800BF27C,
         'bb985e4e5bffb7b13b188e117ace6fc6a4b17f303405b611f69a7f72b628e7ae'),
        ('furniture_instrument',core,CODE_RAM,0x800D1E98,0x800D1EE8,
         'ed23e1d3bbf7cb602b3a16e2b227ed10ab08c830518715563847f291b1dee935'),
        ('furniture_position',core,CODE_RAM,0x800D252C,0x800D2568,
         'e15f7eb189321983c825d796480fd1b46a62bdc1fe93f62ac4411158344d4ef1'),
        ('native_two_track_melody',core,CODE_RAM,0x800FD170,0x800FD280,
         'f99e0184c1fa16d3d22ef37011a0ac69df80188745b3ee68b3708960de6991a8')):
        if sha256(raw[first-ram:end-ram]) != digest:
            raise ValueError('Changed native static-interaction dependency: '+name)
        rows.append(dict(name=name,address=first,bytes=end-first,sha256=digest))
    return dict(blocks=rows,private_pointer=0x80136FD8,wallet_offset=0x38,
        room_clip_pointer=0x80136F2C,melody_callback_offset=0x64)


def encode(rows):
    indices = [r['runtime_index'] for r in rows]
    if not rows or len(rows)>128 or indices != sorted(set(indices)):
        raise ValueError('Invalid shared static-interaction membership')
    data = bytearray(struct.pack('>4I', MAGIC, len(rows), 8, 0))
    for row in rows:
        mode, parameter = row['mode'], row['parameter']
        word = row.get('native_sound_word',0)
        if (not 1024 <= row['runtime_index'] < 2048 or
                mode not in (1,2,3,4) or mode==1 and parameter!=1 or
                mode==2 and (not 0<=parameter<16 or word) or not 0<=word<=65535):
            raise ValueError('Unknown complete static-interaction record')
        if mode==3 and (parameter!=9 or word!=0x55) or mode==4 and parameter:
            raise ValueError('Changed complete static effect-emitter parameters')
        data.extend(struct.pack('>HBBHH',row['runtime_index'],mode,parameter,word,0))
    return bytes(data)


def table_source(rows, output):
    from apply_translation import write_new
    from v3_asset_loader import ROOT
    output = output.resolve()
    if not output.is_relative_to(ROOT/'build'):
        raise ValueError('Static records require ignored build storage')
    output.mkdir(parents=True,exist_ok=False)
    data = encode(rows)
    write_new(output/'records.bin',data)
    assembly = '.section .rodata.af_v3_room_static,"a",@progbits\n.balign 16\n'+\
        '.globl af_v3_room_static_table\naf_v3_room_static_table:\n'+\
        '.incbin "/source/'+str(output.relative_to(ROOT)/'records.bin')+'"\n'
    write_new(output/'records.S',assembly.encode())
    return str(output.relative_to(ROOT)/'records.S'),data


def checked_audio(profile, row, equipment):
    adapter = profile['callback_adapter']
    if adapter['category'] != CATEGORY or any(row.get(k)!=adapter[k] for k in ('mode','parameter')):
        raise ValueError('Changed complete static behaviour binding')
    if adapter['mode'] in (1,4):
        audio = equipment.get('furniture_audio',{})
        source_word = adapter['trigger']['sound_word']
        program = next((p for p in audio.get('programs',[]) if p['source_sound_word']==source_word),None)
        member = next((p for p in audio.get('furniture',[]) if p['item_id']==row['source_item_id']),None)
        if (program is None or member is None or row.get('source_sound_word')!=source_word or
                row.get('native_sound_word')!=program['native_sound_word'] or
                member['callback']!=json.loads(json.dumps(adapter))):
            raise ValueError('Wallet behaviour lacks its complete installed sound')
    elif adapter['mode']==2:
        audio = equipment.get('furniture_melody_audio',{})
        if adapter['parameter'] not in audio.get('installed_instruments',[]):
            raise ValueError('Town melody lacks its complete installed instrument')
    elif adapter['mode']==3:
        audio=equipment.get('furniture_level_audio',{})
        member=next((r for r in audio.get('furniture',[]) if r['item_id']==row['source_item_id']),None)
        if (member is None or member['lifecycle']!=json.loads(json.dumps(adapter['level_sound'])) or
                row.get('native_sound_word')!=adapter['level_sound']['source_sound_id']):
            raise ValueError('Periodic emitter lacks its complete loop audio')
    if adapter['mode'] in (3,4):
        particles=equipment['room_rigs'].get('effects',{}).get('particles')
        if (not particles or not particles['installed'] or
                particles['source']!=json.loads(json.dumps(adapter['effect_source'])) or
                adapter['mode']==4 and particles['sound_word']!=row['native_sound_word']):
            raise ValueError('Static emitter lacks complete installed particles')
    return copy.deepcopy(adapter)


def checked_binding(image, report, blob):
    runtime = report['equipment_resources']['room_rigs']
    rows = runtime.get('static_rows',[])
    if not rows:return {}
    binding = runtime.get('static',{})
    data = encode(rows)
    packet = runtime['packet']; offset = binding.get('address',0)-packet['ram']
    if (binding.get('native')!=native_contract(image) or offset<0 or
            offset+len(data)>runtime['table_ram']-packet['ram'] or
            blob[packet['blob_offset']+offset:packet['blob_offset']+offset+len(data)]!=data or
            binding.get('sha256')!=sha256(data)):
        raise ValueError('Changed complete static-interaction table or native bindings')
    return {r['source_item_id']:r for r in rows}
