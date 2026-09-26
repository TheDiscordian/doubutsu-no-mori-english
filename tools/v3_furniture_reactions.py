"""Source-checked timed material reactions and shared vibration dependencies.

Discovery is by complete callback implementation, never by an item-ID switch.
Preparing these dependencies does not enable an unfinished furniture profile.
"""
import copy
import json
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256

CATEGORY = 'timed-surprise-material'
COLOUR_CATEGORY = 'exclusive-player-colour-loop'
ENGINE_START, ENGINE_END = 0x935D4, 0x93DAC
WAVES_START, WAVES_END, WAVE_TABLE = 0x22F0, 0x2464, 0x23C4
ENGINE_SHA = '767cb482bcfbec50e2339f9cbf52072bad14ae55d4ef1742720a3640b9ca572e'
ENGINE_LINKS_SHA = 'f3c927ae4c8cf076edb08a27e5d58ce0acb4d6a7770b83eff0cfd47ce76d6aaa'
WAVES_SHA = '24460c16dad8a08437fd8dff3943f2df5414a08bc75d3810be484e2be344b707'
WAVES_LINKS_SHA = 'ef15ef25ad21453937a141cfdc5f1d8a2822ad3f621045450474bcc21110bf0b'


def checked_region(source, section, start, end, digest, links_digest):
    origin, size = source.sections[section]
    if not 0 <= start < end <= size:
        raise ValueError('Vibration dependency exceeds source section')
    data = source.rel[origin+start:origin+end]
    links = sorted((offset-start, *value) for (sec, offset), value in source.section_relocations.items()
                   if sec == section and start <= offset < end)
    if (sha256(data) != digest or
            sha256(json.dumps(links, separators=(',', ':')).encode()) != links_digest):
        raise ValueError('Changed complete vibration dependency or relocation')
    return data, dict(section=section, offset=start, bytes=end-start, sha256=digest,
                      relocations_sha256=links_digest, relocations=links)


def vibration_bank(source):
    """Retain all sixteen source waveforms in one bounded, pointer-free bank."""
    _, engine = checked_region(source, 1, ENGINE_START, ENGINE_END, ENGINE_SHA, ENGINE_LINKS_SHA)
    _, waves = checked_region(source, 4, WAVES_START, WAVES_END, WAVES_SHA, WAVES_LINKS_SHA)
    origin = source.sections[4][0]
    result = bytearray(80)
    rows = []
    for index in range(16):
        at = WAVE_TABLE+index*8
        ref = source.section_relocations.get((4, at))
        pointer, count = struct.unpack_from('>II', source.rel, origin+at)
        if (pointer or ref is None or ref[:3] != (1, 1, 4) or not 1 <= count <= 60 or
                not WAVES_START <= ref[3] <= WAVE_TABLE-count):
            raise ValueError('Invalid complete vibration waveform')
        raw = source.rel[origin+ref[3]:origin+ref[3]+count]
        if max(raw) > 2:
            raise ValueError('Unknown donor motor command')
        offset = len(result)
        struct.pack_into('>HH', result, 16+index*4, offset, count)
        result.extend(raw)
        rows.append(dict(index=index, source_offset=ref[3], bytes=count,
                         offset=offset, sha256=sha256(raw)))
    result.extend(bytes(-len(result) % 16))
    struct.pack_into('>4I', result, 0, 0x41465642, len(result), 16, 0)
    return bytes(result), dict(engine=engine, waves=waves, rows=rows,
        bytes=len(result), sha256=sha256(result), elements=4, source_rate=60,
        native_stop_adaptation='Both donor stop commands turn the N64 motor off; no active brake exists')


