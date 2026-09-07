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
from extended_items import install as install_extended_items
from display_names import install as install_display_names
from catchphrases import install as install_catchphrases
from mail_catalog import install as install_mail_catalog
from mail_view_patch import install as install_mail_view
from reference_matches import load_matches
from controller_adaptations import validate_controller_candidate

RELOCATED_BANKS = {
    "message": (0x02000000, 0x8009E474, "3C1800BD27184000", "3C18020027180000"),
    "select": (0x02400000, 0x80065614, "3C1800D027185000", "3C18024027180000"),
}


def apply_translations(rom, replacements, path, *, english_runtime=False, runtime_module=None, module_additions=None):
    layout = ChoiceLayout()
    if runtime_module:
        verify_runtime_module(rom, replacements, module_additions, runtime_module)
        _, module_report = add_runtime_module(rom, {}, runtime_module)
        layout = ChoiceLayout(**module_report["choice_layout"])
        info = module_command_info(rom)
    else:
        info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    if english_runtime:
        verify_english_runtime(rom, replacements, layout)
    edits = json.loads(path.read_text()) if path else []
    source_banks = banks(rom)
    matches = load_matches(Path(__file__).resolve().parents[1]/"translations/reference_matches.json")
    permits = validate_sequences(edits, next(b for b in source_banks if b.name == "message").entries(), info)
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
            replacement = encode(edit["translation"], info)
            try:
                validate_controller_candidate(edit["id"], original, replacement, matches)
                validate_entry(original, replacement, info, bank.name, edit.get("control_policy", "exact"),
                               choice_bytes=layout.capacity if english_runtime else 10,
                               resident_runtime=bool(runtime_module), sequence_permit=permits.get(edit["id"]))
            except ValueError as exc:
                raise ValueError(f"{edit['id']}: {exc}") from exc
            if bank.fixed_size:
                replacement = replacement.ljust(bank.fixed_size, b" ")
            entries[index] = replacement
            count += 1
        data, table = bank.rebuild(entries, allow_expand=(bank.name in RELOCATED_BANKS))
        if bank.name in RELOCATED_BANKS:
            new_vrom, address, expected, patched = RELOCATED_BANKS[bank.name]
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
    return count, relocations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--translations", type=Path)
    parser.add_argument("--english-keyboard", action="store_true")
    parser.add_argument("--english-runtime", action="store_true")
    parser.add_argument("--runtime-module", type=Path, help="Experimental prebuilt resident-module directory")
    parser.add_argument("--extended-items", type=Path, help="Directory containing names.bin and names.json for the sixteen-byte item resource")
    parser.add_argument("--display-names", type=Path, help="Directory containing names.bin and names.json for the eight-byte display-name resource")
    parser.add_argument("--catchphrases", type=Path, help="Directory containing the full default catchphrase display resource")
    parser.add_argument("--mail-catalog", type=Path, help="Directory containing the registered immutable English mail catalog")
    parser.add_argument("--english-mail-layout", action="store_true", help="Experimental pixel-width body/footer in read mode; native editor and saved fields unchanged")
    parser.add_argument("--english-mail-snapshots", action="store_true", help="Experimental full-letter reader and paging; requires mail layout/catalog; no generated records or save approval")
    parser.add_argument("--output", type=Path, default=Path("build/halfwidth"))
    args = parser.parse_args()
    if args.english_mail_snapshots and not (args.english_mail_layout and args.mail_catalog):
        parser.error('--english-mail-snapshots requires --english-mail-layout and --mail-catalog')
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
    report["translation_edits"], relocations = apply_translations(
        rom, replacements, args.translations, english_runtime=args.english_runtime,
        runtime_module=args.runtime_module, module_additions=additions)
    report["vrom_relocations"] = {f"{a:08X}": f"{b:08X}" for a, b in relocations.items()}
    if args.english_mail_layout:
        report['mail_view'] = install_mail_view(rom, replacements, additions, report.get('runtime_module'),
                                              snapshots=args.english_mail_snapshots)
    if args.extended_items:
        report["extended_items"] = install_extended_items(rom, additions, report.get("runtime_module"), args.extended_items)
    if args.display_names:
        report["display_names"] = install_display_names(rom, additions, report.get("runtime_module"), args.display_names)
    if args.catchphrases:
        report["catchphrases"] = install_catchphrases(rom, additions, report.get("runtime_module"), args.catchphrases, replacements)
    if args.mail_catalog:
        report['mail_catalog'] = install_mail_catalog(rom, additions, report.get('runtime_module'), args.mail_catalog)
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
    for name, font in (("original", by_vrom(rom)[FONT_VROM].extract(rom)),
                       ("halfwidth", replacements[FONT_VROM])):
        atlas = pixels(font[ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE])
        (args.output / f"font-{name}.png").write_bytes(png_gray(192, 256, [p*17 for p in atlas]))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
