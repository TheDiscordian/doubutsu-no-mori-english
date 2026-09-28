"""Compile the complete decoration lifecycles against explicit native services.

The source call graph supplies every local movement and interaction function.
Prepared rendering/artwork are retained, not rebuilt. Unbound engine services
remain admission dependencies; generated donor source stays in ignored output.
"""
import copy
import json
import re
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from apply_translation import write_new
from v3_asset_loader import ROOT, compile_part
from v3_holiday_structures import PREPARED, prepared_packet, source_bundle
from v3_furniture_pipeline import Source
from v3_password_policy import constants, function
from v3_registry import DECORATION_NAMES, DECORATION_PROFILES, DECORATION_REGISTRY_VERSION, DECORATION_DUMMIES

RAM, END = 0x8072A000, 0x80730000
CONTEXT, SERVICES, FG_RESULT = 0x80705000, 0x80705100, 0x807051F0
DESCRIPTORS, PROFILES, DATA_END = 0x80705200, 0x80705400, 0x80705600
# Complete current native actor images and the actual foreground write in each
# initializer. Turi uses the translation's relocated owner, not its old VROM.
NATIVE_MARKERS = (
    ('Goza_Profile',0x936470,0x80A761D0,0x80A765BC,0xF108,'f582d19a9ac5e9b590e4ab77de334d03914750843694360fb4d7c910f55b1380'),
    ('Radio_Profile',0x936BC0,0x80A76920,0x80A76C48,0xF109,'4c45b8e61108db3c95e0e046090b474d16abdcbf0aa1f0be4d60380580729226'),
    ('Yatai_Profile',0x937120,0x80A76E80,0x80A7728C,0xF10A,'e5687d71cf30895cfc7166391a1ffb99756de9a7ae3211b07a9633108aaa6395'),
    ('Mikuji_Profile',0x9428A0,0x80A82600,0x80A82974,0xF10D,'f703f3c123d8a1433af942970bae72c8592ea7d53c608a9c608b26a6ff7d8b0d'),
    ('Count_Profile',0x944E90,0x80A84BF0,0x80A85270,0xF10E,'4cd38ec47aa9e77dcb892daff87e8485ddb56de27b2b76e12f2bf0dc55cb9099'),
    ('Count02_Profile',0x94B4B0,0x80A8B230,0x80A8B8E4,0xF10F,'ec0d4ecb90e43428bdccb9ca20ede1ecacb9189bb205e4d07c981607036f1db1'),
    ('Tama_Profile',0x94F170,0x80A8EEF0,0x80A8F0E8,0xF110,'80707356e96e871e46d5b4be50912b2a3605adc72d16875ee1592e065c31148f'),
    ('Kago_Profile',0x94F570,0x80A8F2F0,0x80A8F544,0xF111,'ab7b6ca1c11b87b107a51b889e61871efde7e5e0726b15ec7433807052d497e2'),
    ('Turi_Profile',0x3B40000,0x80A8FCF0,0x80A9065C,0xF111,'1b24b4166dd58c18f2c24fc4841242f0c4628b97cca080e0ecf94400e31f66cd'),
)
ADDITIVE_MARKERS={'Ghog_Profile':0xF125,'Htable_Profile':0xF126}
MARKER_CONSUMERS=(
    ('full-width transient field store',CODE_VROM,CODE_RAM,0x8008A81C,0x8008A960,
        '33ba2059735f9dd36b8a937fe3b2e8633a0ecfcd92ffef19c03c75794e2c78d2'),
    ('non-item categories return the default table',CODE_VROM,CODE_RAM,0x800A5630,0x800A56CC,
        '3f10a86cfa73efde36ac9ff3f08ae9ebf5a4517756ef73f7950a5ab8ce1eaf7e'),
    ('foreground drawing excludes marker category',0x805E30,0x8090D530,0x80913010,0x80913344,
        '75bf81404396388cb475e64b1dd63caea96e9e8b61e66d52208cea23bc567922'),
)
NATIVE = {
    'af_decor_native_player': 'get_player_actor_withoutCheck',
    'af_decor_native_delete': 'Actor_delete',
    'af_decor_native_fg': 'mFI_GetUnitFG',
    'af_decor_native_fg_set': 'mFI_SetFG_common',
    'af_decor_native_status': 'mEv_check_status',
    'af_decor_native_rig_ct': 'cKF_SkeletonInfo_R_ct',
    'af_decor_native_rig_init': 'cKF_SkeletonInfo_R_init',
    'af_decor_native_rig_play': 'cKF_SkeletonInfo_R_play',
    'af_decor_native_make': 'Actor_info_make_actor',
    'af_decor_native_ground': 'mCoBG_GetBgY_OnlyCenter_FromWpos2',
    'af_decor_native_demo': 'mDemo_Check',
    **{n: n for n in ('mFI_Wpos2BlockNum', 'mFI_Wpos2UtNum', 'mFI_UtNum2CenterWpos',
        'mCoBG_GetBgY_OnlyCenter_FromWpos', 'zelda_malloc', 'zelda_free',
        'Matrix_Position', 'Matrix_push', 'Matrix_pull', 'Matrix_translate',
        'cKF_SkeletonInfo_R_dt')},
}
SOURCES = ('tools/v3_decoration_actor.py', 'tools/v3_registry.py',
    'overlays/v3/decoration_actor.c', 'overlays/v3/decoration_actor.h',
    'overlays/v3/decoration_actor.ld', 'overlays/v3/decoration_draw.h',
    'tools/v3_asset_loader.py', 'tools/v3_decoration_draw.py', 'tools/v3_room_goods.py')


