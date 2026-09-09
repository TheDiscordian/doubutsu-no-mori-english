#!/usr/bin/env python3
"""Quick combined estimate of Japanese text replaced in the latest built ROM."""

import argparse
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from runtime_module import MODULE_VROM, module_command_info, verify_test_module
from text_coverage import classify
from textbanks import banks

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CATEGORIES = {'japanese_static_text', 'development_placeholder_text'}
ENGLISH_CATEGORIES = {'latin_static_text', 'numbers_or_symbols_only'}
# These resources have working consumers, but also documented consumers still
# reading the original Japanese fields. Do not count an original ID as fully
# applied merely because one of its readers can use the English resource.
# Replace a pending route with credit only alongside verification of its
# remaining consumers. Native-bank English keeps its independent credit.
PENDING_NAME_CONSUMERS = {
    'extended_items': 'Remaining native ten-byte item-name consumers are not connected to the complete resource',
    'display_names': 'Shared choices and other native six-byte name consumers remain unchanged',
    'catchphrases': 'Shared choices and default-phrase editing still use the native four-byte field',
}


def pending_name_consumers(report):
    """Describe remaining paths for this build, after installed verification."""
    pending = dict(PENDING_NAME_CONSUMERS)
    if report.get('text_extension', {}).get('choices'):
        pending['display_names'] = 'Other native six-byte character-name consumers remain unchanged'
        pending['catchphrases'] = 'Default-phrase editing still uses the native four-byte field'
    if report.get('actor_display_names'):
        pending['display_names'] = 'NPC identity-based name readers and editors still need complete integration'
    return pending


class CounterLedger:
    """One original ID, one source weight, regardless of replacement storage."""

    def __init__(self, info):
        self.info, self.rows = info, {}

    def add(self, identity, source):
        if identity in self.rows:
            raise ValueError('Duplicate original text ID: '+identity)
        details = classify(source, self.info)
        self.rows[identity] = {
            'id': identity, 'source_sha256': sha256(source),
            'source_category': details['category'],
            'source_characters': (details['non_whitespace_static_characters']
                                  if details['category'] in SOURCE_CATEGORIES else 0),
            'replacements': [],
            'pending_replacements': [],
        }

    def credit(self, identity, data, route, *, mail=False, mail_glyphs=False, pending_reason=None):
        info = list(self.info)
        if mail:
            # The full-letter formatter consumes these controls as two bytes.
            info[0x74] = info[0x75] = (2, 0)
        if mail_glyphs and not mail: raise ValueError('Mail glyph credit requires a verified mail route')
        details = classify(data, info, extended_glyphs=identity.startswith('message:'),mail_glyphs=mail_glyphs)
        if (details['category'] in ENGLISH_CATEGORIES
                and details['non_whitespace_static_characters']):
            replacement = {'route': route, 'sha256': sha256(data)}
            field = 'replacements'
            if pending_reason is not None:
                if not pending_reason.strip():
                    raise ValueError('Pending application requires a reason')
                replacement['reason'] = pending_reason
                field = 'pending_replacements'
            self.rows[identity][field].append(replacement)

    def summary(self):
        relevant = [r for r in self.rows.values() if r['source_characters']]
        total = sum(r['source_characters'] for r in relevant)
        done = sum(r['source_characters'] for r in relevant if r['replacements'])
        return {'percent': round(100*done/total, 1) if total else None,
                'replaced_source_characters': done, 'total_source_characters': total,
                'replaced_records': sum(bool(r['replacements']) for r in relevant),
                'total_records': len(relevant),
                'pending_application_source_characters': sum(
                    r['source_characters'] for r in relevant
                    if r['pending_replacements'] and not r['replacements']),
                'pending_application_records': sum(
                    bool(r['pending_replacements']) and not r['replacements'] for r in relevant)}


def latest_build(root):
    reports = [p for p in (root/'build').glob('*/build.json')
               if (p.parent/'animal-forest-halfwidth.z64').is_file()]
    if not reports:
        raise ValueError('No completed translation ROM build found')
    return max(reports, key=lambda p: p.stat().st_mtime_ns)


