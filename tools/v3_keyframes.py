"""Complete native-compatible rotational skeleton and keyframe resources.

These are shared format rules, not item/animation definitions. Graphics and
action dispatch remain separate consumers; a converted rig is not gameplay.
"""
import struct

from aflib import sha256

SEGMENT = 0x06000000
CHANNELS = ('flags', 'keys', 'counts', 'constants')


def resource(source, address, *, size=None, pointers=False):
    name, at, length = source.containing(address, exact=True)
    if size is not None and length != size:
        raise ValueError('Keyframe resource has an unexpected complete size')
    raw = source.data[at:at+length]
    if len(raw) != length or not pointers and source.pointers(at, length):
        raise ValueError('Keyframe array has incomplete data or unexpected pointers')
    return raw, dict(symbol=name, donor_offset=at, bytes=length, source_sha256=sha256(raw))


def animation(source, address, *, joints=None):
    raw, header = resource(source, address, size=20, pointers=True)
    pointers = source.pointers(address, 20)
    if (raw[:16] != bytes(16) or address not in pointers
            or not set(pointers) <= {address+i*4 for i in range(4)}):
        raise ValueError('Incomplete keyframe animation header pointers')
    pad, duration = struct.unpack_from('>hh', raw, 16)
    if pad != -1 or duration < 1:
        raise ValueError('Unsupported keyframe animation duration/header')
    arrays, receipts = {}, {}
    for i, label in enumerate(CHANNELS):
        if address+i*4 in pointers:
            arrays[label], receipts[label] = resource(source, pointers[address+i*4])
        else:
            arrays[label], receipts[label] = b'', None
    flags, keys, counts, constants = (arrays[k] for k in CHANNELS)
    count = len(flags)
    if (not 1 <= count <= 255 or joints is not None and joints != count
            or flags[0] & ~0x3F or any(value & ~7 for value in flags[1:])):
        raise ValueError('Keyframe flags do not match the rotational skeleton')
    keyed = (flags[0] & 0x38).bit_count() + sum((v & 7).bit_count() for v in flags)
    if len(counts) != 2*keyed or len(constants) != 2*(3+3*count-keyed):
        raise ValueError('Keyframe channel counts do not consume complete arrays')
    lengths = [n[0] for n in struct.iter_unpack('>h', counts)]
    if any(n < 1 for n in lengths) or sum(lengths)*6 != len(keys):
        raise ValueError('Keyframe tracks do not consume complete key data')
    tracks, cursor = [], 0
    for length in lengths:
        frames = [struct.unpack_from('>h', keys, (cursor+i)*6)[0] for i in range(length)]
        if (frames[0] < 1 or frames[-1] > duration
                or any(a >= b for a, b in zip(frames, frames[1:]))):
            raise ValueError('Keyframe track has unordered or out-of-duration frames')
        tracks.append(dict(first_key=cursor, keys=length, first_frame=frames[0], last_frame=frames[-1]))
        cursor += length
    # cKF_KeyCalc uses signed 16-bit start and length arguments on N64.
    if cursor > 32767:
        raise ValueError('Keyframe traversal exceeds native signed-index capacity')
    return dict(header=header, arrays=receipts, joints=count, duration=duration,
                tracks=tracks, keyed_channels=keyed, constant_channels=3+3*count-keyed)


def skeleton(source, address):
    raw, header = resource(source, address, size=8, pointers=True)
    pointers = source.pointers(address, 8)
    count, shown = raw[:2]
    if (not count or shown > count or raw[2:] != bytes(6)
            or set(pointers) != {address+4}):
        raise ValueError('Invalid complete rotational skeleton header')
    joint_address = pointers[address+4]
    raw_joints, table = resource(source, joint_address, size=count*12, pointers=True)
    models = source.pointers(joint_address, count*12)
    if len(models) != shown or any((at-joint_address)%12 for at in models):
        raise ValueError('Skeleton models do not match its displayed joints')
    rows, pending = [], 1
    for i in range(count):
        model, children, flags, x, y, z = struct.unpack_from('>IBB3h', raw_joints, i*12)
        if not pending or model or flags not in (0, 1):
            raise ValueError('Invalid skeleton hierarchy, model storage, or draw stream')
        pending += children-1
        row = dict(index=i, children=children, draw_stream=flags, translation=[x,y,z])
        if joint_address+i*12 in models:
            target = models[joint_address+i*12]
            _, row['model'] = resource(source, target, pointers=True)
        rows.append(row)
    if pending:
        raise ValueError('Skeleton hierarchy leaves missing children')
    return dict(header=header, joint_table=table, joints=count, shown_joints=shown, rows=rows)