def source_constants():
    text = ''; refs = {}
    for file in ('m_ftr_def.h', 'm_name_table.h', 'ac_structure.h'):
        raw = (ROOT/'local/ac-decomp/include'/file).read_bytes()
        refs['include/'+file] = sha256(raw)
        clean = re.sub(r'/\*.*?\*/|//[^\n]*', '', raw.decode(), flags=re.S)
        text += constants(clean)
    for file, enum in (('m_demo.h', 'demo_type'), ('m_event.h', 'event_table')):
        raw = (ROOT/'local/ac-decomp/include'/file).read_bytes()
        refs['include/'+file] = sha256(raw)
        text += re.search(r'\benum '+enum+r'\s*\{.*?\};', raw.decode(), re.S)[0]+'\n'
    text += '#define mEv_STATUS_PLAYSOUND (1 << 3)\n#define CHAR_SPACE 32\n'
    return text, refs


def controller_sources(art, renderer, directory):
    prelude, headers = source_constants()
    write_new(directory/'source-constants.h', prelude.encode())
    header = '#include "/source/overlays/v3/decoration_actor.h"\n#include "source-constants.h"\n'
    diagnostic = ''.join('#pragma GCC diagnostic ignored "-W'+w+'"\n' for w in
        ('unused-parameter', 'unused-variable', 'unused-but-set-variable'))
    files = []; owners = []; registry = []; declarations = []; link = {}; draw_tick = None
    if set(art['owners']) != set(DECORATION_PROFILES) or {b['source_name'] for b in art['bindings']} != set(DECORATION_NAMES):
        raise ValueError('Complete decoration registry differs from source layouts')
    pattern = r'(?:extern|static)\s+[^;{}]*?\b(\w+)\s*\([^;{}]*\)\s*\{'
    for index, (owner, row) in enumerate(art['owners'].items()):
        root = next(p for p in row['references'] if p.endswith('.c'))
        text, refs = source_bundle(ROOT/'local/ac-decomp'/root)
        funcs = {m[1]: function(text, m[1]) for m in re.finditer(pattern, text)}
        names = {phase: row['callbacks'].get(str(off), {}).get('symbol')
            for phase, off in (('ctor', 16), ('dtor', 20), ('init', 24))}
        if names['dtor'] not in funcs:
            if names['dtor'] not in (None, 'none_proc1'):
                raise ValueError('Unresolved external decoration destructor: '+str(names['dtor']))
            names['dtor'] = None
        init = funcs[names['init']]
        moves = re.findall(r'\bmv_proc\s*=\s*&?(\w+)\s*;', init)
        if len(moves) != 1 or moves[0] not in funcs:
            raise ValueError('Unresolved actual movement callback: '+owner)
        names['move'] = moves[0]
        # Source init includes exactly one movement step; the native adapter
        # adds the other 60-Hz step without repeating foreground initialization.
        if len(re.findall(r'\b'+names['move']+r'\s*\(', init)) != 1:
            raise ValueError('Changed source initialization movement cadence')
        selected = set(n for n in names.values() if n)
        pending = list(selected)
        while pending:
            name = pending.pop()
            for dep in set(re.findall(r'\b\w+\b', funcs[name])) & funcs.keys():
                if dep not in selected and not dep.endswith('_set_bgOffset'):
                    selected.add(dep); pending.append(dep)
        bodies = [funcs[n] for n in funcs if n in selected]
        entries = {p: f'af_decor_owner_{p}_{index}' for p in names}
        prototypes = [b[:b.index('{')].strip()+';' for b in bodies]
        combined = '\n'.join(bodies)
        dummy = re.findall(r'\bmFI_SetFG_common\((\w+|0x[0-9A-Fa-f]+),', init)
        if len(dummy) != 1: raise ValueError('Unresolved owner foreground identity')
        source_dummy = next((source for native_owner,_,_,_,source,_ in NATIVE_MARKERS
            if native_owner==owner), ADDITIVE_MARKERS.get(owner))
        if source_dummy is None: raise ValueError('Unbound source foreground marker: '+owner)
        native_dummy=DECORATION_DUMMIES[source_dummy]
        # Only native identities differ. Every constructor still computes its
        # actual source variant, rather than indexing with a destination ID.
        combined = re.sub(r'\b(\w+)->npc_id\b', r'af_decor_source_name(\1)', combined)
        combined = re.sub(r'\b\w+_set_bgOffset\(([^,;]+)(?:,[^;]+)?\);',
            r'af_decor_source_collision((ACTOR*)\1);', combined)
        combined, count = re.subn(r'\b([\w.>\-]+)\.mv_proc\s*=\s*&?'+names['move']+r'\s*;',
            lambda m: f'af_decor_source_move_install((ACTOR*)&{m[1]},{entries["move"]});', combined)
        combined, count2 = re.subn(r'\b(\w+)->mv_proc\s*=\s*&?'+names['move']+r'\s*;',
            lambda m: f'af_decor_source_move_install({m[1]},{entries["move"]});', combined)
        if count+count2 != 1: raise ValueError('Missing deletion-safe movement installation')
        combined = re.sub(r'\baCOU_clip\b', 'af_decor_actor_context.countdown', combined)
        combined = re.sub(r'\baTRC_clip\b', 'af_decor_actor_context.fishing', combined)
        # Some donor state callbacks omit the unused game argument and cast
        # the pointer. Supply typed adapters instead of depending on that cast.
        action_wrappers = []
        for name in sorted(set(re.findall(r'\(aSTR_MOVE_PROC\)\s*&?(\w+)', combined)) & selected):
            signature = funcs[name][:funcs[name].index('{')]
            args = re.search(r'\(([^()]*)\)', signature)[1].split(',')
            if len(args) == 1:
                kind = args[0].rsplit('*', 1)[0].strip()
                wrapper = 'af_decor_action_'+name
                action_wrappers.append(f'static void {wrapper}(STRUCTURE_ACTOR *a,GAME_PLAY *g) {{ (void)g;{name}(({kind}*)a); }}')
                combined = re.sub(r'\(aSTR_MOVE_PROC\)\s*&?'+name+r'\b', wrapper, combined)
        # All controller-local tables are constant; clips use explicitly owned
        # storage, and no compiler-created BSS is left outside startup loading.
        combined = re.sub(r'static\s+(?!const\b)((?:aSTR_MOVE_PROC|RADIO_PROC|float|s16|int|u8)\s+)(?=\w+\s*\[)',
            r'static const \1', combined)
        combined = combined.replace('static void* process[]', 'static void* const process[]')
        decl = []
        for kind, name in re.findall(r'extern\s+(cKF_Skeleton_R_c|cKF_Animation_R_c)\s+(\w+)\s*;', text):
            rig = next(b['rig'] for b in renderer['bindings'] if b['owner'] == owner)
            link[name] = rig['skeleton' if kind == 'cKF_Skeleton_R_c' else 'animation']
            decl.append('extern '+kind+' '+name+';')
        enums = '\n'.join(m[0] for m in re.finditer(r'\benum\s*\{.*?\};', text, re.S))
        exports = []
        for phase, entry in entries.items():
            declarations.append(f'void {entry}(ACTOR*,GAME*);')
            call = names[phase]+'(a,g);' if names[phase] else '(void)a;(void)g;'
            exports.append(f'void {entry}(ACTOR *a,GAME *g) {{ {call} }}')
        generated = (header+diagnostic+enums+'\n'+'\n'.join(decl+prototypes+action_wrappers)+
            f'\nvoid {entries["move"]}(ACTOR*,GAME*);\n'+combined+'\n'+'\n'.join(exports)+'\n')
        if native_dummy:
            generated+=f'_Static_assert({dummy[0]}=={source_dummy},"Source foreground identity");\n'
        file = directory/f'owner-{index:02}.c'
        write_new(file, generated.encode()); files.append(str(file.relative_to(ROOT)))
        dependencies = 2 | (1 if 'mDemo_Check' in combined else 0)
        dependencies |= 4 if 'effect_make_proc' in combined else 0
        dependencies |= 8 if 'mFR_' in combined else 0
        dependencies |= 16 if 'mPr_GetPossessionItemIdxWithCond' in combined else 0
        for b in art['bindings']:
            if b['owner'] != owner: continue
            registry.append('{'+','.join(map(str, (b['source_name'], DECORATION_NAMES[b['source_name']],
                DECORATION_PROFILES[owner], index)))+f',{dummy[0]},{native_dummy},{dependencies},'+
                ','.join(entries[p] for p in ('ctor','dtor','init','move'))+'}')
        owners.append(dict(owner=owner, entries=entries, dependencies=dependencies, references=refs,
            source_functions={n: sha256(funcs[n].encode()) for n in sorted(selected)},
            generated_sha256=sha256(generated.encode()), source_dummy=dummy[0],native_dummy=native_dummy))
        # Drawing advances the digit flip once as well as drawing geometry.
        # Extract that exact source tail for the second 60-Hz state step;
        # geometry is submitted only once, and culled/rejected draws do not tick.
        if owner=='Count02_Profile':
            draw=function(text,row['callbacks']['28']['symbol'])
            match=re.search(r'(\n    if \(actor->arg0 != actor->arg1\) \{.*\n    \})\n\}$',draw,re.S)
            if not match: raise ValueError('Changed countdown draw-state transition')
            source_name=next(b['source_name'] for b in art['bindings'] if b['owner']==owner)
            draw_tick=(f'void af_decor_source_draw_tick(ACTOR *a) {{\n'
                f'if (af_decor_source_name(a)!={source_name}) return;\n'
                'STRUCTURE_ACTOR *actor=(STRUCTURE_ACTOR*)a;'+match[1]+'\n}\n')
            owners[-1]['draw_tick_source_sha256']=sha256(draw.encode())
            owners[-1]['draw_tick_tail_sha256']=sha256(match[1].encode())
    if draw_tick is None: raise ValueError('Missing complete countdown draw-state adapter')
    table = header+'\n'.join(declarations)+'\nconst AFDecorActorRecord af_decor_actor_records[18]={\n'+',\n'.join(registry)+'\n};\n'
    table += draw_tick
    file = directory/'registry.c'; write_new(file, table.encode()); files.append(str(file.relative_to(ROOT)))
    return files, link, owners, headers


