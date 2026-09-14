"""Install additive speed-bag sound data through the original N64 audio loader."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32, verified_rom
from v3_speed_bag_audio import bind_font, bind_program, extract
from v3_villager_audio import NATIVE_FILES, NATIVE_HEADERS, header_entry, resource, span

ABI = 45
SOUND_ID, INSTRUMENT = 0x169, 71
RELOCATIONS = {0x27130: 0x01920000, 0xE4D10: 0x019F0000, 0x13D9A0: 0x01A50000}
LIMITS = {0x27130: 0xD0000, 0xE4D10: 0x60000, 0x13D9A0: 0x5B0000}
SOURCES = ('tools/v3_speed_bag_sound_runtime.py', 'tools/v3_speed_bag_audio.py')


def align(value, boundary=16):
    return (value+boundary-1) & -boundary


def append_instrument(bank, parts, sample_offset):
    """Use the verified spare table word; retain every original resource offset."""
    if (len(bank) != 0x29F0 or bank[:8] != bytes(8) or bank[0x124:0x130] != bytes(12)
            or sample_offset % 16 or sample_offset < 0):
        raise ValueError('Changed native bank-140 instrument table or alignment')
    # Bind all original instrument/sample/loop/book/envelope pointer spans so
    # the new table word cannot overwrite any original pointed-to resource.
    spans = []
    def original_span(at, size):
        if at % 4 or at < 0x130 or at+size > len(bank):
            raise ValueError('Native bank resource reaches the spare instrument slot')
        spans.append((at, size))
        return span(bank, at, size)
    for i in range(71):
        inst = original_span(u32(bank, 8+i*4), 32)
        if inst[0]: raise ValueError('Native bank instrument is already relocated')
        # At least the first envelope command is a valid pointed-to resource;
        # the complete source bytes are retained unchanged, not reconstructed.
        original_span(u32(inst, 4), 4)
        for at in (8, 16, 24):
            ptr = u32(inst, at)
            if not ptr:
                if u32(inst, at+4): raise ValueError('Tuned sample has no native pointer')
                continue
            sample = original_span(ptr, 16)
            flags, address, loop, book = struct.unpack('>4I', sample)
            if flags >> 24: raise ValueError('Unsupported native sample flags')
            loop_data = original_span(loop, 16)
            if u32(loop_data, 8): original_span(loop, 48)
            order, count = struct.unpack('>2I', original_span(book, 8))
            if not 1 <= order <= 2 or not 1 <= count <= 16:
                raise ValueError('Unsupported native ADPCM book')
            original_span(book, 8+16*order*count)
    font, _ = bind_font(parts)
    addition = bytearray(font[16:])
    start = len(bank)
    for at in (4, 16, 52, 56):
        # Standalone font has a 16-byte table prefix; remove it for the append.
        target = u32(addition, at)-16+start
        struct.pack_into('>I', addition, at, target)
    struct.pack_into('>I', addition, 48, sample_offset)
    result = bytearray(bank)+addition
    struct.pack_into('>I', result, 0x124, start)
    if len(result) != 0x2AB0:
        raise ValueError('Unexpected complete speed-bag instrument append size')
    return bytes(result), {'instrument': 71, 'instrument_offset': start,
                          'sample_offset': start+44, 'wave_offset': sample_offset,
                          'retained_native_instruments': 71,
                          'original_pointed_spans': len(set(spans)), 'additional_bytes': len(addition)}


def permanent_budget(code):
    def read(at, size): return span(code, at-CODE_RAM, size)
    # Original total/fixed/permanent capacities. No allocation or cache policy
    # is enlarged, and no new permanent-resource ID is added by this adapter.
    if read(0x80119A44, 12) != struct.pack('>3I', 0x47A00, 0x1D800, 0x1A800):
        raise ValueError('Changed native audio heap configuration')
    rows = []
    for kind, base in NATIVE_HEADERS.items():
        count = struct.unpack('>H', read(base, 2))[0]
        for index in range(count):
            entry = header_entry(read, base, index)
            size = u32(entry, 4)
            if size and entry[9] == 0:
                if entry[8] != 2: raise ValueError('Changed permanent audio medium')
                rows.append({'kind': kind, 'index': index, 'bytes': size,
                             'conservative_allocation': align(size, 32)})
    if [(r['kind'], r['index']) for r in rows] != [
            ('seq', 199), ('seq', 203), ('bank', 0), ('bank', 2),
            ('bank', 139), ('bank', 140), ('bank', 141)]:
        raise ValueError('Changed complete permanent audio resource inventory')
    total = sum(r['conservative_allocation'] for r in rows)
    if total > 0x1A800: raise ValueError('Complete permanent audio resources exceed native capacity')
    return {'capacity': 0x1A800, 'all_permanent_resources': rows,
            'conservative_required': total, 'conservative_spare': 0x1A800-total,
            'audio_heap_growth': 0}


def prepare(native, code, donor):
    verified_rom(native)
    original = by_vrom(native)[CODE_VROM].extract(native)
    files = by_vrom(native)
    def read(at, size): return span(original, at-CODE_RAM, size)
    sources = {k: files[v].extract(native) for k, v in NATIVE_FILES.items()}
    parts, provenance = extract(native, *donor)
    native_priority = read(0x80113B84, 128)
    donor_priority = donor[0].read(0x800A9A90, 128)
    if (sha256(native_priority) != '5bce599d4fe055a6ab812d1c2ef18680d9ae87d55d6a44e1293de1b885a77355'
            or native_priority[SOUND_ID & 255] != donor_priority[0x76]
            or donor_priority[0x76] != 70):
        raise ValueError('Speed-bag sound ID does not preserve donor trigger priority')
    sequence, seq_entry = resource(read, NATIVE_HEADERS, sources, 'seq', 199)
    bank, bank_entry = resource(read, NATIVE_HEADERS, sources, 'bank', 140)
    wave, wave_entry = resource(read, NATIVE_HEADERS, sources, 'wave', 5)
    if len(sequence) != 0x4C30 or wave_entry[9] != 4 or bank_entry[10:] != bytes.fromhex('05ff47000000'):
        raise ValueError('Changed native sound resources or wave cache policy')
    # The final wave bank ends at the file boundary. Appending preserves all
    # original waveform addresses; only that final bank's size increases.
    if u32(wave_entry, 0)+len(wave) != len(sources['wave']) or len(wave) % 16:
        raise ValueError('Native wave-five append is not at the file boundary')
    new_bank, instrument = append_instrument(bank, parts, len(wave))
    new_sequence = bytearray(sequence)
    table = len(new_sequence)
    count = (SOUND_ID & 255)+1
    no_op = table+count*2
    # The envelope starts 15 bytes into the donor fragment and is read with
    # native halfword loads. Put the one-byte reserved-ID terminator first so
    # the program is odd-aligned and its complete envelope is even-aligned.
    program_at = no_op+1
    if (program_at+15) % 2:
        raise ValueError('Native sound envelope requires halfword alignment')
    new_sequence.extend(sequence[0x27C:0x33E])
    # Reserved unassigned IDs terminate immediately instead of dispatching into
    # another group's table. Existing IDs keep their exact original pointers.
    new_sequence.extend(struct.pack('>H', no_op)*(count-98))
    new_sequence.extend(struct.pack('>H', program_at))
    new_sequence.append(0xFF)
    new_sequence.extend(bind_program(parts, program_at, 1, INSTRUMENT))
    new_sequence.extend(bytes(-len(new_sequence) % 16))
    struct.pack_into('>H', new_sequence, 0x18A, table)
    if len(new_sequence) != 0x4D20:
        raise ValueError('Changed main-sequence growth')
    payloads = {'seq': bytes(new_sequence), 'bank': new_bank,
                'wave': parts['wave']+bytes(-len(parts['wave']) % 16)}
    changes, patches, records = {}, [], {}
    before_budget = permanent_budget(code)
    for kind, index, entry in (('seq', 199, seq_entry), ('bank', 140, bank_entry), ('wave', 5, wave_entry)):
        original_file = sources[kind]
        payload = payloads[kind]
        if len(original_file) % 16:
            raise ValueError('Native audio append is not aligned')
        data = original_file+payload
        old_vrom = NATIVE_FILES[kind]
        if len(data) > LIMITS[old_vrom]:
            raise ValueError('Extended audio resource exceeds its reserved virtual interval')
        changes[old_vrom] = data
        new_entry = bytearray(entry)
        offset = len(original_file) if kind != 'wave' else u32(entry, 0)
        size = len(payload) if kind != 'wave' else len(wave)+len(payload)
        struct.pack_into('>2I', new_entry, 0, offset, size)
        if kind == 'bank': new_entry[12] = 72
        at = NATIVE_HEADERS[kind]+16+index*16
        if code[at-CODE_RAM:at-CODE_RAM+16] != entry:
            raise ValueError('Audio header changed before speed-bag installation')
        code[at-CODE_RAM:at-CODE_RAM+16] = new_entry
        patches.append({'address': at, 'before': entry.hex(), 'after': new_entry.hex()})
        records[kind] = {'old_vrom': old_vrom, 'vrom': RELOCATIONS[old_vrom],
                         'original_file_bytes': len(original_file), 'bytes': len(data),
                         'original_sha256': sha256(original_file), 'sha256': sha256(data),
                         'appended_bytes': len(payload), 'appended_sha256': sha256(payload),
                         'header_offset': offset, 'header_size': size}
    after_budget = permanent_budget(code)
    if after_budget['conservative_required']-before_budget['conservative_required'] != 416:
        raise ValueError('Unexpected speed-bag permanent audio growth')
    return changes, {'sound_id': f'{SOUND_ID:04X}', 'source': provenance,
                     'sequence_table_offset': table, 'sequence_program_offset': program_at,
                     'sequence_group_one_count': count, 'reserved_no_op_offset': no_op,
                     'trigger_priority': donor_priority[0x76],
                     'instrument': instrument, 'files': records, 'header_patches': patches,
                     'before_budget': before_budget, 'after_budget': after_budget,
                     'native_synthesis_tested': False, 'sound_resources_installed': True,
                     'furniture_callback_installed': False, 'save_format_changed': False}


def bind_physical(native, code, image, report):
    """Bind the normal audio initializer to actual physical ROM file locations."""
    original = by_vrom(native)[CODE_VROM].extract(native)
    start, end = 0x800D28DC, 0x800D2908
    if code[start-CODE_RAM:end-CODE_RAM] != original[start-CODE_RAM:end-CODE_RAM]:
        raise ValueError('Changed native audio initialization argument window')
    files = by_vrom(image)
    entries = {'seq': (0x800D28E8, 0x800D28F4), 'bank': (0x800D28EC, 0x800D28F0),
               'wave': (0x800D28DC, 0x800D28E0)}
    patches = []
    for kind, (hi_at, lo_at) in entries.items():
        resource = report['files'][kind]
        file = files[resource['vrom']]
        if file.pend or sha256(file.extract(image)) != resource['sha256']:
            raise ValueError('Native audio requires the exact uncompressed physical resource')
        address = file.pstart
        for at, half in ((hi_at, (address+0x8000) >> 16), (lo_at, address & 65535)):
            old = u32(code, at-CODE_RAM)
            new = (old & 0xFFFF0000) | half
            struct.pack_into('>I', code, at-CODE_RAM, new)
            patches.append({'address': at, 'before': old, 'after': new})
        resource['physical_rom'] = address
    report['initializer_patches'] = patches
    report['native_audio_initializer_window_sha256'] = sha256(original[start-CODE_RAM:end-CODE_RAM])
