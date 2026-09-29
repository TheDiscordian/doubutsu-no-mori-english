"""Complete native-compatible rotational skeleton and keyframe resources.

These are shared format rules, not item/animation definitions. Graphics and
action dispatch remain separate consumers; a converted rig is not gameplay.
"""
import struct
import math

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
    return _animation(source,address,joints=joints,record_bytes=20)


def _animation(source,address,*,joints,record_bytes):
    raw, header = resource(source, address, size=record_bytes, pointers=True)
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
        track=dict(first_key=cursor, keys=length, first_frame=frames[0], last_frame=frames[-1])
        # Both actual cKF_KeyCalc consumers clamp against the first/last keys,
        # then scan for the FIRST subsequent key strictly beyond the frame.
        # Repeated, descending, or out-of-duration keys are not an array overrun:
        # if neither clamp returned, the last key necessarily ends that scan.
        # Real donor motions contain all three. Sorting/deduplicating or clipping
        # them changes the curve, so preserve every source key and its order.
        irregular=dict(repeated=any(a==b for a,b in zip(frames,frames[1:])),
            descending=any(a>b for a,b in zip(frames,frames[1:])),
            outside_duration=any(f<1 or f>duration for f in frames))
        if any(irregular.values()):track['retained_source_frames']=irregular
        tracks.append(track)
        cursor += length
    # cKF_KeyCalc uses signed 16-bit start and length arguments on N64.
    if cursor > 32767:
        raise ValueError('Keyframe traversal exceeds native signed-index capacity')
    return dict(header=header, arrays=receipts, joints=count, duration=duration,
                tracks=tracks, keyed_channels=keyed, constant_channels=3+3*count-keyed)


def npc_motion(source,address,*,joints=None):
    """A complete NPC motion embeds the keyframe plus 44 bytes of controls.

    This form covers motions without separate face/effect/audio programmes,
    including the cane. Dependent programmes reject rather than disappear.
    The entire source suffix is retained, not replaced with default timing.
    """
    row=_animation(source,address,joints=joints,record_bytes=64)
    raw=source.data[address:address+64]
    if (source.pointers(address+20,44) or any(raw[at:at+4]!=bytes(4) for at in (36,44,56,60))):
        raise ValueError('NPC motion requires explicit face/effect/audio programme conversion')
    start,end,mode,morph=struct.unpack_from('>ffif',raw,20)
    eye,eye_stop,mouth,mouth_stop,feel_frame,feel=(
        *struct.unpack_from('>hh',raw,40),*struct.unpack_from('>hhhh',raw,48))
    if (not all(math.isfinite(v) for v in (start,end,morph)) or mode not in (0,1) or
            not 0<=start<=end<=row['duration'] or eye!=0 or mouth!=0 or eye_stop or mouth_stop or
            feel_frame!=-1 or feel!=-1):
        raise ValueError('Unsupported complete NPC motion controls')
    row['npc']=dict(start=start,end=end,mode=mode,morph=morph,
        eye_type=eye,eye_stop=eye_stop,mouth_type=mouth,mouth_stop=mouth_stop,
        feel_frame=feel_frame,feel=feel,dependent_programmes=False)
    return row


