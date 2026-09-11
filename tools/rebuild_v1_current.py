"""Rebuild every current V1 correction from the reproducible artwork baseline."""
import argparse
import importlib
import json
from pathlib import Path
import subprocess
import time

from aflib import sha256, verified_rom, apply_ups
from apply_translation import write_new
from package_v1_playtest import ROM_SHA as BASE_SHA, REPORT_SHA
from rebuild_v0 import AF_PIN, GC_PIN, clean_revision, output_files
from rebuild_v1 import checked_output, source_inventory, source_state
from setup_toolchain import verify as verify_toolchain
from title_assets import REL_SHA256, SYMBOLS_SHA256
from toolchain import IMAGE, profile_sha256

ROOT = Path(__file__).resolve().parents[1]
FINAL_SHA = '2a04f6e5c54dc2d5ed03009395af815b464bebdef51d67d899554deb54b3bcb4'
PATCH_SHA = 'c3931b2e029bf4182864306ed2cbf28ea4c1d6c9d609cd33d68047132029b769'
ROM_NAME = 'Animal Forest English V1-current.z64'
# Existing grouped recipes contain 7+3+2+1 stages; six later builders follow.
STAGES = (
    ('rc1', 'rebuild_v1_fixes', 'animal-forest-title-preview',
     '63794bd31fe5c7c9ae786b15a41d6a80c2390c890b2edd963ace9a9e5edb8d37', 7),
    ('rc2', 'rebuild_v1rc2', 'animal-forest-title-preview',
     '7a265fca118e522591085d0f7ce3a926b46d78a86c67e6f07443c64befe005bb', 3),
    ('rc3', 'rebuild_v1rc3', 'animal-forest-edge-fixes',
     'b8a4608b62c098b334dcbe5c87ad2483406c559ba3dbcd2ed26fd64ee27368f0', 2),
    ('rc4', 'rebuild_v1rc4', 'animal-forest-memory-fix',
     '5930435f588947df35313ae9cc2ea301af9fc7e68d59a7d8e13a48741d4f3067', 1),
    ('catalogue-repayment', 'rc4_menu_labels', 'replay-only',
     '6ed7d636b953d24d4ad10ae8ea806deb133a752f4295ad79727c52336095dae4', 1),
    ('tune-confirmation', 'tune_confirmation', 'replay-only',
     '5f85299d975858017f6d822664933bc332908cde17adf7ff0f4b175e941b1f13', 1),
    ('pak-heading', 'pak_erase_heading', 'replay-only',
     '800c7e9d4e6a4b81db05d0a8258d151417d02c9edc47806cf3429e3d144fab09', 1),
    ('title-warning', 'title_warning_text', 'replay-only',
     '614e387ee7591d935c091852512f7a60dc181fe25892843a2458c70a69e87037', 1),
    ('gamestate-menu', 'gamestate_menu_text', 'replay-only',
     '3a2e8b4241837daa7cea094deb2f2d229b2fa34755cf9103e493e27b1cf3fd8a', 1),
    ('scene-menu', 'scene_menu_text', 'replay-only', FINAL_SHA, 1),
)


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()


def current_sources():
    return {**source_inventory(), 'Makefile': sha256((ROOT/'Makefile').read_bytes())}


def read_inputs(artwork, native, rel, symbols):
    """Explicit fresh-artwork outputs; never default to a retained RC directory."""
    paths = {
        'native': native, 'rel': rel, 'symbols': symbols,
        'artwork_rom': artwork/'final/animal-forest-title-preview.z64',
        'title_report': artwork/'final/preview.json',
        'translation_report': artwork/'replay/27-civic-interiors/build.json',
    }
    raw = {name: path.read_bytes() for name, path in paths.items()}
    verified_rom(raw['native'])
    title = json.loads(raw['title_report'])
    translation = json.loads(raw['translation_report'])
    if (sha256(raw['artwork_rom']) != BASE_SHA or title.get('output_sha256') != BASE_SHA
            or profile_sha256(title) != REPORT_SHA
            or translation.get('output_sha256') != title.get('baseline_sha256')
            or sha256(raw['rel']) != REL_SHA256 or sha256(raw['symbols']) != SYMBOLS_SHA256):
        raise ValueError('Current V1 recipe requires exact source games and complete artwork/title inputs')
    identities = {name: {'path': str(paths[name].resolve()), 'sha256': sha256(value)}
                  for name, value in raw.items()}
    return raw['native'], raw['artwork_rom'], title, translation, raw['rel'], raw['symbols'], identities


