"""Grow native HRA theme storage without changing its unrolled scoring loops."""
from aflib import sha256, u32
from gc_names import symbol_data
from v3_furniture_art import verify_sources

COUNT = 59
INFO, NAMES, SEARCH = 0x809283B0, 0x80928458, 0x80929750
SOURCES = ('tools/v3_hra_series.py',)
# Three initial necessity rows precede a four-row loop; theme matching has
# one initial row then a two-row loop. 60 would overrun both termination values.
COUNTERS = {
    0x809259E4: 0x28A10037, 0x80926A3C: 0x24120037,
    0x80926E5C: 0x2A010037, 0x80926FD0: 0x240D0037,
    0x80927378: 0x240A0037, 0x80927800: 0x24040036,
    0x80927F18: 0x24130037,
}
POINTERS = {
    0x809259F8: NAMES,
    0x80926A2C: SEARCH, 0x80926A34: INFO,
    0x80926B64: INFO, 0x80926B9C: SEARCH,
    0x80926E6C: INFO, 0x80926E74: INFO+3,
    0x80926E80: INFO+1, 0x80926E90: INFO+2,
    0x80926ED0: INFO+55*3,
    0x80926FC4: SEARCH, 0x80926FC8: INFO,
    0x80927274: INFO, 0x80927288: SEARCH,
    0x809272CC: INFO+3, 0x809272DC: SEARCH+4,
    0x8092731C: INFO+6, 0x80927328: SEARCH+8,
    0x8092736C: SEARCH, 0x80927370: INFO+9,
    0x809277FC: SEARCH,
    0x80927A0C: INFO+1, 0x80927BA8: INFO+1,
    0x80927D44: INFO+1, 0x80927EE0: INFO+1,
    0x80927F10: INFO, 0x80927F94: SEARCH,
}


def prepare(base, rel, symbols):
    from v3_hra import RAM, sources
    native, _ = sources(base)
    verify_sources(rel, symbols)
    donor_info = symbol_data(rel, symbols.decode(), 'mMkRm_series_info')
    donor_names = symbol_data(rel, symbols.decode(), 'mMkRm_series_name')
    if (sha256(donor_info) != '5e8ff8c0d4041c76981c74ba62075d28249dc8d8e1d4cab9191315829738bd65'
            or sha256(donor_names) != '9d5b0d3d4faa60cc780462ef1ed8320bd14b3f01e22f09303ce513e4e41c6e42'
            or donor_info[58*3:59*3] != bytes.fromhex('020041')
            or donor_names[58*16:59*16] != b'boxing          '):
        raise ValueError('Changed donor HRA boxing definition')
    if COUNT != 59 or (COUNT-55) % 4:
        raise ValueError('Expanded series count breaks native unrolled loop termination')
    # Unimplemented donor series 55..57 cannot acquire an accidental native
    # floor/wall match. Boxing keeps its true theme type; its donor surfaces
    # are not installed, so FF explicitly means no matching native surface.
    info = native[INFO-RAM:INFO-RAM+55*3] + bytes.fromhex('FF00FF')*3 + bytes.fromhex('0200FF')
    names = native[NAMES-RAM:NAMES-RAM+55*10] + b' '*30 + b'boxing    '
    return {'af_v3_hra_series_info': info, 'af_v3_hra_series_names': names,
            'af_v3_hra_series_search': bytes(COUNT*4)}


def assembly(resources):
    result = '.section .rodata.hra_series\n'
    for name, data in resources.items():
        result += f'.balign 4\n.globl {name}\n{name}:\n'
        result += ''.join('.byte '+','.join(str(v) for v in data[i:i+16])+'\n'
                          for i in range(0, len(data), 16))
    return result


def replacement(target, symbols):
    for start, width, symbol in ((INFO, 3, 'af_v3_hra_series_info'),
                                 (NAMES, 10, 'af_v3_hra_series_names'),
                                 (SEARCH, 4, 'af_v3_hra_series_search')):
        if start <= target < start+55*width:
            return symbols[symbol]+target-start
    if target == INFO+55*3:
        return symbols['af_v3_hra_series_info']+COUNT*3
    return None


