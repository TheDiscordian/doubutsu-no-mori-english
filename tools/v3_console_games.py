"""Prepare complete donor console games and save recipes as one shared category.

This prepares dependencies, not playable imports. Native launch, memory, save,
and emulator bindings must be installed before a furniture profile is enabled.
"""
import json
import struct
import zlib

from aflib import by_vrom, sha256, u32, verified_rom, yaz0_decode
from apply_translation import write_new
from gamecube import Disc, rarc_files
from v3_villager_audio import Dol, DOL_SHA

ARCHIVE_SHA = '3ac09f56fcd3d6cb0c3cad65a9343b951573d5713a6c88515b2afe12b662e9cf'
TAGS_TABLE = 0x800AAA30
GAME_COUNT = 19
HEADER_BYTES, ENTRY_BYTES, OP_BYTES = 32, 64, 16
SAVE_HEADER_BYTES = 8
SAVE_PLAYER_BYTES, SAVE_PLAYERS, SAVE_CONTAINER_HEADER_BYTES = 0x660, 4, 0x40
PERSISTENCE_FUNCTIONS = (
    ('famicom_save_data_setup',0x80041650,0x1B4,'e1bd92f29e9d756e2b4c5bf7877d83067b5030c579095874d7aaf55eae3cdc7e'),
    ('famicom_save_data_init',0x80041804,0x5C,'eb38ba0d8b27b1468ad3f74d50466e33c12eea56ab785591fa1f012edf2a49b1'),
    ('famicom_save_data_check',0x80041860,0x130,'965f0b8e8752735879457a00b13bb387127f9250971f0b16baa0350870aed398'),
    ('famicom_init',0x80043C54,0xD7C,'5efa64d552e7ac9c7b972643c8b3d9a899d27e87e8420659f8cf47907c7fa97b'),
    ('famicom_cleanup',0x80044BE8,0x228,'0a3a929557ff2a5b7b97d65267bee40081907e5878ea4e105b247bf57774732d'),
    ('update_highscore_raw',0x800468FC,0x128,'e580c558f843460b37cd23a381319ff6e35f8e79f3bd1754ff6c68e1019713f9'),
    ('special_zelda',0x80046DB0,0x188,'0f607b67cbdab77dfa081c40e556a2fbc38b42690f178ba351b02bddaf08c069'),
    ('nesinfo_tag_process1',0x80046F38,0x6E8,'ba07c1df4be07bdaf8cf6bc118627f3da80453c3818954a54956b3a2f7c50109'),
    ('nesinfo_tag_process3',0x80047918,0x29C,'fe309d396ebdac0411d56ecf0f83d6983734ff826c7d8068110abc86b4325ca7'),
    ('nesinfo_update_highscore',0x80047BB4,0x200,'09b3093c9b3b75df2c2927c8ce70e2aef5f83265e9e00a0fd233b02cf8183771'),
    ('highscore_setup_flags',0x80047E0C,0x34,'62aca9c1d30e8454efad4668877faa02aa78af9f5a20d0af71dad922afb33be1'),
)
# This exact donor tag has a six-byte length followed by eight name bytes.
# Repair only the length, retaining the original record and a correction receipt.
BAD_NAME_TAG_SHA = '17e687cb235a547870053a8dbef2994523cdc1561f11caee9469c6b2e4ff07c1'
MOVE_FORMS = {
    124: 'ea346e3ec5449da3899848814ea2bc42b8eca7156570b6390dd5369d155d51d1',
    64: '60e1c633313c109b54338b82f44c2022a955668ac0980fb87005dd6e1f084b23',
}
NATIVE_VROM, NATIVE_RAM = 0x7492E0, 0x8082A070
NATIVE_SHA = '12a57f84c4a600f5cf319f5be82c489ba2c137eada1ed5d4ddb6458ca6c7d1df'


