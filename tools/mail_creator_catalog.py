"""Bind native creator routing to its immutable catalogue and installed font."""

from aflib import by_vrom
from mail_catalog import verify_registered
from npc_mail_capture import catalog_id
from runtime_layout import MODULE_VROM


def vrom(catalog):
    if type(catalog) is not int or catalog not in (2,4):
        raise ValueError('Native reply/system creators require catalogue two or four')
    return 0x03000000 if catalog == 2 else 0x030A0000


def identity(data):
    catalog = verify_registered(data)['catalog']
    vrom(catalog)
    return catalog


def selected(module):
    return catalog_id(module['npc_mail_loader']['overlay'])


def resource(additions,module):
    catalog = selected(module)
    data = additions.get(vrom(catalog),b'')
    if identity(data) != catalog:
        raise ValueError('Creator catalogue resource does not match its compiled variant')
    if catalog == 4:
        from extended_font_cartridge import VROM,verify_configuration
        if module.get('extended_font',{}).get('font',{}).get('mail_glyphs') is not True:
            raise ValueError('Glyph letters require the installed complete cartridge font')
        verify_configuration(additions[MODULE_VROM],additions.get(VROM,b''),module)
    return data


def verify_installation(built,module,report):
    """Call after the creator configuration itself has been verified."""
    catalog = selected(module)
    if report.get('catalog',2) != catalog:
        raise ValueError('Letter coverage report selects a different creator catalogue')
    files = by_vrom(built)
    address = vrom(catalog)
    if address not in files or identity(files[address].extract(built)) != catalog:
        raise ValueError('Selected immutable creator catalogue is not installed')
    if catalog == 4:
        from extended_font_cartridge import VROM,verify_configuration
        if VROM not in files or module.get('extended_font',{}).get('font',{}).get('mail_glyphs') is not True:
            raise ValueError('Glyph letters require the installed complete cartridge font')
        verify_configuration(files[MODULE_VROM].extract(built),files[VROM].extract(built),module)
    return catalog
