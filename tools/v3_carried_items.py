"""Shared remaining carried-item resources, with state variants kept together.

The identity worksheet discovers additions; actual donor tables supply every
name, drawing category, and pocket icon. Destination IDs and usable behaviours
are not inferred from the donor's numeric IDs or from successful conversion.
"""
import json
import re
import struct

from aflib import sha256
from apply_translation import write_new
from item_identity_sheet import SHEET_SHA, sheet_rows
from title_assets import pack4, untile
from v3_asset_loader import ROOT
from v3_item_categories import discover as categories, convert as convert_categories
from v3_villager_art import native_palette

FORMAT='AFV3-CARRIED-ITEMS-PREPARED-1'
SOURCES=('tools/v3_carried_items.py','tools/v3_item_categories.py','tools/v3_ui_art.py',
    'tools/v3_furniture_pipeline.py','tools/v3_furniture_art.py','tools/v3_villager_art.py',
    'tools/map_artwork.py','tools/title_assets.py')
# Source item groups, not a per-item installer/behaviour allowlist. Equipment,
# garments, surfaces, music, and diaries already have their category importers.
GROUPS={0,5,8,9,13}


def states(item):
    """GAFE01-r0 quantity/stamp/count encodings, independent of destination IDs."""
    if item>>8==0x20:return tuple(0x2000+(item&63)+64*n for n in range(4))
    if 0x2523<=item<=0x252F:return tuple(range(0x2523,0x2530))
    if 0x2D28<=item<=0x2D2C:return tuple(range(0x2D28,0x2D2D))
    return (item,)


def group_table(source, main_name, group, stride):
    """Resolve complete relocated tables, retaining their original resources."""
    main,n=source.symbol(main_name);refs=source.pointers(main,n)
    if (n!=64 or source.data[main:main+n]!=bytes(n)
            or set(refs)!=set(range(main,main+n,4)) or not 0<=group<16):
        raise ValueError('Changed complete carried-item table: '+main_name)
    table=refs[main+group*4];symbol,_,size=source.containing(table,exact=True)
    if size%stride:raise ValueError('Incomplete carried-item table records: '+symbol)
    return table,size,dict(main_symbol=main_name,main_offset=main,main_bytes=n,
        main_pointers=refs,symbol=symbol,offset=table,bytes=size,
        sha256=sha256(source.data[table:table+size]))


def records(source, worksheet, installed=()):
    if sha256(worksheet.read_bytes())!=SHEET_SHA:raise ValueError('Changed carried-item identity worksheet')
    excluded=set(installed);parents={}
    for line,fields in sheet_rows(worksheet,'Items'):
        value=fields.get('E','')
        if not re.fullmatch('2[0589D][0-9A-F]{2}',value):continue
        item=int(value,16);family=states(item);parent=family[0];key=f'GAFE01-r0/item/{parent:04X}'
        if (item!=parent or key in excluded or fields.get('HG')!='1'
                or any(fields.get(k,'-')!='-' for k in ('C','H','CG','CJ'))):continue
        if parent in parents:raise ValueError('Ambiguous carried-item worksheet identity')
        parents[parent]=dict(id=key,worksheet_row=line,kind=fields.get('HR','other'),states=family)
    rows=[];tables={}
    for parent,entry in sorted(parents.items()):
        group=(parent>>8)&15
        if group not in tables:
            names,names_size,name_receipt=group_table(source,'itemName_table$398',group,16)
            types,types_size,type_receipt=group_table(source,'item1_tableNo$430',group,1)
            if names_size//16!=types_size:raise ValueError('Carried name/category counts disagree')
            tables[group]=(names,types,types_size,name_receipt,type_receipt)
        names,types,count,name_receipt,_=tables[group]
        for state,item in enumerate(entry['states']):
            index=item&255
            if index>=count:raise ValueError('Carried item state exceeds complete source tables')
            name=source.data[names+index*16:names+(index+1)*16];category=source.data[types+index]
            if not name.rstrip(b' ') or any(c<32 or c>126 for c in name) or not 0<category<53:
                raise ValueError('Unrepresentable carried name or drawing category')
            rows.append(dict(id=entry['id'],item_id=f'{item:04X}',donor_item_id=f'{item:04X}',
                parent_item_id=f'{parent:04X}',state_index=state,state_count=len(entry['states']),
                name=name.decode('ascii').rstrip(),name_sha256=sha256(name),
                name_source_symbol=name_receipt['symbol'],name_source_index=index,
                source_category=category,kind=entry['kind'],worksheet_row=entry['worksheet_row'],
                native_item_id=None,ready=False,selected=False))
    prices=price_records(source,rows)
    return rows,dict(source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()),
        worksheet_sha256=SHEET_SHA,tables=[r for t in tables.values() for r in t[3:]],
        prices=prices,installed_imports=sorted(excluded),parent_count=len(parents),state_count=len(rows))