def source_lifecycle(source, profile):
    from v3_furniture_materials import CATEGORY as MATERIAL
    adapter = profile.get('callback_adapter', {})
    functions = copy.deepcopy(adapter.get('functions', {}))
    if (adapter.get('category') != MATERIAL or
            functions.get('move', {}).get('sha256') !=
            '3e0528a4be5829817b4185fe21e6dfb78aa6b86e358016a5f3ecbdeb217e95fa'):
        return None
    if set(functions) != {'create', 'move', 'draw', 'destroy'}:
        raise ValueError('Changed complete timed-reaction lifecycle')
    for role in ('create', 'move', 'destroy'):
        _, actual = source.function(functions[role]['offset'])
        if actual != functions[role]:
            raise ValueError('Changed complete timed-reaction callback')
    create = functions['create']
    if (create['bytes'] != 16 or create['relocations'] or create['sha256'] !=
            '8fc016fb272f7517c5bf348f35a166da6572febe67ecfafbddceb9bfd9171608'):
        raise ValueError('Changed complete timed-reaction initializer')
    destroy = functions['destroy']
    if (destroy['bytes'] != 4 or destroy['relocations'] or destroy['sha256'] !=
            'f332ea5b5437103cbb6f1508679da89eec9288ad775c96c439a17fccabe3de8e'):
        raise ValueError('Changed complete timed-reaction destructor')
    frames = adapter.get('material_frames', [])
    if (len(frames) != 1 or frames[0]['selector'] !=
            dict(input='actor-s16', offset=0x82C, mask=1)):
        raise ValueError('Changed timed-reaction face selector')
    move = functions['move']
    pointer = move['relocations'].get(0x76)
    if pointer is None or pointer[:3] != (6, 1, 4):
        raise ValueError('Missing source reaction distance binding')
    offset = pointer[3]
    start, size = source.sections[4]
    if not 0 <= offset <= size-4 or source.rel[start+offset:start+offset+4] != bytes(4):
        raise ValueError('Changed source reaction distance')
    helpers = source.checked_callback_code(move, 208,
        'b810f7b58027f39bb83e1362fcdb2b396ed6583b8d089f499b5afeb9138e0c32',
        {0x76: pointer, 0x7E: (4, 1, 4, offset)},
        {0x20: (431232, 'get_player_actor_withoutCheck'),
         0x44: (0x106DF4, 'aMR_SetSurprise'), 0x9C: (0x93D64, 'mVibctl_entry')},
        'timed surprise material', internal_branches=True)
    for name, size, digest, relocations in (
        ('get_player_actor_withoutCheck', 8,
         'a72973a01db91918d562958b8f1ef1811826bba3d0145685efc84135f7894da6', {}),
        ('aMR_SetSurprise', 24,
         'b337b440b007377a140b3dcb670a78f3609311cbe34b08947418f1be8c819ea0', {}),
        ('mVibctl_entry', 72,
         'd321511345f2143aede2810200c743daaf43a6f6a25ca33ae645586fec4a49b6',
         {38: (6, 1, 6, 624856), 50: (4, 1, 6, 624856)})):
        row = helpers[name]
        if row['bytes'] != size or row['sha256'] != digest or row['relocations'] != relocations:
            raise ValueError('Changed complete timed-reaction helper: '+name)
    for offset, name, size, digest, relocations in (
        (0x1070B8, 'aMR_RequestPlayerBikkuri', 124,
         '397394c0b4d4bd7a1f8fb3ed006a80e219ced0c5840fc34fad77af7a52e291f0',
         {34:(6,1,6,625144),38:(4,1,6,625144),58:(6,1,6,625144),
          62:(6,1,4,14460),66:(4,1,6,625144),74:(4,1,4,14460)}),
        (0x6AA3C, 'mPlib_request_main_shock_type1', 108,
         'd84cdc510b03530fccbbe49345c4aff27a51aa335f099dee229dbb1de6dc3600',
         {20:(10,0,4,0x8009AED4),88:(10,0,4,0x8009AF20)})):
        _, row = source.function(offset)
        if (row['symbol'] != name or row['bytes'] != size or row['sha256'] != digest or
                row['relocations'] != relocations):
            raise ValueError('Changed complete player surprise consumer: '+name)
        helpers[name] = row
    start = source.sections[4][0]
    if source.rel[start+14460:start+14464] != struct.pack('>f', 20.0):
        raise ValueError('Changed source player surprise duration')
    # Exact source code above binds these operands; they are not inferred from
    # the item's name, source actor size, or an unrelated native reaction.
    return dict(category=CATEGORY, functions=functions, helpers=helpers,
        source_countdown=0x82A, source_face=0x82C,
        native_countdown=0x1A6, native_face=0x1A4,
        initial_frames=50, vibration_at=20, source_steps_per_native_update=2,
        vibration=dict(percent=100, waves=[1, 1, 13], frames=[0, 7, 7], distance=0.0),
        surprise=dict(source_duration=20.0, native_duration=10.0,
                      angle_offset=0xDE, native_player_offset=0x1C90,
                      native_state_offset=0xCF0, native_shock_state=0x61),
        callback_installed=False)


