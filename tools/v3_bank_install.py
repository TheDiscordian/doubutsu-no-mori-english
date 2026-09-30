"""Install the linked post-office bank, native April owners, text, and saved owner.

This connects cartridge ownership with N64-default banking disabled. Real mail
submission, scheduling, independent bank/reward selection, and native gameplay
remain category work; installation does not make the staged gifts selectable.
"""
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from apply_translation import write_new
from v3_asset_loader import BLOB,ROOT
from v3_bank_link import RAM,ART,END
from v3_bank_resources import checked_link,relocate_owners
from v3_bank_storage import SCRATCH_PRIOR,SCRATCH_BYTES
from v3_event_text import patch_bounds
from v3_holiday_dialogue import check_provenance
from v3_holiday_selection import refresh_receipts
from v3_reward_install import redirect_module
import v3_physical_resources as physical

SOURCES=('tools/v3_bank_install.py','tools/v3_bank_resources.py',
    'tools/v3_room_goods.py','tools/v3_furniture_install.py',
    'tools/v3_furniture_capacity.py','tools/v3_garden_runtime.py','tools/v3_holiday_selection.py')


def replace_packet(value,identity,replacement):
    """Update every alias of the one checked shared startup transfer."""
    if isinstance(value,dict):
        if value.get('id')==identity and value.get('storage')=='physical-ROM':
            value.clear();value.update(copy.deepcopy(replacement));return
        for member in value.values():replace_packet(member,identity,replacement)
    elif isinstance(value,list):
        for member in value:replace_packet(member,identity,replacement)


def refresh_module(value,previous,digest):
    """Retained entry receipts continue to describe their actual trampoline bytes."""
    if isinstance(value,dict):
        if value.get('bytes')==previous['bytes'] and value.get('sha256')==previous['sha256']:
            value['sha256']=digest
        for member in value.values():refresh_module(member,previous,digest)
    elif isinstance(value,list):
        for member in value:refresh_module(member,previous,digest)