def native_bindings(base, prior):
    symbols = (ROOT/'upstream/af/linker_scripts/jp/symbol_addrs_code.txt').read_text()
    addresses = {n: int(a,16) for n,a in re.findall(r'^(\w+) = (0x[0-9A-Fa-f]+);', symbols, re.M)}
    functions = sorted(int(a,16) for a in re.findall(r'^\w+ = (0x[0-9A-Fa-f]+); // type:func', symbols, re.M))
    core = by_vrom(base)[CODE_VROM].extract(base); link = {}; receipts = []
    for name, native in NATIVE.items():
        start = addresses[native]; end = next(a for a in functions if a > start)
        body = core[start-CODE_RAM:end-CODE_RAM]
        if not body or len(body) != end-start: raise ValueError('Missing complete native actor service')
        link[name] = start
        receipts.append(dict(symbol=native, start=start, end=end, sha256=sha256(body)))
    from v3_holiday_transition import MEMORY_NATIVE
    for name,vrom,ram,at,size,digest in MEMORY_NATIVE:
        if name!='memcpy': continue
        data=by_vrom(base)[vrom].extract(base)
        if sha256(data[at-ram:at-ram+size])!=digest:
            raise ValueError('Changed native controller structure-copy helper')
        link[name]=at
    events = prior['equipment_resources']['npc_extra']['events']
    renderer = events['decorations']['renderer']
    link.update({n: renderer['code']['symbols'][n] for n in ('af_decor_draw','af_decor_collision','af_decor_records')})
    link.update(af_decor_segments=addresses['SegmentBaseAddress'], af_decor_native_rtc=0x80136FBC,
        af_decor_actor_context=CONTEXT, af_decor_actor_services=SERVICES, af_decor_fg_result=FG_RESULT,
        af_decor_actor_descriptors=DESCRIPTORS, af_decor_native_structure_clip=0x80136F38,
        af_decor_native_effect_clip=0x80136F3C,
        af_decor_previous_descriptor=prior['equipment_resources']['npc_extra']['code']['symbols']['af_v3_npc_extra_descriptor'],
        af_decor_previous_setup=prior['campsite_exterior']['code']['symbols']['af_v3_campsite_structure_setup'],
        af_holiday_native_type=events['native_directory']['code']['symbols']['af_holiday_native_type'])
    return link, receipts


