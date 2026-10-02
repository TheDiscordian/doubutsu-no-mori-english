"""Bind source password-only categories to the complete installed Nook path.

This adapter never creates shop stock or invents a native counterpart. Complete
models, behaviour, saved identities, and selectable metadata use the ordinary
importer; the shared password map is refreshed after that installation.
"""
import json
import struct
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
    from v3_nook_font import check_pixel_layout
    check_pixel_layout(report,font)
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


def carried_items(report):
    """Use authenticated source permissions and installed bit-gated destinations."""
    p=report.get('equipment_resources',{}).get('passwords',{})
    if not (p.get('acquisition_installed') and p.get('keyboard_installed') and
            p.get('name_conversion_installed') and p.get('nook',{}).get('installed') and
            p.get('conversation',{}).get('native_bindings_installed')):
        return set()
    matrix=(ROOT/'build/v3-password-policy-prepared-03/donor-permissions.bin').read_bytes()
    if sha256(matrix)!=p['source']['donor_matrix_sha256']:
        raise ValueError('Changed carried-item password permissions')
    return {row['id'] for row in p['source']['destinations']['rows']
            if row.get('kind')=='carried' and row.get('enable_mask') and
            row.get('enable_bytes')==4 and matrix[row['source_item']]}


def installed_items(report):
    """Admit complete source password categories, never replacement shop stock."""
    e=report.get('equipment_resources',{});p=e.get('passwords',{});n=p.get('nook',{})
    if not (p.get('acquisition_installed') and p.get('keyboard_installed') and
            p.get('name_conversion_installed') and n.get('installed') and
            p.get('conversation',{}).get('native_bindings_installed')):
        return set()
    result=set()
    for row in report.get('furniture',{}).get('imports',[]):
        a=row.get('password_acquisition',{})
        if (a.get('route') not in ('homepage-famicom','nintendo-code') or
                not a.get('native_delivery_installed') or not row.get('runtime_installed') or
                any(x not in ('representative native execution','ordinary gameplay and save/restart')
                    for x in row.get('remaining',[]))):
            continue
        if row.get('stock_group')!=255 or row.get('reward_route')!=0 or row.get('ordinary_stock') or row.get('catalogue_orderable'):
            raise ValueError('Password-only item acquires substitute stock or ordering')
        result.add(row['id'])
    surfaces=report.get('room_surfaces',{})
    choices=surfaces.get('optional_selection',{}).get('identities',[])
    for row in surfaces.get('stock',{}).get('passwords',[]):
        a=row.get('password_acquisition',{})
        if (row['id'] in choices and a.get('route')=='homepage-surface' and
                a.get('native_delivery_installed') and not row.get('ordinary_stock') and
                not row.get('catalogue_orderable')):
            result.add(row['id'])
    return result


def verify_installed_items(image,report,catalog):
    ids=installed_items(report)
    if not ids:return set()
    from v3_furniture_pipeline import Source
    from v3_registry import furniture_source
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    binding=checked(source,image,report)
    blob=by_vrom(image)[BLOB].extract(image)
    p=report['equipment_resources']['passwords']
    mapping=p['source']['destinations']['rows']
    from v3_password_runtime import MAP
    packet=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
    magic,version,count,stride,n,reserved,unused=struct.unpack_from('>4s6H',packet,MAP)
    if (magic!=b'AFPM' or version!=2 or stride!=16 or n!=16+count*16 or
            n>0x2800 or reserved or unused):
        raise ValueError('Changed complete live password map header')
    ranges=[struct.unpack_from('>3HBBIB3x',packet,MAP+16+i*16) for i in range(count)]
    stock={r['item_id'] for r in report['shops']['imports']}
    for row in report['furniture']['imports']:
        if row['id'] not in ids:continue
        donor,index=furniture_source(row)
        a=row['password_acquisition']
        lists=[('ftr_listHomePage','')] if a['route']=='homepage-famicom' else []
        category=source_category(source,donor,index,lists)
        if (category is None or category['route']!=a['route'] or
                category['source_birth_category']!=a['source_birth_category'] or
                not binding['matrix'][donor]&category['required_mask'] or
                binding['matrix'][donor]!=a['permission_mask'] or row['item_id'] in stock or
                row['donor_list']!=category['symbol'] or
                row['donor_list_sha256']!=sha256(source.raw(category['symbol']))):
            raise ValueError('Changed complete source password acquisition category')
        if lists and struct.unpack('>'+str(len(source.raw('ftr_listHomePage'))//2)+'H',
                source.raw('ftr_listHomePage')).count(donor)!=1:
            raise ValueError('Password console lacks actual donor HomePage membership')
        from v3_furniture_install import catalogue_record,order_mask
        from v3_import_storage import ITEMS
        at=ITEMS+(row['runtime_index']-1024)*32
        if (struct.unpack_from('>2H',blob,at)!=(row['runtime_index'],int(row['item_id'],16)) or
                blob[at+7]!=1 or blob[at+24]!=order_mask(catalogue_record(row)) or blob[at+27]):
            raise ValueError('Changed installed password item metadata or ordering')
    for row in report['room_surfaces']['stock']['passwords']:
        if row['id'] not in ids:continue
        raw=source.raw(row['source_symbol']);donor=int(row['source_item_id'],16)
        if (sha256(raw)!=row['source_sha256'] or
                struct.unpack('>'+str(len(raw)//2)+'H',raw).count(donor)!=1 or
                binding['matrix'][donor]!=row['password_acquisition']['permission_mask']):
            raise ValueError('Changed complete source HomePage surface category')
    for key in ids:
        choice=catalog[key];donor=int(key.rsplit('/',1)[1],16);item=int(choice['item_id'],16)
        rows=[r for r in mapping if r['id']==key]
        count=4 if choice['kind']=='furniture' else 1
        if (len(rows)!=count or any(r['source_item']!=donor+i or r['item']!=item+i or
                r['enable_ram']!=choice['enable_ram'] or r['enable_bytes']!=choice['enable_bytes'] or
                r['enable_offset']!=choice['enable_offset'] for i,r in enumerate(rows)) or
                int.from_bytes(blob[choice['enable_offset']:choice['enable_offset']+choice['enable_bytes']],'big')!=1):
            raise ValueError('Password item lacks complete live selection/destination gates')
        for i in range(count):
            matches=[r for r in ranges if r[0]<=donor+i<=r[1]]
            if (len(matches)!=1 or matches[0][2]+donor+i-matches[0][0]!=item+i or
                    matches[0][3:5]!=(0,0) or matches[0][5:]!=(choice['enable_ram'],choice['enable_bytes'])):
                raise ValueError('Password item differs from actual runtime destination map')
    return ids
