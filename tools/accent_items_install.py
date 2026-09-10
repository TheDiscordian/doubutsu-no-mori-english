"""Install the complete accent routes as one verified cartridge update."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256,verified_rom,replace_dma,make_ups,apply_ups,n64_checksum,DMA_START,DMA_END
from accent_mail_overlays import BASE_SHA,BASE_IMAGES,ROOT
from accent_mail_overlay_profile import wrap,validate as validate_overlay,NAMES_SHA
from accent_mail_catalog import verify as verify_catalog,verify_shop_compatibility,VROM as CATALOG_VROM
from extended_font_cartridge import configuration as font_configuration,validate as validate_font,VROM as FONT_VROM
from npc_mail_loader import configuration as creator_configuration,WORK_BYTES
from runtime_layout import MODULE_VROM
from notice_overlay import metadata as notice_metadata,METADATA as NOTICE_META,OWNER_VROM
import accent_items

BASE=ROOT/'build/apology-input-pilot'
CHANGED=(MODULE_VROM,0x02A00000,0x03200000,FONT_VROM,0x03920000,0x03928000,0x03800000,0x03810000,OWNER_VROM)


def baseline():
    built=(BASE/'animal-forest-halfwidth.z64').read_bytes()
    report=json.loads((BASE/'build.json').read_text())
    if sha256(built)!=BASE_SHA or report['output_sha256']!=BASE_SHA:
        raise ValueError('Changed complete preceding accent cartridge')
    return built,report


def resources(directory):
    value={}
    for kind in ('creator','notice','event'):
        path=directory/kind
        data,reloc=(path/'overlay.bin').read_bytes(),(path/'relocation.bin').read_bytes()
        report=wrap(json.loads((path/'overlay.json').read_text()))
        validate_overlay(kind,data,reloc,report)
        value[kind]=(data,reloc,report)
    return value


def plan(native,base,previous,parts,font,items,catalog):
    files=by_vrom(base);report=deepcopy(previous);module=report['runtime_module']
    fontdata,fontrel,fontreport=font;validate_font(*font)
    if fontreport.get('mail_literals') is not True:raise ValueError('Accented items require the complete literal-mail font')
    catalog_report=verify_catalog(catalog)
    verify_shop_compatibility(files[0x03000000].extract(base),catalog)
    # Reconstruct all eight fields from exact native and donor identities.
    rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    edits=accent_items.candidates(native,rel,symbols)
    expected=bytearray(files[0x02A00000].extract(base))
    for row in edits:
        at=accent_items.offset(row['id']);expected[at:at+16]=accent_items.encoded(accent_items.ROWS[row['accent_item_name']][0])
    if bytes(expected)!=items or sha256(items)!=NAMES_SHA:raise ValueError('Changed complete accented item resource')
    creator,creatorrel,creatorreport=parts['creator'];creatorblob=creator+creatorrel
    fontblob=fontdata+fontrel
    creatorconfig=creator_configuration(creator,creatorrel,creatorreport,module)
    fontconfig=font_configuration(*font)
    binary=bytearray(files[MODULE_VROM].extract(base))
    struct.pack_into('>8I',binary,0x48,*creatorconfig)
    struct.pack_into('>8I',binary,0x68,*fontconfig)
    module['npc_mail_loader'].update(configuration=creatorconfig,blob_sha256=sha256(creatorblob),
        overlay=creatorreport,glyph_font_sha256=sha256(fontblob))
    module['extended_font'].update(configuration=fontconfig,blob_sha256=sha256(fontblob),font=fontreport)
    module['extended_font']['native_evidence']['world_names']['item_resource_sha256']=sha256(items)
    report['extended_font']={**module['extended_font'],'system_allocation_bytes':len(fontblob)+15,
        'scope':'Startup-owned complete font/world labels and immutable accented mail; saved layouts unchanged'}
    report['npc_mail_loader'].update(module['npc_mail_loader'])
    report['npc_mail_loader'].update(temporary_allocation_bytes=len(creatorblob)+WORK_BYTES+15,
                                     configured_module_sha256=sha256(binary))
    report['mail_catalog']['glyph_font_sha256']=sha256(fontblob)
    report['mail_catalog']['accent_catalog']={**catalog_report,'vrom':f'{CATALOG_VROM:08X}'}
    report['extended_items'].update(data_sha256=sha256(items),candidate_slots=4544,
        configured_module_sha256=sha256(binary),status='Complete source-bound English item names with all accent consumers installed')
    for key in ('post_office_letters','shop_notices','quest_replies','shop_item_names'):
        if report[key]['item_resource_sha256']!=previous['extended_items']['data_sha256']:
            raise ValueError('Changed preceding complete item-reader resource binding')
        report[key]['item_resource_sha256']=sha256(items)
    notice,noticerel,noticereport=parts['notice']
    report['noticeboard']['overlay']=noticereport
    for key in ('treasure_owner','seasonal_owner'):
        report['noticeboard'][key]['creator_sha256']=sha256(creatorblob)
    report['event_actor']['overlay']=parts['event'][2]
    owner=bytearray(files[OWNER_VROM].extract(base))
    old_notice=previous['noticeboard']['overlay']
    if owner[NOTICE_META:NOTICE_META+32]!=notice_metadata(old_notice['bytes'],old_notice['symbols'],True):
        raise ValueError('Changed preceding notice ownership')
    owner[NOTICE_META:NOTICE_META+32]=notice_metadata(len(notice),noticereport['symbols'],True)
    updates={MODULE_VROM:bytes(binary),0x02A00000:items,0x03200000:creatorblob,FONT_VROM:fontblob,
        0x03920000:notice,0x03928000:noticerel,0x03800000:parts['event'][0],
        0x03810000:parts['event'][1],OWNER_VROM:bytes(owner),CATALOG_VROM:catalog}
    report['accent_items']={'version':1,'baseline_rom_sha256':BASE_SHA,'names_sha256':NAMES_SHA,
        'source_ids':[row['id'] for row in edits],'font_blob_sha256':sha256(fontblob),
        'catalog_sha256':sha256(catalog),'changed_files':{f'{k:08X}':sha256(v) for k,v in updates.items()},
        'saved_field_growth':0,'resident_module_growth':0,'submenu_pool_growth':0,
        'system_allocation_bytes':len(fontblob)+15,'creator_allocation_bytes':len(creatorblob)+WORK_BYTES+15,
        'status':'Installed complete accented item routes; native execution and ordinary gameplay checks pending'}
    return updates,report


def verify_installation(built,native,report):
    verified_rom(native)
    if report['source_sha256']!=sha256(native) or report['output_sha256']!=sha256(built):
        raise ValueError('Accent report does not identify the actual input and output ROMs')
    base,previous=baseline();files=by_vrom(built);old=by_vrom(base)
    if set(files)!=set(old)|{CATALOG_VROM}:raise ValueError('Accent installation adds or removes unrelated cartridge files')
    native_count=len(by_vrom(native))
    added_order=sorted([v for v,e in old.items() if e.index>=native_count]+[CATALOG_VROM])
    if (files[CATALOG_VROM].index!=native_count+added_order.index(CATALOG_VROM)
            or any(built[DMA_START+(len(files)+1)*16:DMA_END])):
        raise ValueError('Accent catalogue must use one unused DMA row and retain the terminator')
    parts={}
    for kind,key,vrom,relvrom in (('creator',None,0x03200000,None),
            ('notice','noticeboard',0x03920000,0x03928000),('event','event_actor',0x03800000,0x03810000)):
        overlay=report['runtime_module']['npc_mail_loader']['overlay'] if key is None else report[key]['overlay']
        data=files[vrom].extract(built)
        if relvrom is None:data,reloc=data[:overlay['bytes']],data[overlay['bytes']:]
        else:reloc=files[relvrom].extract(built)
        validate_overlay(kind,data,reloc,overlay);parts[kind]=(data,reloc,overlay)
    fontreport=report['runtime_module']['extended_font']['font'];blob=files[FONT_VROM].extract(built)
    font=(blob[:fontreport['bytes']],blob[fontreport['bytes']:],fontreport)
    updates,expected=plan(native,base,previous,parts,font,files[0x02A00000].extract(built),files[CATALOG_VROM].extract(built))
    for vrom,entry in files.items():
        expected_index=(old[vrom].index if vrom in old and old[vrom].index<native_count
                        else native_count+added_order.index(vrom))
        if entry.index!=expected_index:raise ValueError('Accent installation changes native DMA positions or appended ordering')
        wanted=updates[vrom] if vrom in updates else old[vrom].extract(base)
        if vrom==0x00019D40:
            # This file is the DMA table itself. Physical offsets and changed
            # lengths follow repacking; every parsed row and payload is checked
            # above/below, while its independent sixteen-byte prefix is retained.
            if entry.extract(built)[:16]!=wanted[:16]:raise ValueError('Changed DMA-table prefix')
            continue
        if entry.extract(built)!=wanted:raise ValueError(f'Accent installation changes unrelated data at {vrom:08X}')
    for key in ('runtime_module','extended_font','npc_mail_loader','mail_catalog','extended_items','noticeboard',
                'event_actor','accent_items','post_office_letters','shop_notices','quest_replies','shop_item_names'):
        if report[key]!=expected[key]:raise ValueError('Changed accent installation report: '+key)
    if struct.unpack_from('>2I',built,0x10)!=n64_checksum(built):raise ValueError('Invalid accented cartridge checksum')
    from runtime_module import verify_test_module
    verify_test_module(built,report['runtime_module'])
    return edits_from_items(files[0x02A00000].extract(built))


def edits_from_items(items):
    return {id:items[accent_items.offset(id):accent_items.offset(id)+16]
            for id in (*accent_items.ROWS,*accent_items.ALIASES)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--overlays',type=Path,default=ROOT/'build/accent-mail-overlays')
    p.add_argument('--font',type=Path,default=ROOT/'build/accent-mail-font')
    p.add_argument('--output',type=Path,default=ROOT/'build/accent-items-pilot')
    a=p.parse_args();native=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    base,previous=baseline();files=by_vrom(base)
    font=((a.font/'font.bin').read_bytes(),(a.font/'relocation.bin').read_bytes(),json.loads((a.font/'font.json').read_text()))
    updates,report=plan(native,base,previous,resources(a.overlays),font,
        (ROOT/'build/accent-items-candidate/names.bin').read_bytes(),(ROOT/'build/accent-mail-catalog/catalog.bin').read_bytes())
    moved={int(k,16):int(v,16) for k,v in previous['vrom_relocations'].items()};inverse={v:k for k,v in moved.items()}
    replacements={int(v,16):files[moved.get(int(v,16),int(v,16))].extract(base) for v in previous['replacement_files']}
    additions={int(v,16):files[int(v,16)].extract(base) for v in previous['added_files']}
    for vrom,data in updates.items():
        if vrom in additions or vrom==CATALOG_VROM:additions[vrom]=data
        else:
            key=inverse.get(vrom,vrom);replacements[key]=data
            if len(data)!=by_vrom(native)[key].size or key in moved:moved[key]=vrom
    output=replace_dma(native,replacements,moved,additions)
    report.update(source_sha256=sha256(native),output_sha256=sha256(output),size=len(output))
    verify_installation(output,native,report)
    patch=make_ups(native,output)
    if apply_ups(native,patch)!=output:raise ValueError('Accent patch reconstruction failed')
    report.update(source_sha256=sha256(native),output_sha256=sha256(output),patch_sha256=sha256(patch),
        size=len(output),added_files=[f'{v:08X}' for v in additions],
        replacement_files=[f'{v:08X}' for v in replacements],vrom_relocations={f'{k:08X}':f'{v:08X}' for k,v in moved.items()})
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'animal-forest-halfwidth.z64').write_bytes(output)
    (a.output/'animal-forest-halfwidth.ups').write_bytes(patch)
    (a.output/'runtime-module.json').write_text(json.dumps(report['runtime_module'],indent=2)+'\n')
    (a.output/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'output_sha256':sha256(output),'patch_sha256':sha256(patch),'bytes':len(output),
        'applied_accent_names':8,'native_execution_verified':False}))


if __name__=='__main__':main()