def native_markers(base):
    files=by_vrom(base); rows=[]
    for owner,vrom,ram,at,source,digest in NATIVE_MARKERS:
        data=files[vrom].extract(base); native=DECORATION_DUMMIES[source]
        # ori a0,zero,marker followed by the shared foreground setter call.
        if (sha256(data)!=digest or struct.unpack_from('>I',data,at-ram)[0]!=0x34040000|native or
                bytes.fromhex('0c022a89') not in data[at-ram:at-ram+48]):
            raise ValueError('Changed native foreground-marker consumer: '+owner)
        rows.append(dict(owner=owner,vrom=vrom,ram=ram,address=at,source=source,native=native,sha256=digest))
    return rows


def marker_consumers(base,prior=None):
    files=by_vrom(base);rows=[]
    for purpose,vrom,ram,start,end,digest in MARKER_CONSUMERS:
        body=bytearray(files[vrom].extract(base)[start-ram:end-ram])
        installed_sha256=sha256(body);wrappers=[]
        for hook in (prior or {}).get('equipment_resources',{}).get('holiday_items',{}).get('hooks',[]):
            if hook['kind']!='type' or not start<=hook['address']<end:continue
            at=hook['address']-start
            if body[at:at+8]!=bytes.fromhex(hook['after']):raise ValueError('Changed event category wrapper')
            body[at:at+8]=bytes.fromhex(hook['before']);wrappers.append(hook)
        if sha256(body)!=digest: raise ValueError('Changed native marker consumer: '+purpose)
        rows.append(dict(purpose=purpose,vrom=vrom,ram=ram,start=start,end=end,sha256=digest,
            installed_sha256=installed_sha256,wrappers=wrappers))
    return rows