def launch_binding(source, functions, index):
    """Read fixed/indexed game parameters from complete checked move callbacks."""
    if 'move' not in functions:
        return None
    receipt = functions['move']
    raw, _ = source.function(receipt['offset'])
    if len(raw) not in MOVE_FORMS or sha256(raw) != MOVE_FORMS[len(raw)]:
        return None
    module = u32(source.rel, 0)
    tables = {}
    if len(raw) == 64:
        expected = {0xA: (6, module, 6, 48192), 0x12: (4, module, 6, 48192)}
        game, gba = (struct.unpack_from('>H', raw, n)[0] for n in (0xE, 0x1E))
        selection = {}
    else:
        first, last = (struct.unpack_from('>H', raw, n)[0] for n in (0x16, 0x1E))
        count = last-first+1
        selected = index-first if first <= index <= last else 0
        expected = {0x2A: (6, module, 6, 48192), 0x32: (4, module, 6, 48192)}
        for role, hi, lo in (('game', 0x36, 0x4E), ('gba', 0x3E, 0x5A)):
            pointer = receipt['relocations'].get(hi)
            if pointer is None or pointer[:3] != (6, module, 5):
                raise ValueError('Console launch lacks its complete parameter table')
            symbol, base, size = source.containing(pointer[3], exact=True)
            if not 0 < count <= 256 or size != count or source.pointers(base, size):
                raise ValueError('Console launch parameter table has changed')
            expected.update({hi: pointer, lo: (4, module, 5, base)})
            data = source.data[base:base+size]
            tables[role] = dict(symbol=symbol, offset=base, bytes=size,
                                sha256=sha256(data), entries=list(data))
        game, gba = (tables[k]['entries'][selected] for k in ('game', 'gba'))
        selection = dict(first_runtime_index=first, last_runtime_index=last,
                         selected_index=selected, fallback_index=0)
    if receipt['relocations'] != expected:
        raise ValueError('Console launch has changed callback dependencies')
    return dict(game_index=game, gba_game_index=gba, selection=selection,
                tables=tables, function=receipt, donor_room_clip_offset=0x54,
                runtime_installed=False,
                payload_status='present' if 1 <= game <= GAME_COUNT else 'absent-from-donor')


def read_donor(path):
    with Disc(path) as disc:
        if disc.header[:8] != b'GAFE01\0\0':
            raise ValueError('Console imports require the GAFE01 revision 0 donor')
        offset = u32(disc.header, 0x420)
        header = disc.read(offset, 256)
        size = max(u32(header, i*4)+u32(header, 0x90+i*4)
                   for i in range(18) if u32(header, 0x90+i*4))
        executable = disc.read(offset, size)
        entries = [e for e in disc.files() if e['path'] == 'famicom.arc']
        if len(entries) != 1 or entries[0]['size'] != 1699904:
            raise ValueError('Changed donor console archive')
        archive = disc.read(entries[0]['offset'], entries[0]['size'])
    if sha256(executable) != DOL_SHA or sha256(archive) != ARCHIVE_SHA:
        raise ValueError('Changed donor console executable or archive')
    return Dol(executable), archive


def native_contract(rom):
    """Record existing emulator machinery without claiming larger games work."""
    rom = verified_rom(rom)
    overlay = by_vrom(rom)[NATIVE_VROM].extract(rom)
    if sha256(overlay) != NATIVE_SHA:
        raise ValueError('Changed original N64 console emulator')
    records = []
    for mapper in (0, 1, 4, 9):
        address = 0x80836010+mapper*20
        pointers = struct.unpack_from('>5I', overlay, address-NATIVE_RAM)
        if any(p and not NATIVE_RAM <= p < 0x80835DA0 for p in pointers):
            raise ValueError('Native mapper callback outside original code')
        records.append(dict(mapper=mapper, table_address=address,
                            callbacks=list(pointers), execution_verified=False))
    return dict(vrom=NATIVE_VROM, ram=NATIVE_RAM, bytes=len(overlay), sha256=NATIVE_SHA,
        game_range_function=0x8082A91C, original_game_count=7,
        game_range_sha256=sha256(overlay[0x8082A91C-NATIVE_RAM:0x8082A9EC-NATIVE_RAM]),
        mapper_dispatch=0x8082E950, mapper_rows=records,
        original_state_bytes=0x16F90, original_graphics_bytes=0x25008,
        pending=['Extend game lookup without altering existing identities',
                 'Size emulator graphics storage for complete donor CHR data',
                 'Connect save recipes and native furniture launch/return',
                 'Implement complete QD disk emulation dependency'])


