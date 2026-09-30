"""Resolve donor item sets through installed records and the pinned identity sheet.

This map records identities, not permission to award them. Its runtime consumer
must query the installed item reader, which checks the current optional profile.
Unknown/ambiguous identities fail preparation instead of disappearing from lists.
"""
import re

from aflib import sha256
from item_identity_sheet import SHEET_SHA, sheet_rows
from v3_asset_loader import ROOT


def destinations(image, report, source_items, *, lock):
    from v3_optional_composition import catalogue, use_build_lock
    use_build_lock(lock)
    sheet = ROOT/'build/item-identity-megasheet.xlsx'
    if sha256(sheet.read_bytes()) != SHEET_SHA:
        raise ValueError('Changed item destination identity worksheet')
    cells = {}
    for number, row in sheet_rows(sheet, 'Items'):
        if not re.fullmatch('[0-9A-F]{4}', row.get('E', '')):
            continue
        item = int(row['E'], 16)
        if item in cells:
            raise ValueError('Ambiguous donor item destination')
        cells[item] = number, row
    # Selectable imports and complete staged profiles retain their reserved IDs.
    # Do not fall back to a similar native appearance when that import is off.
    installed = dict(catalogue(image, report))
    for row in report.get('staged_furniture', {}).get('rows', []):
        if not (row.get('profile_installed') and row.get('item_record_installed') and row.get('room_runtime')):
            raise ValueError('Incomplete staged destination profile')
        if row['id'] in installed and installed[row['id']]['item_id'] != row['item_id']:
            raise ValueError('Conflicting installed item destinations')
        installed[row['id']] = row
    if report.get('room_surfaces'):
        from v3_surface_selection import options
        from aflib import by_vrom
        from v3_asset_loader import BLOB
        # Complete installed surface records retain canonical destinations even
        # while acquisition is pending. This is identity, not an enable gate.
        options(by_vrom(image)[BLOB].extract(image),report)
        surface=report['room_surfaces']
        for row in surface['rows']:
            item=next(r for r in surface['items']['rows'] if r['id']==row['id'])
            if item['item_id']!=row['destination_item_id']:
                raise ValueError('Conflicting complete surface destination')
            record=dict(row,item_id=row['destination_item_id'])
            if row['id'] in installed and installed[row['id']]['item_id']!=record['item_id']:
                raise ValueError('Conflicting installed surface destination')
            installed[row['id']]=record
    carried = {int(r['donor_item_id'], 16): r for r in
               report['equipment_resources']['carried_items']['rows']}
    result = []
    for donor in sorted(set(source_items)):
        key = f'GAFE01-r0/item/{donor:04X}'
        if donor not in cells:
            raise ValueError('Missing donor item identity: '+key)
        number, fields = cells[donor]
        row = installed.get(key)
        quantity = 1
        if donor in carried:
            native = int(carried[donor]['native_item_id'], 16)
            evidence = 'installed carried record'
        elif row:
            native = int(row['item_id'], 16)
            evidence = 'installed import record'
        else:
            counterpart = fields.get('C', '')
            if donor >> 8 == 0x20:
                # Native paper IDs describe a single sheet, not donor stacks.
                # Preserve the requested quantity for the stack provider; do
                # not invent native IDs by adding the donor quantity bits.
                base = 0x2000+(donor & 63)
                _, parent = cells[base]
                counterpart = parent.get('C', '')
                if re.fullmatch('20[0-3][0-9A-F]', counterpart):
                    quantity = 1+((donor >> 6) & 3)
            if not re.fullmatch('[12][0-9A-F]{3}', counterpart):
                raise ValueError('No installed or native item destination: '+key)
            native = int(counterpart, 16)
            evidence = 'pinned native counterpart'
        if not 0 < native < 65535:
            raise ValueError('Invalid installed item destination')
        result.append(dict(source_item=donor, item=native, quantity=quantity, worksheet_row=number,
                           name=fields['J'], kind=fields['HR'], evidence=evidence))
    return result