def prepare(base, prior, directory):
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    _, art = prepared_packet(source, PREPARED)
    renderer = prior['equipment_resources']['npc_extra']['events']['decorations']['renderer']
    directory.mkdir(parents=True, exist_ok=False)
    markers=native_markers(base);consumers=marker_consumers(base,prior)
    files, link, owners, headers = controller_sources(art, renderer, directory)
    native, receipts = native_bindings(base, prior); link.update(native)
    try:
        code, compiled = compile_part('decoration_actor', directory/'code', extra_sources=files, link_symbols=link)
    except __import__('subprocess').CalledProcessError as error:
        raise ValueError(error.stderr) from error
    report = dict(code=compiled, owners=owners, headers=headers, native_functions=receipts,native_markers=markers,
        marker_consumers=consumers,additive_markers={n:dict(source=s,native=DECORATION_DUMMIES[s])
            for n,s in ADDITIVE_MARKERS.items()},
        registry_version=DECORATION_REGISTRY_VERSION, names=DECORATION_NAMES, profiles=DECORATION_PROFILES,
        timing=dict(source_hz=60,native_hz=30,movement_substeps=2,draw_substeps=2,geometry_submissions=1),
        services_bound=False, native_execution_verified=False,
        sources={p: sha256((ROOT/p).read_bytes()) for p in SOURCES})
    write_new(directory/'prepared.json', (json.dumps(report,indent=2)+'\n').encode())
    return code, report