def image_info(data):
    if data[:4] == b'NES\x1a':
        if len(data) < 16 or data[7] & 15 or any(data[8:16]) or not data[4]:
            raise ValueError('Unsupported or truncated iNES header')
        prg, chr_size = data[4]*16384, data[5]*8192
        trainer = 512 if data[6] & 4 else 0
        if len(data) != 16+trainer+prg+chr_size:
            raise ValueError('Incomplete iNES image or unaccounted trailing data')
        return dict(format='iNES', mapper=(data[7]&240)|(data[6]>>4),
                    prg_bytes=prg, chr_bytes=chr_size, trainer_bytes=trainer,
                    battery=bool(data[6]&2), mirroring=data[6]&9)
    if len(data) == 65536 and data[:15] == b'\x01*NINTENDO-HVC*':
        return dict(format='QD', mapper=None, sides=1, side_bytes=65536)
    raise ValueError('Unsupported console image; no header or payload is fabricated')


def save_recipe(original, payload):
    """Convert complete tags to bounded operations; preserve source ordering.

    Save offsets address the donor payload after its eight-byte header. HSC bit
    15 preserves the loaded-score state on reset; retain it in the operation.
    Runtime address interpretation belongs to the emulator adapter, not here.
    """
    tags = bytes(original)
    corrections = []
    if sha256(tags) == BAD_NAME_TAG_SHA:
        tags = tags[:9]+b'\x08'+tags[10:]
        corrections.append(dict(offset=9, before=6, after=8,
            reason='GNM length must include all eight existing name bytes'))
    at, cursor, extent = 0, None, 0
    operations, parsed, seen = [], [], set()
    game_number = None
    ended = False
    while at < len(tags):
        if at+4 > len(tags):
            raise ValueError('Truncated console save tag header')
        name, size = tags[at:at+3].decode('ascii'), tags[at+3]
        data = tags[at+4:at+4+size]
        if len(data) != size:
            raise ValueError('Console save tag exceeds its source record')
        parsed.append(dict(tag=name, offset=at, bytes=size, value=data.hex()))
        at += 4+size
        if name in ('GID', 'GNM', 'GNO', 'END'):
            if name in seen:
                raise ValueError('Duplicate console save identity or terminator')
            seen.add(name)
        if name in ('GID', 'GNM'):
            if not size or any(c < 32 or c > 126 for c in data):
                raise ValueError('Invalid console save identity text')
        elif name == 'GNO':
            if size != 1 or data[0] >= 32:
                raise ValueError('Console save bit outside the donor field')
            game_number = data[0]
        elif name == 'OFS':
            if size != 2:
                raise ValueError('Invalid console save offset')
            cursor = int.from_bytes(data, 'big')
        elif name in ('HSC', 'BBR', 'QDS'):
            if cursor is None or game_number is None:
                raise ValueError('Console save operation lacks an offset or game identity')
            if name == 'HSC':
                if size < 3:
                    raise ValueError('Invalid console high-score record')
                source = int.from_bytes(data[:2], 'big')
                length, defaults = size-2, data[2:]
                if source & 0x7800 or (source & 0x7FF)+length > 2048:
                    raise ValueError('High-score range exceeds emulator work RAM')
            else:
                if size != (4 if name == 'BBR' else 5):
                    raise ValueError('Invalid console persistence record')
                source = int.from_bytes(data[:-2], 'big')
                length, defaults = int.from_bytes(data[-2:], 'big'), b''
                if not length or source+length > (8192 if name == 'BBR' else len(payload)):
                    raise ValueError('Console persistence range exceeds its backing storage')
            if cursor+length > 65536:
                raise ValueError('Console save operation exceeds offset field')
            operations.append(dict(kind=name, source_offset=source, save_offset=cursor,
                                   bytes=length, default_hex=defaults.hex()))
            cursor += length
            extent = max(extent, cursor)
        elif name == 'SPE':
            if data != b'\x01' or not any(op['kind']=='BBR' for op in operations):
                raise ValueError('Unimplemented special console save operation')
            operations.append(dict(kind=name, parameter=1, bytes=0,
                                   source_offset=0, save_offset=0, default_hex=''))
        elif name == 'END':
            if size or at != len(tags):
                raise ValueError('Unexpected data after console save terminator')
            ended = True
        else:
            raise ValueError('Unsupported console save tag: '+name)
    if not ended or seen != {'GID', 'GNM', 'GNO', 'END'}:
        raise ValueError('Incomplete console save metadata')
    return dict(source_sha256=sha256(original), converted_sha256=sha256(tags),
                corrections=corrections, game_number=game_number,
                payload_extent=extent, operations=operations, tags=parsed), tags