def install(old, data, symbols, resources, pointers, word):
    from v3_hra import RAM, SECTIONS, START
    if {p['low']: p['before'] for p in pointers} != POINTERS:
        raise ValueError('Changed complete native series-reference inventory')
    found = {RAM+at: u32(old, at) for at in range(0, SECTIONS[0], 4)
             if u32(old, at) >> 26 in (9, 10, 11, 12, 13)
             and u32(old, at) & 65535 in (54, 55)}
    if found != COUNTERS:
        raise ValueError('Changed complete HRA series-count inventory')
    for address, before in COUNTERS.items():
        word(address, before, before & 0xFFFF0000 | (COUNT-1 if address == 0x80927800 else COUNT))
    for name, payload in resources.items():
        at = symbols[name]-RAM
        if at < START or at & 3 or data[at:at+len(payload)] != payload:
            raise ValueError('Linked series resource differs or escapes appended storage')
    return {'count': COUNT, 'info_address': symbols['af_v3_hra_series_info'],
            'names_address': symbols['af_v3_hra_series_names'],
            'search_address': symbols['af_v3_hra_series_search'],
            'resource_bytes': sum(map(len, resources.values())),
            'resource_sha256': {name: sha256(value) for name, value in resources.items()},
            'pointer_changes': pointers, 'counter_sites': list(COUNTERS),
            'boxing': {'series': 58, 'type': 2, 'name': 'boxing',
                       'donor_wall_floor_index': 65, 'native_wall_floor_index': 255,
                       'matching_surfaces_installed': False, 'score_letter_name_installed': False},
            'native_scoring_tested': False}


