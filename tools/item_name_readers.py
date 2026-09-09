"""Accounting gate for complete inventoried item-name display/letter readers."""
import struct
from aflib import CODE_RAM, CODE_VROM, by_vrom
from shop_item_names import jump

REQUIRED = ('extended_items', 'song_item_names', 'inventory_english', 'catalogue_names',
            'shop_item_names', 'player_item_names', 'event_item_names', 'stall_choices',
            'npc_mail_loader', 'villager_event_letters', 'academy_score_letters',
            'post_office_letters', 'shop_notices', 'quest_replies', 'event_actor',
            'snowman_actor', 'noticeboard', 'extended_font')


def complete(report):
    return (all(report.get(key) for key in REQUIRED)
            and bool(report.get('text_extension', {}).get('choices'))
            and report.get('inventory_english', {}).get('overlay', {}).get('descriptions') is True
            and report.get('extended_font', {}).get('font', {}).get('world_names') is True
            and bool(report.get('noticeboard', {}).get('treasure_owner')))


def verify_additional_routes(built, native, report):
    """The other required families receive installed verification in measure()."""
    if not complete(report): raise ValueError('Unfinished item-name reader family')
    from runtime_module import MODULE_VROM
    from extended_font_cartridge import VROM as FONT_VROM, verify_configuration
    from catalogue_names import verify_shared_parts
    from song_item_names import verify_installation as verify_song
    files = by_vrom(built); code = files[CODE_VROM].extract(built); module = report['runtime_module']
    for address, symbol, target, linked in (
            (0x8009D88C, 'af_set_item_str', 0x801965AC, False),
            (0x800BB6A0, 'af_quest_set_item', 0x80196814, False),
            (0x800A1820, 'af_copy_item_string', 0x801966AC, True)):
        if (int(module['symbols'].get(symbol, '0'), 16) != target
                or struct.unpack_from('>I', code, address-CODE_RAM)[0] != jump(target, link=linked)
                or not linked and code[address-CODE_RAM+4:address-CODE_RAM+8] != bytes(4)):
            raise ValueError('Missing complete main item-field route')
    if report['extended_font'] != {**module['extended_font'],
            'system_allocation_bytes': report['extended_font'].get('system_allocation_bytes'),
            'scope': report['extended_font'].get('scope')}:
        raise ValueError('Mismatched installed world-name font report')
    verify_configuration(files[MODULE_VROM].extract(built), files[FONT_VROM].extract(built), module)
    verify_shared_parts(built, native, module, report['catalogue_names'])
    verify_song(native, built, report)


def resource_only_weight(ledger, routes=('extended_items',)):
    """Newly applied source weight, excluding any already credited bank/route."""
    return sum(row['source_characters'] for row in ledger.rows.values()
               if row['replacements'] and all(r['route'] in routes for r in row['replacements']))