def actor_data(source, art, compiled):
    raw = bytearray(DATA_END-CONTEXT); profiles = []
    struct.pack_into('>4I',raw,SERVICES-CONTEXT,7,
        *(compiled['symbols']['af_decor_actor_'+n] for n in ('demo','resolve','effect')))
    for index, (owner, row) in enumerate(art['owners'].items()):
        donor = source.raw(owner)
        profile, part, flags, name, bank, size = struct.unpack_from('>HHIHHI', donor)
        if (len(donor)!=36 or size!=0x2DC or part!=0x100 or flags & ~0x830 or bank!=3 or
                profile!=next(b['profile'] for b in art['bindings'] if b['owner']==owner)):
            raise ValueError('Changed complete source structure profile')
        # Dolphin TA bit has no native meaning. Native cull controls retain
        # the source's move/draw choices; all native instances are 0x2D8 bytes.
        dest = DECORATION_PROFILES[owner]; native_name = DECORATION_NAMES[name]
        address = PROFILES+index*36
        struct.pack_into('>8I',raw,DESCRIPTORS-CONTEXT+index*32,0,0,0,0,0,address,0,0)
        struct.pack_into('>HHIHH6I',raw,address-CONTEXT,dest,0,flags & 0x30,native_name,3,0x2D8,
            *(compiled['symbols']['af_decor_actor_'+p] for p in ('ctor','dtor','init','draw')),0)
        profiles.append(dict(owner=owner,source_profile=profile,source_bytes=size,profile=dest,
            name=native_name,descriptor=DESCRIPTORS+index*32,address=address,bytes=0x2D8,
            source_flags=flags,native_flags=flags & 0x30))
    return raw, profiles


