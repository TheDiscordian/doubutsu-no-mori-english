"""Bind source password-only categories to the complete installed Nook path.

This adapter never creates shop stock or invents a native counterpart. Complete
models, behaviour, saved identities, and selectable metadata use the ordinary
importer; the shared password map is refreshed after that installation.
"""
import json
import zlib

from aflib import by_vrom,sha256
from v3_asset_loader import BLOB,ROOT

SOURCES=('tools/v3_password_acquisition.py','tools/v3_password_policy.py',
    'tools/v3_password_runtime.py','tools/v3_furniture_pipeline.py',
    'tools/v3_furniture_install.py','tools/v3_room_rig_runtime.py')


def checked(source,image,report):
    from v3_password_runtime import RAM,SIZE,POLICY
    from v3_password_policy import evaluator,compact
    p=report.get('equipment_resources',{}).get('passwords')
    if not p or not p.get('acquisition_installed'):return None
    nook=p.get('nook',{});editor=report.get('password_editor',{})
    if (not nook.get('installed') or not p.get('keyboard_installed') or
            not p.get('name_conversion_installed') or not editor.get('installed') or
            not p.get('conversation',{}).get('native_bindings_installed') or
            not nook.get('shared_session_gift_count') or not nook.get('complete_names_and_code_rows')):
        raise ValueError('Password acquisition needs the complete native frontend')
    files=by_vrom(image);blob=files[BLOB].extract(image)
    packet=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
    if (p['ram']!=RAM or p['bytes']!=SIZE or len(packet)!=SIZE or
            sha256(packet)!=p['sha256'] or zlib.crc32(packet)!=p['crc32'] or
            packet[-16:]!=bytes.fromhex('AF5057DE')*4):
        raise ValueError('Changed complete password acquisition packet')
    matrix=(ROOT/'build/v3-password-policy-prepared-03/donor-permissions.bin').read_bytes()
    if sha256(matrix)!='22a5c233464f1779aa1d80944166b4ba4657b25392ff563cba7e9b02a04a2cc9':
        raise ValueError('Changed complete donor password permissions')
    _,contract=evaluator(source);permissions,_=compact(matrix,contract)
    if p['source']['policy']!=json.loads(json.dumps(contract)) or packet[POLICY:POLICY+len(permissions)]!=permissions:
        raise ValueError('Installed password eligibility differs from the complete donor rules')
    for name,binding in nook['native']['owners'].items():
        owner=report['shop_actors']['owners'][name]
        if (sha256(files[owner['vrom']].extract(image))!=binding['overlay_sha256'] or
                sha256(files[binding['installed_reloc_vrom']].extract(image))!=binding['relocation_sha256']):
            raise ValueError('Changed complete Nook counter or relocation: '+name)
    if set(nook['native']['owners'])!={'cranny','conv','super','depart'}:
        raise ValueError('Incomplete front-counter password category')
    font=nook['font']
    from v3_console_disk_install import reservations
    # Nook's title receipt also describes the patched allocator function with a
    # `bytes` field; it is not a second retained owner of its own new buffer.
    retained=dict(report)
    equipment=dict(report['equipment_resources'])
    passwords=dict(p);passwords.pop('nook')
    equipment['passwords']=passwords;retained['equipment_resources']=equipment
    for a,b in reservations(retained):
        for first,last in ((font['pixels_ram'],font['pixels_end']),
                (font['title_buffer']['ram'],font['title_buffer']['end'])):
            if first<b and a<last:
                raise ValueError('Password acquisition font/title overlaps a retained RAM owner')
    if sha256(files[font['vrom']].extract(image))!=font['blob_sha256']:
        raise ValueError('Changed complete Nook name font')
    for resource in nook['dialogue']['resources']:
        if sha256(files[resource['vrom']].extract(image))!=resource['sha256']:
            raise ValueError('Changed complete Nook result dialogue')
    for owner in editor['owner_resizes']:
        if sha256(files[owner['vrom']].extract(image))!=owner['sha256']:
            raise ValueError('Changed complete code-entry keyboard')
    return dict(matrix=matrix,packet_sha256=p['sha256'],runtime_abi=report['runtime_abi'],
        native_delivery_installed=True,ordinary_gameplay_tested=False)


def source_category(source,item,index,lists):
    """Identify acquisition from the actual list or complete birth directory."""
    birth=source.raw('mRmTp_birth_type')
    if not 0<=index<len(birth):raise ValueError('Password furniture birth index exceeds its source table')
    homepage=len(lists)==1 and lists[0][0]=='ftr_listHomePage'
    nintendo=birth[index]==34 and not lists
    if not homepage and not nintendo:return None
    return dict(symbol='ftr_listHomePage' if homepage else 'mRmTp_birth_type',
        route='homepage-famicom' if homepage else 'nintendo-code',
        required_mask=1 if homepage else 4,source_birth_category=birth[index])


def furniture(source,item,index,lists):
    """Return only source-established HomePage/Nintendo-code acquisition."""
    category=source_category(source,item,index,lists)
    if category is None:return None
    binding=getattr(source,'password_acquisition',None)
    if binding is None:
        from v3_furniture_pipeline import ReviewRequired
        raise ReviewRequired('acquisition needs an adapter: complete native Nook password delivery')
    mask=binding['matrix'][item]
    if not mask&category['required_mask']:
        raise ValueError('Password-only source category lacks its actual donor permission')
    symbol=category['symbol']
    return dict(donor_list=symbol,donor_list_sha256=sha256(source.raw(symbol)),
        stock_group=255,reward_route=0,ordinary_stock=False,catalogue_orderable=False,
        password_acquisition=dict(route=category['route'],
            permission_mask=mask,source_birth_category=category['source_birth_category'],
            native_delivery_installed=True,ordinary_gameplay_tested=False))


def catalogue_source(source,item,index,row):
    """Check the birth-directory form without pretending it is a stock list."""
    category=source_category(source,item,index,[])
    acquisition=row.get('password_acquisition',{})
    return (category is not None and category['symbol']=='mRmTp_birth_type' and
        row.get('donor_acquisition_list')==category['symbol'] and
        row.get('catalogue_orderable') is False and
        acquisition.get('route')==category['route'] and
        acquisition.get('source_birth_category')==category['source_birth_category'] and
        acquisition.get('permission_mask',0)&category['required_mask'] and
        acquisition.get('native_delivery_installed') is True)
