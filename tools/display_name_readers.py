"""Accounting gate for the completed inventoried character-name display routes."""
import struct
from aflib import CODE_RAM, CODE_VROM, by_vrom
from shop_item_names import jump

REQUIRED = ('display_names', 'actor_display_names', 'map_names', 'guide_name', 'fishing_name',
            'conversation_names', 'house_name', 'letter_editor_names', 'npc_mail_loader',
            'departed_letters', 'villager_event_letters', 'quest_replies')


def complete(report):
    """All these reports receive installed verification during measure()."""
    return (all(report.get(key) for key in REQUIRED)
            and bool(report.get('text_extension', {}).get('choices'))
            and bool(report.get('text_extension', {}).get('identities'))
            and report.get('mail_view', {}).get('snapshot_reader') is True
            and report.get('inventory_english', {}).get('overlay', {}).get('descriptions') is True
            and bool(report.get('noticeboard', {}).get('treasure_owner')))


def verify_main_routes(built, report):
    """The older resource counter did not need to credit these full-name hooks."""
    if not complete(report): raise ValueError('Unfinished character-name reader family')
    code = by_vrom(built)[CODE_VROM].extract(built); module = report['runtime_module']
    # Bind actual main-message/nameplate routes, not descriptive scope strings.
    for address, symbol, target in ((0x8009D324, 'af_get_display_name', 0x80195D20),
                                    (0x800A2BCC, 'af_get_display_name', 0x80195D20),
                                    (0x800A1100, 'af_copy_talk_name', 0x80195E2C)):
        if (int(module['symbols'].get(symbol, '0'), 16) != target
                or struct.unpack_from('>I', code, address-CODE_RAM)[0] != jump(target, link=True)):
            raise ValueError('Missing full English main character-name reader')
    if struct.unpack_from('>I', code, 0x8009D334-CODE_RAM)[0] != 0x24050008:
        raise ValueError('Main character-name field still has its native width')
