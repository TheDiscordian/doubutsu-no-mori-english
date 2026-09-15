"""Observe real conversation sample caches without invoking or replacing audio."""
import json
import math
from pathlib import Path
import struct

from aflib import by_vrom, sha256, u32
from v3_asset_loader import BLOB


def place_player(debug, target, record):
    """Explicit test positioning in one loaded acre; never alter an NPC or audio."""
    from emulator_smoke import message_snapshot, npc_actors_snapshot, player_snapshot
    if target != 'E0DA':
        raise ValueError('This bounded speech fixture only positions beside Maelle')
    record(debug.pause_game_thread())
    if message_snapshot(debug).get('loaded'):
        raise ValueError('Do not reposition a player during dialogue')
    player = player_snapshot(debug)
    matches = [row for row in npc_actors_snapshot(debug)['live_npc_actors']
               if row.get('animal_id') == target]
    if len(matches) != 1:
        raise ValueError('Expected exactly one live Maelle actor')
    npc = matches[0]
    source, destination = player['world_position'], dict(npc['world_position'])
    destination['z'] += 30
    if (abs(source['y']-destination['y']) > 2 or
            any(math.floor(source[axis]/640) != math.floor(destination[axis]/640)
                for axis in ('x', 'z'))):
        raise ValueError('Test positioning must remain on the same loaded acre and level')
    address = int(player['player_pointer'], 16)
    # Pinned m_actor.h: world.pos 28, prevPos 3C, world.rot.y 36, shape.rot.y DE.
    position = struct.pack('>3f', *(destination[axis] for axis in ('x', 'y', 'z')))
    writes = [(address+0x28, position), (address+0x3C, position),
              (address+0x36, bytes.fromhex('8000')), (address+0xDE, bytes.fromhex('8000'))]
    for at, value in writes:
        debug.write_memory(at, value)
        if debug.read_memory(at, len(value)) != value:
            raise ValueError('Test player-position write did not persist')
    record({'test_player_position': True, 'player': player, 'npc': npc,
            'destination': destination, 'normal_navigation': False,
            'npc_schedule_or_audio_writes': False})


def observe(debug, rom_path, record, frames=120):
    if type(frames) is not int or not 1 <= frames <= 240:
        raise ValueError('Voice observation needs a bounded frame count')
    path = Path(rom_path)
    rom = path.read_bytes()
    report = json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or report['runtime_abi'] != 60:
        raise ValueError('Voice observation requires the current ABI-60 cartridge')
    resources = report['complete_villager_audio']['files']
    font_row, wave_row = resources['bank'], resources['wave']
    start, length = font_row['physical_rom'], font_row['bytes']
    font = rom[start:start+length]
    wave_start, wave_end = wave_row['physical_rom'], wave_row['physical_rom']+wave_row['bytes']
    samples = []
    for instrument in range(84, 88):
        offset = u32(font, 8+instrument*4)
        for field in (8, 16, 24):
            pointer = u32(font, offset+field)
            if not pointer:
                continue
            size, source = struct.unpack_from('>2I', font, pointer)
            source += wave_start
            if not 0 < size < 0x1000000 or not wave_start <= source < source+size <= wave_end <= len(rom):
                raise ValueError('Imported voice sample escapes its checked waveform resource')
            samples.append((instrument, source, source+size))
    active, cached, matches, tags, previous_rows = set(), set(), {}, set(), None
    table_changes, active_rows, wave_matches = 0, 0, 0
    record(debug.pause_game_thread())
    for frame in range(frames+1):
        count = u32(debug.read_memory(0x8014BB20, 4), 0)
        table = u32(debug.read_memory(0x8014BB1C, 4), 0)
        if not 0 < count <= 256 or table & 3 or not 0x80000400 <= table <= 0x80400000-count*16:
            raise ValueError('Invalid native sample-cache table')
        rows = debug.read_memory(table, count*16)
        table_changes += previous_rows is not None and rows != previous_rows
        previous_rows = rows
        tags.add(debug.read_memory(0x80462B00, 32).hex())
        for at in range(0, len(rows), 16):
            ram, source, unused, size = struct.unpack_from('>2I2H', rows, at)
            ttl = rows[at+14]
            if not size or not wave_start <= source < wave_end:
                continue
            if ram & 3 or not 0x80000400 <= ram <= 0x80400000-size or source+size > len(rom):
                raise ValueError('Invalid native voice-cache range')
            data = debug.read_memory(ram, size)
            if ttl:
                active_rows += 1
                wave_matches += data == rom[source:source+size]
            for instrument, begin, end in samples:
                first, last = max(source, begin), min(source+size, end)
                if first >= last or data[first-source:last-source] != rom[first:last]:
                    continue
                cached.add(instrument)
                if ttl:
                    active.add(instrument)
                key = (instrument, first, last)
                matches[key] = {'instrument': instrument, 'source': f'{first:08X}',
                    'bytes': last-first, 'ram': f'{ram+first-source:08X}', 'ttl': ttl,
                    'frame': frame, 'sha256': sha256(data[first-source:last-source])}
        if frame < frames:
            debug.advance_game_frame()
    package_guard = by_vrom(rom)[BLOB].extract(rom)[0x7EFF0:0x7F000]
    if len(package_guard) != 16 or not any(package_guard):
        raise ValueError('Missing installed accessory/audio guard')
    for address, value in ((0x8003CE34, bytes(4)),
                           (0x8019C8D0, bytes.fromhex('AF32C0DE')*4),
                           (0x8046C350, bytes.fromhex('AF53C0DE')*4),
                           (0x80481FF0, package_guard)):
        if debug.read_memory(address, len(value)) != value:
            raise ValueError(f'Post-conversation guard changed at {address:08X}')
    result = {'ordinary_voice_cache_observation': True, 'frames': frames,
              'active_imported_instruments': sorted(active), 'cached_imported_instruments': sorted(cached),
              'completed_sample_matches': list(matches.values()), 'native_voice_tags': sorted(tags),
              'cache_table_changes': table_changes, 'active_voice_wave_rows': active_rows,
              'matching_active_voice_wave_rows': wave_matches,
              'guards_intact': True, 'audio_calls_or_data_writes': False,
              'physical_audio_playback': False}
    record(result)
    return result