def reference_state():
    return {'af': clean_revision(ROOT/'upstream/af', AF_PIN),
            'gc': clean_revision(ROOT/'local/ac-decomp', GC_PIN)}


def construct(stage, native, image, title, translation, rel, symbols, out):
    name, module_name, stem, expected, _ = stage
    module = importlib.import_module(module_name)
    if name == 'rc1':
        module.rebuild(native, image, title, translation, rel, symbols, out)
    elif name == 'rc2':
        module.rebuild(native, image, rel, symbols, out)
    elif name in ('rc3', 'rc4'):
        module.rebuild(native, image, out)
    else:
        out.mkdir(parents=True, exist_ok=False)
        if name == 'catalogue-repayment':
            result = module.build(native, image, rel, symbols, module.compile_adapter(out/'adapter'))
        elif name == 'tune-confirmation':
            result = module.build(native, image, rel, symbols)
        else:
            result = module.build(native, image)
        image, patch, report = result
        for filename, data in {stem+'.z64': image, stem+'.ups': patch, 'fixes.json': json_bytes(report)}.items():
            write_new(out/filename, data)
    image = (out/(stem+'.z64')).read_bytes()
    patch = (out/(stem+'.ups')).read_bytes()
    if sha256(image) != expected or apply_ups(native, patch) != image:
        raise ValueError('Correction group differs from its checked cartridge: '+name)
    return image, patch


def completed_stage(output, index, stage, previous, sources, native):
    """Verify all recorded group outputs before treating a boundary as reusable."""
    record = output/f'stage-{index:02}.json'
    if record.is_symlink():
        raise ValueError('Redirected completed stage receipt')
    saved = json.loads(record.read_text())
    name, module_name, stem, expected, count = stage
    if (saved.get('name') != name or saved.get('module') != module_name
            or saved.get('input_sha256') != previous or saved.get('output_sha256') != expected
            or saved.get('correction_stages') != count
            or saved.get('builder_sha256') != sources['tools/'+module_name+'.py']
            or saved.get('outputs') != output_files(output, name)):
        raise ValueError('Changed completed correction group: '+name)
    image = (output/name/(stem+'.z64')).read_bytes()
    patch = (output/name/(stem+'.ups')).read_bytes()
    if sha256(image) != expected or sha256(patch) != saved.get('patch_sha256') or apply_ups(native, patch) != image:
        raise ValueError('Completed correction group no longer reconstructs')
    return saved, image, patch


def publish_final(output, native, image, patch, manifest, records):
    if sha256(image) != FINAL_SHA or sha256(patch) != PATCH_SHA or apply_ups(native, patch) != image:
        raise ValueError('Complete current V1 result differs from the checked final translation')
    final = output/'final'
    final.mkdir(exist_ok=False)
    result = {
        'version': 1, 'complete': True, 'kind': 'current_v1_correction_rebuild',
        'source_revision': manifest['source_revision'], 'recipe_sha256': manifest['recipe_sha256'],
        'toolchain_image': IMAGE, 'worktree_modified': False,
        'source_sha256': sha256(native), 'baseline_sha256': BASE_SHA,
        'output_sha256': FINAL_SHA, 'patch_sha256': PATCH_SHA, 'rom_bytes': len(image),
        'groups': len(records), 'correction_stages': sum(stage[4] for stage in STAGES),
        'stages': records, 'required_ram_bytes': 0x800000,
        'save_type': 'FlashRAM', 'save_bytes': 131072, 'rtc_required': True,
        'save_format_changed': False, 'native_tests_run': False, 'original_hardware_verified': False,
        'prior_human_acceptance': 'Reported fixes and ordinary save/restart/reload remain accepted; this is a build check',
        'scope': 'All corrections after explicit artwork inputs; the complete command regenerates those inputs',
        'final_directory': 'final', 'final_rom': ROM_NAME,
    }
    for name, value in {ROM_NAME: image, 'animal-forest-english.ups': patch,
                        'build.json': json_bytes(result)}.items():
        write_new(final/name, value)
    write_new(output/'rebuild.json', json_bytes(result))
    return result


