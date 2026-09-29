"""Prepare all Shrine spirit effects with the existing source/model converters.

The enclosing reward-family installer must bind sound, visibility, profiles,
and scene cleanup before these callbacks become available in a cartridge.
"""
import json
import os
import re
import struct
import subprocess
from pathlib import Path

from aflib import by_vrom, sha256
from apply_translation import write_new
from toolchain import IMAGE
from v3_asset_loader import ROOT
from v3_furniture_pipeline import Source, prepare_models, compile_models, assemble_models
from v3_holiday_sky import native_bindings
from v3_password_policy import function
from v3_room_effects import flash_art
from v3_room_particles import append_object

REFERENCE = 'ed80ecf6c0f85347dec47c52a55af4dcb6e0d479e2a7b8fc719b8fe82b135eaf'
FAMILY = (('sphere', 'eMH', 'make_hem'), ('kira', 'eMHK', 'make_hem_kira'),
          ('light', 'eMHL', 'make_hem_light'))
SOURCES = ('tools/v3_reward_effects.py', 'overlays/v3/reward_effects.h',
           'overlays/v3/reward_effects.c', 'overlays/v3/reward_effects_draw.c',
           'tools/v3_holiday_sky.py', 'tools/v3_furniture_art.py')
NATIVE_SERVICES = ('Light_point_ct', 'Global_light_list_new', 'Global_light_list_delete',
    'add_calc', 'Setpos_HiliteReflect_xlu_init', 'mCoBG_GetBgY_OnlyCenter_FromWpos2',
    '_texture_z_light_fog_prim', '_texture_z_light_fog_prim_shadow', 'xyz_t_add')


def generate(source, first_id=122):
    raw = (ROOT/'local/ac-decomp/src/effect/ef_make_hem.c').read_bytes()
    header = (ROOT/'local/ac-decomp/include/ef_effect_control.h').read_bytes()
    if sha256(raw) != REFERENCE or sha256(header) != '8308dd443efa5518826f11b8b529b9acb1aa0119744e53c23b782ea22daa4126':
        raise ValueError('Changed complete Shrine effect source')
    enum = re.search(r'enum effect_type\s*\{([^}]+)\}', header.decode())[1]
    names = [s.strip() for s in re.sub(r'/\*.*?\*/|//[^\n]*', '', enum, flags=re.S).split(',') if s.strip()]
    if any(not re.fullmatch(r'eEC_EFFECT_\w+', s) for s in names):
        raise ValueError('Changed effect identity enumeration')
    unique = source.raw('eEC_effect_feature')
    if len(unique) != names.index('eEC_EFFECT_NUM') or any(v not in (0, 1) for v in unique):
        raise ValueError('Incomplete effect uniqueness policies')
    text = re.sub(r'/\*.*?\*/|//[^\n]*', '', raw.decode(), flags=re.S)
    declared = re.findall(r'^static\s+[^\n;{}=]+?\b(e\w+)\([^;{}]*\)\s*\{', text, re.M)
    if len(declared) != 12 or len(set(declared)) != 12:
        raise ValueError('Incomplete three-effect callback family')
    pieces = ['#include "reward_effects.h"', '#define eHM_TIMER 2000',
              '#pragma GCC diagnostic ignored "-Wunused-parameter"']
    functions, profiles = [], []
    substitutions = {
        'eEC_CLIP->make_effect_proc': 'af_rw_effect_create',
        'eEC_CLIP->effect_make_proc': 'af_rw_effect_request',
        'eEC_CLIP->effect_kill_proc': 'af_rw_effect_kill',
        'eEC_CLIP->calc_adjust_proc': 'af_sky_adjust',
        'eEC_CLIP->set_continious_env_proc': 'af_sky_continuous',
        'Common_Get(hem_visible)': '(*af_rw_hem_visible())',
        'Common_Set(hem_visible, TRUE)': '(*af_rw_hem_visible() = TRUE)',
        'Common_Set(hem_visible, FALSE)': '(*af_rw_hem_visible() = FALSE)',
        'eMH_special_point_light_num': 'af_rw_effect_light_index',
        'mEnv_ReservePointLight': 'af_rw_effect_light_reserve',
        'mEnv_CancelReservedPointLight': 'af_rw_effect_light_cancel',
        'mEnv_OperateReservedPointLight_Color': 'af_rw_effect_light_colour',
        'sAdo_OngenTrgStart': 'af_rw_effect_sound',
        'GAME_PLAY*': 'void*', 'GAME*': 'void*',
        'static xyz_t xyz0': 'static const xyz_t xyz0',
        's16 rnd_angle = RANDOM_F(66536.0f);': 's16 rnd_angle = (s16)(int)RANDOM_F(66536.0f);',
    }
    for name in declared:
        matches = [at for at, rows in source.functions.items() if any(n == name for n, _ in rows)]
        if len(matches) != 1:
            raise ValueError('Missing complete donor effect function: '+name)
        functions.append(source.function(matches[0])[1])
        if name.endswith('_dw'):
            continue
        body = function(text, name)
        for before, after in substitutions.items():
            body = body.replace(before, after)
        body = re.sub(r'GETREG\(MYKREG,\s*(\d+)\)', r'af_sky_debug(\1)', body)
        if re.search(r'\b(?:Common_Get|Common_Set|GETREG|eEC_CLIP)\b', body):
            raise ValueError('Unbound donor memory in Shrine effect')
        pieces.append(body)
    for i, (kind, prefix, stem) in enumerate(FAMILY):
        symbol = 'iam_ef_'+stem
        at, size = source.symbol(symbol)
        profile = source.raw(symbol)
        refs = {p-at: r for (section, p), r in source.section_relocations.items()
                if section == 5 and at <= p < at+size}
        expected = {j*4: (1, 1, 1, next(f['offset'] for f in functions if f['symbol'] == prefix+'_'+role))
                    for j, role in enumerate(('init', 'ct', 'mv', 'dw'))}
        policy = '00c300ffc47a0cff' if kind == 'light' else 'fffe00ffc47a0cff'
        if profile != bytes(16)+bytes.fromhex(policy) or refs != expected:
            raise ValueError('Changed complete Shrine effect profile')
        donor_id = names.index('eEC_EFFECT_'+stem.upper())
        profiles.append(dict(kind=kind, source_id=donor_id, native_id=first_id+i,
            source_symbol=symbol, offset=at, sha256=sha256(profile), policy_hex=policy,
            unique=unique[donor_id], callbacks=expected))
        target = 'af_rw_effect_'+kind
        pieces.extend((
            f'void {target}_init(xyz_t p,int priority,s16 angle,void *g,u16 item,s16 a,s16 b) {{',
            f' if(af_rw_effect_ready(g)){prefix}_init(p,priority,angle,g,item,a,b);}}',
            f'void {target}_ct(RoomEffect *e,void *g,void *arg) {{',
            f' if(af_rw_effect_ready(g)){prefix}_ct(e,g,arg);else e->timer=0;}}',
            f'void {target}_mv(RoomEffect *e,void *g) {{',
            ' if(!af_rw_effect_ready(g)){e->timer=0;return;}',
            ' for(unsigned int i=0,n=af_hp_native_ticks;i<n;i++){',
            f'  if(i){{if(e->timer<=1)break;--e->timer;}} {prefix}_mv(e,g);}} }}',
            f'void {target}_dw(RoomEffect *e,void *g) {{{target}_draw(e,g);}}'))
    return '\n\n'.join(pieces)+'\n', dict(reference_sha256=REFERENCE, functions=functions,
        profiles=profiles, native_ticks_maximum=2, visibility_transition_source_tick=150,
        sphere_end_source_tick=196, source_rel_sha256=sha256(source.rel),
        source_symbols_sha256=sha256(source.symbols.encode()))


