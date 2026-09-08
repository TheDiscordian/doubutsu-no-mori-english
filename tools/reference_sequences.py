"""Exact, all-or-nothing approvals for reviewed dialogue sequences."""

from dataclasses import dataclass
import json
from pathlib import Path
import re

from aflib import sha256
from textcodec import decode, encode, tokenize
from native_sequences import source_kind, validate_native_group, native_reference, audit_native_translation
from sequence_prices import validate_price_group, audit_native_price, adapt_reference_price

APPROVALS = Path(__file__).resolve().parents[1]/"translations/reference_sequences.json"
# Native font consumers and argument constraints are audited in REFERENCE_LAYOUT.
PRESENTATION = {0x02, 0x03, 0x04, 0x05, 0x50, 0x52, 0x53, 0x54, 0x5A}
ACTOR = set(range(0x08, 0x0D))
FIELDS = set(range(0x1A, 0x30)) | set(range(0x31, 0x40)) | {0x76}


@dataclass(frozen=True)
class SequencePermit:
    sequence: str
    source_sha256: str
    encoded_sha256: str


def load_sequences(path=APPROVALS):
    records = json.loads(path.read_text())
    if not isinstance(records, list):
        raise ValueError("Reference sequences must be a list")
    result, seen = {}, set()
    for record in records:
        if (not re.fullmatch(r"[a-z][a-z0-9_]*", record.get("id", ""))
                or record["id"] in result or not record.get("evidence", "").strip()):
            raise ValueError("Duplicate, invalid, or unexplained reference sequence")
        members = record.get("members")
        if type(record.get('requires_resident_runtime', False)) is not bool:
            raise ValueError('Invalid sequence resident-runtime requirement')
        if ('retain_reference_sound_triggers' in record
                and record['retain_reference_sound_triggers'] is not True):
            raise ValueError('Sequence sound-trigger permission must be explicitly true')
        if 'timed_end' in record and record['timed_end'] != '7F5808':
            raise ValueError('Only the reviewed native timed ending is supported')
        if (('retain_reference_sound_triggers' in record or 'timed_end' in record)
                and source_kind(record) != 'gamecube'):
            raise ValueError('Sound/timed-ending permissions require a complete GameCube reference')
        if not isinstance(members, list) or not 1 <= len(members) <= 16:
            raise ValueError("Reference sequence requires one to sixteen members")
        for member in members:
            if type(member.get('remove_redundant_cutarticle', False)) is not bool:
                raise ValueError('Invalid sequence article-suppression requirement')
            if (not re.fullmatch(r"message:[0-9A-F]{4}", member.get("id", ""))
                    or member["id"] in seen):
                raise ValueError("Duplicate or invalid sequence member")
            if not re.fullmatch(r"message:[0-9A-F]{4}", member.get("reference_id", member["id"])):
                raise ValueError("Invalid sequence reference ID")
            if "reference_slice" in member:
                span = member["reference_slice"]
                if (not isinstance(span, list) or len(span) != 2 or any(type(n) is not int for n in span)
                        or not 0 <= span[0] < span[1]):
                    raise ValueError("Invalid reference sequence slice")
            for key in ("source_sha256", "reference_sha256", "encoded_sha256"):
                if not re.fullmatch(r"[0-9a-f]{64}", member.get(key, "")):
                    raise ValueError("Invalid reference sequence hash")
            seen.add(member["id"])
        actor_sources = record.get('actor_sources',[])
        if not isinstance(actor_sources,list) or len(actor_sources) > 8:
            raise ValueError('Invalid additional actor-source approvals')
        for actor_source in actor_sources:
            if (not isinstance(actor_source,dict) or set(actor_source) != {'id','source_sha256','commands'}
                    or not re.fullmatch(r'message:[0-9A-F]{4}',actor_source.get('id',''))
                    or not re.fullmatch(r'[0-9a-f]{64}',actor_source.get('source_sha256',''))
                    or not isinstance(actor_source.get('commands'),list) or not actor_source['commands']
                    or any(not isinstance(c,str) or not re.fullmatch(r'7F090000[0-9A-F]{2}',c)
                           for c in actor_source['commands'])):
                raise ValueError('Additional actor approvals require exact native speaker emotion commands')
        validate_native_group(record)
        validate_price_group(record)
        result[record["id"]] = record
    return result


def commands(data, info):
    return [t.data for t in tokenize(data, info) if t.kind == "cmd"]


def message_targets(data, info):
    for cmd in commands(data, info):
        if 0x0E <= cmd[1] <= 0x15:
            for at in range(2, len(cmd), 2):
                yield int.from_bytes(cmd[at:at+2], "big")