def extend_current(data, relocation, report, source, surfaces):
    """Install every donor theme through the existing native scoring machinery.

    Preserve the original 55 definitions. The three padding rows are inert;
    series 63 remains the absent-item sentinel, outside every counted array.
    """
    import copy
    import struct
    from catalogue_names import Image
    from npc_mail_show import relocate_verified_data
    from v3_hra import RAM, START
    donor = source.raw('mMkRm_series_info')
    names = source.raw('mMkRm_series_name')
    if (sha256(donor) != '5e8ff8c0d4041c76981c74ba62075d28249dc8d8e1d4cab9191315829738bd65'
            or sha256(names) != '9d5b0d3d4faa60cc780462ef1ed8320bd14b3f01e22f09303ce513e4e41c6e42'
            or sha256(data) != report['output_sha256']
            or sha256(relocation) != report['relocation_sha256']):
        raise ValueError('Changed complete theme source or current scoring owner')
    result = copy.deepcopy(report)
    series = result['series']
    if series['count'] != 59:
        raise ValueError('Theme extension requires the checked 59-row category')
    old_resources = {}
    for key, width in (('info', 3), ('names', 10), ('search', 4)):
        at = series[key+'_address']-RAM
        payload = data[at:at+59*width]
        if len(payload) != 59*width or sha256(payload) != series['resource_sha256']['af_v3_hra_series_'+key]:
            raise ValueError('Changed complete installed theme resource')
        old_resources[key] = payload
    if any(old_resources['search']):
        raise ValueError('Persistent scoring search scratch must start empty')
    paired = []
    for kind in ('floor', 'wall'):
        paired.append({r['source_index']: r['destination_index'] for r in surfaces['rows'] if r['kind'] == kind})
    if paired[0] != paired[1] or len(paired[0]) != 5:
        raise ValueError('Incomplete stable floor/wall pair mapping')
    info = bytearray(old_resources['info'][:55*3])
    keys = bytearray(old_resources['names'][:55*10])
    additions = []
    for index in range(55, len(donor)//3):
        row, name = donor[index*3:index*3+3], names[index*16:index*16+16]
        if row[0] not in (1, 2) or row[1] or row[2] not in paired[0] or name[10:] != b' '*6:
            raise ValueError('Unsupported complete donor theme category or name width')
        mapped = row[:2]+bytes([paired[0][row[2]]])
        label = name.decode('ascii').rstrip()
        if index < 59 and old_resources['info'][index*3:index*3+3] != b'\xff\0\xff':
            if (old_resources['info'][index*3:index*3+3] != mapped
                    or old_resources['names'][index*10:index*10+10] != name[:10]):
                raise ValueError('New category changes an existing theme')
        else:
            additions.append(index)
        info.extend(mapped)
        keys.extend(name[:10])
        series[label] = dict(series=index, type=row[0], name=label,
            donor_wall_floor_index=row[2], native_wall_floor_index=mapped[2],
            matching_surfaces_installed=True, score_letter_name_installed=False)
    count = 63
    if (count-3) % 4 or (count-1) % 2 or count != len(donor)//3+3:
        raise ValueError('Theme padding violates native unrolled loops')
    resources = dict(info=bytes(info)+b'\xff\0\xff'*3, names=bytes(keys)+b' '*30, search=bytes(count*4))
    image = bytearray(data)
    old_addresses = {key: series[key+'_address'] for key in resources}
    for key, payload in resources.items():
        image.extend(bytes(-len(image) % 4))
        series[key+'_address'] = RAM+len(image)
        image.extend(payload)
    image.extend(bytes(-len(image) % 16))
    if len(image) > 0x8000 or len(image)+len(relocation) > 0x8800:
        raise ValueError('Theme resources exceed the bounded scoring owner')
    patches = []
    def word(at, before, after):
        if u32(image, at) not in (before, after) or u32(data, at) != before:
            raise ValueError('Changed or conflicting theme instruction')
        struct.pack_into('>I', image, at, after)
        if before != after and not any(p['offset'] == at for p in patches):
            patches.append(dict(offset=at, before=before, after=after))
    sections = struct.unpack_from('>5I', relocation)
    if sections[:4] != (len(data), 0, 0, 0):
        raise ValueError('Changed scoring relocation sections')
    high, found = {}, []
    expected = {p['low']: p for p in series['pointer_changes']}
    metadata_pointers = {p['low']: p for p in report['pointer_changes']}
    if set(expected) != set(POINTERS):
        raise ValueError('Changed complete native theme pointer inventory')
    for (value,) in struct.iter_unpack('>I', relocation[20:20+sections[4]*4]):
        kind, at = value >> 24 & 63, value & 0xFFFFFF
        instruction = u32(data, at)
        if value >> 30 != 1:
            raise ValueError('Unexpected theme relocation section')
        if kind == 5:
            high[instruction >> 16 & 31] = at, instruction
        elif kind == 6:
            hi_at, hi = high[instruction >> 21 & 31]
            target = (hi & 65535)*65536+(instruction & 65535)-(65536 if instruction & 32768 else 0)
            # The metadata end pointer shares the old info table's address.
            # Its identity comes from its original reference, not that address.
            if RAM+at in metadata_pointers:
                bound = metadata_pointers[RAM+at]
                if (bound['high'], bound['after']) != (RAM+hi_at, target):
                    raise ValueError('Changed complete furniture metadata reference')
                continue
            key = next((k for k, width in (('info', 3), ('names', 10), ('search', 4))
                        if old_addresses[k] <= target < old_addresses[k]+59*width), None)
            end = target == old_addresses['info']+59*3
            if key is None and not end:
                continue
            key = 'info' if end else key
            new = series[key+'_address']+(count*3 if end else target-old_addresses[key])
            prior = expected.get(RAM+at)
            if not prior or (prior['high'], prior['after']) != (RAM+hi_at, target):
                raise ValueError(f'Unaccounted theme table reference {RAM+at:08X} -> {target:08X}; {prior}')
            word(hi_at, hi, hi & 0xFFFF0000 | (new+0x8000) >> 16 & 65535)
            word(at, instruction, instruction & 0xFFFF0000 | new & 65535)
            found.append({**prior, 'after': new})
    if {p['low'] for p in found} != set(expected):
        raise ValueError('Missing native theme table reference')
    for address, original in COUNTERS.items():
        word(address-RAM, original & 0xFFFF0000 | (58 if address == 0x80927800 else 59),
             original & 0xFFFF0000 | (62 if address == 0x80927800 else 63))
    # The source helper rejects the sentinel before scanning metadata. Its
    # unsigned comparison retains that property with a 63-entry bound.
    word(START, 0x2CA2003B, 0x2CA2003F)
    fixed = bytearray(relocation)
    struct.pack_into('>I', fixed, 0, len(image))
    allowed = {i for p in patches for i in range(p['offset'], p['offset']+4)}
    for destination in (0x801A0010, 0x802F8010, 0x803D0010):
        before = relocate_verified_data(Image(RAM, len(data), sections), data, relocation, destination)
        after = relocate_verified_data(Image(RAM, len(image), (len(image), 0, 0, 0, sections[4])), image, fixed, destination)
        if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(before, after))):
            raise ValueError('Theme expansion changes unrelated relocated instructions/data')
    series.update(count=count, resource_bytes=sum(map(len, resources.values())), pointer_changes=found,
        resource_sha256={'af_v3_hra_series_'+k: sha256(v) for k, v in resources.items()})
    receipt = dict(format='AFV3-HRA-THEMES-1', donor_count=len(donor)//3, count=count,
        added_series=additions, padding_series=[60, 61, 62], excluded_sentinel=63,
        donor_info_sha256=sha256(donor), donor_names_sha256=sha256(names), patches=patches,
        old_bytes=len(data), bytes=len(image), on_demand_growth=len(image)-len(data),
        old_output_sha256=sha256(data), output_sha256=sha256(image),
        relocated_destinations_checked=3, native_test='pending', acquisition_installed=False)
    result.update(bytes=len(image), output_sha256=sha256(image), relocation_sha256=sha256(fixed),
        on_demand_growth=len(image)-result['source_resident_bytes'], theme_extension=receipt)
    return bytes(image), bytes(fixed), result