def artwork(source, bank, output, reuse=None):
    objects = {}
    cached = json.loads((reuse/'prepared.json').read_bytes()) if reuse else None
    if cached and (cached['source']['source_rel_sha256'] != sha256(source.rel) or
                   cached['source']['source_symbols_sha256'] != sha256(source.symbols.encode())):
        raise ValueError('Changed reusable reward-effect source')
    for kind, name in (('sphere', 'ef_sphere_light_model'), ('light', 'ef_circle_light_model')):
        directory = output/kind
        directory.mkdir()
        prepared = prepare_models(source, dict(models={'model': source.containing(source.symbol(name)[0], exact=True)},
            callback_adapter=dict(category='actor-model-assets')))
        if cached:
            old = cached['artwork'][kind]
            asset = (reuse/kind/'object.bin').read_bytes()
            models = old['models_compiled']
            sections = {r['layer']: asset[r['native_offset']:r['native_offset']+r['bytes']] for r in models}
            rebuilt, offsets, rebuilt_models, sequence = assemble_models(prepared, sections)
            if (rebuilt != asset or rebuilt_models != models or old['resources'] != prepared[2] or
                    (reuse/kind/'commands.c').read_text() != prepared[5]):
                raise ValueError('Incomplete reusable reward-effect artwork')
            write_new(directory/'commands.c', prepared[5].encode())
        else:
            asset, offsets, models, sequence = compile_models(directory, prepared)
        if sequence is not None:
            raise ValueError('Shrine effect cannot become a furniture sequence')
        bank, row = append_object(bank, asset, models)
        write_new(directory/'object.bin', asset)
        objects[kind] = dict(row, resources=prepared[2], models_compiled=models, offsets=offsets)
    asset, receipt = flash_art(source)
    mode = source.raw('ef_takurami01_normal_render_mode')
    if mode.hex() != 'e200001cc8104b50df00000000000000':
        raise ValueError('Changed complete sparkle render mode')
    models = [dict(layer='model', native_offset=320, bytes=144, output_sha256=sha256(asset[320:])),
              dict(layer='mode', native_offset=len(asset), bytes=len(mode), output_sha256=sha256(mode))]
    bank, row = append_object(bank, asset+mode, models)
    objects['kira'] = dict(row, source=receipt, models_compiled=models)
    write_new(output/'kira-object.bin', asset+mode)
    write_new(output/'effect-art-bank.bin', bank)
    code = '#include "reward_effects.h"\nconst u32 af_rw_effect_models[3]={'
    code += ','.join(hex(objects[k]['models']['model']) for k in ('sphere', 'kira', 'light'))+'};\n'
    code += 'const u32 af_rw_effect_kira_mode='+hex(objects['kira']['models']['mode'])+';\n'
    return bank, code, objects