def normalize_assignments(cmds):
    """Branch slots are assignments, not execution-order-dependent jumps."""
    result, pending = [], []
    for cmd in [*cmds, None]:
        if cmd is not None and 0x0F <= cmd[1] <= 0x12:
            if any(item[1] == cmd[1] for item in pending):
                raise ValueError("Repeated conditional branch assignment")
            pending.append(cmd)
        else:
            result.extend(sorted(pending, key=lambda item: item[1]))
            pending = []
            if cmd is not None:
                result.append(cmd)
    return result


def audit_sequence(original, replacements, member_numbers, info, extra_actor=(), *, resident_runtime=False,
                   retain_reference_sound_triggers=False, timed_end=None):
    """Check semantics independently of the approved payload hashes."""
    if type(retain_reference_sound_triggers) is not bool:
        raise ValueError('Invalid sequence sound-trigger permission')
    root = commands(original, info)
    ending = bytes.fromhex(timed_end) if timed_end == '7F5808' else original[-2:]
    end_codes = (0, 1, 0x58)
    if (timed_end not in (None, '7F5808') or not root or root[-1] != ending
            or not original.endswith(ending) or sum(c[1] in end_codes for c in root) != 1
            or timed_end is None and ending not in (b"\x7f\x00", b"\x7f\x01")):
        raise ValueError("Sequence root must have one final terminator")
    available_fields = {c[1] for c in root if c[1] in FIELDS}
    # The existing English hour formatter prepares AM/PM for this same record.
    # No actor-prepared field or cross-record clock state is inherited here.
    if resident_runtime and 0x21 in available_fields:
        available_fields.add(0x76)
    available_actor = {c for c in root if c[1] in ACTOR} | set(extra_actor)
    translated = []
    for index, data in enumerate(replacements):
        part = commands(data, info)
        terminator = b"\x7f\x01" if index+1 < len(replacements) else ending
        if not part or part[-1] != terminator or not data.endswith(terminator) or sum(c[1] in end_codes for c in part) != 1:
            raise ValueError("Sequence part changes the required final/continuing terminator")
        links = [c for c in part if c[1] == 0x0E]
        expected = ([b"\x7f\x0e"+member_numbers[index+1].to_bytes(2, "big")]
                    if index+1 < len(replacements) else [c for c in root if c[1] == 0x0E])
        if links != expected or index+1 < len(replacements) and part[-2] != expected[0]:
            raise ValueError("Sequence continuation link changed")
        if any(c[1] in FIELDS and c[1] not in available_fields for c in part):
            raise ValueError("Sequence requests an unavailable text field")
        hour_seen = False
        pacing_locked = False
        for command in part:
            if command[1] == 0x21:
                hour_seen = True
            elif command[1] == 0x76 and (not resident_runtime or not hour_seen):
                raise ValueError('Sequence AM/PM requires a preceding hour in the same resident-runtime record')
            if command[1] in (0x72, 0x73):
                if not resident_runtime or (command[1] == 0x72) == pacing_locked:
                    raise ValueError('Sequence pacing requires a balanced resident-runtime span')
                pacing_locked = command[1] == 0x72
        if pacing_locked:
            raise ValueError('Sequence pacing span crosses a message boundary')
        if any(c[1] in ACTOR and c not in available_actor for c in part):
            raise ValueError("Sequence requests a new actor argument")
        translated.extend(c for c in part if c[1] != 0x0E or index+1 == len(replacements))
    # Complete reference presentation may repeat/reposition only the speaker's
    # existing expressions. Quest, mood, duration, handoff, and other actor
    # requests must retain their exact original order and multiplicity.
    actor_requests = lambda cmds: [c for c in cmds if c[1] in ACTOR and c[:3] != b'\x7f\x09\x00']
    if actor_requests(root) != actor_requests(translated):
        raise ValueError('Sequence changes a non-expression actor request')
    if retain_reference_sound_triggers:
        # These are separate audible cues, not idempotent state assignments.
        # Keep every cue in the full approved English; allow only repetitions
        # of native Resetti cues in the same actor/action interval.
        def sound_intervals(cmds):
            result = []
            for cmd in cmds:
                if cmd[1] in PRESENTATION | FIELDS | {0, 1}:
                    continue
                if cmd[1] == 0x59:
                    if cmd not in (b'\x7f\x59\x05', b'\x7f\x59\x06'):
                        raise ValueError('Sequence sound cue is outside the reviewed native pair')
                    if result and result[-1] == cmd:
                        continue
                result.append(cmd)
            return normalize_assignments(result)
        if not any(c[1] == 0x59 for c in root) or sound_intervals(root) != sound_intervals(translated):
            raise ValueError('Sequence sound cues change native actor/action intervals')
    # Existing capitalization and balanced protected-pacing implementation;
    # exact complete payload approvals and native cancellation controls remain.
    ignored = (PRESENTATION | ACTOR | FIELDS | {0x00, 0x01}
               | ({0x72, 0x73, 0x75} if resident_runtime else set())
               | ({0x59} if retain_reference_sound_triggers else set()))
    native_flow = normalize_assignments([c for c in root if c[1] not in ignored])
    translated_flow = normalize_assignments([c for c in translated if c[1] not in ignored])
    if native_flow != translated_flow:
        raise ValueError("Sequence gameplay commands changed")


