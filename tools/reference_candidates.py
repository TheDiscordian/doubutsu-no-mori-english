#!/usr/bin/env python3
"""Build auditable local candidates; never label a mechanical match reviewed."""

import argparse
from collections import Counter
import json
from pathlib import Path

from aflib import CODE_VROM, by_vrom, sha256, verified_rom
from font import make_halfwidth
from gc_adapter import adapt_reference
from textbanks import banks
from textcodec import TAG, command_info, encode
from textvalidate import expanded_bound, layout_issues, validate_entry
from runtime_module import MODULE_COMMANDS, add_runtime_module, module_command_info
from reference_matches import load_matches, resolve_reference, verify_native_equivalents
from reference_sequences import load_sequences, reference_sequence_edits
from name_candidates import npc_candidates
from item_candidates import item_candidates
from controller_adaptations import adapt_controller_reference, validate_controller_candidate
from reference_choices import adapt_choice_reference, validate_choice_candidate
from reference_actor_requests import adapt_actor_request_reference, validate_actor_request_candidate
from reference_fields import (field_permit, verify_field_reference, catchphrase_permit,
                              verify_catchphrase_reference)
from item_aliases import confirmed_aliases, update_alias_reports
from message_aliases import confirmed_message_aliases
from dialogue_dates import requires_dialogue_dates
from reference_animations import animation_permit, verify_animation_reference, verify_native_consumer
from reference_content import adapt_content_reference, validate_content_candidate
from placeholder_text import placeholder_edit
from reference_mail_fragments import load_fragment_matches, reference_fragment_edits
from contextual_choices import load_contextual_choices, contextualize_edits

REFERENCE_BANKS = ("message", "select", "string", "mail", "super", "ps",
                   "maila", "mailb", "mailc", "psz", "superz")


def load_drafts(paths):
    drafts = []
    for path in paths:
        rows = json.loads(path.read_text())
        if not isinstance(rows, list):
            raise ValueError("Original translations must be a list")
        drafts.extend(rows)
    ids = [row["id"] for row in drafts]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate original translation ID")
    return drafts


def draft_module_commands(text):
    """Recognise actual extension tokens, rejecting unsupported or malformed ones."""
    info = [(0, 0)] * 0x77
    for code, descriptor in MODULE_COMMANDS.items():
        info[code] = descriptor
    commands = set()
    for match in TAG.finditer(text):
        if match[1] != 'cmd':
            continue
        data = bytes.fromhex(match[2])
        if len(data) >= 2 and data[0] == 0x7f and data[1] > 0x60:
            encode(match[0], info)
            commands.add(f'7F{data[1]:02X}')
    return sorted(commands)


def select_drafts(drafts, *, english_dialogue_dates=False, resident_runtime=False):
    selected, withheld = [], []
    for edit in drafts:
        needs_dates = requires_dialogue_dates(edit)
        commands = draft_module_commands(edit['translation'])
        if needs_dates and not english_dialogue_dates:
            withheld.append({'id': edit['id'], 'reason': 'runtime_requirement_unavailable',
                             'runtime_requirements': edit['runtime_requirements']})
        elif commands and not resident_runtime:
            withheld.append({'id': edit['id'], 'reason': 'resident_runtime_unavailable',
                             'module_commands': commands})
        else:
            selected.append(edit)
    return selected, withheld


def record_candidate(edit, info, advances, name, edits, manifests, counts, *, resident_runtime=False):
    candidate = encode(edit["translation"], info)
    policy = edit["control_policy"]
    issues = layout_issues(candidate, info, advances, resident_runtime=resident_runtime) if name == "message" else []
    manifest = {k: v for k, v in edit.items() if k != "translation"}
    manifest.update(encoded_sha256=sha256(candidate), encoded_bytes=len(candidate),
                    layout_issues=issues,
                    expanded_bound=expanded_bound(candidate, info) if name == "message" else len(candidate))
    edits.append(edit)
    manifests.append(manifest)
    counts["accepted_candidates"] += 1
    counts["adapted_candidates"] += bool(edit.get("adaptations"))
    counts["text_field_delivery_candidates"] += policy == "reference_text"
    counts["reference_page_delivery_candidates"] += policy == "reference_delivery"
    counts["reference_layout_candidates"] += policy == "reference_layout"
    counts["reviewed_sequence_candidates"] += policy == "reviewed_sequence"
    counts["layout_review_required"] += bool(issues)