def installed_entries(bank, extract, relocations):
    data = extract(relocations.get(bank.data_vrom, bank.data_vrom))
    table = None
    if bank.table_vrom is not None:
        table = extract(relocations.get(bank.table_vrom, bank.table_vrom))
        if bank.name not in ('message', 'select', 'string'):
            table = table[bank.table_offset:bank.table_offset+len(bank.table)]
    if bank.name not in ('message', 'select', 'string'):
        data = data[bank.data_offset:bank.data_offset+len(bank.data)]
    return replace(bank, data=data, table=table).entries()


def measure(native, built, report):
    native = verified_rom(native)
    if report['source_sha256'] != sha256(native) or report['output_sha256'] != sha256(built):
        raise ValueError('Build report does not match the source and output ROMs')
    if report.get('text_extension'):
        from text_extension import verify_installation
        verify_installation(built, native, report)
    if report.get('actor_display_names') and not report.get('text_extension'):
        raise ValueError('Actor display-name application lacks the verified text extension')
    pending_names = pending_name_consumers(report)
    info = module_command_info(native)
    ledger = CounterLedger(info)
    original = {b.name: b for b in banks(native)}
    files, cache = by_vrom(built), {}

    def extract(vrom):
        if vrom not in cache:
            cache[vrom] = files[vrom].extract(built)
        return cache[vrom]

    relocations = {int(k, 16): int(v, 16) for k, v in report.get('vrom_relocations', {}).items()}
    for bank in original.values():
        entries = installed_entries(bank, extract, relocations)
        for number, source in enumerate(bank.entries()):
            identity = f'{bank.name}:{number:04X}'
            ledger.add(identity, source)
            ledger.credit(identity, entries[number], 'native_bank')

    module = report.get('runtime_module')
    if module:
        verify_test_module(built, module)
        binary = extract(MODULE_VROM)

        def resource(key, offset):
            entry = report.get(key)
            if not entry:
                return None
            vrom = int(entry['vrom'], 16)
            data = extract(vrom)
            if (struct.unpack_from('>I', binary, offset)[0] != vrom
                    or sha256(data) != entry['data_sha256']):
                raise ValueError('Changed installed resource: '+key)
            return data

        items = resource('extended_items', 56)
        if items is not None:
            from extended_items import HEADER, COUNTS, WIDTH
            if items[:32] != HEADER or len(items) != 32+sum(COUNTS)*WIDTH:
                raise ValueError('Invalid extended item resource')
            position = 32
            for group, count in zip([*range(0x20, 0x30), 0x10], COUNTS):
                for number in range(count):
                    ledger.credit(f'item_{group:02X}:{number:04X}',
                                  items[position:position+WIDTH], 'extended_items',
                                  pending_reason=pending_names['extended_items'])
                    position += WIDTH

        names = resource('display_names', 60)
        if names is not None:
            from display_names import HEADER, NPC_COUNT, SPECIAL_COUNT, WIDTH, special_table
            if names[:32] != HEADER or len(names) != 32+(NPC_COUNT+SPECIAL_COUNT)*WIDTH:
                raise ValueError('Invalid display-name resource')
            identities = [f'npc_names:{i:04X}' for i in range(NPC_COUNT)]
            identities += [f'string:{i:04X}' for _, _, i, _ in special_table(native)]
            for number, identity in enumerate(identities):
                ledger.credit(identity, names[32+number*WIDTH:32+(number+1)*WIDTH], 'display_names',
                              pending_reason=pending_names['display_names'])

        phrases = resource('catchphrases', 64)
        if phrases is not None:
            from catchphrases import HEADER, NPC_COUNT, ROW_WIDTH, native_table
            if phrases[:32] != HEADER or len(phrases) != 32+NPC_COUNT*ROW_WIDTH:
                raise ValueError('Invalid catchphrase resource')
            defaults = native_table(native)
            seen = set()
            for at in range(32, len(phrases), ROW_WIDTH):
                actor = struct.unpack_from('>H', phrases, at+4)[0]-0xE000
                if not 0 <= actor < NPC_COUNT or actor in seen:
                    raise ValueError('Invalid catchphrase actor identity')
                seen.add(actor)
                ledger.credit(f'string:{defaults[actor][1]:04X}', phrases[at+6:at+16], 'catchphrases',
                              pending_reason=pending_names['catchphrases'])

        if report.get('gyroid_default'):
            from gyroid_default_actor import verify_installation
            _, default = verify_installation(built, native, module, report['gyroid_default'])
            ledger.credit('string:055C', default, 'gyroid_default')

        if any(report.get(key) for key in ('npc_mail_loader', 'fortune_actor', 'renewal_actor', 'event_actor')):
            from mail_view_patch import install as install_reader
            baseline = bytearray(binary)
            baseline[56:0x88] = bytes(0x88-56)
            expected_reader = {}
            install_reader(native, expected_reader, {MODULE_VROM: bytes(baseline)}, module, snapshots=True)
            if any(extract(vrom) != data for vrom, data in expected_reader.items()):
                raise ValueError('Complete letter reader is not installed')

        def credit_mail(vrom, selected, route):
            from mail_catalog import parse, verify_registered
            data = extract(vrom)
            catalog = verify_registered(data)['catalog']
            contents = parse(data)[1]
            for name, numbers in selected.items():
                for number in numbers:
                    identity = f'{name}:{number:04X}'
                    # GC-only letters must never add native coverage.
                    if identity not in ledger.rows:
                        raise ValueError('Letter mapping has no original source: '+identity)
                    value = contents[name][number]
                    if value is not None:
                        ledger.credit(identity, value, route, mail=True,mail_glyphs=catalog==4)

        if report.get('npc_mail_loader'):
            import mail_creator_catalog as creator_catalog
            creator_catalog.verify_installation(built,module,{'catalog':creator_catalog.selected(module)})
            creator_vrom = creator_catalog.vrom(creator_catalog.selected(module))
            from npc_mail_capture import call_patches
            from npc_mail_delivery import START, END, patch
            from npc_mail_generation import GROUPS, classic_selection
            source_code = by_vrom(native)[CODE_VROM].extract(native)
            code = extract(CODE_VROM)
            for address, _, after in call_patches(source_code, module):
                if code[address-CODE_RAM:address-CODE_RAM+4] != after:
                    raise ValueError('NPC letter capture hook is not installed')
            expected = patch(source_code[START-CODE_RAM:END-CODE_RAM],
                             int(module['symbols']['af_npc_mail_load'], 16))
            if code[START-CODE_RAM:END-CODE_RAM] != expected:
                raise ValueError('NPC letter delivery hook is not installed')
            composite = sorted({start+i for group in GROUPS for start in group for i in range(32)})
            classic = sorted({classic_selection(f, p, i) for f in range(2) for p in range(6) for i in range(3)})
            credit_mail(creator_vrom,
                        {**{k: composite for k in ('superz', 'maila', 'mailb', 'mailc', 'psz')},
                         **{k: classic for k in ('super', 'mail', 'ps')}}, 'npc_letters')

        for key, vrom, numbers in (('fortune_actor', 0x03050000, (114, 115, 116)),
                                   ('renewal_actor', 0x03000000, (24, 25, 26)),
                                   ('event_actor', 0x03000000, (*range(2, 18), 49, 50, 51))):
            if not report.get(key):
                continue
            actor = report[key]
            for field, digest in (('vrom', 'overlay_sha256'), ('relocation_vrom', 'relocation_sha256')):
                if sha256(extract(int(actor[field], 16))) != actor['overlay'][digest]:
                    raise ValueError('Changed installed letter actor: '+key)
            credit_mail(vrom, {k: numbers for k in ('super', 'mail', 'ps')}, key)

        if report.get('mother_letters'):
            from mother_letters import verify_installation
            verify_installation(built, native, module, report['mother_letters'])
            credit_mail(creator_vrom, {k: report['mother_letters']['complete_templates'] for k in ('super', 'mail', 'ps')}, 'mother_letters')

        if report.get('departed_letters'):
            from departed_letters import TEMPLATES, verify_installation
            verify_installation(built, native, module, report['departed_letters'])
            credit_mail(creator_vrom, {k: TEMPLATES for k in ('super', 'mail', 'ps')}, 'departed_letters')

        if report.get('villager_event_letters'):
            from villager_event_letters import verify_installation
            verify_installation(built, native, module, report['villager_event_letters'])
            credit_mail(creator_vrom, {k: report['villager_event_letters']['complete_templates'] for k in ('super', 'mail', 'ps')}, 'villager_event_letters')

        if report.get('academy_letters'):
            from academy_letters import TEMPLATES, verify_installation
            verify_installation(built, native, module, report['academy_letters'])
            credit_mail(creator_vrom, {k: TEMPLATES for k in ('super', 'mail', 'ps')}, 'academy_letters')

        if report.get('academy_score_letters'):
            from academy_score_letters import verify_installation
            verify_installation(built, native, module, report['academy_score_letters'])
            credit_mail(creator_vrom, {k: report['academy_score_letters']['complete_templates'] for k in ('super', 'mail', 'ps')}, 'academy_score_letters')

        if report.get('post_office_letters'):
            from post_office_letters import TEMPLATES, verify_installation
            verify_installation(built, native, module, report['post_office_letters'])
            credit_mail(creator_vrom, {k: TEMPLATES for k in ('super', 'mail', 'ps')}, 'post_office_letters')

        if report.get('museum_letters'):
            from museum_letters import TEMPLATES, verify_installation
            verify_installation(built, native, module, report['museum_letters'])
            credit_mail(creator_vrom, {k: TEMPLATES for k in ('super', 'mail', 'ps')}, 'museum_letters')

        if report.get('shop_notices'):
            from shop_notice_letters import TEMPLATES, verify_installation
            verify_installation(built, native, module, report['shop_notices'])
            credit_mail(creator_vrom, {k: TEMPLATES for k in ('super', 'mail', 'ps')}, 'shop_notices')

        if report.get('quest_replies'):
            from quest_reply_letters import TEMPLATES, verify_installation
            verify_installation(built, native, module, report['quest_replies'])
            credit_mail(creator_vrom, {k: TEMPLATES for k in ('super', 'mail', 'ps')}, 'quest_replies')

        if report.get('snowman_actor'):
            from snowman_actor import verify_installation
            verify_installation(built,native,module,report['snowman_actor'])
            credit_mail(0x030A0000,{k: range(0x202,0x20E) for k in ('super','mail','ps')},'snowman_actor')

        if report.get('secret_actor'):
            from secret_actor import TEMPLATES,verify_installation
            verify_installation(built,native,module,report['secret_actor'])
            credit_mail(0x030A0000,{k:TEMPLATES for k in ('super','mail','ps')},'secret_actor')

        if report.get('noticeboard'):
            from notice_overlay import INITIAL_IDS, verify_installation
            from audit_noticeboard import initial_body
            from mail_catalog import parse
            from mail_record import Record
            verify_installation(built, native, module, report['noticeboard'])
            catalog_banks = parse(extract(0x030A0000))[1]
            for number in INITIAL_IDS:
                body = initial_body(Record(4, 0, (number,), ()), catalog_banks)
                ledger.credit(f'mail:{number:04X}', body, 'noticeboard', mail=True, mail_glyphs=True)
            if report['noticeboard'].get('treasure_owner'):
                from notice_treasure import IDS, body as treasure_body, fields_for
                from mail_record import Field
                samples = {1: Field(b'ABCDEFGHIJKLMNOP'), 2: Field(b'abcdefghijklmnop', 1),
                           3: Field(b'6'), 4: Field(b'5'), 5: Field(b'TownXX')}
                for number in IDS:
                    record = Record(4, 0, (number,), tuple((i, samples[i]) for i in fields_for(number)))
                    ledger.credit(f'mail:{number:04X}', treasure_body(record, catalog_banks),
                                  'noticeboard', mail=True, mail_glyphs=True)
            if report['noticeboard'].get('seasonal_owner'):
                from notice_seasonal import reviewed_templates, complete_body
                from mail_record import Field
                samples = {0: Field(b'TownXX'), 1: Field(b'Nookington\'s    '),
                           2: Field(b'September 30th'), 3: Field(b'October 31st'), 4: Field(b'October 14th')}
                for entry in reviewed_templates(native, extract(0x030A0000)):
                    record = Record(4, 0, (entry['template'],), tuple((i, samples[i]) for i in entry['fields']))
                    ledger.credit(f'mail:{entry["template"]:04X}', complete_body(record, entry),
                                  'noticeboard', mail=True, mail_glyphs=True)

    if report.get('town_suffix'):
        from town_suffix import verify_installation
        evidence = verify_installation(built, native, report)
        # The exact English reference intentionally omits this grammatical
        # suffix. Only its verified source/data/consumer-bound route can credit
        # an empty replacement; arbitrary blank entries still receive no credit.
        row = ledger.rows[evidence['id']]
        if row['source_sha256'] != evidence['source_sha256']:
            raise ValueError('Town-suffix progress source does not match')
        row['replacements'].append({'route': 'town_suffix', 'sha256': evidence['encoded_sha256'],
                                    'intentional_omission': True})

    if report.get('shop_item_names'):
        from shop_item_names import verify_installation
        verify_installation(built, native, report)
        # Connected shop/Redd readers do not finish every item-name consumer.
        # Resource-only item records remain pending until the rest are connected.
    if report.get('player_item_names'):
        from player_item_names import verify_installation
        verify_installation(built, native, report)
    if report.get('event_item_names'):
        from event_item_names import verify_installation
        verify_installation(built, native, report)

    from stall_choices import measure_labels as measure_stall_labels
    measure_stall_labels(ledger, native, built, report)

    # Inventory source prompts even when measuring a build without the patch.
    def add_keyboard():
        from keyboard import EDITOR_VROM, LEDIT_VROM, LEDIT_RAM, LABELS_VROM, LABELS, make_english_keyboard
        keyboard_applied = bool(report.get('keyboard'))
        if keyboard_applied:
            replacements, _ = make_english_keyboard(native, info, report['advance_by_glyph'])
            for vrom, value in replacements.items():
                if vrom == EDITOR_VROM and report.get('hboard_editor'):
                    # The complete owner editor moves this DMA pair and keeps
                    # the original English-first keyboard in its verified prefix.
                    from hboard_overlay import verify_shared_parts as verify_editor
                    verify_editor(built, native)
                elif extract(vrom) != value:
                    raise ValueError('Changed installed English keyboard')
        source = by_vrom(native)[LEDIT_VROM].extract(native)
        for number in range(5):
            at, size = struct.unpack_from('>II', source, 0xA28+number*0x28)
            identity = f'ui_name_entry:{number:04X}'
            ledger.add(identity, source[at-LEDIT_RAM:at-LEDIT_RAM+size])
            at, size = struct.unpack_from('>II', extract(LEDIT_VROM), 0xA28+number*0x28)
            ledger.credit(identity, extract(LEDIT_VROM)[at-LEDIT_RAM:at-LEDIT_RAM+size], 'keyboard')
        ledger.add('ui_name_entry:0005', source[0xAF4:0xAF7])
        ledger.credit('ui_name_entry:0005', extract(LEDIT_VROM)[0xAF4:0xAF8], 'keyboard')
        # Original Japanese labels are visually transcribed, in LABELS order.
        from textcodec import encode
        labels = ('ひらがな', 'カタカナ', 'きごう', 'えいご', 'すうじ',
                  'けってい', 'カーソル', 'けす', 'おわる', 'へんかん')
        for number, (text, (at, width, height, fmt, _)) in enumerate(zip(labels, LABELS)):
            identity = f'ui_keyboard_label:{number:04X}'
            ledger.add(identity, encode(text, info))
            size = width*height//(2 if fmt == 'I4' else 1)
            ledger.rows[identity]['source_sha256'] = sha256(
                by_vrom(native)[LABELS_VROM].extract(native)[at:at+size])
            if keyboard_applied:
                ledger.rows[identity]['replacements'].append(
                    {'route': 'keyboard_graphics', 'sha256': sha256(extract(LABELS_VROM)[at:at+size])})

    add_keyboard()
    # Embedded menu labels are original text too, including in older builds
    # where no English overlay is installed. One source record counts once,
    # regardless of how many menu definitions reference that label.
    from inventory_english import (LABEL_FIRST, LABEL_NAMES, RAM as TAG_RAM, NEW_VROM as TAG_VROM,
                                   native_sources as tag_sources, verify_shared_parts as verify_inventory)
    tag_source = tag_sources(native)[0]
    labels = None
    if report.get('inventory_english'):
        verify_inventory(built, native, module, report['inventory_english'])
        tag = report['inventory_english']
        data = extract(TAG_VROM)
        start = tag['overlay']['symbols']['af_tag_labels']
        labels = [data[start+i*20:start+i*20+16] for i in range(len(LABEL_NAMES))]
    for i in range(len(LABEL_NAMES)):
        identity = f'ui_inventory_label:{i:04X}'
        at = LABEL_FIRST-TAG_RAM+i*12
        ledger.add(identity, tag_source[at:at+8])
        if labels is not None:
            ledger.credit(identity, labels[i], 'inventory_english')
    from inventory_menu_text import SOURCES as MENU_SOURCES
    menu_installed = bool(report.get('inventory_english', {}).get('overlay', {}).get('menu_text'))
    for name, address, length, offset, size in MENU_SOURCES:
        identity = 'ui_inventory_text:'+name
        ledger.add(identity, tag_source[address-TAG_RAM:address-TAG_RAM+length])
        if menu_installed:
            # The complete selected inventory profile has already been verified.
            ledger.credit(identity, data[offset:offset+size], 'inventory_menu_text')
    from tag_descriptions import SOURCES as DESCRIPTION_SOURCES
    descriptions_installed = bool(report.get('inventory_english', {}).get('overlay', {}).get('descriptions'))
    for name, address, length, english in DESCRIPTION_SOURCES:
        identity = 'ui_inventory_description:'+name
        source, ram = ((tag_source, TAG_RAM) if address >= TAG_RAM else
                       (by_vrom(native)[CODE_VROM].extract(native), CODE_RAM))
        ledger.add(identity, source[address-ram:address-ram+length])
        if descriptions_installed:
            # The whole composition/draw/name profile is verified above. Native
            # suffix slices belong to their containing record, not extra IDs.
            ledger.credit(identity, english, 'inventory_descriptions')
    return ledger


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, help='build.json; default is newest completed ROM build')
    parser.add_argument('--native', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--output', type=Path, default=ROOT/'build/translation-progress')
    args = parser.parse_args()
    report_path = args.build or latest_build(ROOT)
    report_bytes = report_path.read_bytes()
    report = json.loads(report_bytes)
    ledger = measure(args.native.read_bytes(),
                     (report_path.parent/'animal-forest-halfwidth.z64').read_bytes(), report)
    result = {'schema': 2, 'measured_at': datetime.now(timezone.utc).isoformat(),
              'build': str(report_path.resolve().relative_to(ROOT)),
              'rom_sha256': report['output_sha256'], 'build_report_sha256': sha256(report_bytes),
              'method': 'Japanese-source non-whitespace character weight; each original ID counted once',
              'kind': 'combined applied translation approximation, not testing or release completion',
              'application_rule': 'Native-bank English or verified complete replacement route; partially connected name resources alone receive no credit',
              'pending_name_consumers': pending_name_consumers(report),
              'inventory_complete': False,
              'inventory_gaps': ['Other embedded interface text and text-bearing artwork need inventory expansion'],
              'source_categories': dict(Counter(r['source_category'] for r in ledger.rows.values())),
              **ledger.summary()}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'latest.json').write_text(json.dumps(result, indent=2)+'\n')
    (args.output/'entries.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in ledger.rows.values()))
    print(f"{result['percent']:.1f}% — {result['replaced_source_characters']:,} / "
          f"{result['total_source_characters']:,} inventoried Japanese-source characters replaced with English.")


if __name__ == '__main__':
    main()