def validate_sequences(edits, source, info, groups=None, *, resident_runtime=False):
    """Builder authority comes from repository approvals, never edit metadata."""
    groups = load_sequences() if groups is None else groups
    selected = {}
    for edit in edits:
        if edit.get("control_policy") == "reviewed_sequence" or "reference_sequence" in edit:
            group = edit.get("reference_sequence")
            if group not in groups or edit.get("control_policy") != "reviewed_sequence":
                raise ValueError("Unknown or invalid reviewed sequence request")
            if edit["id"] in selected:
                raise ValueError("Duplicate reviewed sequence member")
            selected[edit["id"]] = edit
    used = {edit["reference_sequence"] for edit in selected.values()}
    permits = {}
    for name in used:
        group = groups[name]
        if group.get('requires_resident_runtime', False) and not resident_runtime:
            raise ValueError('Reviewed sequence requires the resident runtime')
        members = group["members"]
        ids = {member["id"] for member in members}
        if ids != {id for id, edit in selected.items() if edit["reference_sequence"] == name}:
            raise ValueError("Partial or unexpected reference sequence members")
        numbers = [int(member["id"].split(":")[1], 16) for member in members]
        if any(n >= len(source) for n in numbers):
            raise ValueError("Reference sequence slot is absent from the native bank")
        replacements = []
        for member, number in zip(members, numbers):
            edit = selected[member["id"]]
            replacement = encode(edit["translation"], info)
            if (sha256(source[number]) != member["source_sha256"]
                    or edit.get("source_sha256") != member["source_sha256"]):
                raise ValueError("Stale reference sequence source or placeholder")
            if sha256(replacement) != member["encoded_sha256"]:
                raise ValueError("Reference sequence translated bytes changed")
            replacements.append(replacement)
        if source_kind(group) == 'native_original':
            audit_native_translation(group, source[numbers[0]], info)
            if replacements != reference_payloads(group, {}, info):
                raise ValueError('Native sequence parts do not reconstruct the complete original translation')
        audit_native_price(group, source[numbers[0]], info)
        reserved = set(numbers[1:])
        for number, data in enumerate(source):
            if reserved.intersection(message_targets(data, info)):
                raise ValueError(f"Native message {number:04X} targets a reserved sequence slot")
        extra_actor = set()
        for approval in group.get('actor_sources',[]):
            index = int(approval['id'].split(':')[1],16)
            if index >= len(source) or sha256(source[index]) != approval['source_sha256']:
                raise ValueError('Stale additional native actor source')
            supplied = commands(source[index],info)
            for value in approval['commands']:
                if not isinstance(value,str) or not re.fullmatch(r'7F090000[0-9A-F]{2}',value):
                    raise ValueError('Additional actor approval is not a native speaker emotion')
                command = bytes.fromhex(value)
                if command not in supplied:
                    raise ValueError('Additional actor command is absent from its native source')
                extra_actor.add(command)
        audit_sequence(source[numbers[0]], replacements, numbers, info, extra_actor,
                       resident_runtime=resident_runtime,
                       retain_reference_sound_triggers=group.get('retain_reference_sound_triggers', False),
                       timed_end=group.get('timed_end'))
        for member in members:
            permits[member["id"]] = SequencePermit(name, member["source_sha256"], member["encoded_sha256"])
    return permits


