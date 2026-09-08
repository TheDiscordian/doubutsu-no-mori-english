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
from item_matches import load_matches as load_item_matches
from name_candidates import npc_candidates
from item_candidates import item_candidates
from controller_adaptations import adapt_controller_reference, validate_controller_candidate
from reference_choices import adapt_choice_reference, validate_choice_candidate
from reference_actor_requests import adapt_actor_request_reference, validate_actor_request_candidate
from reference_fields import (field_permit, verify_field_reference, catchphrase_permit,
                              verify_catchphrase_reference)
from item_aliases import confirmed_aliases, update_alias_reports
from message_aliases import confirmed_message_aliases
from dialogue_dates import REQUIREMENT, requires_dialogue_dates
from birthday_fields import message_ids as birthday_message_ids
from reference_animations import animation_permit, verify_animation_reference, verify_native_consumer
from reference_content import adapt_content_reference, validate_content_candidate, validate_glyph_candidate
from fortune_strings import candidates as fortune_candidates, permits as fortune_permits
from resetti_replies import candidates as resetti_candidates, permits as resetti_permits
from shop_units import candidates as shop_unit_candidates, permits as shop_unit_permits
from resident_words import candidates as resident_word_candidates, permits as resident_word_permits
from shared_npc_words import candidates as shared_word_candidates
from placeholder_text import placeholder_edit
from reference_mail_fragments import load_fragment_matches, reference_fragment_edits
from contextual_choices import load_contextual_choices, contextualize_edits
from extended_choices import verify_reference_labels

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


def record_candidate(edit, info, advances, name, edits, manifests, counts, *, resident_runtime=False,
                     extended_glyphs=False):
    use_glyphs = extended_glyphs and name == 'message'
    candidate = encode(edit["translation"], info, extended_glyphs=use_glyphs)
    policy = edit.get("control_policy", "exact")
    issues = layout_issues(candidate, info, advances, resident_runtime=resident_runtime,
                           extended_glyphs=use_glyphs) if name == "message" else []
    manifest = {k: v for k, v in edit.items() if k != "translation"}
    manifest.update(encoded_sha256=sha256(candidate), encoded_bytes=len(candidate),
                    layout_issues=issues,
                    expanded_bound=expanded_bound(candidate, info, extended_glyphs=use_glyphs) if name == "message" else len(candidate))
    edits.append(edit)
    manifests.append(manifest)
    counts["accepted_candidates"] += 1
    counts["adapted_candidates"] += bool(edit.get("adaptations"))
    counts["text_field_delivery_candidates"] += policy == "reference_text"
    counts["reference_page_delivery_candidates"] += policy == "reference_delivery"
    counts["reference_layout_candidates"] += policy == "reference_layout"
    counts["reviewed_sequence_candidates"] += policy == "reviewed_sequence"
    counts["layout_review_required"] += bool(issues)