def patch_owners(base, prior, symbols):
    from v3_import_storage import jump
    files = by_vrom(base); changed = {}; hooks = []
    def put(vrom, ram, at, before, after, purpose):
        data = changed.setdefault(vrom, bytearray(files[vrom].extract(base)))
        off = at-ram
        if data[off:off+len(before)] != before: raise ValueError(f'Changed decoration owner at {at:08X}')
        data[off:off+len(before)] = after
        hooks.append(dict(vrom=vrom,ram=ram,address=at,before=before.hex(),after=after.hex(),purpose=purpose))
    installed=prior['equipment_resources']['npc_extra']['events']['decorations'].get('controllers')
    previous = (installed['code']['symbols']['af_decor_actor_descriptor'] if installed else
        prior['equipment_resources']['npc_extra']['code']['symbols']['af_v3_npc_extra_descriptor'])
    put(CODE_VROM,CODE_RAM,0x80057E4C,struct.pack('>2I',jump(previous,link=True),0x00C02025),
        struct.pack('>2I',jump(symbols['af_decor_actor_descriptor'],link=True),0x00C02025),
        'additional structure descriptors, preserving the NPC/balloon/campsite/native chain')
    old_free=(struct.pack('>2I',jump(installed['code']['symbols']['af_decor_actor_free'],link=True),0)
        if installed else bytes.fromhex('0320f80900000000'))
    put(CODE_VROM,CODE_RAM,0x800583D4,old_free,
        struct.pack('>2I',jump(symbols['af_decor_actor_free'],link=True),0),
        'native structure-pool release and resident descriptor reference accounting')
    previous = (installed['code']['symbols']['af_decor_actor_setup'] if installed else
        prior['campsite_exterior']['code']['symbols']['af_v3_campsite_structure_setup'])
    setup = symbols['af_decor_actor_setup']
    vrom, ram = 0x008CB690, 0x809E7ED0
    put(vrom,ram,0x809E93F8,struct.pack('>I',0x3C0F0000 | ((previous+0x8000)>>16)),
        struct.pack('>I',0x3C0F0000 | ((setup+0x8000)>>16)), 'shared structure setup high address')
    put(vrom,ram,0x809E9400,struct.pack('>I',0x25EF0000 | (previous&65535)),
        struct.pack('>I',0x25EF0000 | (setup&65535)), 'shared structure setup low address')
    relocation = files[0x008CD350].extract(base)
    sizes = struct.unpack_from('>5I',relocation)
    for word, in struct.iter_unpack('>I',relocation[20:20+sizes[4]*4]):
        section, off = word>>30, word&0xFFFFFF
        if section not in (1,2,3): raise ValueError('Invalid retained structure relocation')
        if ram+sum(sizes[:section-1])+off in (0x809E93F8,0x809E9400):
            raise ValueError('Resident structure setup still has an overlay relocation')
    return changed, hooks