def cstring(dol, at):
    result = bytearray()
    for i in range(96):
        c = dol.read(at+i, 1)
        if c == b'\0':
            return result.decode('ascii')
        if not 32 <= c[0] <= 126:
            raise ValueError('Non-ASCII console display name')
        result.extend(c)
    raise ValueError('Unterminated console display name')


def build_bundle(dol, archive):
    # Archive traversal, not alphabetical sorting, defines the source game IDs.
    files = [(p, d) for p, d in rarc_files(archive) if p.startswith('game/')]
    if len(files) != GAME_COUNT or len({p for p, _ in files}) != GAME_COUNT:
        raise ValueError('Changed complete console game directory')
    blob = bytearray(HEADER_BYTES+GAME_COUNT*ENTRY_BYTES)
    rows, occupied, game_numbers = [], {}, set()

    def append(data):
        blob.extend(bytes((-len(blob)) & 15))
        offset = len(blob)
        blob.extend(data)
        return offset

    for number, (path, packed) in enumerate(files, 1):
        if not path.startswith(f'game/01/{number:02d}_') or packed[:4] != b'Yaz0':
            raise ValueError('Changed console archive ordering or compression')
        payload = yaz0_decode(packed)
        info = image_info(payload)
        tag_at, tag_size, title_at, kanji_at = struct.unpack('>4I', dol.read(TAGS_TABLE+(number-1)*16, 16))
        if not 4 <= tag_size <= 4096:
            raise ValueError('Unbounded console tag source')
        original_tags = dol.read(tag_at, tag_size)
        recipe, tags = save_recipe(original_tags, payload)
        if recipe['game_number'] in game_numbers:
            raise ValueError('Shared save bit aliases two console games')
        game_numbers.add(recipe['game_number'])
        payload_at, original_at, converted_at = append(payload), append(original_tags), append(tags)
        operations = bytearray()
        for op in recipe['operations']:
            if op['bytes']:
                for byte in range(op['save_offset'], op['save_offset']+op['bytes']):
                    if byte in occupied:
                        raise ValueError('Console save ranges overlap')
                    occupied[byte] = number
            defaults = bytes.fromhex(op['default_hex'])
            default_at = append(defaults) if defaults else 0
            operations.extend(struct.pack('>BBHIII', ('HSC', 'BBR', 'QDS', 'SPE').index(op['kind'])+1,
                op.get('parameter', 0), op['bytes'], op['save_offset'], op['source_offset'], default_at))
        ops_at = append(operations) if operations else 0
        kind = 1 if info['format'] == 'iNES' else 2
        struct.pack_into('>16I', blob, HEADER_BYTES+(number-1)*ENTRY_BYTES,
            number, kind, info['mapper'] if kind==1 else 0xFFFFFFFF, 0,
            payload_at, len(payload), original_at, len(original_tags), converted_at, len(tags),
            ops_at, len(recipe['operations']), recipe['game_number'], recipe['payload_extent'], 0, 0)
        rows.append(dict(game_index=number, path=path, image=info,
            bytes=len(payload), sha256=sha256(payload), packed_sha256=sha256(packed),
            payload_offset=payload_at, source_tags_offset=original_at, converted_tags_offset=converted_at,
            operations_offset=ops_at, save=recipe, tags_address=tag_at,
            name=cstring(dol, title_at), alternate_name=cstring(dol, kanji_at),
            native_launch_installed=False, persistence_installed=False))
    extent = max(occupied, default=-1)+1
    if extent+SAVE_HEADER_BYTES > SAVE_PLAYER_BYTES:
        raise ValueError('Complete console saves exceed their donor player allocation')
    blob.extend(bytes((-len(blob)) & 15))
    struct.pack_into('>4s7I', blob, 0, b'AFNE', 1, GAME_COUNT, ENTRY_BYTES,
                     HEADER_BYTES+GAME_COUNT*ENTRY_BYTES, extent, SAVE_HEADER_BYTES, len(blob))
    report = dict(format='AFV3-CONSOLE-GAMES-1', source_dol_sha256=sha256(dol.data),
        source_archive_sha256=sha256(archive), rows=rows, bytes=len(blob), sha256=sha256(blob),
        save_payload_bytes=extent, save_header_bytes=SAVE_HEADER_BYTES,
        save_layout=persistence_contract(dol),
        runtime_installed=False, choice_eligible=False)
    return report, bytes(blob)


