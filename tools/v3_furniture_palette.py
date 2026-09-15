"""Install one generated-layout palette-fade category, preserving legacy art."""
import copy
import struct

from aflib import sha256
from v3_asset_loader import BLOB, compile_part, ROOT
from v3_import_storage import PACKAGE, PACKAGE_RAM, replace_checked, jump
from v3_tent_model import native_contract, asset_contract

RAM, LIMIT, VTABLE, LEGACY_VTABLE, LEGACY_LAYOUT = (0x80483400,0x80483800,0x80483720,0x80483700,0x80483740)
SOURCES = ('tools/v3_furniture_palette.py','tools/v3_tent_model.py',
    'overlays/v3/tent_model.c','overlays/v3/palette_fade.ld','overlays/v3/furniture.c',
    'overlays/v3/furniture_expanded.ld','tools/v3_asset_loader.py')


def install(original, base, prior, blob, source, output, rows):
    if not any(r.get('profile',{}).get('callback_adapter',{}).get('category') == 'switch-palette-fade'
               for r in rows):
        return None, copy.deepcopy(prior['furniture']['expanded_tables'])
    contract = native_contract(original,base,expected_sha=sha256(base))
    legacy, _ = asset_contract(source.rel,source.symbols.encode())
    # The compatibility layout describes the already-installed complete object;
    # neither the existing object nor its profile/identity is rewritten.
    old_row = next(r for r in prior['tent_model']['imports'] if r['item_id']=='336C')
    at = int(old_row['object_vrom'],16)-BLOB
    if blob[at:at+len(legacy)] != legacy: raise ValueError('Changed retained legacy palette model')
    legacy_layout = struct.pack('>IHH6I',0x41465031,len(legacy),4,32,64,
                               0x06000C50,0x06000D18,0x06000E00,0x06000FF0)
    at = PACKAGE+RAM-PACKAGE_RAM
    previous = prior.get('furniture_palette_fade')
    if previous:
        if sha256(blob[at:at+LIMIT-RAM]) != previous['resident_sha256']:
            raise ValueError('Changed shared palette callback reservation')
    else:
        old = prior['tent_model']['code']; table = bytes.fromhex(prior['tent_model']['vtable_hex'])
        expected = bytearray(LIMIT-RAM)
        expected[:old['bytes']] = blob[at:at+old['bytes']]
        expected[LEGACY_VTABLE-RAM:LEGACY_VTABLE-RAM+20] = table
        if (old['bytes']>LEGACY_VTABLE-RAM or sha256(expected[:old['bytes']]) != old['sha256']
                or blob[at:at+LIMIT-RAM] != expected):
            raise ValueError('Palette callback reservation is not the retained tent code/table and unused padding')
    code, compiled = compile_part('palette_fade',output/'palette-fade',
        defines=('AF_V3_SHARED_PALETTE_FADE=1',),primary_source='overlays/v3/tent_model.c')
    if (len(code)>LIMIT-RAM or any(code[LEGACY_VTABLE-RAM:LEGACY_LAYOUT-RAM+32])):
        raise ValueError('Palette code overlaps its immutable layout/vtables')
    resident=bytearray(code+bytes(LIMIT-RAM-len(code))); symbols=compiled['symbols']
    common=[symbols['af_v3_tent_model_'+r] for r in ('ct','mv','dw','dt')]
    tables={LEGACY_VTABLE:struct.pack('>5I',*common,0)}
    common[2]=symbols['af_v3_palette_fade_dw'];tables[VTABLE]=struct.pack('>5I',*common,0)
    for address,table in tables.items():
        if any(v and (v&3 or not RAM<=v<LIMIT) for v in struct.unpack('>5I',table)):
            raise ValueError('Palette callback table leaves its checked code')
        resident[address-RAM:address-RAM+20]=table
    resident[LEGACY_LAYOUT-RAM:LEGACY_LAYOUT-RAM+32]=legacy_layout
    blob[at:at+len(resident)] = resident
    expanded=copy.deepcopy(prior['furniture']['expanded_tables']);old=expanded['expanded_code']
    defines=tuple(flag[2:] for flag in old['flags'] if flag.startswith('-D'))
    if 'AF_V3_SHARED_PALETTE_FADE=1' not in defines: defines+=('AF_V3_SHARED_PALETTE_FADE=1',)
    helper, helper_report=compile_part('furniture_expanded',output/'palette-loader',defines=defines,
        primary_source='overlays/v3/furniture.c',extra_sources=('overlays/v3/furniture_entry.S',))
    if (sha256(blob[0x5800:0x5800+old['bytes']])!=old['sha256'] or
            any(blob[0x5800+old['bytes']:0x6000]) or len(helper)>0x800 or
            helper_report['symbols']['af_v3_furniture_secure_banks'] != old['symbols']['af_v3_furniture_secure_banks']):
        raise ValueError('Shared palette loader changes its reservation or existing bank hook target')
    blob[0x5800:0x6000]=helper+bytes(0x800-len(helper))
    for row in expanded['public_entries']:
        target=helper_report['symbols'][row['name']];after=struct.pack('>2I',jump(target),0)
        replace_checked(blob,row['entry']-0x80460000,bytes.fromhex(row['after']),after)
        row.update(before=row['after'],after=after.hex(),target=target)
    expanded['expanded_code']=helper_report
    return dict(category='switch-palette-fade',ram=RAM,bytes=LIMIT-RAM,code=compiled,
        resident_sha256=sha256(resident),native_contract=contract,legacy_layout_hex=legacy_layout.hex(),
        vtables={f'{a:08X}':t.hex() for a,t in tables.items()},
        additional_resident_bytes=0,heap_bytes=0,frame_palette_bytes=32,
        installed=[r['item_id'] for r in rows if r.get('profile',{}).get('callback_adapter',{}).get('category')=='switch-palette-fade'],
        native_test='pending',ordinary_gameplay_tested=False),expanded