def record_contextual_candidates(before, edits, context_ids, withheld_ids, info, advances,
                                 manifests, counts, *, resident_runtime=False):
    """Original drafts retain draft accounting when only their labels change."""
    counted = {m['id'] for m in manifests}
    affected = set(context_ids) | set(withheld_ids)
    result = [m for m in manifests if m['id'] not in affected]
    for id in sorted(affected):
        if id not in counted:
            if id in withheld_ids:
                counts['original_draft_override'] -= 1
            continue
        previous = Counter()
        record_candidate(before[id], info, advances, 'message', [], [], previous,
                         resident_runtime=resident_runtime)
        counts.subtract(previous)
    for edit in edits:
        if edit['id'] not in context_ids:
            continue
        current = Counter()
        record_candidate(edit, info, advances, 'message', [], result, current,
                         resident_runtime=resident_runtime)
        if edit['id'] in counted:
            counts.update(current)
    counts['contextual_choice_candidates'] = len(context_ids)
    counts['contextual_original_draft_candidates'] = len(set(context_ids)-counted)
    return result


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
    parser.add_argument('--english-fortunes', action='store_true', help='Complete source-verified Katrina phrases; requires resident module')
    parser.add_argument('--english-resetti-replies', action='store_true', help='Complete source-verified Resetti reply dictionary and matching lengths')
    parser.add_argument('--english-shop-units', action='store_true', help='Complete source-verified native shop counter families')
    parser.add_argument('--english-resident-words', action='store_true', help='Complete source-verified ordinary resident words; requires resident module')
    parser.add_argument('--english-shared-npc-words', action='store_true', help='Complete shared reply words; build also requires cartridge NPC generation')
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--gc-text", type=Path, default=Path("build/gamecube/text"))
    parser.add_argument("--gc-names", type=Path, default=Path("build/gamecube/names"))
    parser.add_argument("--inventory", type=Path, default=Path("build/inventory"))
    parser.add_argument("--drafts", type=Path, action="append", help="Repeat to select explicit original-edit files")
    parser.add_argument("--matches", type=Path, default=Path("translations/reference_matches.json"))
    parser.add_argument("--output", type=Path, default=Path("build/candidates"))
    parser.add_argument("--english-runtime", action="store_true")
    parser.add_argument("--runtime-module", type=Path)
    parser.add_argument('--extended-font', type=Path,
                        help='Include reviewed glyph references with this validated cartridge font')
    parser.add_argument('--english-dialogue-dates', action='store_true',
                        help='Include drafts requiring English resident-date preparation')
    args = parser.parse_args()
    if args.english_dialogue_dates and not args.runtime_module:
        parser.error('--english-dialogue-dates requires --runtime-module')
    if args.english_fortunes and not args.runtime_module:
        parser.error('--english-fortunes requires --runtime-module')
    if args.english_resident_words and not args.runtime_module:
        parser.error('--english-resident-words requires --runtime-module')
    if args.english_shared_npc_words and not (args.english_resident_words and args.runtime_module):
        parser.error('--english-shared-npc-words requires --english-resident-words and --runtime-module')
    if args.extended_font and not (args.runtime_module and args.english_runtime):
        parser.error('--extended-font requires the resident module and English runtime')
    rom = verified_rom(args.rom.read_bytes())
    info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    choice_bytes = 16 if args.english_runtime else 10
    if args.runtime_module:
        _, module_report = add_runtime_module(rom, {}, args.runtime_module)
        if args.english_runtime:
            choice_bytes = module_report["choice_layout"]["capacity"]
        info = module_command_info(rom)
    _, font_report = make_halfwidth(rom)
    if args.extended_font:
        from english_runtime import make_english_runtime, ChoiceLayout
        from extended_font_cartridge import planned_capability
        font_replacements, _ = make_halfwidth(rom)
        additions, font_module = add_runtime_module(rom, font_replacements, args.runtime_module)
        runtime, _ = make_english_runtime(rom, font_replacements, ChoiceLayout(**font_module['choice_layout']))
        font_replacements.update(runtime)
        planned_capability(rom,font_replacements,additions,font_module,args.extended_font)
    advances = {int(k, 16): v for k, v in font_report["advance_by_glyph"].items()}
    source_banks = {bank.name: bank for bank in banks(rom)}
    birthday_ids = birthday_message_ids(rom)
    disabled_birthdays = birthday_ids if not args.english_dialogue_dates else frozenset()
    item_matches = load_item_matches()
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
                                       Path("translations/n64-letter-question.json"),
                                       Path("translations/n64-storage-raffle.json"),
                                       Path("translations/n64-connected-services.json"),
                                       Path("translations/n64-menu-followups.json"),
                                       Path("translations/n64-special-followups.json"),
                                       Path("translations/n64-return-greetings.json"),
                                       Path("translations/n64-daily-greetings.json"),
                                       Path("translations/n64-reunion-greetings.json"),
                                       Path("translations/n64-moving-conversations.json"),
                                       Path("translations/n64-nes-launch-prompts.json"),
                                       Path("translations/n64-diagnostic-labels.json"),
                                       Path("translations/n64-engine-diagnostics.json"),
                                       Path("translations/n64-travel-advice.json"),
                                       Path("translations/n64-startup-errors.json"),
                                       Path("translations/n64-renovations.json"),
                                       Path("translations/n64-topic-gaps.json")])
    override_ids = {r["id"] for r in drafts if not r.get("reference_fallback", False)}
    for edit in drafts:
        if edit['id'] in birthday_ids:
            requires_dialogue_dates(edit)  # Reject malformed metadata before adding the source dependency.
            edit['runtime_requirements'] = [REQUIREMENT]
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
    if any('resident_animations' in record or 'native_mood' in record.get('complete_reference', {})
           for record in matches.values()):
        verify_native_consumer(rom)
    verify_native_equivalents(matches, source_banks)
    visited_matches = set()
    if override_ids & matches.keys():
        raise ValueError("Reviewed reference match conflicts with an original draft override")
    edits, manifests, reports = [], [], {}
    for name in REFERENCE_BANKS:
        use_glyphs = bool(args.extended_font) and name == 'message'
        gc = {row["id"]: row for row in map(json.loads, (args.gc_text/(name+".jsonl")).read_text().splitlines())}
        inventory = [json.loads(line) for line in (args.inventory/(name+".jsonl")).read_text().splitlines()]
        source = source_banks[name].entries()
        fortunes = (fortune_candidates(rom, gc, {r['id']: r for r in inventory}, info)
                    if name == 'string' and args.english_fortunes else {})
        string_permits = fortune_permits(rom, list(fortunes.values()), info) if fortunes else {}
        replies = (resetti_candidates(rom,gc,{r['id']:r for r in inventory},info)
                   if name == 'string' and args.english_resetti_replies else {})
        reply_permits = resetti_permits(rom,list(replies.values()),info) if replies else {}
        units = (shop_unit_candidates(rom,gc,{r['id']:r for r in inventory},info)
                 if name=='string' and args.english_shop_units else {})
        unit_permits = shop_unit_permits(rom,list(units.values()),info) if units else {}
        words = (resident_word_candidates(rom,gc,{r['id']:r for r in inventory},info)
                 if name=='string' and args.english_resident_words else {})
        word_permits = resident_word_permits(rom,list(words.values()),info) if words else {}
        shared = (shared_word_candidates(rom,gc,{r['id']:r for r in inventory},info)
                  if name=='string' and args.english_shared_npc_words else {})
        if shared.keys() & (override_ids | matches.keys() | fortunes.keys() | replies.keys() | units.keys() | words.keys()):
            raise ValueError('Shared-word group conflicts with another approved group')
        if words.keys() & (override_ids | matches.keys() | fortunes.keys() | replies.keys() | units.keys()):
            raise ValueError('Resident-word group conflicts with another approved group')
        if units.keys() & (override_ids | matches.keys() | fortunes.keys() | replies.keys()):
            raise ValueError('Shop-unit group conflicts with another approved group')
        if replies.keys() & (override_ids | matches.keys() | fortunes.keys()):
            raise ValueError('Resetti dictionary conflicts with another approved group')
        if fortunes.keys() & (override_ids | matches.keys()):
            raise ValueError('Fortune group conflicts with a draft or identity override')
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
            if id in shared:
                # The complete resource hash validates values and their identities.
                # Installation is deferred until both consumer checks pass; there
                # is deliberately no generic text-validator capacity exception.
                edit=shared[id]
                counts['complete_shared_npc_words'] += 1
            elif id in words:
                edit=words[id]
                validate_entry(original,encode(edit['translation'],info),info,name,
                               resident_runtime=True,resident_word_permit=word_permits[id])
                counts['complete_resident_words'] += 1
            elif id in units:
                edit=units[id]
                validate_entry(original,encode(edit['translation'],info),info,name,
                               shop_unit_permit=unit_permits[id])
                counts['complete_shop_units'] += 1
            elif id in replies:
                edit = replies[id]
                validate_entry(original,encode(edit['translation'],info),info,name,
                               resetti_permit=reply_permits[id])
                counts['complete_resetti_replies'] += 1
            elif id in fortunes:
                edit = fortunes[id]
                validate_entry(original, encode(edit['translation'], info), info, name,
                               resident_runtime=True, fortune_permit=string_permits[id])
                counts['complete_fortune_phrases'] += 1
            elif id in fragments:
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
                        if (requires_dialogue_dates(matches.get(id, {})) or id in birthday_ids) and not args.english_dialogue_dates:
                            raise ValueError('runtime_requirement_unavailable')
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
                                                                retain_resident_animations=bool(animations),
                                                                extended_glyphs=use_glyphs)
                            candidate = encode(text, info, extended_glyphs=use_glyphs)
                            validate_entry(original, candidate, info, name, policy,
                                           choice_bytes=choice_bytes,
                                           resident_runtime=bool(args.runtime_module),
                                           field_permit=field_permit(id, original, candidate, matches),
                                           catchphrase_permit=catchphrase_permit(id, original, candidate, matches),
                                           animation_permit=animation_permit(id, original, candidate, matches),
                                           extended_glyphs=use_glyphs)
                        except ValueError as exc:
                            if added_fields or added_catchphrase or animations or name != "message" or str(exc) != "Control signature changed":
                                raise
                            for policy in ("reference_text", "reference_delivery", "reference_layout"):
                                try:
                                    text, adaptations = adapt_reference(reference_text, original, info, policy,
                                                                        resident_runtime=bool(args.runtime_module),
                                                                        extended_glyphs=use_glyphs)
                                    candidate = encode(text, info, extended_glyphs=use_glyphs)
                                    validate_entry(original, candidate, info, name, policy,
                                                   choice_bytes=choice_bytes,
                                                   resident_runtime=bool(args.runtime_module),
                                                   extended_glyphs=use_glyphs)
                                    break
                                except ValueError as exc:
                                    if policy == "reference_layout" or str(exc) != "Control signature changed":
                                        raise
                        validate_controller_candidate(id, original, candidate, matches)
                        validate_choice_candidate(id, original, candidate, matches)
                        validate_actor_request_candidate(id, original, candidate, matches)
                        validate_content_candidate(id, original, candidate, matches)
                        validate_glyph_candidate(id, original, candidate, matches, info)
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
                if requires_dialogue_dates(matches.get(id, {})) or id in birthday_ids:
                    edit['runtime_requirements'] = [REQUIREMENT]
            record_candidate(edit, info, advances, name, edits, manifests, counts,
                             resident_runtime=bool(args.runtime_module),extended_glyphs=use_glyphs)
        if name == "message":
            aliases, conflicts = confirmed_message_aliases(source, edits, gc, info,
                skip_ids=override_ids | matches.keys() | fragments.keys() | disabled_birthdays,
                resident_runtime=bool(args.runtime_module))
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
            info, override_ids, matches=item_matches)
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
    extended_labels = verify_reference_labels({r['id']: r for r in map(json.loads,
        (args.gc_text/'select.jsonl').read_text().splitlines())}, info)
    edits, context_ids, context_withheld = contextualize_edits(
        edits, source_banks['message'].entries(), source_banks['select'].entries(),
        load_contextual_choices(matches), info, extended_labels=extended_labels)
    context_removed = {r['id'] for r in context_withheld}
    context_counts = Counter(reports['message'])
    manifests = record_contextual_candidates(before_context, edits, context_ids, context_removed,
        info, advances, manifests, context_counts, resident_runtime=bool(args.runtime_module))
    reports['message'] = dict(context_counts)
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