def persistence_contract(dol):
    functions=[]
    for name,address,size,digest in PERSISTENCE_FUNCTIONS:
        raw=dol.read(address,size)
        if sha256(raw)!=digest:
            raise ValueError('Changed complete console persistence function: '+name)
        functions.append(dict(name=name,address=address,bytes=size,sha256=digest))
    return dict(players=SAVE_PLAYERS, player_bytes=SAVE_PLAYER_BYTES,
        player_header_bytes=SAVE_HEADER_BYTES,
        all_player_bytes=SAVE_PLAYERS*SAVE_PLAYER_BYTES,
        donor_container_header_bytes=SAVE_CONTAINER_HEADER_BYTES,
        donor_container_bytes=SAVE_CONTAINER_HEADER_BYTES+SAVE_PLAYERS*SAVE_PLAYER_BYTES,
        native_storage_installed=False, functions=functions)


def streaming_bundle(report, bundle, archive):
    """Keep all recipes resident, but load only the selected complete image.

    Version-two entries reference 32-byte image descriptors. Their first sixteen
    bytes are the actual image header; the rest records compressed CRC, offset,
    and length in the separate, aligned original-Yaz0 pool, then reserved zero.
    The entry's former flags word binds the complete uncompressed image CRC.
    """
    if len(bundle)!=report['bytes'] or sha256(bundle)!=report['sha256']:
        raise ValueError('Changed complete console preparation')
    packed_files=dict(rarc_files(archive))
    metadata=bytearray(HEADER_BYTES+GAME_COUNT*ENTRY_BYTES);pool=bytearray();rows=[]
    def append(raw):
        metadata.extend(bytes(-len(metadata)%16));at=len(metadata);metadata.extend(raw);return at
    for row in report['rows']:
        game=row['game_index'];entry=list(struct.unpack_from('>16I',bundle,HEADER_BYTES+(game-1)*ENTRY_BYTES))
        image=bundle[entry[4]:entry[4]+entry[5]];packed=packed_files[row['path']]
        if (sha256(image)!=row['sha256'] or sha256(packed)!=row['packed_sha256'] or
                yaz0_decode(packed)!=image):raise ValueError('Changed complete streamed console image')
        pool.extend(bytes(-len(pool)%16));offset=len(pool);pool.extend(packed)
        pool.extend(bytes(-len(pool)%16))
        entry[3]=zlib.crc32(image)
        entry[4]=append(image[:16]+struct.pack('>4I',zlib.crc32(packed),offset,len(packed),0))
        entry[6]=append(bundle[entry[6]:entry[6]+entry[7]])
        entry[8]=append(bundle[entry[8]:entry[8]+entry[9]])
        ops=bytearray(bundle[entry[10]:entry[10]+entry[11]*OP_BYTES])
        for i in range(entry[11]):
            at=i*OP_BYTES;size=struct.unpack_from('>H',ops,at+2)[0];default=u32(ops,at+12)
            if default:struct.pack_into('>I',ops,at+12,append(bundle[default:default+size]))
        entry[10]=append(ops) if ops else 0
        struct.pack_into('>16I',metadata,HEADER_BYTES+(game-1)*ENTRY_BYTES,*entry)
        rows.append(dict(game_index=game,pool_offset=offset,packed_bytes=len(packed),
            stored_bytes=(len(packed)+15)&~15,packed_sha256=sha256(packed),
            packed_crc32=zlib.crc32(packed),image_bytes=len(image),
            image_sha256=sha256(image),image_crc32=zlib.crc32(image)))
    metadata.extend(bytes(-len(metadata)%16))
    struct.pack_into('>4s7I',metadata,0,b'AFNE',2,GAME_COUNT,ENTRY_BYTES,
        HEADER_BYTES+GAME_COUNT*ENTRY_BYTES,report['save_payload_bytes'],SAVE_HEADER_BYTES,len(metadata))
    result=dict(format='AFV3-CONSOLE-STREAM-1',metadata_bytes=len(metadata),
        metadata_sha256=sha256(metadata),pool_bytes=len(pool),pool_sha256=sha256(pool),
        rows=rows,source_bundle_sha256=sha256(bundle),
        maximum_image_bytes=max(r['image_bytes'] for r in rows),
        native_storage_installed=False,launch_installed=False)
    return result,bytes(metadata),bytes(pool)