def npc_expression_motion(source,address,*,joints=None):
    """Complete NPC curves with fixed eye/mouth programmes and scalar effects.

    Preserve all sixty-four control bytes and every expression frame. Separate
    effect/audio programmes still require their own converter. The installer
    must map nonnegative source effect identities before native admission.
    """
    row=_animation(source,address,joints=joints,record_bytes=64)
    raw=source.data[address:address+64];pointers=source.pointers(address+20,44)
    if set(pointers)-{address+36,address+44}:
        raise ValueError('NPC expression motion has unsupported dependent programmes')
    if any(raw[at:at+4]!=bytes(4) for at in (36,44,56,60)):
        raise ValueError('NPC expression motion has unexpected pointer storage')
    start,end,mode,morph=struct.unpack_from('>ffif',raw,20)
    eye,eye_stop,mouth,mouth_stop,feel_frame,feel=(
        *struct.unpack_from('>hh',raw,40),*struct.unpack_from('>hhhh',raw,48))
    if (not all(math.isfinite(v) for v in (start,end,morph)) or mode not in (0,1) or
            not 0<=start<=end<=row['duration'] or eye not in (-1,0,1,2) or
            mouth not in (-1,0,1,2) or not -1<=eye_stop<8 or not -1<=mouth_stop<8 or
            feel_frame < -1 or feel < -1):
        raise ValueError('Unsupported complete NPC expression controls')
    expressions={}
    for label,offset in (('eye',36),('mouth',44)):
        if address+offset not in pointers:
            sequence=eye if label=='eye' else mouth
            stop=eye_stop if label=='eye' else mouth_stop
            # Positive sequences use the native random-blink/talking tables;
            # -1 is a valid unused stop frame, not a missing fixed programme.
            # Mouth -1 falls back to neutral when not talking. A stopped eye,
            # in contrast, actually indexes its stop texture and must be valid.
            if sequence<0 or (label=='eye' and sequence==0 and stop<0):
                raise ValueError('Invalid unprogrammed NPC expression sequence/stop')
            continue
        data,receipt=resource(source,pointers[address+offset])
        if len(data)<row['duration'] or any(value>7 for value in data):
            raise ValueError('Incomplete or unrepresentable NPC expression programme')
        expressions[label]=receipt
    row['npc_expressions']=dict(start=start,end=end,mode=mode,morph=morph,
        eye_type=eye,eye_stop=eye_stop,mouth_type=mouth,mouth_stop=mouth_stop,
        feel_frame=feel_frame,source_effect=feel,programmes=expressions,
        native_effect_mapping_required=feel>=0)
    return row


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


def compile_animations(source, descriptions, *, start=0,address_base=SEGMENT):
    """Pack complete arrays once and relocate headers into one native object."""
    if (not descriptions or type(start) is not int or not 0 <= start < 0x1000000 or start % 16 or
            type(address_base) is not int or address_base&15 or not 0<=address_base<=0xFFFFFFFF-start):
        raise ValueError('No checked animations or invalid object offset')
    checked = {}
    for row in descriptions:
        at = row['header']['donor_offset']
        describe=(npc_expression_motion if 'npc_expressions' in row else
            npc_motion if 'npc' in row else animation)
        if at in checked or row != describe(source, at, joints=row['joints']):
            raise ValueError('Duplicate or changed animation description')
        checked[at] = row
    output, offsets, arrays = bytearray(), {}, []
    resources={r['donor_offset'] for row in checked.values() for r in row['arrays'].values() if r}
    resources.update(r['donor_offset'] for row in checked.values()
        for r in row.get('npc_expressions',{}).get('programmes',{}).values())
    for at in sorted(resources):
        raw, receipt = resource(source, at)
        output.extend(bytes(-len(output)%4)); offsets[at] = start+len(output)
        output.extend(raw)
        arrays.append(dict(**receipt, native_offset=offsets[at], output_sha256=sha256(raw)))
    headers, relocations = [], []
    for at, row in sorted(checked.items()):
        raw, _ = resource(source, at, size=64 if 'npc' in row or 'npc_expressions' in row else 20, pointers=True)
        fixed = bytearray(raw)
        output.extend(bytes(-len(output)%4)); header_at = start+len(output)
        for i, label in enumerate(CHANNELS):
            if row['arrays'][label] is None:
                continue
            target = offsets[row['arrays'][label]['donor_offset']]
            if address_base+target>0xFFFFFFFF:raise ValueError('Animation pointer overflows its address space')
            struct.pack_into('>I', fixed, i*4, address_base+target)
            relocations.append(dict(offset=header_at+i*4, target_offset=target))
        for label,offset in (('eye',36),('mouth',44)):
            programme=row.get('npc_expressions',{}).get('programmes',{}).get(label)
            if programme:
                target=offsets[programme['donor_offset']]
                if address_base+target>0xFFFFFFFF:raise ValueError('Expression pointer overflows its address space')
                struct.pack_into('>I',fixed,offset,address_base+target)
                relocations.append(dict(offset=header_at+offset,target_offset=target))
        output.extend(fixed)
        headers.append(dict(**row['header'], native_offset=header_at, output_sha256=sha256(fixed),
                            joints=row['joints'], duration=row['duration']))
    output.extend(bytes(-len(output)%16))
    if start+len(output) >= 0x1000000 or address_base+start+len(output)>0x100000000:
        raise ValueError('Animation object exceeds a segmented address range')
    return bytes(output), dict(arrays=arrays, headers=headers, relocations=relocations,
                              segment=address_base, runtime_installed=False)


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
