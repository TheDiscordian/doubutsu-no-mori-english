"""Shared donor scoring categories, independent of artwork and acquisition."""
import struct

from aflib import CODE_RAM, by_vrom, sha256, u32
from v3_asset_loader import ROOT
from v3_furniture_pipeline import Source
import v3_hra as hra
import v3_hra_mail as mail
import v3_hra_series as series

SOURCES = ('tools/v3_furniture_scoring.py', 'tools/v3_hra_series.py',
           'tools/v3_hra_mail.py', 'tools/v3_furniture_install.py', 'tools/v3_furniture_pipeline.py')


def install(base, prior, core, module):
    files = by_vrom(base)
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    data, reloc, report = series.extend_current(files[hra.NEW_VROM].extract(base),
        files[hra.NEW_RELOC].extract(base), prior['hra'], source, prior['room_surfaces'])
    letters, report['score_letters'] = mail.extend_current(files[mail.VROM].extract(base),
        module, prior['hra']['score_letters'], source.raw('mMkRm_series_name'))
    for adapter in report['series'].values():
        if isinstance(adapter, dict) and 'series' in adapter:
            adapter['score_letter_name_installed'] = True
    for row in report['scheduler']:
        address, before = row['address'], row['after']
        if u32(core, address-CODE_RAM) != before:
            raise ValueError('Changed complete HRA scheduler')
        value = (hra.RAM+len(data) if address in (0x8009CED0, 0x8009CED8, 0x8009CF0C, 0x8009CF10)
                 else hra.NEW_VROM+len(data) if address in (0x8009CF04, 0x8009CF18) else None)
        after = before if value is None else before & 0xFFFF0000 | (
            (value+0x8000) >> 16 & 65535 if before >> 26 == 15 else value & 65535)
        struct.pack_into('>I', core, address-CODE_RAM, after)
        row.update(before=before, after=after)
    changes = {hra.NEW_VROM: data, hra.NEW_RELOC: reloc, mail.VROM: letters}
    return changes, dict(hra=report, furniture_scoring=dict(
        format='AFV3-FURNITURE-SCORING-1', theme_extension=report['theme_extension'],
        added_letter_names=report['score_letters']['added_names'],
        additional_permanent_ram=0, saved_format_changed=False, saved_profile_changed=False,
        owner_resizes=[dict(vrom=v, previous_bytes=files[v].size,
            previous_sha256=sha256(files[v].extract(base)), bytes=len(b), sha256=sha256(b))
            for v, b in changes.items() if len(b) != files[v].size],
        acquisition_installed=False, new_item_ids_enabled=False,
        sources={p: sha256((ROOT/p).read_bytes()) for p in SOURCES}))
