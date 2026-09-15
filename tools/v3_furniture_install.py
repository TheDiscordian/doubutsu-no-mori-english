"""Install a source-discovered furniture batch through the shared V3 readers.

No item IDs, model descriptions, theme membership lists, or family switches live
here. A pinned base receipt and converter output supply all item records.
"""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import (CODE_RAM, CODE_VROM, DMA_START, DMA_END, by_vrom, fix_checksum,
                   sha256, verified_rom, make_ups, apply_ups)
from apply_translation import write_new
from v3_asset_loader import BLOB, CONFIG, MODULE, STARTUP, ROOT, compile_part
from v3_campsite_calendar import PACKAGE_SIZE
from v3_furniture_pipeline import Source, LAYERS, prepare, metadata, identity_rows
from v3_garden_runtime import install_catalogue
from v3_import_storage import PACKAGE, PACKAGE_RAM, ROWS, ROWS_RAM, ITEMS, TABLE_END, END, slot
import v3_furniture_behaviours as behaviours
import v3_furniture_placement as placement
import v3_catalogue as catalogue
import v3_hra as hra
import v3_feng_shui as feng
import v3_shops as shops

VERSION = 3
LOCK = ROOT/'config/v3-import-build.json'
STABLE = ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64'
STABLE_SHA = '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507'
SOURCES = ('tools/v3_furniture_pipeline.py', 'tools/v3_furniture_install.py',
    'tools/v3_furniture_art.py', 'tools/v3_registry.py', 'tools/v3_catalogue.py',
    'tools/v3_garden_runtime.py', 'tools/v3_shops.py', 'overlays/v3/catalogue.c',
    'overlays/v3/startup.c', 'translations/provenance.json') + behaviours.SOURCES + placement.SOURCES


def inputs(lock=LOCK):
    pin = json.loads(lock.read_bytes())
    directory = (ROOT/pin['directory']).resolve()
    if not directory.is_relative_to(ROOT/'build'): raise ValueError('Base is not an ignored build')
    base = (directory/'animal-forest-v3-asset-loader.z64').read_bytes()
    raw = (directory/'build.json').read_bytes()
    report = json.loads(raw)
    if (sha256(base) != pin['rom_sha256'] or sha256(raw) != pin['report_sha256']
            or report['output_sha256'] != pin['rom_sha256'] or report['runtime_abi'] != pin['runtime_abi']
            or report.get('optional_composition_updated') or 'composition' in report):
        raise ValueError('Changed base cartridge, receipt, ABI, or selected-only base')
    return base, report


def profile(row, vrom):
    n, offsets = row['object_bytes'], row['model_offsets']
    scalar = bytes.fromhex(row['native_profile_scalar_hex'])
    if (not 0 < n <= 9216 or n%16 or vrom%16 or vrom+n > END or len(scalar) != 16
            or not offsets or set(offsets)-set(LAYERS)
            or any(type(at) is not int or at%8 or not 0 <= at <= n-8 for at in offsets.values())):
        raise ValueError('Invalid complete native object/profile bounds')
    pointers = [0x06000000+offsets[k] if k in offsets else 0 for k in LAYERS]
    return struct.pack('>12I', vrom, vrom+n, 0x06000000, 0x06000000+n, *pointers, 0,0,0,0)+scalar+bytes(4)


def catalogue_record(row):
    return dict(item_id=row['item_id'], runtime_index=row['runtime_index'],
        catalogue_index=(int(row['item_id'],16)-0x1000)//4, mode=0,
        donor_position=row['donor_catalogue_position'], donor_acquisition_list=row['donor_list'],
        donor_preview_mode=row['preview_mode'],donor_preview_scalar_hex=row['donor_preview_scalar_hex'],
        preview_override=row['preview_mode']!=0,preview_define='AF_V3_CATALOGUE_PREVIEW_RECORDS',
        ordinary_shop_list=row['donor_list'] if row['ordinary_stock'] else None,
        shop_list_sha256=row['donor_list_sha256'], catalogue_orderable=row['catalogue_orderable'])