def install(base, prior, output):
    from v3_console_disk_install import reservations
    from v3_furniture_capacity import checked
    from v3_holiday_state import RAM as STATE_RAM, GUARD
    import v3_physical_resources as physical
    equipment = copy.deepcopy(prior['equipment_resources'])
    decorations = equipment['npc_extra']['events']['decorations']
    renderer = decorations.get('renderer')
    installed=decorations.get('controllers')
    if not renderer:
        raise ValueError('Decoration controllers require the installed complete renderer')
    checked(base,prior)
    if END>0x807DA800 or (not installed and any(a<END and RAM<b for a,b in reservations(prior))):
        raise ValueError('Complete decoration controllers overlap retained reserved RAM')
    old = equipment['holiday_state']['packet']
    prefix = base[old['physical']:old['physical']+old['bytes']]
    if (old['ram']!=STATE_RAM or STATE_RAM+len(prefix)!=(END if installed else RAM) or
            sha256(prefix)!=old['sha256'] or prefix[-16:]!=GUARD):
        raise ValueError('Changed complete decoration packet')
    if installed:
        if (not installed['installed'] or installed['loaded_code']['ram']!=RAM or
                installed['data']['ram']!=CONTEXT or installed['data']['bytes']!=DATA_END-CONTEXT or
                installed['packet_bytes']!=END-STATE_RAM or old['id']!='holiday-decoration-actors-GAFE01-r0'):
            raise ValueError('Changed owned controller refresh reservation')
        for part in ('loaded_code','data'):
            row=installed[part];at=row['ram']-STATE_RAM
            if sha256(prefix[at:at+row['bytes']])!=row['sha256']:
                raise ValueError('Changed controller refresh predecessor')
        if not 0<installed['loaded_code']['bytes']<=END-RAM-16:
            raise ValueError('Changed controller code extent')
        if any(prefix[RAM-STATE_RAM+installed['loaded_code']['bytes']:-16]):
            raise ValueError('Occupied controller refresh padding')
    elif (old['id']!='holiday-decoration-runtime-GAFE01-r0' or
            any(prefix[CONTEXT-STATE_RAM:DATA_END-STATE_RAM])):
        raise ValueError('Changed renderer packet or occupied actor-state reservation')
    directory = output/'decoration-actors'
    code, report = prepare(base,prior,directory)
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    # The installed renderer already records the verified complete source batch.
    art = json.loads((PREPARED/'art.json').read_bytes())
    data, profiles = actor_data(source,art,report['code'])
    changes, hooks = patch_owners(base,prior,report['code']['symbols'])
    raw = bytearray(prefix[:RAM-STATE_RAM])+bytearray(END-RAM)
    raw[RAM-STATE_RAM:RAM-STATE_RAM+len(code)] = code
    raw[CONTEXT-STATE_RAM:DATA_END-STATE_RAM] = data
    raw[-16:] = GUARD
    resources = copy.deepcopy(prior['physical_resources'])
    if installed:
        physical.verify(base,resources)
        resource=next(r for r in resources if r['id']==old['id'])
        if (resource['physical'],resource['bytes'],resource['sha256'])!=(old['physical'],old['bytes'],old['sha256']):
            raise ValueError('Changed physical controller refresh owner')
        resource['sha256']=sha256(raw)
        write_resource=dict(resource,previous_sha256=old['sha256'])
    else:
        resource = physical.allocate(base,resources,raw,'holiday-decoration-actors-GAFE01-r0');resources.append(resource)
        write_resource=resource
    equipment['holiday_state']['packet'] = dict(resource,ram=STATE_RAM,crc32=zlib.crc32(raw),
        storage='physical-ROM',guard=GUARD.hex())
    preserved = [dict(ram=a,bytes=b-a,sha256=sha256(prefix[a-STATE_RAM:b-STATE_RAM]))
        for a,b in ((STATE_RAM,CONTEXT),(DATA_END,RAM))]
    report.update(installed=True,actors_active=False,profiles=profiles,hooks=hooks,
        original_packet=installed['original_packet'] if installed else old,input_packet=old,refresh=bool(installed),
        bound_services=['native ordinary/scripted acre-transition predicates',
            'native foreground markers for all eleven owners/eighteen variants',
            'native radio musical-note effect and source-rate request cadence'],
        packet_ram=STATE_RAM,packet_bytes=len(raw),additional_resident_bytes=END-RAM,
        loaded_code=dict(ram=RAM,bytes=len(code),sha256=sha256(code)),
        data=dict(ram=CONTEXT,bytes=len(data),sha256=sha256(data)),preserved=preserved,
        pending=['fishing record/text consumers, Harvest fork item/player pickup',
            'shared event activation, attendance, calendar choice, and native execution'])
    decorations['controllers'] = report
    decorations['additional_resident_bytes'] = END-0x80700000
    equipment['npc_extra']['sources'].update(report['sources'])
    write_new(directory/'installed.json',(json.dumps(report,indent=2)+'\n').encode())
    write_new(directory/'state-packet.bin',raw)
    return equipment,changes,dict(physical_resources=resources),[(write_resource,bytes(raw))]