def colour_lifecycle(source, profile):
    """Bind the full exclusive-switch loop and its actual player-colour consumers.

    This is a source descriptor, not evidence of native player-draw integration.
    The sound batch can be prepared while the complete lifecycle is connected.
    """
    from v3_furniture_materials import CATEGORY as MATERIAL
    adapter = profile.get('callback_adapter', {})
    functions = copy.deepcopy(adapter.get('functions', {}))
    if (adapter.get('category') != MATERIAL or functions.get('move', {}).get('sha256') !=
            'a7190b59a2ea0fc81a0de835efc1d7f988c999906bc4fa2094893a2c17285493'):
        return None
    if set(functions) != {'create', 'move', 'draw'} or adapter.get('pending_profile_fields'):
        raise ValueError('Changed complete exclusive-colour lifecycle')
    for role in ('create', 'move'):
        if source.function(functions[role]['offset'])[1] != functions[role]:
            raise ValueError('Changed complete exclusive-colour callback')
    create = functions['create']
    if (create['bytes'] != 12 or create['relocations'] or create['sha256'] !=
            'aa0ae11bb7776e75009f3036e23193be2e2ca28470dcb9ebbd1eea377039ef4f'):
        raise ValueError('Changed exclusive-colour switch initializer')
    frames = adapter.get('material_frames', [])
    if (len(frames) != 1 or frames[0]['selector'] != dict(input='room-or-preview-frame',
            division=10, modulo=4, signed=True, stopped_in_room_when_switch_off=True)):
        raise ValueError('Changed complete switched palette selector')
    move = functions['move']
    helpers = source.checked_callback_code(move, 144,
        'b8bdeacdd0939d0c6adfc54e517bfce4928922ac363033572f6fb42e5e9204fb', {},
        {0x4C: (0x2BDD84, 'sAdo_OngenPos'), 0x50: (0x6E5C4, 'mPlib_Set_change_color_request'),
         0x70: (0x103E0C, 'aMR_SameFurnitureSwitchOFF')}, 'exclusive player colour loop')
    loop = helpers['sAdo_OngenPos']
    if (loop['bytes'] != 100 or loop['sha256'] !=
            'b982dbca7ed68e0565b554e142e64d69a1d2c47ec061169d114502a25e61f885' or
            loop['relocations'] != {72:(10,0,4,0x80012E2C),10:(6,1,6,2306744),34:(4,1,6,2306744)}):
        raise ValueError('Changed complete exclusive-colour loop helper')
    consumers = {}
    for name, at, size, digest, links in (
        ('request', 0x6E5C4, 52,
         '4579949df53398a31f9b2fc5c7d8e198a3b46a14814df4afa781bfa0b389993a',
         '7bae22be2ad13329fee72435fd33fd188b3c2c92b92d72b9de962d4a1a6efdc3'),
        ('exclusive_switch', 0x103E0C, 96,
         '5b4e4d21f6bd4bb2eeed0dff465ab8e6189a0035cdd84001ec7eedb5c4db513f',
         'b4929e14576c094b0f571fdc94f5fa60766ce3786e8adb4670801919acea6d80'),
        ('update', 0x16E8B8, 140,
         'e928928d88b0a2e8186ac8653344a48ec4fa3365cbb4ddce4e5ad8b840d2710d',
         '9898445a3b0562db17a16578af987880f4c43fba5aa7124367ebdce4d5db174c'),
        ('draw', 0x1741C4, 1444,
         '1d67fff479c10b2c3224bf90945128dd1855e7a14e2df32dc751864671b6ce14',
         'fa3626f406a55b6ed514a1cc5b8bd50ddbde52ee8aae6c60fa7c126148b266fb'),
        ('fog', 0x74EA0, 88,
         '0ccecb8d1814b6e783bda8e869012327f06532f06b6067de4d7c17e6f389efdf',
         '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945')):
        _, consumers[name] = checked_region(source, 1, at, at+size, digest, links)
    constants = {}
    for name, offset, expected in (
        ('step',0x53F0,'3f800000'), ('zero',0x53F4,'00000000'), ('period',0x6B68,'429f5c29'),
        ('colour_frames',0x71C4,'411f5c29'), ('near',0x71C8,'43520000'),
        ('far',0x71CC,'44430000'), ('distance_bias',0x71D0,'43b00000'),
        ('distance_scale',0x71D4,'3d913f8c'), ('distance_fraction',0x71D8,'3e800000')):
        raw = source.rel[source.sections[4][0]+offset:source.sections[4][0]+offset+4]
        if raw.hex() != expected:
            raise ValueError('Changed source player-colour constant: '+name)
        constants[name] = dict(offset=offset, hex=expected, value=struct.unpack('>f',raw)[0])
    origin = source.sections[4][0]+0x7194
    raw = source.rel[origin:origin+48]
    if sha256(raw) != '6426871f1f5ddb91ca087bea8c46ba2d6831ccbdb446e6999c644f1e60b88dde':
        raise ValueError('Changed complete player-colour table')
    words = struct.unpack('>12I',raw)
    # The compiled draw indexes three rows at stride 3, including column 3.
    # Preserve the actual binary accesses through one bounded flat table;
    # copying the decompiler's [4][3] C indexing would invoke undefined behaviour.
    colours = [[words[channel*3+frame] for channel in range(3)] for frame in range(4)]
    return dict(category=COLOUR_CATEGORY, functions=functions, helpers=helpers,
        consumers=consumers, constants=constants,
        colours=dict(offset=0x7194, bytes=48, sha256=sha256(raw), rgb=colours),
        source_sound_id=95, exclusive_source_index=1223, source_steps_per_native_update=2,
        excluded_states=[12,13,14,15], state_offset=0x3C, position_offset=8,
        source_switch_offset=0x12C, source_changed_offset=0x12D, start_disabled=True,
        switch_clicks=[], callback_installed=False)