def rebuild(inputs, output, *, through=STAGES[-1][0], resume=False):
    native, image, title, translation, rel, symbols, identities = inputs
    if through not in [stage[0] for stage in STAGES]:
        raise ValueError('Unknown correction boundary')
    if output.is_symlink():
        raise ValueError('Output must not be a symlink')
    output = output.resolve() if resume else checked_output(output)
    if (not output.is_relative_to(ROOT.resolve()/'build') or output.is_symlink()
            or source_state()['worktree_modified']):
        raise ValueError('Use committed sources and an unredirected build directory')
    sources = current_sources()
    references = reference_state()
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True,
                              capture_output=True, text=True).stdout.strip()
    state = {'version': 1, 'source_revision': revision, 'sources': sources, 'inputs': identities,
             'recipe_sha256': sha256(Path(__file__).read_bytes()), 'toolchain_image': IMAGE,
             'stages': json.loads(json.dumps(STAGES)), 'references': references,
             'retained_rc_inputs': []}
    if resume:
        if (output/'inputs.json').is_symlink():
            raise ValueError('Redirected current-recipe input receipt')
        manifest = json.loads((output/'inputs.json').read_text())
        if any(manifest.get(key) != value for key, value in state.items()):
            raise ValueError('Changed recipe, sources, input identities, or compiler; cannot resume')
    else:
        compiler = verify_toolchain()
        output.mkdir(parents=True, exist_ok=False)
        manifest = {**state, 'compiler_verification': compiler}
        write_new(output/'inputs.json', json_bytes(manifest))
    records = []
    previous = BASE_SHA
    end = [stage[0] for stage in STAGES].index(through)+1
    try:
        for index, stage in enumerate(STAGES[:end], 1):
            name, module_name, stem, expected, count = stage
            if (output/f'stage-{index:02}.json').exists():
                record, image, patch = completed_stage(output, index, stage, previous, sources, native)
            else:
                if (output/name).exists() or (output/name).is_symlink():
                    raise ValueError('Incomplete stage output is preserved; inspect before a fresh run: '+name)
                started = time.monotonic()
                image, patch = construct(stage, native, image, title, translation, rel, symbols, output/name)
                if current_sources() != sources or source_state()['worktree_modified']:
                    raise ValueError('Sources changed during current V1 construction')
                record = {'name': name, 'module': module_name, 'input_sha256': previous,
                          'output_sha256': expected, 'patch_sha256': sha256(patch), 'correction_stages': count,
                          'builder_sha256': sources['tools/'+module_name+'.py'],
                          'seconds': round(time.monotonic()-started, 3), 'outputs': output_files(output, name)}
                write_new(output/f'stage-{index:02}.json', json_bytes(record))
                print(json.dumps({key: record[key] for key in ('name', 'output_sha256', 'seconds')}), flush=True)
            records.append(record)
            previous = expected
        if (current_sources() != sources or source_state()['worktree_modified']
                or reference_state() != references):
            raise ValueError('Sources changed during current V1 construction')
        if end == len(STAGES):
            # A successful completed run is not silently republished.
            if (output/'final').exists() or (output/'rebuild.json').exists():
                raise ValueError('Final artifacts already exist; keep the completed run unchanged')
            return publish_final(output, native, image, patch, manifest, records)
        result = {'complete': False, 'groups_complete': end, 'through': through,
                  'output_sha256': previous, 'source_revision': revision}
        boundary = output/f'boundary-{end:02}.json'
        if not boundary.exists():
            write_new(boundary, json_bytes(result))
        return result
    except Exception as error:
        failure = output/f'failure-{len(records)+1:02}.json'
        if not failure.exists():
            write_new(failure, json_bytes({'complete': False, 'groups_complete': len(records), 'error': str(error)}))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artwork', type=Path, default=ROOT/'build/v1-complete')
    parser.add_argument('--native', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--rel', type=Path, default=ROOT/'build/gamecube/files/foresta.rel.szs.decoded')
    parser.add_argument('--symbols', type=Path, default=ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt')
    parser.add_argument('--output', type=Path, default=ROOT/'build/v1-current')
    parser.add_argument('--through', choices=[stage[0] for stage in STAGES], default=STAGES[-1][0])
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.output.is_symlink():
        parser.error('Output must not be a symlink')
    if not args.resume:
        checked_output(args.output)
    inputs = read_inputs(args.artwork, args.native, args.rel, args.symbols)
    result = rebuild(inputs, args.output, through=args.through, resume=args.resume)
    print(json.dumps({key: result[key] for key in ('complete', 'output_sha256', 'source_revision')}))


if __name__ == '__main__':
    main()