def prepare(output, lock, reuse=None):
    from v3_furniture_install import inputs
    output = output.resolve()
    if reuse:
        reuse = reuse.resolve()
        if not reuse.is_relative_to(ROOT/'build'):
            raise ValueError('Reusable effect resources must belong to ignored builds')
    if output.exists() or not output.is_relative_to(ROOT/'build'):
        raise ValueError('Use a fresh ignored reward-effect preparation')
    base, prior = inputs(lock)
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    effects = prior['equipment_resources']['room_rigs']['effects']
    first = effects['controller']['count']
    if first != 122 or [p['id'] for p in effects['profiles']] != list(range(111, first)):
        raise ValueError('Changed current effect identities; recheck free slots')
    bank_row = effects['bank']
    bank = by_vrom(base)[bank_row['vrom']].extract(base)
    if sha256(bank) != bank_row['sha256']:
        raise ValueError('Changed retained complete effect bank')
    generated, contract = generate(source, first)
    output.mkdir(parents=True)
    bank, art_code, art = artwork(source, bank, output, reuse)
    for name, body in (('source.c', generated), ('art.c', art_code)):
        write_new(output/name, body.encode())
    from v3_holiday_participants import trigger_audio
    audio_files = {}
    audio = trigger_audio(base, prior, audio_files, prefix='reward', words=(0x468, 0x469),
        symbol='af_rw_effect_sounds', header='reward_effects.h')
    for name, body in audio_files.items():
        write_new(output/name, body.encode() if isinstance(body, str) else body)
    docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
        '-v', f'{ROOT}:/source:ro', '-v', f'{output}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        return subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
            check=True, text=True, capture_output=True, timeout=60).stdout
    flags = ['-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0', '-mno-abicalls',
        '-fno-pic', '-ffreestanding', '-fno-builtin', '-fno-common', '-fno-stack-protector',
        '-ffunction-sections', '-fdata-sections', '-fstack-usage', '-Wall', '-Wextra', '-Werror',
        '-I/source/overlays/v3', '-I/out', f'-DAF_RW_EFFECT_FIRST={first}']
    run('gcc', *flags, 'source.c', 'art.c', 'reward-audio.c', '/source/overlays/v3/reward_effects.c',
        '/source/overlays/v3/reward_effects_draw.c')
    run('ld', '-EB', '-r', 'source.o', 'art.o', 'reward-audio.o', 'reward_effects.o', 'reward_effects_draw.o', '-o', 'reward-effects.o')
    links, native = native_bindings(base, {name: name for name in NATIVE_SERVICES})
    result = dict(format='AFV3-REWARD-EFFECTS-1', family=contract['profiles'], source=contract,
        artwork=art, audio=audio, reused_artwork=str(reuse.relative_to(ROOT)) if reuse else None,
        base_abi=prior['runtime_abi'], base_sha256=sha256(base),
        bank=dict(previous_sha256=bank_row['sha256'], bytes=len(bank), sha256=sha256(bank)),
        object=dict(sha256=sha256((output/'reward-effects.o').read_bytes()), compiler=IMAGE,
            flags=flags, size=run('size', 'reward-effects.o'), linked=False),
        unbound_services=run('nm', '--undefined-only', 'reward-effects.o').strip().splitlines(),
        native_service_candidates=links, native_service_evidence=native,
        sources={p: sha256((ROOT/p).read_bytes()) for p in SOURCES},
        generated_sha256={p: sha256((output/p).read_bytes()) for p in ('source.c', 'art.c')},
        installed=False, native_execution_verified=False,
        pending=['install prepared complete sound resources', 'reward visibility provider',
                 'native profile directory and loader bounds', 'scene-owned light reset',
                 'reward-family actor entry points and combined gameplay'])
    write_new(output/'prepared.json', (json.dumps(result, indent=2)+'\n').encode())
    return result