NATIVE_BLOCKS = (
    ('memset', 0x1060, 0x80025C60, 0x8003B9B0, 48,
     '9842231309587a8f054ce82e257f9dc0fd864608cf90266f53aff570e37e1adf'),
    ('memcpy', 0x1060, 0x80025C60, 0x80034BF8, 44,
     '770c81b6c68fa85d2b98688a09dd33a41366dd56288fda754c24eb3247e8763d'),
    ('interrupt_mask', 0x1060, 0x80025C60, 0x8002E0E0, 160,
     'cab6cee48ddb221c7a511c8b7398b0b36f98f6bddc521738e244327214b0c84b'),
    ('motor_init', 0x1060, 0x80025C60, 0x80031574, 348,
     '244e53fc157bd21dd45d388ec26d48866e233663f42f609de34c7b444904d75b'),
    ('motor_access', 0x1060, 0x80025C60, 0x80031300, 360,
     'c9aa53208a27554b414304c07fef83a60ef837732ae19356475be20fc5bb47f2'),
    ('controller_retrace', CODE_VROM, CODE_RAM, 0x800D7050, 304,
     '4208163e7b607bcd4279d64fcccb21be965715f4cb62957e4164c94ea0a93630'),
    ('controller_pre_nmi', CODE_VROM, CODE_RAM, 0x800D7180, 24,
     '64feaace6cae10d08bebd4f872e09488642dc6095865eda343501c4486c8869c'),
    ('controller_connection', CODE_VROM, CODE_RAM, 0x800D6ED0, 384,
     '8f8be6e11c560acbb1cca95500f76ccad92cb1ecb493109efaae8704aa16b31a'),
    ('pak_connection', CODE_VROM, CODE_RAM, 0x800D6B8C, 252,
     '5e8a86e05ffaab7bad48472163d363ca925cda883fdf5d8f05744fa9d83f51d4'),
    ('player_pointer', CODE_VROM, CODE_RAM, 0x800B1C84, 12,
     'f680a77d022740add2a8ead09c6438223d596b51cd655775b7a7ec0c80725404'),
    ('player_state', CODE_VROM, CODE_RAM, 0x800B1CBC, 36,
     'df027c0746ec5e111ed95aa4d07a77330cbfa923fc799617dbd4e483b7d6e350'),
    ('player_shock', CODE_VROM, CODE_RAM, 0x800B2B08, 88,
     'd03815c6b99d5f5b79863e25db356688f4c30dff5963fd472a331ba9050d4fd7'),
)


