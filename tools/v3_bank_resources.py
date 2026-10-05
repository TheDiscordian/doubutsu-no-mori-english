"""Relocate the complete bank's native owners through the shared ROM planner.

Keep each overlay beside its relocation entry in the DMA directory. The native
loader follows the next directory entry, not the descriptor's nominal end or
an assumed physical adjacency. This plan is consumed by the enclosing bank
installer; emitting a plan alone does not install or enable banking.
"""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from v3_asset_loader import BLOB,ROOT
from v3_bank_link import RAM,ART,END,CODE_GUARD,ART_GUARD,layout
from v3_bank_storage import layout as saved_layout
from v3_post_office_install import MENU_RAM,MENU_VROM,native_entries
from v3_bank_april_install import native_owners

# Resource identities are independent of import selections. Retain the native
# DMA indices; only these complete resource pairs receive new virtual addresses.
PAIRS=((0x79B120,0x79BF10,0x04700000,0x04701000,0x808979C0),
       (0x8A6C10,0x8A8A10,0x04710000,0x04712000,0x809C3420))
PELLY_DESCRIPTOR=0x80101010
PELLY_DESCRIPTOR_SHA='aa25c3f064b59f2ab3e72dd89fac62413dd8b4b76659da4021e9f9843fd32515'


def checked_link(base,prior,directory):
    """Authenticate complete prepared resources and reproduce every native edit."""
    directory=Path(directory).resolve()
    if not directory.is_relative_to(ROOT/'build'):
        raise ValueError('Bank resources must belong to the ignored build tree')
    report=json.loads((directory/'linked.json').read_bytes())
    if (report['format']!='AFV3-BANK-LINKED-1' or not report['fully_linked'] or
            report['installed'] or report['base_sha256']!=sha256(base) or
            report['base_abi']!=prior['runtime_abi'] or report['memory']!=layout(prior) or
            report['saved_owner_memory']!=saved_layout(prior)):
        raise ValueError('Changed complete bank link or base reservations')
    prepared=ROOT/report['prepared']
    if not prepared.resolve().is_relative_to(ROOT/'build') or\
            sha256((prepared/'prepared.json').read_bytes())!=report['prepared_sha256']:
        raise ValueError('Changed complete bank preparation receipt')
    preparation=json.loads((prepared/'prepared.json').read_bytes())
    for receipts in (report['sources'],preparation['sources']):
        for path,digest in receipts.items():
            if sha256((ROOT/path).read_bytes())!=digest:
                raise ValueError('Stale complete bank source: '+path)
    for path,digest in preparation['generated_sha256'].items():
        if sha256((prepared/path).read_bytes())!=digest:
            raise ValueError('Changed complete generated bank source: '+path)
    for path,digest in report['original_objects'].items():
        if sha256((prepared/path).read_bytes())!=digest:
            raise ValueError('Changed complete original bank object: '+path)
    packet=(directory/'bank-packet.bin').read_bytes();code=report['code']
    begin,end=code['bss_start']-RAM,code['bss_end']-RAM
    mode=report['account_mode']
    if (report['packet']['ram']!=RAM or report['packet']['bytes']!=END-RAM or
            len(packet)!=END-RAM or sha256(packet)!=report['packet']['sha256'] or
            code['ram']!=RAM or not 0<code['bytes']<=begin<=end<=ART-RAM-16 or
            code['used_bytes']!=end or sha256(packet[:code['bytes']])!=code['sha256'] or
            any(packet[code['bytes']:ART-RAM-16]) or
            packet[ART-RAM-16:ART-RAM]!=CODE_GUARD or packet[-16:]!=ART_GUARD or
            mode['bytes']!=1 or mode['initial_value']!=0 or
            not RAM+begin<=mode['address']<RAM+end or packet[mode['address']-RAM] or
            mode['profile_control_installed']):
        raise ValueError('Changed complete bank packet, BSS, mode, or guards')
    art=report['artwork'];raw=packet[ART-RAM:ART-RAM+art['bytes']]
    if (sha256(raw)!=art['sha256'] or art['bytes']>END-ART-16 or
            any(packet[ART-RAM+art['bytes']:-16]) or
            raw!=(directory/'bank-art-linked.bin').read_bytes() or
            packet[:code['bytes']]!=(directory/'bank-code.bin').read_bytes()):
        raise ValueError('Changed complete linked bank code/art resource')
    owners,entries=native_entries(base,report['symbols'],code_bounds=(RAM,ART-16))
    april,april_entries=native_owners(base,prior,report['symbols'],
        code_bounds=(RAM,ART-16),entry_core=owners[CODE_VROM])
    owners.update(april)
    if entries!=report['entries'] or april_entries!=report['april_entries'] or\
            len(report['owners'])!=len(owners) or {r['vrom'] for r in report['owners']}!=set(owners):
        raise ValueError('Changed complete native bank/April entry plan')
    for row in report['owners']:
        data=owners[row['vrom']]
        if (len(data)!=row['bytes'] or sha256(data)!=row['sha256'] or
                data!=(directory/f'owner-{row["vrom"]:08X}.bin').read_bytes()):
            raise ValueError('Changed complete native bank owner')
    return packet,owners,report