def price_records(source, rows):
    """Bind complete source price lookup, including paper quantity arithmetic."""
    raw,function=source.function(0x784E0)
    if (len(raw)!=544 or sha256(raw)!='3f45cc5bf10f883d41575bc4f66cd1f8cfa1f86e46795ec386baaf412a7edb2b'
            or raw[0x90:0x94]!=bytes.fromhex('281d251e') or raw[0x98:0x9C]!=bytes.fromhex('386001f4')):
        raise ValueError('Changed complete carried price function')
    at,n=source.symbol('l_price_info');refs=source.pointers(at,n)
    if n!=64 or source.data[at:at+n]!=bytes(n):raise ValueError('Changed complete carried price directory')
    tables={}
    for row in rows:
        item=int(row['donor_item_id'],16);group=item>>8&15
        if group not in GROUPS:raise ValueError('Unsupported carried price group')
        pointer=refs.get(at+group*4);price=0
        if pointer is not None:
            if group not in tables:
                owner,_,width=source.containing(pointer,exact=True);p=source.pointers(pointer,width)
                if width!=4 or set(p)!={pointer} or source.data[pointer:pointer+4]!=bytes(4):
                    raise ValueError('Incomplete carried price-table reference')
                address=p[pointer];symbol,_,size=source.containing(address,exact=True)
                data=source.data[address:address+size]
                if size%2 or source.pointers(address,size):raise ValueError('Incomplete carried price values')
                values=[v for v, in struct.iter_unpack('>H',data)]
                if values[-1]!=65535 or 65535 in values[:-1]:raise ValueError('Unbounded carried price table')
                tables[group]=dict(symbol=symbol,offset=address,bytes=size,sha256=sha256(data),
                    pointer_symbol=owner,pointer_offset=pointer,values=values[:-1])
            index=item&63 if group==0 else item&255
            if index>=len(tables[group]['values']):raise ValueError('Carried state exceeds price table')
            price=tables[group]['values'][index]*(1+(item&255)//64 if group==0 else 1)
        if item==0x251E:price=struct.unpack_from('>H',raw,0x9A)[0]
        row['price']=price
    return dict(function=function,directory=dict(offset=at,bytes=n,pointers=refs),tables=list(tables.values()))


def pocket_icons(source, rows, *, ram=0x06000000):
    """Convert complete CI4 icon pairs; paper chooses quantity, not paper style."""
    if ram%32 or not 0<=ram<=0xFFFFFFFF:raise ValueError('Unaligned carried icon base')
    tables={};pairs={};data=bytearray();bindings=[];seen=set()
    for row in rows:
        item=int(row['donor_item_id'],16);group=(item>>8)&15
        if item>>12!=2 or item in seen:raise ValueError('Duplicate or invalid carried icon identity')
        seen.add(item)
        if group not in tables:
            at,size,receipt=group_table(source,'item_tex_data_table$779',group,8)
            refs=source.pointers(at,size)
            if source.data[at:at+size]!=bytes(size) or set(refs)!=set(range(at,at+size,4)):
                raise ValueError('Incomplete carried pocket-icon bindings')
            tables[group]=(at,size,refs,dict(receipt,pointers=refs))
        at,size,refs,_=tables[group];index=(item&255)//64 if group==0 else item&255
        if index>=size//8:raise ValueError('Carried pocket icon exceeds source table')
        pair=tuple(refs[at+index*8+4*lane] for lane in range(2))
        if pair not in pairs:
            offset=len(data);data.extend(struct.pack('>2I',ram+offset+32,ram+offset+64)+bytes(24));resources=[]
            for lane,address in enumerate(pair):
                symbol,_,size=source.containing(address,exact=True);raw=source.data[address:address+size]
                if size!=(32,512)[lane] or source.pointers(address,size):
                    raise ValueError('Unsupported complete carried pocket icon')
                converted=native_palette(raw) if lane==0 else pack4(untile(raw,32,32,4))
                resources.append(dict(symbol=symbol,source_offset=address,source_sha256=sha256(raw),
                    offset=len(data),bytes=size,sha256=sha256(converted)))
                data.extend(converted)
            pairs[pair]=dict(offset=offset,address=ram+offset,resources=resources)
        bindings.append(dict(item_id=row['item_id'],**pairs[pair]))
    return bytes(data),dict(ram=ram,tables=[r[3] for r in tables.values()],bindings=bindings,
        unique_icons=len(pairs),width=32,height=32,format_native='CI4/RGBA5551')


def discover(source, worksheet, installed=()):
    rows,receipt=records(source,worksheet,installed)
    # Some items (notably spirits) have a handover cage but no direct seasonal
    # ground descriptor. Keep that distinction; do not fabricate a drop model.
    art=categories(source,rows,require_ground=False)
    _,icons=pocket_icons(source,rows)
    _,papers=paper_art(source,rows)
    return dict(receipt,format=FORMAT,rows=rows,icons=icons,categories=art,
        stationery=papers,
        runtime_installed=False,selectable=False,
        pending=['additive destination/readers and saved-profile integration',
            'complete item interactions and ground/field representations',
            'stationery letter-display readers',
            'independent optional selection'])


def paper_art(source, rows):
    """Both donor letter owners must agree on complete backgrounds/line art."""
    from v3_ui_art import Packet
    packet=Packet(source);styles=sorted({int(r['donor_item_id'],16)&63 for r in rows
                                        if int(r['donor_item_id'],16)>>8==0x20})
    tables={};receipt=[];bindings=[]
    for symbol in ('paper_disp_model','paper_disp_sen_model'):
        spans=sorted(source.names[symbol])
        if len(spans)!=2:raise ValueError('Incomplete stationery drawing owners')
        tables[symbol]=[]
        for at,n in spans:
            if n!=256*4 or source.data[at:at+n]!=bytes(n):
                raise ValueError('Changed complete stationery drawing table')
            refs=source.pointers(at,n);tables[symbol].append((at,refs))
            receipt.append(dict(symbol=symbol,offset=at,bytes=n,pointers=refs))
    colours=[(at,n) for at,n in source.names['letter_color'] if n==256*4]
    if len(colours)!=1:raise ValueError('Missing complete stationery text-colour table')
    at,n=colours[0]
    if source.pointers(at,n):raise ValueError('Stationery colour table contains pointers')
    receipt.append(dict(symbol='letter_color',offset=at,bytes=n,sha256=sha256(source.data[at:at+n])))
    for style in styles:
        binding=dict(source_style=style,text_rgba=list(source.data[at+4*style:at+4*style+4]))
        for role,symbol,mode in (('background','paper_disp_model','lat_letter_mode'),
                                 ('lines','paper_disp_sen_model','lat_letter_sen_mode')):
            targets=[refs.get(start+style*4) for start,refs in tables[symbol]]
            if targets[0]!=targets[1] or role=='background' and targets[0] is None:
                raise ValueError('Stationery owners disagree or lack their background')
            if targets[0] is None:binding[role]=None;continue
            root=source.containing(targets[0],exact=True);label=f'paper_{style:02X}_{role}'
            packet.model(label,[mode,root]);binding[role]=label
        bindings.append(binding)
    return packet.prepared() if styles else None,dict(tables=receipt,bindings=bindings,
        installed=False,rendered=False)


def prepare(source, worksheet, output, installed=(), reuse_assets=()):
    from v3_furniture_pipeline import compile_models,assemble_models
    output=output.resolve()
    if not output.is_relative_to(ROOT/'build'):raise ValueError('Donor resources must stay in ignored build output')
    report=discover(source,worksheet,installed)
    output.mkdir(parents=True,exist_ok=False)
    category_reuse=[p/'categories' if (p/'items.json').is_file() else p for p in reuse_assets]
    art=convert_categories(source,output/'categories',parent_records=report['rows'],
        require_ground=False,reuse_assets=category_reuse)
    data,icons=pocket_icons(source,report['rows'])
    write_new(output/'icons.bin',data)
    report.update(categories=art,icons=icons,icon_bytes=len(data),icon_sha256=sha256(data))
    prepared,papers=paper_art(source,report['rows'])
    if prepared:
        directory=output/'stationery';directory.mkdir()
        compiled=None
        for reuse in reuse_assets:
            reuse=reuse.resolve()
            if not (reuse/'items.json').is_file():continue
            prior=json.loads((reuse/'items.json').read_bytes());p=prior['stationery']
            if (prior['format']!=FORMAT or prior['source_rel_sha256']!=report['source_rel_sha256']
                    or prior['source_symbols_sha256']!=report['source_symbols_sha256']
                    or any(p[k]!=json.loads(json.dumps(v)) for k,v in papers.items())):
                raise ValueError('Changed reusable stationery source/bindings')
            file=(reuse/p['file']).resolve()
            if not file.is_relative_to(reuse):raise ValueError('Reusable stationery escapes its bundle')
            old=file.read_bytes()
            if (len(old)!=p['bytes'] or sha256(old)!=p['sha256'] or old[:len(prepared[1])]!=prepared[1]
                    or p['resources']!=prepared[2] or (reuse/'stationery/commands.c').read_text()!=prepared[5]):
                raise ValueError('Changed complete reusable stationery resources')
            compiled={}
            for model in p['models']:
                label=model['layer'];start=model['native_offset'];n=model['bytes'];code=old[start:start+n]
                if label in compiled or sha256(code)!=model['output_sha256']:
                    raise ValueError('Changed reusable stationery display list')
                compiled[label]=code
            data,offsets,models,_=assemble_models(prepared,compiled)
            if data!=old or offsets!=p['offsets'] or models!=p['models']:
                raise ValueError('Reusable stationery differs from complete assembly')
            papers['reused_from']=str(reuse.relative_to(ROOT))
            write_new(directory/'commands.c',prepared[5].encode())
            break
        if compiled is None:data,offsets,models,_=compile_models(directory,prepared)
        write_new(directory/'paper.bin',data)
        papers.update(file='stationery/paper.bin',bytes=len(data),sha256=sha256(data),
            resources=prepared[2],models=models,offsets=offsets,
            caller_contracts={name:model['caller'] for name,model in prepared[4].items()})
    report['stationery']=papers
    report['sources']={path:sha256((ROOT/path).read_bytes()) for path in SOURCES}
    write_new(output/'items.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def design_field_art(source):
    """Complete placed-object models with live, not baked-in, design bindings."""
    from v3_furniture_pipeline import prepare_models
    frames=[]
    for kind,segment,names in (
        ('palette',0x08000000,['hakushi_pal']+[f'needlework{i}_pal' for i in range(16)]),
        ('texture',0x09000000,['hakushi_tex'])):
        rows=[]
        for name in names:
            at,n=source.symbol(name)
            if n!=(32 if kind=='palette' else 512) or source.pointers(at,n):
                raise ValueError('Changed complete custom-design material')
            rows.append(dict(symbol=name,donor_offset=at,bytes=n))
        frames.append(dict(kind=kind,segment_address=segment,frames=rows,
            selector='live player design or blank sign'))
    descriptor=dict(kind='custom-design-field-models',models={
        label:(name,*source.symbol(name)) for label,name in (
            ('pattern','write_model'),('ordinary','obj_sign_s_model'),
            ('winter','obj_sign_w_model'),('shadow','obj_kanban_shadowT_model'))},
        callback_adapter=dict(category='actor-model-assets',material_frames=frames),
        vertex_bindings={0x0A000000:source.symbol('obj_kanban_shadow_v')[0]})
    return prepare_models(source,descriptor)


def design_defaults(source, disc_path):
    """Read the actual four templates and complete palette/name providers.

    Only the first four 512-byte blocks of my_original.bin are design images.
    The donor initializer never reads its unrelated trailing archive bytes.
    Empty slots use mNW_InitOriginalData, not the overwritten plain-cloth names.
    """
    from gamecube import Disc,rarc_files
    from v3_import_catalog import DONOR_FILES,DECODER_SHA
    from v3_villager_text import read_text_donor
    from textbanks import Bank
    from gc_text import decoder_tables,decode_gc
    from textcodec import ENCODE,LATIN
    first=read_text_donor(disc_path)
    with Disc(disc_path) as disc:
        entries=[e for e in disc.files() if e['path']=='forest_2nd.arc']
        size,digest=DONOR_FILES['forest_2nd.arc']
        if disc.header[:8]!=b'GAFE01\0\0' or len(entries)!=1 or entries[0]['size']!=size:
            raise ValueError('Custom designs require the complete GAFE01-r0 archive')
        raw=disc.read(entries[0]['offset'],size)
        if sha256(raw)!=digest:raise ValueError('Changed custom-design donor archive')
    members=dict(rarc_files(first));second=dict(rarc_files(raw))
    original=second['data/my_original.bin']
    if len(original)!=11712 or sha256(original)!='2109ff2ac7682fce001e79b52b56f9c9db2326633760a42790b8cbcba2d7e1e6':
        raise ValueError('Changed complete custom-design template resource')
    decoder=ROOT/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes())!=DECODER_SHA:raise ValueError('Changed official design-name decoder')
    strings=Bank('string',0,0,members['data/string_data.bin'],members['data/string_data_table.bin']).entries()
    tables=decoder_tables(decoder);initial_palettes=source.raw('pal_table$400')
    blank=source.raw('name$543')
    if initial_palettes!=bytes((0,8,7,7,0,0,0,0)) or blank!=b'blank           ':
        raise ValueError('Changed source design initialization')
    at,n=source.symbol('mNW_needlework_pallet_table');refs=source.pointers(at,n)
    if (n!=64 or source.data[at:at+n]!=bytes(n) or
            refs!={at+4*i:source.symbol(f'needlework{i}_pal')[0] for i in range(16)}):
        raise ValueError('Incomplete design palette directory')
    templates=bytearray();credits=[]
    for i in range(8):
        name=strings[0x6DF+i] if i<4 else blank
        text=decode_gc(name,tables).rstrip(' ')
        encoded=bytes(ENCODE[c] for c in text)
        if not 0<len(encoded)<=16 or any(c not in LATIN for c in encoded):
            raise ValueError('Unrepresentable complete design name')
        encoded=encoded.ljust(16,b' ')
        texture=pack4(untile(original[i*512:(i+1)*512],32,32,4)) if i<4 else bytes([255])*512
        templates.extend(encoded+bytes((initial_palettes[i],))+bytes(15)+texture)
        if i<5:
            key=f'v3/carried/design/name/{i}'
            credits.append(dict(id=key,native_sha256=None,locales=dict(en=dict(
                credit='official',locator=['tools/v3_carried_items.py:design_defaults',key],
                source=dict(source='user-supplied GAFE01 revision 0 disc',
                    reference_id=f'string:{0x6DF+i:04X}' if i<4 else 'REL:name$543',
                    reference_sha256=sha256(name)),
                adaptations=['Native encoding and field padding; unchanged official wording'],
                human_review='not_recorded',encoded_sha256=sha256(encoded)))))
    return bytes(templates),dict(players=4,designs_per_player=8,record_bytes=544,
        texture_bytes=512,palette_count=16,width=32,height=32,
        archive_sha256=sha256(raw),template_member='data/my_original.bin',
        template_member_bytes=len(original),template_member_sha256=sha256(original),
        consumed_template_bytes=2048,palette_indices=list(initial_palettes),
        palette_directory=dict(offset=at,bytes=n,pointers=refs),
        provenance_entries=credits)


def prepare_design_fields(source, disc_path, output):
    """Shared carried category dependency; no admission or native hook claims."""
    from v3_furniture_pipeline import compile_models
    from text_provenance import validate
    from v3_asset_loader import compile_part
    output=output.resolve()
    if not output.is_relative_to(ROOT/'build'):raise ValueError('Design assets must remain in ignored build output')
    prepared=design_field_art(source);templates,defaults=design_defaults(source,disc_path)
    catalogue=json.loads((ROOT/'translations/provenance.json').read_bytes());validate(catalogue)
    indexed={r['id']:r for r in catalogue['entries']}
    if any(indexed.get(r['id'])!=r for r in defaults['provenance_entries']):
        raise ValueError('Custom-design names require their exact single-catalogue credits')
    output.mkdir(parents=True,exist_ok=False)
    data,offsets,models,_=compile_models(output,prepared)
    code,compiled=compile_part('carried_designs',output/'services',
        link_symbols={'AF_CARRIED_DESIGN_RAM':0x807C9000})
    write_new(output/'field.bin',data);write_new(output/'templates.bin',templates)
    functions={}
    for at,labels in source.functions.items():
        names=[name for name,_ in labels if name.startswith('aSIGN_') or
               name.startswith('mNW_') and 0x59644<=at<0x59CD4]
        if names:
            _,receipt=source.function(at);functions[names[0]]=receipt
    if len([name for name in functions if name.startswith('aSIGN_')])!=31:
        raise ValueError('Incomplete placed-design actor consumer map')
    report=dict(format='AFV3-CARRIED-DESIGN-FIELDS-1',source_rel_sha256=sha256(source.rel),
        source_symbols_sha256=sha256(source.symbols.encode()),
        art=dict(file='field.bin',bytes=len(data),sha256=sha256(data),offsets=offsets,
            resources=prepared[2],models=models,descriptor=prepared[0]),
        defaults=dict(defaults,file='templates.bin',bytes=len(templates),sha256=sha256(templates)),
        services=dict(compiled,file='services/code.bin',ram=0x807C9000,
            saved_bytes=17440,installed=False),
        functions=functions,runtime_installed=False,selectable=False,
        pending=['native placement, collision, pickup, renderer, and interaction callbacks',
            'design selector and pixel-editor menu integration',
            'complete town/save/travel transaction integration','independent sign-board selection'])
    report['sources']={p:sha256((ROOT/p).read_bytes()) for p in (*SOURCES,
        'overlays/v3/carried_designs.c','overlays/v3/carried_designs.h','overlays/v3/carried_designs.ld')}
    write_new(output/'designs.json',(json.dumps(report,indent=2)+'\n').encode())
    return report
