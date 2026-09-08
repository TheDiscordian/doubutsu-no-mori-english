#!/usr/bin/env python3
"""Build experimental halfwidth ROMs from verified retail input."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, make_ups, n64_checksum, replace_dma, sha256, verified_rom
from font import ATLAS_OFFSET, ATLAS_SIZE, FONT_VROM, make_halfwidth, pixels, png_gray
from textbanks import banks
from textcodec import command_info, encode
from textvalidate import validate_entry
from keyboard import make_english_keyboard
from english_runtime import ChoiceLayout, make_english_runtime, verify_english_runtime
from runtime_module import add_runtime_module, module_command_info, verify_runtime_module
from reference_sequences import validate_sequences
from item_matches import load_matches as load_item_matches, validate_candidate as validate_item_candidate
from extended_items import install as install_extended_items
from display_names import install as install_display_names
from catchphrases import install as install_catchphrases
from mail_catalog import install as install_mail_catalog
from mail_view_patch import install as install_mail_view
from mail_grading import install as install_mail_grading
from mail_npc import install as install_mail_npc
from pelly_receipt import install as install_pelly_receipt
from npc_mail_loader import install as install_npc_mail_loader
from reference_matches import load_matches
from controller_adaptations import validate_controller_candidate
from reference_choices import validate_choice_candidate
from reference_actor_requests import validate_actor_request_candidate
from reference_fields import field_permit, catchphrase_permit
from dialogue_dates import install as install_dialogue_dates, verify_requirements
from reference_animations import animation_permit, verify_native_consumer
from reference_content import validate_content_candidate, validate_glyph_candidate
from reference_mail_fragments import load_fragment_matches, validate_fragment_candidate
from contextual_choices import load_contextual_choices, canonical_candidate, validate_labels
from extended_choices import payloads as extended_choice_payloads, install as install_extended_choices
from fortune_strings import permits as fortune_permits, install as install_fortunes, STRING_RELOCATION
from resetti_replies import permits as resetti_permits, install as install_resetti
from shop_units import permits as shop_unit_permits, verify_callers as verify_shop_unit_callers
from resident_words import permits as resident_word_permits, install as install_resident_words
from credits_strings import permits as credits_permits, install as install_credits
from shared_npc_words import (IDS as SHARED_WORD_IDS, validated_values as shared_word_values,
                              install as install_shared_words)

RELOCATED_BANKS = {
    "message": (0x02000000, 0x8009E474, "3C1800BD27184000", "3C18020027180000"),
    "select": (0x02400000, 0x80065614, "3C1800D027185000", "3C18024027180000"),
}


def apply_translations(rom, replacements, path, *, english_runtime=False, runtime_module=None, module_additions=None,
                       extended_font=None, english_fortunes=False, english_resetti_replies=False,
                       english_shop_units=False, english_resident_words=False, defer_shared_npc_words=False,
                       english_credits=False):
    if english_fortunes and not runtime_module:
        raise ValueError('English fortunes require the complete resident runtime')
    if english_resident_words and not runtime_module:
        raise ValueError('Resident words require the complete resident runtime')
    if defer_shared_npc_words and not (runtime_module and english_resident_words):
        raise ValueError('Shared NPC words require the complete resident-word runtime')
    relocated_banks = {**RELOCATED_BANKS, **({'string': STRING_RELOCATION}
                       if english_fortunes or english_resetti_replies or english_shop_units or english_resident_words or english_credits else {})}
    layout = ChoiceLayout()
    module_report = None
    if runtime_module:
        verify_runtime_module(rom, replacements, module_additions, runtime_module)
        _, module_report = add_runtime_module(rom, {}, runtime_module)
        layout = ChoiceLayout(**module_report["choice_layout"])
        info = module_command_info(rom)
    else:
        info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    if english_runtime:
        verify_english_runtime(rom, replacements, layout)
    if extended_font:
        if not (runtime_module and english_runtime):
            raise ValueError('Extended dialogue glyphs require the complete English runtime')
        from extended_font_cartridge import planned_capability
        planned_capability(rom,replacements,module_additions,module_report,extended_font)
    edits = json.loads(path.read_text()) if path else []
    if defer_shared_npc_words:
        shared_word_values(rom, edits, info)
        # Long shared words remain native until the final creator/reader checks.
        edits = [edit for edit in edits if edit['id'] not in SHARED_WORD_IDS]
    string_permits = fortune_permits(rom, edits, info) if english_fortunes else {}
    reply_permits = resetti_permits(rom, edits, info) if english_resetti_replies else {}
    unit_permits = shop_unit_permits(rom, edits, info) if english_shop_units else {}
    word_permits = resident_word_permits(rom, edits, info) if english_resident_words else {}
    credit_permits = credits_permits(rom, edits, info) if english_credits else {}
    source_banks = banks(rom)
    item_matches = load_item_matches()
    item_sources = {bank.name: bank.entries() for bank in source_banks if bank.name.startswith('item_')}
    matches = load_matches(Path(__file__).resolve().parents[1]/"translations/reference_matches.json")
    verify_requirements(edits, rom, replacements, module_additions, module_report, matches=matches)
    contextual = load_contextual_choices(matches)
    edits_by_id = {edit['id']: edit for edit in edits}
    source_labels = next(b for b in source_banks if b.name == 'select').entries()
    fragment_matches = load_fragment_matches()
    fragment_sources = {b.name: b.entries() for b in source_banks if b.name in ('maila', 'mailb', 'mailc')}
    if any('resident_animations' in matches.get(edit['id'], {})
           or 'native_mood' in matches.get(edit['id'], {}).get('complete_reference', {}) for edit in edits):
        verify_native_consumer(rom, replacements)
    permits = validate_sequences(edits, next(b for b in source_banks if b.name == "message").entries(), info,
                                 resident_runtime=bool(runtime_module))
    grouped, seen = {}, set()
    for edit in edits:
        bank, index = edit["id"].split(":")
        if edit["id"] in seen:
            raise ValueError("Duplicate translation ID")
        seen.add(edit["id"])
        grouped.setdefault(bank, {})[int(index, 16)] = edit
    count = 0
    relocations = {}
    files = by_vrom(rom)
    for bank in source_banks:
        if bank.name not in grouped:
            continue
        entries = bank.entries()
        for index, edit in grouped.pop(bank.name).items():
            if not 0 <= index < len(entries):
                raise ValueError(f"Unknown entry: {edit['id']}")
            original = entries[index]
            if sha256(original) != edit["source_sha256"]:
                raise ValueError(f"Stale translation: {edit['id']}")
            use_glyphs = bool(extended_font) and bank.name == 'message'
            replacement = encode(edit["translation"], info, extended_glyphs=use_glyphs)
            try:
                validate_item_candidate(edit, item_sources, info, item_matches)
                checked = canonical_candidate(edit['id'], original, replacement, contextual, info)
                if edit['id'] in contextual:
                    validate_labels(contextual[edit['id']], edits_by_id, source_labels, info,
                                    extended_labels=extended_choice_payloads())
                validate_controller_candidate(edit["id"], original, checked, matches)
                validate_choice_candidate(edit["id"], original, checked, matches)
                validate_actor_request_candidate(edit["id"], original, checked, matches)
                validate_content_candidate(edit["id"], original, checked, matches)
                validate_glyph_candidate(edit['id'], original, checked, matches, info)
                validate_fragment_candidate(edit['id'], original, checked, fragment_matches,
                                            fragment_sources, info, edit.get('control_policy', 'exact'))
                validate_entry(original, checked, info, bank.name, edit.get("control_policy", "exact"),
                               choice_bytes=layout.capacity if english_runtime else 10,
                               resident_runtime=bool(runtime_module), sequence_permit=permits.get(edit["id"]),
                               field_permit=field_permit(edit["id"], original, checked, matches),
                               catchphrase_permit=catchphrase_permit(edit["id"], original, checked, matches),
                               animation_permit=animation_permit(edit['id'], original, checked, matches),
                               extended_glyphs=use_glyphs, fortune_permit=string_permits.get(edit['id']),
                               resetti_permit=reply_permits.get(edit['id']),
                               shop_unit_permit=unit_permits.get(edit['id']),
                               resident_word_permit=word_permits.get(edit['id']),
                               credits_permit=credit_permits.get(edit['id']))
            except ValueError as exc:
                raise ValueError(f"{edit['id']}: {exc}") from exc
            if bank.fixed_size:
                replacement = replacement.ljust(bank.fixed_size, b" ")
            entries[index] = replacement
            count += 1
        data, table = bank.rebuild(entries, allow_expand=(bank.name in relocated_banks))
        if bank.name in relocated_banks:
            new_vrom, address, expected, patched = relocated_banks[bank.name]
            relocations[bank.data_vrom] = new_vrom
            data += bytes(-len(data) % 16)
            code = bytearray(replacements[CODE_VROM])
            offset = address-CODE_RAM
            if code[offset:offset+8] != bytes.fromhex(expected):
                raise ValueError(f"Retail {bank.name} loader address does not match")
            code[offset:offset+8] = bytes.fromhex(patched)
            replacements[CODE_VROM] = bytes(code)
        for vrom, offset, content in ((bank.data_vrom, bank.data_offset, data),
                                      (bank.table_vrom, bank.table_offset, table)):
            if vrom is None:
                continue
            whole = bytearray(replacements.get(vrom, files[vrom].extract(rom)))
            whole[offset:offset+len(content)] = content
            replacements[vrom] = bytes(whole)
    if grouped:
        raise ValueError(f"Unknown translation banks: {list(grouped)}")
    if english_fortunes:
        install_fortunes(rom, replacements)
    if english_resetti_replies:
        install_resetti(rom, replacements)
    if english_shop_units:
        verify_shop_unit_callers(rom, replacements)
    if english_resident_words:
        install_resident_words(rom, replacements, module_report)
    if english_credits:
        install_credits(rom,replacements)
    if any(label.get('source_kind') == 'appended_gamecube'
           for id in seen if id in contextual for label in contextual[id]['labels']):
        install_extended_choices(rom, replacements)
    return count, relocations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--translations", type=Path)
    parser.add_argument("--english-keyboard", action="store_true")
    parser.add_argument("--english-runtime", action="store_true")
    parser.add_argument("--runtime-module", type=Path, help="Experimental prebuilt resident-module directory")
    parser.add_argument('--english-fortunes', action='store_true', help='Complete Katrina phrases and sixteen-byte caller; requires resident module')
    parser.add_argument('--english-resetti-replies', action='store_true', help='Complete Resetti rude replies with their native substring lengths')
    parser.add_argument('--english-shop-units', action='store_true', help='Complete native shop counter families within their ten-byte callers')
    parser.add_argument('--english-resident-words', action='store_true', help='Complete resident word fields and their sixteen-byte callers; requires resident module')
    parser.add_argument('--english-shared-npc-words', action='store_true', help='Complete shared reply words; requires resident words and the complete cartridge NPC creator')
    parser.add_argument('--english-credits', action='store_true', help='Complete native credits and owned twenty-five-byte loader/drawer rows')
    parser.add_argument('--english-fortune-slips', type=Path, help='Experimental complete Katrina letter hand-off actor; requires the full snapshot reader and fortune catalog')
    parser.add_argument('--english-leaflet-dates', type=Path, help='Complete shop/Redd leaflet dates and AM/PM; directory containing the compiled native hour formatter')
    parser.add_argument('--english-renewal-letters', type=Path, help='Complete renewal mailbox publication actor; requires leaflet dates and the full snapshot reader')
    parser.add_argument('--extended-font',type=Path,help='Source-verified persistent English glyph cartridge directory')
    parser.add_argument('--english-dialogue-dates', action='store_true',
                        help='English dates prepared by ordinary resident conversations; requires the resident module')
    parser.add_argument("--extended-items", type=Path, help="Directory containing names.bin and names.json for the sixteen-byte item resource")
    parser.add_argument("--display-names", type=Path, help="Directory containing names.bin and names.json for the eight-byte display-name resource")
    parser.add_argument("--catchphrases", type=Path, help="Directory containing the full default catchphrase display resource")
    parser.add_argument("--mail-catalog", type=Path, help="Directory containing the registered immutable English mail catalog")
    parser.add_argument("--english-mail-layout", action="store_true", help="Experimental pixel-width body/footer in read mode; native editor and saved fields unchanged")
    parser.add_argument("--english-mail-snapshots", action="store_true", help="Experimental full-letter reader and paging; requires mail layout/catalog; does not itself enable generation")
    parser.add_argument('--english-mail-grading', type=Path, help='Directory containing the source-verified on-demand English mail-scoring overlay')
    parser.add_argument('--npc-mail-generation', type=Path, help='Experimental complete NPC creator overlay directory; enables guarded cartridge loading and delivery; gameplay/save acceptance remains')
    parser.add_argument("--output", type=Path, default=Path("build/halfwidth"))
    args = parser.parse_args()
    if args.english_dialogue_dates and not args.runtime_module:
        parser.error('--english-dialogue-dates requires --runtime-module')
    if args.english_leaflet_dates and not (args.runtime_module and args.english_runtime):
        parser.error('--english-leaflet-dates requires --runtime-module and --english-runtime')
    if args.english_renewal_letters and not (args.english_leaflet_dates and args.english_mail_snapshots):
        parser.error('--english-renewal-letters requires --english-leaflet-dates and --english-mail-snapshots')
    if args.english_fortunes and not args.runtime_module:
        parser.error('--english-fortunes requires --runtime-module')
    if args.english_resident_words and not args.runtime_module:
        parser.error('--english-resident-words requires --runtime-module')
    if args.english_shared_npc_words and not (args.english_resident_words and args.runtime_module and args.npc_mail_generation):
        parser.error('--english-shared-npc-words requires --english-resident-words, --runtime-module, and --npc-mail-generation')
    if args.extended_font and not (args.runtime_module and args.english_runtime):
        parser.error('--extended-font requires the resident module and English runtime')
    if args.english_mail_snapshots and not (args.english_mail_layout and args.mail_catalog):
        parser.error('--english-mail-snapshots requires --english-mail-layout and --mail-catalog')
    if args.english_fortune_slips and not (args.runtime_module and args.english_runtime and args.english_mail_snapshots):
        parser.error('--english-fortune-slips requires the resident module, English runtime, and full snapshot reader')
    if args.npc_mail_generation and not (args.runtime_module and args.english_runtime
                                        and args.english_mail_snapshots and args.english_mail_grading):
        parser.error('--npc-mail-generation requires the runtime module, English runtime, full snapshot reader, and English mail grading')
    rom = verified_rom(args.rom.read_bytes())
    replacements, report = make_halfwidth(rom)
    if args.english_keyboard:
        info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
        keyboard, report["keyboard"] = make_english_keyboard(rom, info, report["advance_by_glyph"])
        replacements.update(keyboard)
    additions = {}
    layout = ChoiceLayout()
    if args.runtime_module:
        additions, report["runtime_module"] = add_runtime_module(rom, replacements, args.runtime_module)
        layout = ChoiceLayout(**report["runtime_module"]["choice_layout"])
    if args.english_runtime:
        runtime, report["english_runtime"] = make_english_runtime(rom, replacements, layout)
        replacements.update(runtime)
    if args.english_dialogue_dates:
        report['dialogue_dates'] = install_dialogue_dates(rom, replacements, additions, report['runtime_module'])
    report["translation_edits"], relocations = apply_translations(
        rom, replacements, args.translations, english_runtime=args.english_runtime,
        runtime_module=args.runtime_module, module_additions=additions,extended_font=args.extended_font,
        english_fortunes=args.english_fortunes, english_resetti_replies=args.english_resetti_replies,
        english_shop_units=args.english_shop_units, english_resident_words=args.english_resident_words,
        defer_shared_npc_words=args.english_shared_npc_words, english_credits=args.english_credits)
    if args.english_mail_layout:
        report['mail_view'] = install_mail_view(rom, replacements, additions, report.get('runtime_module'),
                                              snapshots=args.english_mail_snapshots)
    if args.english_mail_grading:
        report['mail_grading'] = install_mail_grading(rom,replacements,additions,report.get('runtime_module'),args.english_mail_grading)
        if args.english_mail_snapshots:
            report['mail_npc'] = install_mail_npc(rom,replacements,additions,report.get('runtime_module'))
            report['pelly_receipt'] = install_pelly_receipt(rom,replacements,additions,report.get('runtime_module'))
    if args.extended_items:
        report["extended_items"] = install_extended_items(rom, additions, report.get("runtime_module"), args.extended_items)
    if args.display_names:
        report["display_names"] = install_display_names(rom, additions, report.get("runtime_module"), args.display_names)
    if args.catchphrases:
        report["catchphrases"] = install_catchphrases(rom, additions, report.get("runtime_module"), args.catchphrases, replacements)
    if args.mail_catalog:
        report['mail_catalog'] = install_mail_catalog(rom, additions, report.get('runtime_module'), args.mail_catalog)
    if args.npc_mail_generation:
        report['npc_mail_loader'] = install_npc_mail_loader(rom,replacements,additions,report.get('runtime_module'),args.npc_mail_generation)
    if args.english_shared_npc_words:
        report['shared_npc_words'] = install_shared_words(rom, replacements, additions, report['runtime_module'],
            json.loads(args.translations.read_text()) if args.translations else [], module_command_info(rom))
        report['translation_edits'] += report['shared_npc_words']['translation_edits']
    if args.extended_font:
        from extended_font_cartridge import install as install_font
        report['extended_font'] = install_font(rom,replacements,additions,report.get('runtime_module'),args.extended_font)
    if args.english_fortune_slips:
        from fortune_actor import install as install_fortune_actor
        report['fortune_actor'] = install_fortune_actor(rom,replacements,additions,relocations,
                                                       report.get('runtime_module'),args.english_fortune_slips)
    if args.english_leaflet_dates:
        from leaflet_dates import install as install_leaflet_dates
        report['leaflet_dates'] = install_leaflet_dates(rom,replacements,additions,relocations,
                                                       report.get('runtime_module'),args.english_leaflet_dates)
    if args.english_renewal_letters:
        from renewal_actor import install as install_renewal_actor
        report['renewal_actor'] = install_renewal_actor(rom,replacements,additions,relocations,
                                                       report.get('runtime_module'),args.english_renewal_letters)
    report["vrom_relocations"] = {f"{a:08X}": f"{b:08X}" for a, b in relocations.items()}
    output = replace_dma(rom, replacements, relocations, additions)
    files = by_vrom(output)
    for vrom, data in {**replacements, **additions}.items():
        if files[relocations.get(vrom, vrom)].extract(output) != data:
            raise ValueError("Reinserted file does not match replacement")
    if n64_checksum(output) != struct.unpack_from(">2I", output, 16):
        raise ValueError("Output checksum failure")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "animal-forest-halfwidth.z64").write_bytes(output)
    patch = make_ups(rom, output)
    if apply_ups(rom, patch) != output:
        raise ValueError("Generated patch round trip failed")
    (args.output / "animal-forest-halfwidth.ups").write_bytes(patch)
    report.update(source_sha256=sha256(rom), output_sha256=sha256(output),
                  size=len(output), patch_sha256=sha256(patch),
                  replacement_files=[f"{v:08X}" for v in replacements],
                  added_files=[f"{v:08X}" for v in additions],
                  release_status="experimental; original hardware untested")
    (args.output / "build.json").write_text(json.dumps(report, indent=2) + "\n")
    if args.runtime_module:
        (args.output / 'runtime-module.json').write_text(json.dumps(report['runtime_module'],indent=2)+'\n')
    for name, font in (("original", by_vrom(rom)[FONT_VROM].extract(rom)),
                       ("halfwidth", replacements[FONT_VROM])):
        atlas = pixels(font[ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE])
        (args.output / f"font-{name}.png").write_bytes(png_gray(192, 256, [p*17 for p in atlas]))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