def relocate_owners(base,prior,owners,report,*,blob_bytes,reservations=None):
    """Plan all native resource moves and update their actual allocation readers."""
    from v3_furniture_install import relocate_resource_plan
    files=by_vrom(base);changes=dict(owners);growth=[];pairs=[]
    if (report['base_sha256']!=sha256(base) or report['base_abi']!=prior['runtime_abi'] or
            len(report['owners'])!=len(changes) or
            {r['vrom'] for r in report['owners']}!=set(changes) or any(
                len(changes[r['vrom']])!=r['bytes'] or sha256(changes[r['vrom']])!=r['sha256']
                for r in report['owners'])):
        raise ValueError('Changed complete linked bank owners before relocation')
    records=prior.get('physical_resources',[]) if reservations is None else reservations
    blob_start=files[BLOB].pstart
    if (type(blob_bytes) is not int or blob_bytes<=0 or blob_bytes&15 or
            not 0<=blob_start<blob_start+blob_bytes<=len(base)):
        raise ValueError('Changed pending import-blob reservation')
    for body,reloc,target,target_rel,ram in PAIRS:
        if (files[reloc].index!=files[body].index+1 or
                any(e.vstart<target+len(changes[body]) and target<e.vend for e in files.values()) or
                any(e.vstart<target_rel+len(changes[reloc]) and target_rel<e.vend for e in files.values())):
            raise ValueError('Bank overlay pair loses its native DMA order or virtual reservation')
        head=struct.unpack_from('>5I',changes[reloc])
        if head[:4]!=(len(changes[body]),0,0,0) or target+len(changes[body])>target_rel:
            raise ValueError('Bank overlay pair has incomplete loaded dimensions')
        for vrom,destination in ((body,target),(reloc,target_rel)):
            _,move=relocate_resource_plan(base,files,vrom,changes[vrom],
                minimum_physical=0x100000,target_vrom=destination,
                reservations=[*records,*growth],append_only=False,allow_compressed=True,
                excluded_spans=((blob_start,blob_start+blob_bytes),))
            growth.append(move)
        pairs.append(dict(vrom=body,relocation_vrom=reloc,target_vrom=target,
            target_relocation_vrom=target_rel,directory_index=files[body].index,
            relocation_directory_index=files[reloc].index,ram=ram,bytes=len(changes[body]),
            sha256=sha256(changes[body]),relocation_sha256=sha256(changes[reloc]),
            native_next_entry_preserved=True))
    menu=bytearray(changes[MENU_VROM]);descriptor=report['entries']['descriptor']
    at=descriptor['offset'];before=bytes.fromhex(descriptor['after'])
    if menu[at:at+32]!=before:
        raise ValueError('Changed complete linked bank menu descriptor')
    after=bytearray(before);struct.pack_into('>2I',after,0,PAIRS[0][2],PAIRS[0][2]+len(changes[PAIRS[0][0]]))
    menu[at:at+32]=after;menu_rel=files[0x7778B0].extract(base)
    head=struct.unpack_from('>5I',menu_rel);spec=Image(MENU_RAM,sum(head[:4]),head)
    for load in (0x80200010,0x80348010):
        old=relocate_verified_data(spec,changes[MENU_VROM],menu_rel,load)
        new=relocate_verified_data(spec,menu,menu_rel,load)
        if (new[at:at+32]!=after or
                any(a!=b and not at<=i<at+8 for i,(a,b) in enumerate(zip(old,new)))):
            raise ValueError('Bank VROM move changes unrelated relocated menu bytes')
    changes[MENU_VROM]=bytes(menu)
    core=bytearray(changes[CODE_VROM]);at=PELLY_DESCRIPTOR-CODE_RAM
    previous=bytes(core[at:at+32]);old=files[CODE_VROM].extract(base)[at:at+32]
    expected=(0x8A6C10,0x8A8A10,0x809C3420,0x809C5220,0,0x809C5000,0,0)
    if previous!=old or sha256(old)!=PELLY_DESCRIPTOR_SHA or struct.unpack('>8I',old)!=expected:
        raise ValueError('Changed complete Pelly allocation descriptor')
    updated=bytearray(old);length=len(changes[PAIRS[1][0]])
    struct.pack_into('>4I',updated,0,PAIRS[1][2],PAIRS[1][2]+length,expected[2],expected[2]+length)
    core[at:at+32]=updated;changes[CODE_VROM]=bytes(core)
    # April retains its virtual identities: its complete new body still fits
    # below the existing relocation resource. Use the same physical planner.
    april=report['april_entries']
    for vrom in (april['vrom'],april['reloc']):
        _,move=relocate_resource_plan(base,files,vrom,changes[vrom],
            minimum_physical=0x100000,reservations=[*records,*growth],
            append_only=False,allow_compressed=True,
            excluded_spans=((blob_start,blob_start+blob_bytes),))
        growth.append(move)
    return changes,growth,dict(pairs=pairs,
        submenu_descriptor=dict(vrom=MENU_VROM,offset=descriptor['offset'],
            before=before.hex(),after=bytes(after).hex(),whole_loaded_images_checked=True,
            owner_sha256=sha256(changes[MENU_VROM])),
        pelly_descriptor=dict(address=PELLY_DESCRIPTOR,before=old.hex(),after=bytes(updated).hex(),
            retained_profile=expected[5],retained_allocation_type=0,
            additional_loaded_bytes=length-(expected[3]-expected[2])),
        submenu_additional_pool_bytes=report['entries']['arena']['additional_pool_bytes'],
        original_physical_copies_preserved=True,installed=False,native_execution_verified=False)