def reference_payloads(group, references, info):
    if source_kind(group) == 'native_original':
        whole = native_reference(group, info)
        references = {whole['id']: whole}
    members = group["members"]
    payloads, encoded_references = [], []
    for member in members:
        reference = references.get(member.get("reference_id", member["id"]))
        if not reference or reference.get("sha256") != member["reference_sha256"]:
            raise ValueError("Stale reviewed sequence reference")
        text = reference['text']
        reference_info = list(info)
        remove_article = member.get('remove_redundant_cutarticle', False)
        if type(remove_article) is not bool:
            raise ValueError('Invalid sequence article-suppression requirement')
        if remove_article:
            reference_info += [(0, 0)]*max(0, 0x75-len(reference_info))
            reference_info[0x74] = (2, 0)
        if sha256(encode(text, reference_info)) != member['reference_sha256']:
            raise ValueError('Sequence requires the exact complete encoded reference')
        text = adapt_reference_price(group, text, info)
        if remove_article:
            # Import at use time: the existing adapter also uses textvalidate,
            # whose sequence-permit type is defined in this module.
            from gc_adapter import remove_redundant_article_suppression
            text, changes = remove_redundant_article_suppression(text)
            if not changes:
                raise ValueError('Sequence article approval requires a redundant CUTARTICLE')
        encoded_references.append(encode(text, info))
    # Each reference may contribute one complete record or a contiguous group
    # of fully covering slices. This also handles a long final record after
    # earlier complete GameCube continuation records without dropping wording.
    used, index = set(), 0
    while index < len(members):
        first = members[index]
        reference_id = first.get('reference_id',first['id'])
        encoded = encoded_references[index]
        if reference_id in used:
            raise ValueError('Sequence reference is repeated outside its contiguous slices')
        used.add(reference_id)
        if 'reference_slice' not in first:
            payloads.append(encoded);index += 1;continue
        last = index+1
        while last < len(members) and members[last].get('reference_id',members[last]['id']) == reference_id:
            last += 1
        selected = members[index:last]
        if (any('reference_slice' not in member for member in selected)
                or any(data != encoded for data in encoded_references[index:last])
                or any(member['reference_sha256'] != first['reference_sha256']
                       or member.get('remove_redundant_cutarticle', False)
                       != first.get('remove_redundant_cutarticle', False) for member in selected)):
            raise ValueError('Sliced sequence requires the exact complete encoded reference')
        boundaries = {t.offset for t in tokenize(encoded,info)} | {len(encoded)}
        if selected[0]['reference_slice'][0] != 0 or selected[-1]['reference_slice'][1] != len(encoded):
            raise ValueError('Sequence slices do not cover the complete reference')
        for part_index,member in enumerate(selected):
            start,end = member['reference_slice']
            if start not in boundaries or end not in boundaries or not start < end:
                raise ValueError('Sequence slice cuts a reference token')
            part = encoded[start:end]
            if part_index+1 < len(selected):
                following = selected[part_index+1]
                next_start = following['reference_slice'][0]
                if next_start <= end or encoded[end:next_start] != b'\x7f\x04\xcd\x7f\x02':
                    raise ValueError('Sequence slice gap must be exactly one native wait/page boundary')
                number = int(following['id'].split(':')[1],16)
                part += b'\x7f\x0e'+number.to_bytes(2,'big')+b'\xcd\x7f\x01'
            payloads.append(part)
        index = last
    return payloads


def reference_sequence_edits(references, source, info, groups=None, *, resident_runtime=False):
    groups = load_sequences() if groups is None else groups
    edits = []
    for name, group in groups.items():
        if group.get('requires_resident_runtime', False) and not resident_runtime:
            continue
        payloads = reference_payloads(group, references, info)
        native = source_kind(group) == 'native_original'
        for member, payload in zip(group["members"], payloads):
            reference = (native_reference(group, info) if native else
                         references[member.get("reference_id", member["id"])])
            edits.append({"id": member["id"], "source_sha256": member["source_sha256"],
                          "translation": decode(payload, info), "control_policy": "reviewed_sequence",
                          "reference_sequence": name,
                          "provenance": {"source": "user-supplied GAFE01 revision 0 disc",
                                         "reference_id": reference["id"],
                                         "reference_sha256": reference["sha256"],
                                         "match_basis": "reviewed_sequence_identity"},
                          "status": "mechanically_validated_candidate_not_reviewed",
                          "adaptations": [{"kind": "reviewed_multi_message_sequence", "sequence": name}]})
            if native:
                edits[-1]['status'] = 'draft'
                edits[-1]['provenance'] = {
                    'source': 'original translation of the Japanese N64 record',
                    'native_id': reference['id'], 'draft_sha256': reference['sha256'],
                    'match_basis': 'complete_native_original_sequence'}
            if "reference_slice" in member:
                edits[-1]["provenance"]["draft_slice" if native else "reference_slice"] = member["reference_slice"]
            if member.get('remove_redundant_cutarticle', False):
                edits[-1]['adaptations'].append({'kind': 'remove_redundant_cutarticle_before_string'})
            if 'native_price' in group:
                edits[-1]['adaptations'].append({'kind': 'reviewed_native_invoice_price',
                                                **group['native_price']})
    return edits, validate_sequences(edits, source, info, groups, resident_runtime=resident_runtime)
