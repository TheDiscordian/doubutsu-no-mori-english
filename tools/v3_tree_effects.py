"""Complete tree-effect resources, shared across families, seasons, and actions.

All fourteen source tables feed the existing model and keyframe converters in
one batch. Preparation is not native effect installation or item admission.
"""
import json
import re
import struct

from aflib import sha256
from apply_translation import write_new
from v3_furniture_pipeline import prepare_models,assemble_models,compile_commands_batch
from v3_keyframes import skeleton,animation,compile_skeleton,compile_animations
from v3_scenery import consumers,palettes

FORMAT='AFV3-TREE-EFFECT-ASSETS-1'
FUNCTIONS=(
    (0xA721C,'9e32c6a9e5e1b58553e8f7531df30981a3e6b21c5979857dcdff617f7d13956a'),
    (0xA72C4,'f332ea5b5437103cbb6f1508679da89eec9288ad775c96c439a17fccabe3de8e'),
    (0xA72C8,'6ca65f93fe23218f8415d5c4b5fc9acb0e54f3d2879b5237cab8c4f2c09a58e8'),
    (0xA7658,'963b2d9717fd9dfbe84d8148e39769f2b4ca5a260e85e4cac6307c00f3043762'),
    (0xA7A90,'4c9cf607e1018f149d6b1d808310c7d99da963db5aff5ea875e3976b9c3c31ed'),
    (0xA7F10,'4b03e9d88b4223997ca54f860d33e054ddf5a23c06580c22c0e26903e840bce8'),
    (0xA7F1C,'7d1d0e7d47bf117ea8cf9a6817ead6f9b450ebd14b919a659e7b1818ed559b2e'),
    (0xA8408,'262cc63befdc6167240c78fddf0eec76804bb87a3162bb8d224a9595f1a25f10'),
    (0xA846C,'53da5c104980501ad3ad61431b8a9c9a948d1d6f4df70cf92f190e588657eddb'),
    (0xA8694,'07d1fbff385694368aaf01d199c641da6b59d4b4f599d777f8267167769dbfd9'),
    (0xA892C,'8ba574d15f8cc4c3a4e55f5ff13a5fcc99dcef4592e406ea2178e8edeea8aac0'),
    (0xA89F0,'5925b3069bc5bb3186668138b230a345f49770a435cd5c913bb16b0981895fc1'),
    (0xA8C40,'97e54a242695236d868a7c49463f9261b0bacce991a6d684e9f59d90b6255014'),
    (0xA8E84,'c7dbb63a8912c43e570cd3f643180ce8a400deecbe77ebf8498094aa6ccb3a1a'),
    (0x2967C0,'c1434202b2d081ceb44973a6260e290b2b563f6b6e0d9057cbcb74fb52a9dce5'),
    (0x296860,'03942c3695c75665941c9fa315ef39922f939b28e4624156a20d63b23dfdb97c'),
    (0x296BBC,'ef32379dc3e015efea5981b62979abbc224063168ce3b37d53586bb27a931398'),
    (0x296D7C,'f328efa80f0caf86dbdc6341cfba5ae1d41b1bf3d07591960e114e10773ac603'),
    (0x2B66AC,'195c13297d3b4484cd47c1c5c7bc5994dc14ce239233fbcffa67b9327f0ff829'),
    (0x2B6728,'761fc7e2e18cdc2416911dcb1e6f14ef2697db0a326e0ac8f84eb31d513c40c0'),
    (0x2B68D8,'a5a37526ca140fa24571aa7559cd4f16769823aee0dd43e1287c65712ebe6daf'),
    (0x2B6B8C,'4d61cc33e69eb4da29a9f068237d9ca93097603f13d21d8fa4c0679a62f04c18'))