def menu_allocation(image,report):
    """Check the bank's complete late menu owner before retaining its allowance."""
    bank=report['equipment_resources']['bank'];files=by_vrom(image)
    row=bank['menu_allocation'];plan=bank['resources'];pair=plan['pairs'][0]
    origin=report['catalogue']['menu_category_pool_origin'];extra=report['catalogue']['category_pool_bytes']
    descriptor=plan['submenu_descriptor'];parent=files[MENU_VROM].extract(image)
    patch=row['pool_patch'];growth=row['additional_pool_bytes'];core=files[CODE_VROM].extract(image)
    if (not bank['installed'] or not plan['installed'] or growth!=64 or patch['address']!=0x800C4B10 or
            patch['after']-patch['before']!=growth or origin>extra or
            bank['menu_category_pool_origin']!=origin or
            row['offset']!=descriptor['offset'] or row['after']!=descriptor['after'] or
            parent[row['offset']:row['offset']+32].hex()!=row['after'] or
            sha256(parent)!=descriptor['owner_sha256'] or
            sha256(files[pair['target_vrom']].extract(image))!=pair['sha256'] or
            sha256(files[pair['target_relocation_vrom']].extract(image))!=pair['relocation_sha256'] or
            files[pair['target_relocation_vrom']].index!=files[pair['target_vrom']].index+1 or
            struct.unpack_from('>I',core,patch['address']-CODE_RAM)[0]!=patch['after']+extra-origin):
        raise ValueError('Changed complete bank submenu allocation binding')
    return row


def refresh_parent_receipt(image,report):
    """Retain the bank descriptor's complete parent hash after checked writers."""
    bank=report.get('equipment_resources',{}).get('bank')
    if not bank:return
    parent=by_vrom(image)[MENU_VROM].extract(image)
    descriptor=bank['resources']['submenu_descriptor']
    if parent[descriptor['offset']:descriptor['offset']+32].hex()!=descriptor['after']:
        raise ValueError('Shared catalogue writer changed the bank menu descriptor')
    descriptor['owner_sha256']=sha256(parent)
    report['equipment_resources']['diaries']['native_menu_owner_sha256']=sha256(parent)