def native_placeholder_fallback(row, original, info, *, skip_ids):
    """Explicit matches and complete sequences retain their own approval path."""
    if row['id'] in skip_ids:
        return None
    edit = placeholder_edit(row['id'], original, info)
    if edit is not None:
        if row['source_sha256'] != edit['source_sha256']:
            raise ValueError('Stale placeholder inventory')
        validate_entry(original, encode(edit['translation'], info), info, 'message', 'exact')
    return edit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--gc-text", type=Path, default=Path("build/gamecube/text"))
    parser.add_argument("--gc-names", type=Path, default=Path("build/gamecube/names"))
    parser.add_argument("--inventory", type=Path, default=Path("build/inventory"))
    parser.add_argument("--drafts", type=Path, action="append", help="Repeat to select explicit original-edit files")
    parser.add_argument("--matches", type=Path, default=Path("translations/reference_matches.json"))
    parser.add_argument("--output", type=Path, default=Path("build/candidates"))
    parser.add_argument("--english-runtime", action="store_true")
    parser.add_argument("--runtime-module", type=Path)
    parser.add_argument('--english-dialogue-dates', action='store_true',
                        help='Include drafts requiring English resident-date preparation')
    args = parser.parse_args()
    if args.english_dialogue_dates and not args.runtime_module:
        parser.error('--english-dialogue-dates requires --runtime-module')
    rom = verified_rom(args.rom.read_bytes())
    info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    choice_bytes = 16 if args.english_runtime else 10
    if args.runtime_module:
        _, module_report = add_runtime_module(rom, {}, args.runtime_module)
        if args.english_runtime:
            choice_bytes = module_report["choice_layout"]["capacity"]
        info = module_command_info(rom)
    _, font_report = make_halfwidth(rom)
    advances = {int(k, 16): v for k, v in font_report["advance_by_glyph"].items()}
    source_banks = {bank.name: bank for bank in banks(rom)}
    drafts = load_drafts(args.drafts or [Path("translations/opening.json"), Path("translations/n64-exercise.json"),
                                       Path("translations/n64-intro-jobs.json"),
                                       Path("translations/n64-shop-menus.json"),
                                       Path("translations/n64-advice-travel.json"),
                                       Path("translations/n64-festivals.json"),
                                       Path("translations/n64-seasonal-conversations.json"),
                                       Path("translations/n64-town-advice.json"),
                                       Path("translations/n64-community-conversations.json"),
                                       Path("translations/n64-native-context.json"),
                                       Path("translations/n64-pak-storage-dialogue.json"),
                                       Path("translations/n64-carp-fireworks.json"),
                                       Path("translations/n64-service-save-dialogue.json"),
                                       Path("translations/n64-seasonal-topics.json"),
                                       Path("translations/n64-startup-pak.json"),
                                       Path("translations/n64-startup-greetings.json"),
                                       Path("translations/n64-resident-gaps.json"),
                                       Path("translations/n64-gyroid-charm-dialogue.json"),
                                       Path("translations/n64-letter-fragments.json"),
                                       Path("translations/n64-native-menus.json"),
                                       Path("translations/n64-contextual-choice-replies.json"),
                                       Path("translations/n64-return-greetings.json")])
    override_ids = {r["id"] for r in drafts if not r.get("reference_fallback", False)}
    drafts, withheld_drafts = select_drafts(drafts, english_dialogue_dates=args.english_dialogue_dates,
                                           resident_runtime=bool(args.runtime_module))
    matches = load_matches(args.matches)
    fragment_matches = load_fragment_matches()
    fragment_references, fragment_inventory = {}, {}
    for name in ('maila', 'mailb', 'mailc'):
        fragment_references.update({r['id']: r for r in map(json.loads,
            (args.gc_text/(name+'.jsonl')).read_text().splitlines())})
        fragment_inventory.update({r['id']: r for r in map(json.loads,
            (args.inventory/(name+'.jsonl')).read_text().splitlines())})
    fragments = reference_fragment_edits(fragment_matches,
        {name: bank.entries() for name, bank in source_banks.items()},
        fragment_references, fragment_inventory, info)
    sequence_members = {m['id'] for group in load_sequences().values() for m in group['members']}
    if fragments.keys() & (override_ids | matches.keys() | sequence_members):
        raise ValueError('Mail-fragment reference conflicts with another approval or draft')
    if any('resident_animations' in record for record in matches.values()):
        verify_native_consumer(rom)
    verify_native_equivalents(matches, source_banks)
    visited_matches = set()
    if override_ids & matches.keys():
        raise ValueError("Reviewed reference match conflicts with an original draft override")
    edits, manifests, reports = [], [], {}
    for name in REFERENCE_BANKS:
        gc = {row["id"]: row for row in map(json.loads, (args.gc_text/(name+".jsonl")).read_text().splitlines())}
        inventory = [json.loads(line) for line in (args.inventory/(name+".jsonl")).read_text().splitlines()]
        source = source_banks[name].entries()
        sequence_edits, permits = (reference_sequence_edits(gc, source, info,
                                  resident_runtime=bool(args.runtime_module)) if name == "message" else ([], {}))
        sequences = {edit["id"]: edit for edit in sequence_edits}
        if sequences.keys() & (override_ids | matches.keys()):
            raise ValueError("Reviewed sequence conflicts with a draft or identity override")
        if sequences.keys() - {row["id"] for row in inventory}:
            raise ValueError("Reviewed sequence is absent from the inventory")
        if name == 'message' and fragments.keys() - {row['id'] for row in inventory}:
            raise ValueError('Reviewed mail fragment is absent from the inventory')
        counts, review = Counter(), []
        for row in inventory:
            id = row["id"]
            if id in override_ids:
                counts["original_draft_override"] += 1
                continue
            original = source[int(id.split(":")[1], 16)]
            if id in fragments:
                edit = fragments[id]
                if row['source_sha256'] != edit['source_sha256']:
                    raise ValueError('Stale mail-fragment main inventory')
                counts['cross_bank_mail_fragments'] += 1
            elif id in sequences:
                edit = sequences[id]
                if row["source_sha256"] != edit["source_sha256"]:
                    raise ValueError("Stale sequence inventory")
                text, policy, adaptations = edit["translation"], edit["control_policy"], edit["adaptations"]
                candidate = encode(text, info)
                validate_entry(original, candidate, info, name, policy, choice_bytes=choice_bytes,
                               resident_runtime=bool(args.runtime_module), sequence_permit=permits[id])
            else:
                reference, match_basis, reason = resolve_reference(row, gc, matches, original)
                if id in matches:
                    visited_matches.add(id)
                if reason is None:
                    try:
                        reference_text, actor_edits = adapt_actor_request_reference(reference, original, matches.get(id), info)
                        reference_text, choice_edits = adapt_choice_reference(
                            {**reference, "text": reference_text}, original, matches.get(id), info)
                        reference_text, controller_edits = adapt_controller_reference(
                            {**reference, "text": reference_text}, original, matches.get(id), info)
                        added_fields = matches.get(id, {}).get("available_fields")
                        added_catchphrase = matches.get(id, {}).get("speaker_catchphrase")
                        animations = matches.get(id, {}).get('resident_animations')
                        verify_field_reference(reference, original, matches.get(id), info)
                        verify_catchphrase_reference(reference, original, matches.get(id), info)
                        verify_animation_reference(reference, original, matches.get(id), info)
                        reference_text, content_edits = adapt_content_reference(
                            {**reference, 'text': reference_text}, original, matches.get(id), info)
                        policy = "reference_layout" if added_fields or added_catchphrase or animations else "presentation"
                        try:
                            text, adaptations = adapt_reference(reference_text, original, info, policy,
                                                                resident_runtime=bool(args.runtime_module),
                                                                retain_resident_animations=bool(animations))
                            candidate = encode(text, info)
                            validate_entry(original, candidate, info, name, policy,
                                           choice_bytes=choice_bytes,
                                           resident_runtime=bool(args.runtime_module),
                                           field_permit=field_permit(id, original, candidate, matches),
                                           catchphrase_permit=catchphrase_permit(id, original, candidate, matches),
                                           animation_permit=animation_permit(id, original, candidate, matches))
                        except ValueError as exc:
                            if added_fields or added_catchphrase or animations or name != "message" or str(exc) != "Control signature changed":
                                raise
                            for policy in ("reference_text", "reference_delivery", "reference_layout"):
                                try:
                                    text, adaptations = adapt_reference(reference_text, original, info, policy,
                                                                        resident_runtime=bool(args.runtime_module))
                                    candidate = encode(text, info)
                                    validate_entry(original, candidate, info, name, policy,
                                                   choice_bytes=choice_bytes,
                                                   resident_runtime=bool(args.runtime_module))
                                    break
                                except ValueError as exc:
                                    if policy == "reference_layout" or str(exc) != "Control signature changed":
                                        raise
                        validate_controller_candidate(id, original, candidate, matches)
                        validate_choice_candidate(id, original, candidate, matches)
                        validate_actor_request_candidate(id, original, candidate, matches)
                        validate_content_candidate(id, original, candidate, matches)
                        adaptations = actor_edits+choice_edits+controller_edits+content_edits+adaptations
                        if added_fields:
                            adaptations.append({"operation": "use_reviewed_current_player_town_fields",
                                                "commands": added_fields["commands"]})
                        if added_catchphrase:
                            adaptations.append({"operation": "use_reviewed_resident_catchphrase",
                                                "context": added_catchphrase["context"], "commands": ["1C"]})
                        if animations:
                            adaptations.append({'operation': 'retain_reviewed_resident_animations',
                                                'context': animations['context'], 'command': '7F0900'})
                    except ValueError as exc:
                        reason = str(exc)
                if reason:
                    counts["rejected"] += 1
                    review.append({"id": id, "reason": reason})
                    continue
                edit = {"id": id, "source_sha256": row["source_sha256"],
                        "translation": text, "control_policy": policy,
                        "provenance": {"source": "user-supplied GAFE01 revision 0 disc",
                                       "reference_id": reference["id"], "reference_sha256": reference["sha256"],
                                       "match_basis": match_basis},
                        "status": "mechanically_validated_candidate_not_reviewed", "adaptations": adaptations}
            record_candidate(edit, info, advances, name, edits, manifests, counts, resident_runtime=bool(args.runtime_module))
        if name == "message":
            aliases, conflicts = confirmed_message_aliases(source, edits, gc, info,
                skip_ids=override_ids | matches.keys() | fragments.keys(), resident_runtime=bool(args.runtime_module))
            for edit in aliases:
                rejected = [row for row in review if row["id"] == edit["id"]]
                if len(rejected) != 1:
                    raise ValueError("Message alias is not a unique previously rejected record")
                review.remove(rejected[0])
                counts["rejected"] -= 1
                record_candidate(edit, info, advances, name, edits, manifests, counts, resident_runtime=bool(args.runtime_module))
            # Preserve valid English reference labels, including confirmed native
            # aliases, before translating the remaining exact native labels.
            inventory_by_id = {row['id']: row for row in inventory}
            unresolved, placeholder_ids = [], set()
            for rejected in review:
                row = inventory_by_id[rejected['id']]
                original = source[int(row['id'].split(':')[1], 16)]
                fallback = native_placeholder_fallback(row, original, info,
                           skip_ids=sequence_members | matches.keys())
                if fallback is None:
                    unresolved.append(rejected)
                    continue
                record_candidate(fallback, info, advances, name, edits, manifests, counts,
                                 resident_runtime=bool(args.runtime_module))
                counts['native_placeholder_labels'] += 1
                counts['rejected'] -= 1
                placeholder_ids.add(row['id'])
            review = unresolved
            conflicts = [row for row in conflicts if row['id'] not in placeholder_ids]
            counts["confirmed_native_aliases"] = len(aliases)
            counts["native_alias_conflicts"] = len(conflicts)
            args.output.mkdir(parents=True, exist_ok=True)
            (args.output/"message-alias-conflicts.jsonl").write_text("".join(json.dumps(r)+"\n" for r in conflicts))
        reports[name] = {**dict(counts), "source_entries": len(source),
                         "remaining_by_reason": dict(Counter(r["reason"] for r in review))}
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output/(name+"-remaining.jsonl")).write_text("".join(json.dumps(r)+"\n" for r in review))
    name_edits, name_manifests, name_remaining, name_report = npc_candidates(
        source_banks["npc_names"],
        list(map(json.loads, (args.inventory/"npc_names.jsonl").read_text().splitlines())),
        list(map(json.loads, (args.gc_names/"npc_names.jsonl").read_text().splitlines())),
        info, override_ids)
    edits.extend(name_edits)
    manifests.extend(name_manifests)
    reports["npc_names"] = name_report
    (args.output/"npc_names-remaining.jsonl").write_text("".join(json.dumps(r)+"\n" for r in name_remaining))
    item_remaining_by_bank = {}
    for name, bank in source_banks.items():
        if not name.startswith("item_"):
            continue
        reference_name = "furniture" if name == "item_10" else name
        item_edits, item_manifests, item_remaining, item_report = item_candidates(
            bank, list(map(json.loads, (args.inventory/(name+".jsonl")).read_text().splitlines())),
            list(map(json.loads, (args.gc_names/(reference_name+".jsonl")).read_text().splitlines())),
            info, override_ids)
        edits.extend(item_edits)
        manifests.extend(item_manifests)
        reports[name] = item_report
        item_remaining_by_bank[name] = item_remaining
    aliases = confirmed_aliases(source_banks, edits, info, skip_ids=override_ids)
    update_alias_reports(edits, aliases, item_remaining_by_bank, reports)
    edits.extend(aliases)
    for edit in aliases:
        encoded = encode(edit["translation"], info)
        manifest = {k: v for k, v in edit.items() if k != "translation"}
        manifest.update(encoded_bytes=len(encoded), encoded_sha256=sha256(encoded), stored_bytes=10,
                        stored_sha256=sha256(encoded.ljust(10, b" ")), layout_issues=[], expanded_bound=len(encoded))
        manifests.append(manifest)
    for name, remaining in item_remaining_by_bank.items():
        (args.output/(name+"-remaining.jsonl")).write_text("".join(json.dumps(r)+"\n" for r in remaining))
    if matches.keys()-visited_matches:
        raise ValueError(f"Reviewed references are absent from the inventory: {matches.keys()-visited_matches}")
    selected = {edit["id"] for edit in edits}
    edits += [edit for edit in drafts if edit["id"] not in selected]
    before_context = {edit['id']: edit for edit in edits}
    edits, context_ids, context_withheld = contextualize_edits(
        edits, source_banks['message'].entries(), source_banks['select'].entries(),
        load_contextual_choices(matches), info)
    context_removed = {r['id'] for r in context_withheld}
    contextual_ids = set(context_ids) | context_removed
    manifests = [m for m in manifests if m['id'] not in contextual_ids]
    for id in sorted(contextual_ids):
        previous_counts = Counter()
        record_candidate(before_context[id], info, advances, 'message', [], [], previous_counts,
                         resident_runtime=bool(args.runtime_module))
        for key, value in previous_counts.items():
            reports['message'][key] -= value
    for edit in edits:
        if edit['id'] in context_ids:
            current_counts = Counter()
            record_candidate(edit, info, advances, 'message', [], manifests, current_counts,
                             resident_runtime=bool(args.runtime_module))
            for key, value in current_counts.items():
                reports['message'][key] += value
    reports['message']['contextual_choice_candidates'] = len(context_ids)
    if context_withheld:
        remaining_path = args.output/'message-remaining.jsonl'
        remaining = list(map(json.loads, remaining_path.read_text().splitlines()))
        remaining.extend(context_withheld)
        reports['message']['rejected'] += len(context_withheld)
        reports['message']['remaining_by_reason'] = dict(Counter(r['reason'] for r in remaining))
        remaining_path.write_text(''.join(json.dumps(r)+'\n' for r in remaining))
    (args.output/"translations.json").write_text(json.dumps(edits, ensure_ascii=False, indent=2)+"\n")
    (args.output/'drafts-withheld.json').write_text(json.dumps(withheld_drafts, indent=2)+'\n')
    (args.output/"manifest.json").write_text(json.dumps(manifests, indent=2)+"\n")
    (args.output/"summary.json").write_text(json.dumps(reports, indent=2)+"\n")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