def native_contract(base, bridge=None):
    files = by_vrom(base)
    core = restored_core(files[CODE_VROM].extract(base), bridge)
    result = []
    for name, vrom, ram, address, size, digest in NATIVE_BLOCKS:
        owner = core if vrom == CODE_VROM else files[vrom].extract(base)
        raw = owner[address-ram:address-ram+size]
        if sha256(raw) != digest:
            raise ValueError('Changed native reaction dependency: '+name)
        result.append(dict(name=name, vrom=vrom, ram=ram, address=address, bytes=size, sha256=digest))
    return dict(blocks=result, serial_hook=0x800D7150, original_call=0x800D6B8C,
                serial_queue_owned=True, read_and_query_completed=True,
                controller=0, independent_pfs_bytes=104, callback_installed=False)


BRIDGE_WINDOWS = (
    (0x800B11B8, 0x800B11F8, 'af_v3_player_animation_size',
     '73ddefbd6504009b91117ed4eb6a843bd3ee8bdb2f503de0f491f2f69c82d3d4'),
    (0x800B1324, 0x800B1364, 'af_v3_equipment_size',
     '52b110e8d99029d10e3723f691f798fd29944ffb9a52c12cd88ab9d534fe3f30'),
)


def bridge_reservation(base, report, bridge=None):
    """Only fully replaced readers qualify; native part-copy still has a fallback."""
    from v3_asset_loader import BLOB
    from v3_npc_clothing import guard_incoming
    files = by_vrom(base)
    core = restored_core(files[CODE_VROM].extract(base), bridge)
    equipment = report['equipment_resources']
    blob = files[BLOB].extract(base)
    module = blob[equipment['blob_offset']:equipment['blob_offset']+equipment['bytes']]
    if sha256(module) != equipment['sha256']:
        raise ValueError('Changed complete resource readers before bridge reservation')
    windows = []
    for start, end, name, digest in BRIDGE_WINDOWS:
        target = equipment['code']['symbols'][name]
        entry = struct.pack('>II', 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
        if (core[start-CODE_RAM-8:start-CODE_RAM] != entry or
                sha256(core[start-CODE_RAM:end-CODE_RAM]) != digest):
            raise ValueError('Native reader is not completely redirected: '+name)
        # Reject direct/pointer fallback references from the retained equipment
        # module as well as branches and pointers in main code. In particular,
        # this does not reclaim 800B1DF0, the active native part-copy fallback.
        for at in range(0, len(module)-3, 4):
            word = int.from_bytes(module[at:at+4], 'big')
            direct = 0x80000000 | ((word & 0x3FFFFFF) << 2)
            if start <= word < end or word >> 26 in (2, 3) and start <= direct < end:
                raise ValueError('Retained runtime enters proposed rumble bridge storage')
        windows.append(dict(address=start, bytes=end-start, sha256=digest,
                            replaced_reader=name, replacement_entry=target))
    # The generic guard allows entry at the beginning of its window. Include
    # the checked original jump's NOP delay slot so even the first reclaimed
    # instruction is forbidden as an incoming target.
    guard_incoming(core, len(core), CODE_RAM, [(a-CODE_RAM-4, b-a+4) for a, b, _, _ in BRIDGE_WINDOWS])
    for window in windows:
        a = window['address']-CODE_RAM
        window['before'] = core[a:a+window['bytes']].hex()
    return dict(windows=windows, original_entries_preserved=True,
                native_part_copy_fallback_preserved=True, installed=False)


STATE_RAM, STATE_BYTES, SERIAL_HOOK = 0x804CD000, 1024, 0x800D7150
ORIGINAL_SERIAL_CALL = struct.pack('>I', 0x0C000000 | (0x800D6B8C >> 2 & 0x3FFFFFF))


def restored_core(core, bridge):
    """Verify installed writes before restoring only those bytes for contracts."""
    if not bridge or not bridge.get('installed'):
        return core
    core = bytearray(core)
    expected = {a: (b-a, digest) for a, b, _, digest in BRIDGE_WINDOWS}
    expected[SERIAL_HOOK] = (4, sha256(ORIGINAL_SERIAL_CALL))
    hooks = bridge.get('hooks', [])
    if len(hooks) != 3 or {r['address'] for r in hooks} != set(expected):
        raise ValueError('Incomplete installed controller bridge')
    for row in hooks:
        a = row['address']-CODE_RAM
        before, after = bytes.fromhex(row['before']), bytes.fromhex(row['after'])
        n, digest = expected[row['address']]
        if (len(before) != n or len(after) != n or sha256(before) != digest or
                core[a:a+n] != after):
            raise ValueError('Changed complete controller bridge write')
        core[a:a+n] = before
    return bytes(core)


def profile_lifecycle(profile, lifecycle):
    """Structural profile guard; installation independently checks actual source."""
    if not isinstance(lifecycle, dict) or lifecycle.get('category') != CATEGORY:
        return False
    functions = profile.get('callback_adapter', {}).get('functions', {})
    if set(functions) != {'create', 'move', 'draw', 'destroy'}:
        return False
    for role in ('create', 'move', 'destroy'):
        expected = lifecycle.get('functions', {}).get(role, {})
        if any(json.loads(json.dumps(functions[role].get(k))) != json.loads(json.dumps(expected.get(k))) for k in
               ('symbol', 'offset', 'bytes', 'sha256', 'relocations')):
            return False
    return (lifecycle.get('native_face') == 0x1A4 and lifecycle.get('native_countdown') == 0x1A6 and
            lifecycle.get('initial_frames') == 50 and lifecycle.get('vibration_at') == 20 and
            lifecycle.get('source_steps_per_native_update') == 2 and
            lifecycle.get('vibration') == dict(percent=100, waves=[1,1,13], frames=[0,7,7], distance=0.0))


def checked_lifecycle(source, profile, binding):
    lifecycle = source_lifecycle(source, profile)
    if (lifecycle is None or binding.get('lifecycle') != 2 or binding.get('mode') != 2 or
            binding.get('state_offset') != 0x1A4 or not binding.get('lifecycle_installed') or
            binding.get('material_lifecycle') != json.loads(json.dumps(lifecycle))):
        raise ValueError('Incomplete installed timed material reaction')
    return json.loads(json.dumps(lifecycle))


def state_reservation(report):
    room = report['equipment_resources']['room_rigs']
    packet = room['packet']
    if (packet['ram'] != 0x804C8000 or packet['bytes'] != 20480 or
            room['table_ram'] != 0x804CC000 or packet['ram']+packet['bytes'] != STATE_RAM or
            STATE_RAM+STATE_BYTES > report['furniture']['bank_pool']['start']):
        raise ValueError('Reaction state overlaps room code or model storage')
    # Reject another explicitly owned runtime region, including future modules.
    def visit(value):
        if isinstance(value, dict):
            ram, size = value.get('ram'), value.get('bytes')
            if type(ram) is int and type(size) is int and ram < STATE_RAM+STATE_BYTES and STATE_RAM < ram+size:
                if value != dict(ram=STATE_RAM, bytes=STATE_BYTES, mutable=True, saved=False, installed=True):
                    raise ValueError('Reaction state overlaps another reported runtime owner')
            for key, child in value.items():
                if key != 'reactions': visit(child)
        elif isinstance(value, list):
            for child in value: visit(child)
    visit(report['equipment_resources'])
    return dict(ram=STATE_RAM, bytes=STATE_BYTES, mutable=True, saved=False, installed=True)


def prepare_installation(source, base, report):
    bank, receipt = vibration_bank(source)
    return dict(format='AFV3-ROOM-REACTIONS-1', bank=json.loads(json.dumps(receipt)),
        native=native_contract(base), bridge=bridge_reservation(base, report), state=state_reservation(report),
        additional_resident_bytes=STATE_BYTES, installed=False, native_execution_tested=False, hardware_tested=False)


def wave_source(source, output):
    from apply_translation import write_new
    from v3_asset_loader import ROOT
    output = output.resolve()
    if not output.is_relative_to(ROOT/'build'):
        raise ValueError('Reaction preparation requires ignored build storage')
    output.mkdir(parents=True, exist_ok=False)
    bank, receipt = vibration_bank(source)
    write_new(output/'waves.bin', bank)
    assembly = '.section .rodata.af_v3_rumble_waves,"a",@progbits\n.balign 16\n'+\
        '.globl af_v3_rumble_waves\naf_v3_rumble_waves:\n'+\
        '.incbin "/source/'+str(output.relative_to(ROOT)/'waves.bin')+'"\n'
    write_new(output/'waves.S', assembly.encode())
    return str(output.relative_to(ROOT)/'waves.S'), bank, receipt


def publish_bridge(core, reactions, packet, symbols, output):
    from v3_asset_loader import compile_part
    if core is None:
        raise ValueError('Reaction publication requires the current main-code owner')
    bridge = reactions['bridge']
    restored = restored_core(core, bridge)
    target = symbols['af_v3_room_rumble_retrace']
    crc = packet['crc32']
    if not packet['ram'] <= target < 0x804CC000 or target & 3 or not crc:
        raise ValueError('Controller callback escapes the published room packet')
    raw, compiled = compile_part('room_rumble_bridge', output/'room_rumble_bridge',
        primary_source='overlays/v3/room_rumble_bridge.S',
        defines=(f'AF_ROOM_CRC=0x{crc:X}', f'AF_ROOM_RUMBLE_RETRACE=0x{target:X}'))
    first = BRIDGE_WINDOWS[0][0]
    hooks = []
    for start, end, _, digest in BRIDGE_WINDOWS:
        at = start-CODE_RAM
        before = restored[at:at+end-start]
        if sha256(before) != digest:
            raise ValueError('Occupied native controller-bridge reservation')
        after = raw[start-first:end-first].ljust(end-start, b'\0')
        hooks.append(dict(address=start, before=before.hex(), after=after.hex()))
        core[at:at+len(after)] = after
    at = SERIAL_HOOK-CODE_RAM
    if restored[at:at+4] != ORIGINAL_SERIAL_CALL:
        raise ValueError('Changed serial-queue-safe controller call')
    after = struct.pack('>I', 0x0C000000 | (first >> 2 & 0x3FFFFFF))
    core[at:at+4] = after
    hooks.append(dict(address=SERIAL_HOOK, before=ORIGINAL_SERIAL_CALL.hex(), after=after.hex()))
    bridge.update(hooks=hooks, code=compiled, packet_crc32=crc, callback=target, installed=True)
    reactions.update(installed=True)


def checked_binding(source, base, report):
    from v3_asset_loader import BLOB
    room = report['equipment_resources']['room_rigs']
    reactions = room.get('reactions')
    if reactions is None:
        return None
    if reactions.get('format') != 'AFV3-ROOM-REACTIONS-1' or not reactions.get('installed'):
        raise ValueError('Incomplete installed reaction engine')
    bank, receipt = vibration_bank(source)
    bridge = reactions['bridge']
    native = native_contract(base, bridge)
    reservation = bridge_reservation(base, report, bridge)
    if (reactions['bank'] != json.loads(json.dumps(receipt)) or reactions['native'] != native or
            reactions['state'] != state_reservation(report) or
            any(bridge.get(k) != reservation[k] for k in ('windows', 'original_entries_preserved',
                                                        'native_part_copy_fallback_preserved')) or
            not bridge.get('installed') or bridge['packet_crc32'] != room['packet']['crc32'] or
            bridge['callback'] != room['code']['symbols']['af_v3_room_rumble_retrace']):
        raise ValueError('Changed complete reaction engine bindings')
    blob = by_vrom(base)[BLOB].extract(base)
    at = room['packet']['blob_offset']+room['code']['symbols']['af_v3_rumble_waves']-room['packet']['ram']
    if blob[at:at+len(bank)] != bank:
        raise ValueError('Changed complete installed vibration wave bank')
    if '-DAF_ROOM_REACTIONS' not in room['bootstrap']['flags']:
        raise ValueError('Missing reaction state reset on packet publication')
    return reactions


def compile_runtime(source, output):
    """Compile actual VR4300 reaction and motor code with the extracted bank."""
    from v3_asset_loader import ROOT, compile_part
    assembly, bank, receipt = wave_source(source, output)
    code, compiled = compile_part('room_reactions', output/'code',
        extra_sources=('overlays/v3/room_rumble.c', assembly))
    return code, compiled, receipt


SOURCES = ('tools/v3_furniture_reactions.py', 'tools/v3_furniture_pipeline.py',
    'tools/v3_asset_loader.py', 'overlays/v3/room_reactions.c', 'overlays/v3/room_reactions.h',
    'overlays/v3/room_reactions.ld', 'overlays/v3/room_rumble.c', 'overlays/v3/room_rumble.h',
    'overlays/v3/room_rumble_bridge.S', 'overlays/v3/room_rumble_bridge.ld',
    'overlays/v3/room_rigs_bootstrap.c', 'overlays/v3/room_rigs_bootstrap.ld')


def prepare_batch(source, image, inventory, output, selected=(), category=None, report=None):
    from apply_translation import write_new
    from v3_asset_loader import ROOT, compile_part
    import zlib
    if category != CATEGORY or report is None:
        raise ValueError('Timed reactions require an explicit category and checked build')
    rows = []
    for row in inventory['rows']:
        if row['installed'] or selected and row['item_id'] not in selected:
            continue
        lifecycle = source_lifecycle(source, row.get('profile', {}))
        if lifecycle:
            rows.append(dict(source_item_id=row['item_id'], name=row['name'], **lifecycle))
    if not rows or selected and set(selected) != {r['source_item_id'] for r in rows}:
        raise ValueError('Empty or unsupported complete reaction selection')
    native = native_contract(image)
    reservation = bridge_reservation(image, report)
    code, compiled, bank = compile_runtime(source, output)
    # The published shared packet will supply its own CRC and linked address.
    # This validates the complete bridge's split layout, not cartridge installation.
    crc = zlib.crc32(code)
    target = compiled['symbols']['af_v3_room_rumble_retrace']
    bridge, bridge_code = compile_part('room_rumble_bridge', output/'bridge',
        primary_source='overlays/v3/room_rumble_bridge.S',
        defines=(f'AF_ROOM_CRC=0x{crc:X}', f'AF_ROOM_RUMBLE_RETRACE=0x{target:X}'))
    first = BRIDGE_WINDOWS[0][0]
    reservation.update(code=bridge_code, standalone_crc32=crc, standalone_target=target,
                       rebind_to_shared_packet_required=True)
    for window in reservation['windows']:
        at = window['address']-first
        data = bridge[at:at+window['bytes']].ljust(window['bytes'], b'\0')
        window.update(compiled_hex=data.hex(), compiled_sha256=sha256(data))
    defines = [s[2:] for s in report['equipment_resources']['room_rigs']['bootstrap']['flags']
               if s.startswith('-D')]
    _, bootstrap = compile_part('room_rigs_bootstrap', output/'bootstrap-capacity',
                                defines=(*defines, 'AF_ROOM_REACTIONS'))
    if bootstrap['bytes'] > 1536:
        raise ValueError('Reaction state reset exceeds the existing bootstrap')
    result = dict(format='AFV3-FURNITURE-LIFECYCLES-PREPARED-1', category=CATEGORY,
        base_sha256=sha256(image), source_rel_sha256=sha256(source.rel),
        source_symbols_sha256=sha256(source.symbols.encode()), rows=rows, code=compiled,
        bank=bank, native=native, bridge=reservation, bootstrap_capacity_check=bootstrap,
        state=dict(ram=0x804CD000, bytes=1024, mutable=True, saved=False, installed=False),
        runtime_installed=False, native_execution_tested=False, complete_dependencies=0,
        pending=['shared packet publication and reset', 'controller hook installation',
                 'material lifecycle dispatch and ordinary category import'],
        sources={name:sha256((ROOT/name).read_bytes()) for name in SOURCES})
    write_new(output/'lifecycles.json', (json.dumps(result, indent=2)+'\n').encode())
    return result