def model_descriptor(rig, **fields):
    """Keep every shown joint while deduplicating shared display-list roots."""
    models, labels, bindings = {}, {}, []
    for joint in rig['rows']:
        if 'model' not in joint:
            continue
        model = joint['model']; at = model['donor_offset']
        if at not in labels:
            label = 'joint'+str(joint['index']); labels[at] = label
            models[label] = model['symbol'], at, model['bytes']
        bindings.append(dict(joint_index=joint['index'], model_label=labels[at]))
    return dict(**fields, skeleton=rig, joint_models=bindings, models=models)


def compile_animations(source, descriptions, *, start=0):
    """Pack complete arrays once and relocate headers into one native object."""
    if not descriptions or type(start) is not int or not 0 <= start < 0x1000000 or start % 16:
        raise ValueError('No checked animations or invalid object offset')
    checked = {}
    for row in descriptions:
        at = row['header']['donor_offset']
        if at in checked or row != animation(source, at, joints=row['joints']):
            raise ValueError('Duplicate or changed animation description')
        checked[at] = row
    output, offsets, arrays = bytearray(), {}, []
    for at in sorted({r['donor_offset'] for row in checked.values() for r in row['arrays'].values() if r}):
        raw, receipt = resource(source, at)
        output.extend(bytes(-len(output)%4)); offsets[at] = start+len(output)
        output.extend(raw)
        arrays.append(dict(**receipt, native_offset=offsets[at], output_sha256=sha256(raw)))
    headers, relocations = [], []
    for at, row in sorted(checked.items()):
        raw, _ = resource(source, at, size=20, pointers=True)
        fixed = bytearray(raw)
        output.extend(bytes(-len(output)%4)); header_at = start+len(output)
        for i, label in enumerate(CHANNELS):
            if row['arrays'][label] is None:
                continue
            target = offsets[row['arrays'][label]['donor_offset']]
            struct.pack_into('>I', fixed, i*4, SEGMENT+target)
            relocations.append(dict(offset=header_at+i*4, target_offset=target))
        output.extend(fixed)
        headers.append(dict(**row['header'], native_offset=header_at, output_sha256=sha256(fixed),
                            joints=row['joints'], duration=row['duration']))
    output.extend(bytes(-len(output)%16))
    if start+len(output) >= 0x1000000:
        raise ValueError('Animation object exceeds a segmented address range')
    return bytes(output), dict(arrays=arrays, headers=headers, relocations=relocations,
                              segment=SEGMENT, runtime_installed=False)


def compile_skeleton(source, description, model_offsets, *, start):
    """Append a complete rig after shared artwork, retaining each joint binding.

    Model offsets refer to complete lists already emitted in the same object.
    The returned suffix does not move that artwork or bake joint transforms.
    """
    at = description['header']['donor_offset']
    if description != skeleton(source, at):
        raise ValueError('Changed skeleton description')
    roots = {r['model']['donor_offset'] for r in description['rows'] if 'model' in r}
    if (type(start) is not int or not 0 <= start < 0x1000000 or start % 16 or set(model_offsets) != roots or
            len(set(model_offsets.values())) != len(model_offsets) or
            any(type(p) is not int or p % 8 or not 0 <= p <= start-8 for p in model_offsets.values())):
        raise ValueError('Skeleton models do not bind complete preceding artwork')
    table = description['joint_table']; size = table['bytes']
    output = bytearray(source.data[table['donor_offset']:table['donor_offset']+size])
    relocations = []
    for row in description['rows']:
        if 'model' not in row:
            continue
        target = model_offsets[row['model']['donor_offset']]
        offset = row['index']*12
        struct.pack_into('>I', output, offset, SEGMENT+target)
        relocations.append(dict(offset=start+offset, target_offset=target))
    header = bytearray(source.data[at:at+8])
    struct.pack_into('>I', header, 4, SEGMENT+start)
    output.extend(header)
    relocations.append(dict(offset=start+size+4, target_offset=start))
    output.extend(bytes(-len(output)%16))
    if start+len(output) >= 0x1000000:
        raise ValueError('Skeleton object exceeds a segmented address range')
    return bytes(output), dict(segment=SEGMENT, joints=description['joints'],
        shown_joints=description['shown_joints'], relocations=relocations,
        joint_table=dict(**table, native_offset=start, output_sha256=sha256(output[:size])),
        header=dict(**description['header'], native_offset=start+size,
                    output_sha256=sha256(header)), runtime_installed=False)