def prepare_persistence(output):
    """Compile the common executor without assigning live RAM or installing it."""
    from v3_asset_loader import ROOT, compile_part
    code, compiled=compile_part('console_save',output/'console_save')
    files=('tools/v3_console_games.py','tools/v3_asset_loader.py',
           'overlays/v3/console_save.c','overlays/v3/console_save.h',
           'overlays/v3/console_save.ld')
    return dict(format='AFV3-CONSOLE-PERSISTENCE-1', compiled=compiled,
        bytes=len(code),sha256=sha256(code),linked_ram=0,
        sources={p:sha256((ROOT/p).read_bytes()) for p in files},
        native_hooks_installed=False,flash_storage_installed=False)


def prepare_storage(output):
    """Prepare the lossless bank envelope; native I/O integration stays separate."""
    from v3_asset_loader import ROOT, compile_part
    code,compiled=compile_part('save_compressed',output/'save_compressed')
    files=('tools/v3_console_games.py','tools/v3_asset_loader.py',
           'overlays/v3/save_compressed.c','overlays/v3/save_compressed.h',
           'overlays/v3/save_compressed.ld')
    return dict(format='AFV3-CONSOLE-STORAGE-1',compiled=compiled,bytes=len(code),
        sha256=sha256(code),linked_ram=0,bank_bytes=65536,canonical_bytes=65536,
        console_bytes=6528,decoded_bytes=72064,hash_workspace_bytes=16384,
        compressed_capacity=63850,save_format=5,
        sources={p:sha256((ROOT/p).read_bytes()) for p in files},
        capacity_failure='reject-before-output-or-flash-writes',
        native_storage_installed=False)


def prepare_image_loader(output):
    from v3_asset_loader import ROOT,compile_part
    code,compiled=compile_part('console_image',output/'console_image',
        extra_sources=('overlays/v3/console_save.c',))
    files=('tools/v3_console_games.py','tools/v3_asset_loader.py',
        'overlays/v3/console_image.c','overlays/v3/console_image.h','overlays/v3/console_image.ld',
        'overlays/v3/console_save.c','overlays/v3/console_save.h')
    return dict(compiled=compiled,bytes=len(code),sha256=sha256(code),
        workspace_bytes=1024,linked_ram=0,native_hooks_installed=False,
        sources={p:sha256((ROOT/p).read_bytes()) for p in files})


def prepare(source, path, output, original_rom):
    dol, archive = read_donor(path)
    report, blob = build_bundle(dol, archive)
    # Find the shared callback from every donor profile, not a list of game names.
    launches = []
    for item in [*range(0x1000, 0x2000, 4), *range(0x3000, 0x33C8, 4)]:
        index = (item-0x1000)//4 if item < 0x2000 else 1024+(item-0x3000)//4
        targets = [table.get(at+index*4) for (at, _), table in
                   zip(source.names['furniture_quality'], source.quality)]
        if targets[0] is None or targets[0] != targets[1]:
            raise ValueError('Console source profile tables disagree')
        pointer = source.relocations.get(targets[0]+48)
        if pointer is None or pointer[:3] != (1, True, 5):
            continue
        move = source.relocations.get(pointer[3]+4)
        if move is None or move[:3] != (1, True, 1):
            continue
        _, receipt = source.function(move[3])
        launch = launch_binding(source, {'move': receipt}, index)
        if launch:
            profile = source.profile(item)
            if profile['callback_adapter'].get('console_launch') != launch:
                raise ValueError('Console artwork and launch source bindings disagree')
            launches.append(dict(item_id=f'{item:04X}', source_profile_sha256=profile['profile_sha256'], **launch))
    report['furniture'] = launches
    report['original_native_emulator'] = native_contract(original_rom)
    output.mkdir(parents=True, exist_ok=False)
    write_new(output/'games.bin', blob)
    streaming,metadata,pool=streaming_bundle(report,blob,archive)
    write_new(output/'games-metadata.bin',metadata)
    write_new(output/'games-pool.bin',pool)
    report['streaming']=streaming
    report['streaming']['loader']=prepare_image_loader(output)
    report['persistence_core']=prepare_persistence(output)
    report['storage_core']=prepare_storage(output)
    from v3_console_disk import prepare as prepare_disk
    report['disk_core']=prepare_disk(dol,archive,output,original_rom)
    write_new(output/'games.json', (json.dumps(report, indent=2)+'\n').encode())
    return report