def prepare(source):
    functions=[]
    for at,digest in FUNCTIONS:
        raw,row=source.function(at)
        if sha256(raw)!=digest:raise ValueError('Changed complete tree-effect consumer: '+row['symbol'])
        functions.append(row)
    names=sorted(n for n in source.names if re.fullmatch(
        r'(cherry_tree|summer_(tree|palm|cedar)|winter_(tree|palm|cedar))_(model|anime)_tbl',n))
    if len(names)!=14:raise ValueError('Incomplete tree-effect seasonal tables')
    tables=[];rigs={};motions={};models={}
    for name in names:
        at,n=source.symbol(name);refs=source.pointers(at,n)
        if n!=60 or any(source.data[at:at+n]) or set(refs)!=set(range(at,at+n,4)):
            raise ValueError('Incomplete tree-effect model/animation table')
        targets=[refs[at+i*4] for i in range(15)]
        tables.append(dict(symbol=name,donor_offset=at,bytes=n,sha256=sha256(source.data[at:at+n]),targets=targets))
        for target in targets:
            if '_model_' in name:rigs.setdefault(target,skeleton(source,target))
            else:motions.setdefault(target,animation(source,target))
    ctor=next(f for f in functions if f['symbol']=='EffectBG_object_ct')
    referenced={r[3] for r in ctor['relocations'].values() if r[1:3]==(1,5)}
    # The checked compiler uses one common base plus constant table offsets,
    # not fourteen separately relocated addresses.
    addresses=sorted(t['donor_offset'] for t in tables)
    if referenced!={addresses[0]} or addresses!=list(range(addresses[0],addresses[0]+14*60,60)):
        raise ValueError('Seasonal resources are not bound to the complete effect constructor')
    indexed={t['symbol']:t for t in tables}
    for table in tables:
        if '_model_' not in table['symbol']:continue
        partner=indexed[table['symbol'].replace('_model_','_anime_')]
        for bone,motion in zip(table['targets'],partner['targets'],strict=True):
            if rigs[bone]['joints']!=motions[motion]['joints']:
                raise ValueError('Tree-effect joint/animation dimensions differ')
    for rig in rigs.values():
        if rig['joints']>6 or rig['shown_joints']>6:raise ValueError('Unbounded tree-effect joint workspace')
        for joint in rig['rows']:
            if 'model' in joint:
                row=joint['model'];models[row['donor_offset']]=(row['symbol'],row['donor_offset'],row['bytes'])
    extras=[];retained=[]
    for function in (f for f in functions if f['symbol'] in ('eBushHappa_dw','eYoung_Tree_dw')):
        targets={r[3] for r in function['relocations'].values() if r[1:3]==(1,5)}
        for target in sorted(targets):
            name,at,n=source.containing(target,exact=True)
            if not name.endswith('modelT'):raise ValueError('Unresolved tree-effect sprite dependency')
            if name=='ef_s_yabu01_00_modelT':
                # The source's arg1<=3 path is the original shrub effect, with
                # its separate live BSS palette. Keep that native path intact.
                retained.append(dict(symbol=name,donor_offset=at,bytes=n,reason='original shrub branch'))
                continue
            models[at]=(name,at,n);extras.append(dict(symbol=name,donor_offset=at,bytes=n,consumer=function['symbol']))
    pal_functions=consumers(source)
    banks={name:palettes(source,pal_functions,name)[0] for name in ('cedar','palm','gold')}
    frames=[]
    for family,bank in banks.items():
        row=bank['bank']
        for i in range(bank['palette_count']):
            at=row['donor_offset']+i*32
            frames.append(dict(symbol=f'{row["symbol"]}[{i}]',donor_offset=at,bytes=32,
                source_sha256=sha256(source.data[at:at+32]),family=family,frame=i))
    descriptor=dict(kind='tree-effect-models',models={f'm{at:X}':row for at,row in sorted(models.items())},
        callback_adapter=dict(category='actor-model-assets',material_frames=[
            dict(kind='palette',segment_address=segment,frames=frames,
                selector=dict(input='tree-family-and-calendar-term',native_consumer_required=True))
            for segment in (0x08000000,0x09000000)]))
    prepared=prepare_models(source,descriptor)
    info=dict(format='AFV3-TREE-EFFECT-SOURCES-1',category='tree-effects',
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()),
        functions=functions,tables=tables,skeletons=list(rigs.values()),animations=list(motions.values()),
        sprites=extras,retained_native=retained,palettes=banks,
        counts=dict(tables=len(tables),table_entries=sum(len(t['targets']) for t in tables),
            skeletons=len(rigs),animations=len(motions),models=len(models),sprites=len(extras),
            resources=len(prepared[2]),max_joints=max(r['joints'] for r in rigs.values())),
        runtime_installed=False,selectable=False,logical_imports_added=0,
        pending_reason='Bind complete native actor/effect callbacks, lifetimes, seasonal callers, and selected-family admission.')
    return info,prepared