def install(base,prior,blob,core,module,output,directory):
    del module # Native core/menu and the shared startup carry all new consumers.
    directory=Path(directory).resolve();files=by_vrom(base)
    bank,owners,linked=checked_link(base,prior,directory)
    preparation=json.loads((ROOT/linked['prepared']/'prepared.json').read_bytes())
    if (prior['save_codec']['format_version']!=20 or prior['equipment_resources'].get('bank') or
            bytes(core)!=files[CODE_VROM].extract(base)):
        raise ValueError('Bank installation requires the unchanged format-twenty baseline')
    e=copy.deepcopy(prior['equipment_resources']);q=e['carried_items']['quest']
    (output/'bank').mkdir()
    old=copy.deepcopy(q['packet']);records=copy.deepcopy(prior['physical_resources'])
    physical.verify(base,records)
    raw=bytearray(base[old['physical']:old['physical']+old['bytes']])
    if (old['ram']!=0x807AC000 or old['ram']+old['bytes']!=RAM or
            sha256(raw)!=old['sha256'] or q['rewards']['end']!=RAM or
            any(parent['packet']!=old for parent in (q['npc'],q['rewards'],
                e['carried_items']['spawning'],e['carried_items']['paper']['quantities']))):
        raise ValueError('Bank startup is not adjacent to the complete retained quest owner')
    previous=copy.deepcopy(q['storage']);origin=q['storage_ram']
    if (previous!=prior['save_codec']['active_storage_code'] or
            previous['sha256']!=preparation['saved_owner']['retained_storage_sha256']):
        raise ValueError('Changed complete active saved-town owner')
    storage=dict(linked['code'],symbols=copy.deepcopy(linked['symbols']),
        flags=preparation['saved_owner']['flags'],link_symbols=preparation['saved_owner']['bound_services'],
        toolchain=linked['compiler'],code_bounds=(RAM,RAM+linked['code']['bytes']),
        shared_bank_implementation=True)
    prefixes=('af_v3_','af_holiday_cards_','af_carried_','af_reward_')
    retained=copy.deepcopy(previous)
    redirects=redirect_module(raw,old,retained,origin,storage,RAM,prefixes)
    required={name for name,address in previous['symbols'].items()
        if name.startswith(prefixes) and origin<=address<origin+previous['bytes']}
    if (not required or required!={r['name'] for r in redirects} or
            {r['address'] for r in redirects}&set(linked['retained_services'].values())):
        raise ValueError('Incomplete or recursive complete bank save redirects')
    refresh_module(e,previous,retained['sha256'])
    raw.extend(bank)
    # One existing startup descriptor now loads the whole contiguous owner.
    # Both old and new physical copies remain owned; no save or ROM is erased.
    changes,growth,resource_plan=relocate_owners(base,prior,owners,linked,
        blob_bytes=len(blob),reservations=records)
    allocation=physical.allocate(base,records,bytes(raw),'post-office-bank-GAFE01-r0',best_fit=True,
        excluded_spans=((files[BLOB].pstart,files[BLOB].pstart+len(blob)),
            *((r['physical'],r['physical']+r['bytes']) for r in growth)))
    records.append(allocation)
    packet=dict(allocation,ram=old['ram'],crc32=zlib.crc32(raw),storage='physical-ROM')
    replace_packet(e,old['id'],packet)
    refresh_receipts(e,records,{packet['id']:raw})
    q=e['carried_items']['quest']
    q.update(active_storage_code=copy.deepcopy(storage),save_format=21,wire_version=7)
    for saved in (e['carried_items']['storage'],e['holiday_items']['controls']['storage']):
        saved.update(active_code=copy.deepcopy(storage),save_format=21,wire_version=7)
    e['console_storage'].update(save_format=21,card_runtime=copy.deepcopy(storage))
    if e['diaries']['memory']['scratch']['bytes']!=SCRATCH_PRIOR:
        raise ValueError('Changed complete retained bank save scratch')
    e['diaries']['memory']['scratch']['bytes']=SCRATCH_BYTES
    core[:]=changes.pop(CODE_VROM)
    text=copy.deepcopy(preparation['dialogue']);check_provenance(text)
    source=ROOT/text['prepared']
    if not source.resolve().is_relative_to(ROOT/'build'):
        raise ValueError('Bank dialogue must belong to the ignored preparation')
    text['choice_vrom']=prior['import_storage']['choice_vrom']
    text['hooks']=patch_bounds(core,text['first_id'],text['count'])
    address=0x80065544;before=0x2A010000|text['first_choice']
    after=0x2A010000|(text['first_choice']+text['choice_count'])
    if u32(core,address-CODE_RAM)!=before:
        raise ValueError('Changed complete bank choice reader bound')
    struct.pack_into('>I',core,address-CODE_RAM,after)
    text['hooks'].append(dict(address=address,before=before,after=after))
    for row in text['resources']:
        data=(source/row['file']).read_bytes()
        if (len(data)!=row['bytes'] or sha256(data)!=row['sha256'] or
                sha256(files[row['vrom']].extract(base))!=row['previous_sha256']):
            raise ValueError('Changed complete prepared bank text')
        target='bank/'+row['file'];write_new(output/target,data)
        row.update(file=target,original_sha256=row.pop('previous_sha256'))
    text['installed']=True
    report=dict(format='AFV3-BANK-INSTALLED-1',installed=True,
        packet=copy.deepcopy(packet),previous_packet=old,ram=RAM,end=END,
        linked=str(directory.relative_to(ROOT)),linked_sha256=sha256((directory/'linked.json').read_bytes()),
        loaded_packet=copy.deepcopy(linked['packet']),packet_offset=RAM-packet['ram'],
        code=copy.deepcopy(storage),artwork=copy.deepcopy(linked['artwork']),
        memory=copy.deepcopy(linked['saved_owner_memory']),save_format=21,wire_version=7,
        account_mode=copy.deepcopy(linked['account_mode']),
        entries=dict(linked['entries'],installed=True,resource_relocation_required=False),
        april_entries=dict(linked['april_entries'],installed=True),resources=dict(resource_plan,installed=True),
        text=text,saved_redirects=redirects,
        startup_uses_retained_descriptor=True,additional_resident_bytes=len(bank)+64+SCRATCH_BYTES-SCRATCH_PRIOR,
        additional_menu_bytes=resource_plan['submenu_additional_pool_bytes'],
        additional_pelly_overlay_bytes=resource_plan['pelly_descriptor']['additional_loaded_bytes'],
        native_execution_verified=False,ordinary_gameplay_verified=False,selectable=False,
        saved_format_changed=True,saved_profile_changed=False,
        pending=['native bank menu, transaction, April lifecycle, and physical save/restart verification',
            'official mail templates, native submission, milestone acknowledgement, and scheduling',
            'independent bank mechanic and source reward browser/offline selections'],
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    report['memory']['installed']=True;e['bank']=report
    extra=prior['catalogue']['category_pool_bytes'];origin=prior['catalogue']['menu_category_pool_origin']
    arena=linked['entries']['arena'];descriptor=resource_plan['submenu_descriptor']
    report['menu_category_pool_origin']=origin
    report['menu_allocation']=dict(offset=descriptor['offset'],
        before=files[descriptor['vrom']].extract(base)[descriptor['offset']:descriptor['offset']+32].hex(),
        after=descriptor['after'],additional_pool_bytes=arena['additional_pool_bytes'],
        pool_patch=dict(address=arena['address'],before=arena['before']-(extra-origin),after=arena['after']-(extra-origin)))
    updates={key:copy.deepcopy(prior[key]) for key in ('save_codec','clothing','room_surfaces','campsite_manager','catalogue','save_runtime')}
    catalogue=updates['catalogue'];pool_growth=arena['additional_pool_bytes']
    catalogue['retained_submenu_pool_patches'].append(dict(address=arena['address'],
        before=arena['before']-extra,after=arena['after']-extra))
    catalogue['category_pool_patch']=dict(address=arena['address'],before=arena['after']-extra,after=arena['after'])
    for key in ('pool_reserved','conservative_pool_required'):catalogue[key]+=pool_growth
    updates['save_runtime']['bank_account_bytes']=48
    updates['save_runtime']['bank_account_guard_bytes']=16
    updates['save_codec'].update(format_version=21,active_storage_code=copy.deepcopy(storage),
        card_storage_code=copy.deepcopy(storage))
    ext=updates['clothing']['save_extension'];ext.update(format_version=21,active_storage_code=copy.deepcopy(storage))
    ext['legacy_formats_read']=list(dict.fromkeys([*ext['legacy_formats_read'],'AFS3-v20']))
    updates['room_surfaces']['save']['disk_format_version']=21
    april=report['april_entries']
    manager=e['harvest']['manager']
    manager.update(previous_sha256=manager['sha256'],sha256=april['sha256'],bytes=april['bytes'],
        relocation_sha256=april['relocation_sha256'],relocation_bytes=april['relocation_bytes'],
        control_count=76,bank_april=copy.deepcopy(april))
    updates['campsite_manager'].update(control_count=76,output_sha256=april['sha256'],
        relocation_sha256=april['relocation_sha256'],bytes=april['bytes'],bank_april=april)
    updates.update(physical_resources=records,resource_growth=growth,
        save_warning='Format-21 experimental saves require this or a newer compatible build, even with banking disabled. '
            'Supported older saves migrate forward with empty accounts. V2 and format-20-or-earlier V3 cannot read these saves. '
            'Keep separate builds, saves, and backups; ordinary save/restart compatibility is unverified.')
    write_new(output/'bank/packet.bin',raw)
    write_new(output/'bank/installed.json',(json.dumps(report,indent=2)+'\n').encode())
    return e,changes,updates,[(allocation,bytes(raw))]


def finish(image,base,output,equipment,records):
    from v3_event_text import install as install_text
    text=equipment['bank']['text']
    image=install_text(image,base,output,text,relocate=True,physical_resources=records)
    extensions={row['vrom']:row for row in text['resources']}
    for owner in (equipment['passwords']['nook']['dialogue'],equipment['harvest']['text']):
        for row in owner['resources']:
            extension=extensions.get(row['vrom'])
            if extension is None or row['sha256']!=extension['original_sha256']:
                raise ValueError('Bank text append changes a retained whole text owner')
            row.update(sha256=extension['sha256'],bytes=extension['bytes'])
    return image