def order_mask(row):
    if not row.get('catalogue_orderable', True): return 0
    group = row.get('donor_acquisition_list') or row['ordinary_shop_list']
    masks = {'ftr_listA':7, 'ftr_listB':7, 'ftr_listC':7, 'ftr_listEvent':8, 'ftr_listLottery':32}
    if group not in masks: raise ValueError('Unsupported orderable acquisition category')
    return masks[group]


def provenance_patch(rows):
    """Generate additions to the sole text catalogue, preserving human edits."""
    existing = {r['id']:r for r in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
    additions = []
    for row in rows:
        key = row['id']+'/name'
        if key in existing:
            locale = existing[key]['locales']['en']
            if locale['credit'] != 'official' or locale.get('encoded_sha256') != row['name_sha256']:
                raise ValueError('Existing text attribution differs; preserve it for review')
            continue
        entry = dict(id=key,native_sha256=None,locales={'en':dict(credit='official',
            locator=['tools/v3_furniture_pipeline.py','tools/v3_furniture_install.py'],
            source=dict(source='user-supplied GAFE01 revision 0 disc',symbol='ftrName2_table',
                index=row['name_source_index'],reference_sha256=row['name_sha256']),
            text=row['name'],evidence_id=key,human_review='not_recorded',encoded_sha256=row['name_sha256'])})
        additions.append('+'+'    '+json.dumps(entry,separators=(',',':'))+',')
    if not additions: return ''
    return ('*** Begin Patch\n*** Update File: '+str(ROOT/'translations/provenance.json')+
            '\n@@\n   "entries": [\n'+'\n'.join(additions)+'\n*** End Patch\n')


def scoring(base, prior, rows):
    changes, reports = {}, {}
    files = by_vrom(base)
    for key, tool, width in (('hra',hra,4), ('feng_shui',feng,2)):
        report = copy.deepcopy(prior[key]); data = bytearray(files[tool.NEW_VROM].extract(base))
        if (sha256(data) != report['output_sha256'] or
                sha256(files[tool.NEW_RELOC].extract(base)) != report['relocation_sha256']):
            raise ValueError('Changed scoring owner or relocation resource')
        table = report['metadata_address']-tool.RAM
        for row in rows:
            index = row['runtime_index']; at = table+index*width
            if not 1024 <= index < 2048 or data[at:at+width] != (bytes.fromhex('fc000000') if width==4 else bytes(2)):
                raise ValueError('Scoring record would replace an installed identity')
            if width == 4:
                series = report['series']; start = series['info_address']-hra.RAM+row['series']*3
                actual = data[start:start+3]; expected = bytes.fromhex(row['donor_series_hex'])
                # Existing theme adapters explicitly omit unavailable matching
                # surfaces. Do not invent a surface ID or another per-item rule.
                adapters = [r for r in series.values() if isinstance(r,dict) and r.get('series')==row['series']]
                if actual != expected and not (len(adapters)==1 and not adapters[0]['matching_surfaces_installed']
                        and actual == expected[:2]+b'\xff' and expected[2]==adapters[0]['donor_wall_floor_index']):
                    raise ValueError('Scoring series needs a shared category adapter')
                if row['birth_category'] >= report['birth_extension']['count']:
                    raise ValueError('Unimplemented scoring birth category')
            payload = bytes.fromhex(row['native_hra_hex'] if width==4 else row['feng_hex'])
            if len(payload) != width: raise ValueError('Incomplete scoring record')
            data[at:at+width] = payload
            report['imports'].append(dict(item_id=row['item_id'], runtime_index=index, metadata=payload.hex(),
                **({k:row[k] for k in ('series','birth_category','surface')} if width==4 else {})))
        report.update(output_sha256=sha256(data), metadata_sha256=sha256(data[table:table+report['metadata_rows']*width]))
        changes[tool.NEW_VROM], reports[key] = bytes(data), report
    return changes, reports


def checked_assets(art_path, source, worksheet):
    raw = (art_path/'art.json').read_bytes(); art = json.loads(raw)
    if (art['format'] != 'AFV3-AUTO-FURNITURE-ASSETS-1' or art['version'] != VERSION
            or art['source_rel_sha256'] != sha256(source.rel)
            or art['source_symbols_sha256'] != sha256(source.symbols.encode())):
        raise ValueError('Unknown converter/source revision')
    identities = identity_rows(worksheet); seen = set(); rows = []
    for row in art['objects']:
        item = int(row['item_id'],16)
        if item in seen: raise ValueError('Duplicate batch identity')
        seen.add(item)
        descriptor, body, resources, _, models, commands, sections = prepare(source,item)
        meta = metadata(source,item,descriptor,identities[item])
        if any(row.get(k) != v for k,v in meta.items()) or row['profile'] != json.loads(json.dumps(descriptor)):
            raise ValueError('Import metadata differs from source discovery')
        path = (art_path/row['object_file']).resolve()
        if path.parent != art_path.resolve(): raise ValueError('Object path escapes batch')
        asset = path.read_bytes()
        if (sha256(asset) != row['object_sha256'] or len(asset) != row['object_bytes']
                or asset[:len(body)] != body or row['resources'] != resources
                or row['native_profile_scalar_hex'] != descriptor['scalar_hex']
                or set(row['model_offsets']) != set(models)
                or len(asset) != (len(body)+sum(n for _,n in sections)+15)&~15
                or (art_path/row['item_id']/'commands.c').read_text() != commands):
            raise ValueError('Changed complete converted asset or emitter input')
        # Verify compiled display lists against the emitter's checked receipt.
        for model in row['models']:
            at,n = row['model_offsets'][model['layer']],model['bytes']
            if sha256(asset[at:at+n]) != model['output_sha256']:
                raise ValueError('Changed converted display list')
        rows.append((row,asset))
    if not rows: raise ValueError('Empty automatic import batch')
    return rows, sha256(raw)


def reuse_resource_tail(base, prior, old_blob):
    """Retire only the three terminal resources this builder regenerates.

    Input files remain untouched. Existing object VROMs never move. Receipts,
    DMA mappings, padding, and every resident profile must agree before reuse.
    """
    previous=prior.get('automatic_furniture')
    if not previous:
        return bytearray(old_blob),dict(reused_bytes=0)
    files=by_vrom(base);moves=previous['resource_moves']
    owners={catalogue.VROM,catalogue.RELOC,shops.VROM}
    if (len(moves)!=3 or {r['vrom'] for r in moves}!=owners
            or sha256(old_blob)!=prior['blob_sha256'] or files[BLOB].pend):
        raise ValueError('Changed regenerated resource tail inventory')
    first=min(r['blob_offset'] for r in moves);cursor=first
    if first%16 or not PACKAGE+PACKAGE_SIZE <= first < len(old_blob):
        raise ValueError('Regenerated resource tail overlaps resident data')
    for row in sorted(moves,key=lambda r:r['blob_offset']):
        at,n=row['blob_offset'],row['bytes'];entry=files[row['vrom']]
        if (at!=(cursor+15)&~15 or n<=0 or at+n>len(old_blob) or any(old_blob[cursor:at])
                or entry.pend or entry.size!=n or entry.pstart!=files[BLOB].pstart+at
                or row['physical']!=entry.pstart or sha256(old_blob[at:at+n])!=row['sha256']
                or entry.extract(base)!=old_blob[at:at+n]):
            raise ValueError('Changed regenerated resource extent, mapping, padding, or contents')
        cursor=at+n
    if cursor!=len(old_blob): raise ValueError('Regenerated resources are not the complete terminal tail')
    physical=files[BLOB].pstart+first;end=files[BLOB].pstart+len(old_blob)
    if any(e.pstart<end and physical<(e.pend or e.pstart+e.size)
           for v,e in files.items() if v not in owners|{BLOB} and e.pstart!=0xFFFFFFFF):
        raise ValueError('Regenerated resource tail overlaps another DMA resource')
    for at in range(ROWS,ITEMS,80):
        if any(old_blob[at:at+80]):
            lo,hi=struct.unpack_from('>II',old_blob,at+8)
            if lo<BLOB+len(old_blob) and BLOB+first<hi:
                raise ValueError('Regenerated resource tail overlaps retained furniture')
    return bytearray(old_blob[:first]),dict(reused_bytes=len(old_blob)-first,
        blob_offset=first,source_blob_sha256=sha256(old_blob),
        retained_prefix_sha256=sha256(old_blob[:first]),retired_resources=copy.deepcopy(moves))


def build(output, art_path, lock=LOCK):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'): raise ValueError('Use a fresh ignored build directory')
    base, prior = inputs(lock); files = by_vrom(base)
    base_pin=json.loads(lock.read_bytes())
    if base_pin['rom_sha256']!=sha256(base): raise ValueError('Base lock changed during the build')
    stable = STABLE.read_bytes()
    if sha256(stable) != STABLE_SHA: raise ValueError('Changed translation-only cartridge')
    original = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                    (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    prepared, art_sha = checked_assets(art_path.resolve(), source, ROOT/'build/item-identity-megasheet.xlsx')
    old_blob = files[BLOB].extract(base); blob = bytearray(old_blob)
    package = blob[PACKAGE:PACKAGE+PACKAGE_SIZE]
    profile_bits = bytearray.fromhex(prior['save_runtime']['profile_hex'])
    if (prior['runtime_abi'] < 84 or len(base) != 0x4000000 or PACKAGE_SIZE != 0x30000
            or sha256(blob) != prior['blob_sha256'] or blob[0x20:0xE0] != profile_bits
            or sha256(package) != prior['import_storage']['package_sha256']
            or sha256(blob[ROWS:ITEMS]) != prior['import_storage']['profile_rows_sha256']
            or sha256(blob[ITEMS:TABLE_END]) != prior['import_storage']['item_rows_sha256']
            or struct.unpack_from('>4I',blob,0xF0) != (BLOB+PACKAGE,PACKAGE_SIZE,zlib.crc32(package),PACKAGE_RAM)
            or package[-16:] != bytes.fromhex('AFACC0DE')*4
            or DMA_START+(len(files)+1)*16 != DMA_END or base[DMA_END-16:DMA_END] != bytes(16)):
        raise ValueError('Changed complete shared storage prerequisite')
    blob,reused=reuse_resource_tail(base,prior,old_blob)
    changes, score_reports = scoring(base,prior,[r for r,_ in prepared])
    installed = []
    for row,asset in prepared:
        item,index = int(row['item_id'],16),row['runtime_index']; i=slot(item)
        if (index != 1024+i or any(blob[ROWS+i*80:ROWS+(i+1)*80])
                or any(blob[ITEMS+i*32:ITEMS+(i+1)*32]) or profile_bits[32+i//8]&(1<<(i&7))):
            raise ValueError('Canonical identity is already installed')
        blob.extend(bytes(-len(blob)%16)); vrom = BLOB+len(blob)
        native = profile(row,vrom); blob.extend(asset)
        blob[ROWS+i*80:ROWS+(i+1)*80] = struct.pack('>HHI',index,item,1)+native+bytes(4)
        record = struct.pack('>HHHBB',index,item,row['price'],row['size_code'],1)+row['name'].encode().ljust(16,b' ')+bytes(8)
        blob[ITEMS+i*32:ITEMS+(i+1)*32] = record
        profile_bits[32+i//8] |= 1<<(i&7)
        installed.append({**row, 'registry_version':2, 'object_vrom':f'{vrom:08X}',
            'profile_ram':f'{ROWS_RAM+i*80+8:08X}', 'profile_sha256':sha256(native),
            'record_sha256':sha256(record), 'runtime_installed':True, 'enabled':True,
            'selectable':False, 'ordinary_gameplay_tested':False,
            'remaining':['representative native execution', 'ordinary gameplay and save/restart']})
    all_furniture = copy.deepcopy(prior['furniture']); all_furniture['imports'].extend(installed)
    imports = all_furniture['imports']+[prior['speed_bag']]
    cat_rows = prior['catalogue']['imports']+[catalogue_record(r) for r in installed]
    for row in cat_rows:
        at = ITEMS+slot(int(row['item_id'],16))*32
        old = blob[at+24]
        if old not in (0,order_mask(row)) or any(blob[at+27:at+32]):
            raise ValueError('Catalogue mask overwrites reserved metadata')
        blob[at+24] = order_mask(row)
    preview_report=catalogue.install_preview_records(blob,prior,source,cat_rows)
    output.mkdir(parents=True)
    text_patch=provenance_patch([r for r,_ in prepared])
    if text_patch: write_new(output/'provenance.patch',text_patch.encode())
    cat_changes, cat_report = install_catalogue(base,stable,prior,imports,output,source.rel,
        source.symbols.encode(),reviewed_rows=cat_rows)
    changes.update(cat_changes)
    stock_rows = prior['shops']['imports']+[dict(item_id=r['item_id'],group=r['stock_group'],
        donor_list=r['donor_list'],donor_list_sha256=r['donor_list_sha256']) for r in installed]
    stock_ids = {r['item_id'] for r in stock_rows}
    goods,table_at,stock_rows = shops.goods(stable,source.rel,source.symbols.encode(),
        [r for r in imports if r['item_id'] in stock_ids],reviewed_rows=stock_rows)
    code = bytearray(files[CODE_VROM].extract(base)); stock = prior['shops']
    if (sha256(files[shops.VROM].extract(base)) != stock['output_sha256']
            or struct.unpack_from('>3I',code,shops.DESCRIPTOR-CODE_RAM) !=
                (shops.VROM,shops.VROM+stock['bytes'],0x06000000|stock['table_offset'])):
        raise ValueError('Changed goods owner/descriptor')
    struct.pack_into('>3I',code,shops.DESCRIPTOR-CODE_RAM,shops.VROM,shops.VROM+len(goods),0x06000000|table_at)
    behaviour_report=behaviours.install(original,base,prior,blob,code,imports,source,output)
    placement_changes,placement_report=placement.install(original,base,prior,blob,imports,source)
    changes.update(placement_changes)
    changes[shops.VROM],changes[CODE_VROM] = goods,code
    stock_report = {**stock,'imports':stock_rows,'bytes':len(goods),'table_offset':table_at,'output_sha256':sha256(goods)}
    moves = []
    for vrom in (catalogue.VROM,catalogue.RELOC,shops.VROM):
        blob.extend(bytes(-len(blob)%16)); at=len(blob); data=changes.pop(vrom); blob.extend(data)
        moves.append(dict(vrom=vrom,blob_offset=at,bytes=len(data),physical=files[BLOB].pstart+at,sha256=sha256(data)))
    for vrom,data in list(changes.items()):
        entry=files[vrom]; at=entry.pstart-files[BLOB].pstart
        if entry.pend or len(data)!=entry.size: raise ValueError('Unexpected fixed-owner allocation change')
        if 0 <= at <= len(old_blob)-len(data):
            if at+len(data)>reused.get('blob_offset',len(old_blob)):
                raise ValueError('Fixed owner update overlaps reused resource tail')
            blob[at:at+len(data)]=data; changes.pop(vrom)
    abi=prior['runtime_abi']+1
    blob[0x20:0xE0]=profile_bits; package=blob[PACKAGE:PACKAGE+PACKAGE_SIZE]
    struct.pack_into('>I',blob,0xF8,zlib.crc32(package)); struct.pack_into('>I',blob,4,abi)
    module=bytearray(files[MODULE].extract(base))
    defines=tuple(f[2:] if not f.startswith('-DAF_V3_ABI=') else f'AF_V3_ABI={abi}'
                  for f in prior['startup']['flags'] if f.startswith('-D'))
    startup,startup_report=compile_part('startup',output/'startup',defines=defines)
    old=prior['startup']
    if (sha256(module[STARTUP:STARTUP+old['bytes']]) != old['sha256']
            or any(module[STARTUP+old['bytes']:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed startup reservation')
    module[STARTUP:CONFIG]=startup+bytes(CONFIG-STARTUP-len(startup))
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),abi)
    start,end=files[BLOB].pstart+len(old_blob),files[BLOB].pstart+len(blob)
    if (len(blob)<len(old_blob) or BLOB+len(blob)>END or end>len(base) or any(base[start:end])
            or any(e.pstart<end and start<(e.pend or e.pstart+e.size)
                   for v,e in files.items() if v!=BLOB and e.pstart!=0xFFFFFFFF)
            or any(e.vstart<BLOB+len(blob) and BLOB+len(old_blob)<e.vend for v,e in files.items() if v!=BLOB)):
        raise ValueError('Batch overlaps a live physical or virtual resource')
    changes.update({BLOB:blob,MODULE:module}); result=bytearray(base)
    for vrom,data in changes.items(): result[files[vrom].pstart:files[vrom].pstart+len(data)]=data
    struct.pack_into('>I',result,DMA_START+files[BLOB].index*16+4,BLOB+len(blob))
    for row in moves:
        struct.pack_into('>4I',result,DMA_START+files[row['vrom']].index*16,
            row['vrom'],row['vrom']+row['bytes'],row['physical'],0)
    fix_checksum(result); result=bytes(result)
    if set(by_vrom(result))!=set(files) or result[DMA_END-16:DMA_END]!=bytes(16): raise ValueError('Directory changed')
    patch=make_ups(original,result)
    if apply_ups(original,patch)!=result: raise ValueError('Patch reconstruction failed')
    report=copy.deepcopy(prior)
    report.update(build='v3-automatic-furniture',runtime_abi=abi,input_build_sha256=sha256(base),
        output_sha256=sha256(result),patch_sha256=sha256(patch),blob_sha256=sha256(blob),
        blob_bytes=len(blob),blob_file_bytes=len(blob),startup=startup_report,furniture=all_furniture,
        catalogue=cat_report,shops=stock_report,furniture_behaviours=behaviour_report,
        catalogue_preview_records=preview_report,
        furniture_placement=placement_report,**score_reports,
        native_test='pending representative automatic-import execution')
    report['save_runtime'].update(profile_hex=profile_bits.hex(),profile_sha256=sha256(profile_bits))
    report['furniture_items']['imports'].extend(installed)
    report['furniture_items']['active_metadata_rows']=len(imports)
    for section in report.values():
        if isinstance(section,dict) and 'package_sha256' in section: section['package_sha256']=sha256(package)
    report['import_storage'].update(remaining_bytes=END-BLOB-len(blob),static_installed=len(imports)-1,
        items_installed=len(imports),profile_rows_sha256=sha256(blob[ROWS:ITEMS]),
        item_rows_sha256=sha256(blob[ITEMS:TABLE_END]),saved_profile_changed=True)
    for section in (report['furniture']['imports'],report['furniture_items']['imports']):
        for row in section:
            at=ITEMS+slot(int(row['item_id'],16))*32; row['record_sha256']=sha256(blob[at:at+32])
            row['action_sound']=blob[at+25]
            row['layer_type']=source.raw('aMR_layer_set_info')[row['runtime_index']]
    report['automatic_furniture']=dict(version=VERSION,imports=installed,art_report_sha256=art_sha,
        base=base_pin,art_directory=str(art_path.resolve().relative_to(ROOT)),
        resource_moves=moves,resource_tail_reuse=reused,additional_resident_bytes=0,saved_format_changed=False,
        saved_profile_changed=True,older_builds_accept_new_saves=False,web_patcher_enabled=False,
        catalogue_masks_sha256=sha256(bytes(blob[ITEMS+i*32+24] for i in range(1024))),
        provenance_catalogue_complete=not bool(text_patch))
    report['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    write_new(output/'animal-forest-v3-asset-loader.z64',result); write_new(output/'asset-loader.ups',patch)
    write_new(output/'build.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    pin=dict(directory=str(output.relative_to(ROOT)),runtime_abi=abi,rom_sha256=sha256(result),
        report_sha256=sha256((output/'build.json').read_bytes()))
    write_new(output/'build-lock.json',(json.dumps(pin,indent=2)+'\n').encode())
    write_new(output/'base-lock.json',(json.dumps(base_pin,indent=2)+'\n').encode())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True); parser.add_argument('--art',type=Path,required=True)
    parser.add_argument('--base-lock',type=Path,default=LOCK)
    args=parser.parse_args(); result=build(args.output,args.art,args.base_lock)
    print(json.dumps({k:result[k] for k in ('runtime_abi','output_sha256','patch_sha256')},indent=2))