def discover(source):return prepare(source)[0]


def assemble(source,info,prepared,compiled):
    asset,offsets,models,sequence=assemble_models(prepared,compiled)
    if sequence is not None:raise ValueError('Tree joints cannot become a flattened draw sequence')
    body=bytearray(asset);rigs=[]
    roots={m[1]:offsets[k] for k,m in prepared[0]['models'].items()}
    for rig in info['skeletons']:
        used={r['model']['donor_offset'] for r in rig['rows'] if 'model' in r}
        suffix,receipt=compile_skeleton(source,rig,{p:roots[p] for p in used},start=len(body))
        body.extend(suffix);rigs.append(receipt)
    motion,animations=compile_animations(source,info['animations'],start=len(body))
    body.extend(motion)
    return bytes(body),dict(profile=prepared[0],resources=prepared[2],compiled_models=models,
        model_offsets=offsets,artwork_bytes=len(asset),rigs=rigs,compiled_animations=animations,
        object_file='tree-effects.n64obj.bin',object_bytes=len(body),object_sha256=sha256(body))


def checked(source,directory):
    info,prepared=prepare(source);art=json.loads((directory/'art.json').read_bytes())
    if art.get('format')!=FORMAT or any(art.get(k)!=json.loads(json.dumps(v)) for k,v in info.items() if k!='format'):
        raise ValueError('Prepared tree effects differ from the complete source category')
    row=art['object'];data=(directory/'tree-effects.n64obj.bin').read_bytes()
    if (row['object_file']!='tree-effects.n64obj.bin' or len(data)!=row['object_bytes'] or
            sha256(data)!=row['object_sha256'] or (directory/'commands.c').read_text()!=prepared[5]):
        raise ValueError('Changed complete tree-effect asset or command source')
    sections={m['layer']:data[m['native_offset']:m['native_offset']+m['bytes']] for m in row['compiled_models']}
    rebuilt,receipt=assemble(source,info,prepared,sections)
    if rebuilt!=data or json.loads(json.dumps(receipt))!=row:
        raise ValueError('Incomplete tree-effect models, skeletons, or animation channels')
    return art,data,sections


def convert(source,output,selected=(),*,reuse_assets=()):
    if selected:raise ValueError('Tree effects are a complete dependency category, not individual imports')
    info,prepared=prepare(source);cached=None
    for directory in reuse_assets:
        _,data,sections=checked(source,directory)
        if cached and cached!=(data,sections):raise ValueError('Conflicting complete tree-effect caches')
        cached=data,sections
    output.mkdir(parents=True,exist_ok=False);commands=output/'commands.c'
    write_new(commands,prepared[5].encode())
    sections=cached[1] if cached else compile_commands_batch(output/'compiled',[
        ('tree-effects',commands,prepared[6])])['tree-effects']
    data,receipt=assemble(source,info,prepared,sections)
    if cached and data!=cached[0]:raise ValueError('Reused tree effects differ from assembly')
    write_new(output/receipt['object_file'],data)
    report=dict(info,format=FORMAT,version=1,object=receipt)
    write_new(output/'inventory.json',(json.dumps(info,indent=2)+'\n').encode())
    write_new(output/'art.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps(dict(converted='tree-effects',bytes=len(data),**info['counts'])),flush=True)
    return report
