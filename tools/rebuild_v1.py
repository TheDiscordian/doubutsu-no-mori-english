"""Rebuild every post-v0 layer into a fresh directory, with exact final identities."""
import argparse
import importlib
import json
from pathlib import Path
import subprocess
import time

from aflib import by_vrom, sha256, verified_rom
from apply_translation import write_new
from check_keyboard_assembly import IMAGE
from package_v0 import HARDWARE_FIX_SHA256
from package_v1_playtest import ROM_SHA, PATCH_SHA, REPORT_SHA
from title_assets import REL_SHA256, SYMBOLS_SHA256
from toolchain import profile_sha256
from setup_toolchain import verify as verify_toolchain

ROOT = Path(__file__).resolve().parents[1]
BASE_REPORT_SHA = '5fe4d9b4731470dd9f095f88165133fc629622d6478d9e0b6dd86e65742606a0'
STAGES = (
    ('shops', 'building_artwork', 'reference'),
    ('map', 'map_artwork', 'map_commands'),
    ('inventory', 'inventory_artwork', 'commands'),
    ('clock', 'time_setting', 'reference'),
    ('collections', 'collection_artwork', 'commands'),
    ('grid-replay-only', 'keyboard_grid_overlay', 'grid1'),
    ('nookington', 'nookington_sign', 'commands'),
    ('sold-out-and-hints', 'shop_signs', 'reference'),
    ('police', 'police_artwork', 'commands'),
    ('redd', 'redd_artwork', 'reference'),
    ('corrected-grid', 'keyboard_grid_cursor', 'grid2'),
    ('noticeboard', 'notice_artwork', 'commands'),
    ('tune', 'tune_artwork', 'commands'),
    ('catalogue', 'catalogue_artwork', 'commands'),
    ('service', 'service_artwork', 'commands'),
    ('birthday', 'birthday_screen', 'birthday'),
    ('controller-pak', 'controller_pak_artwork', 'native'),
    ('submenu-text', 'submenu_text', 'native'),
    ('gyroid-service', 'gyroid_service', 'native'),
    ('nookington-details', 'nookington_details', 'reference'),
    ('dump', 'dump_artwork', 'reference'),
    ('fishing', 'fishing_artwork', 'commands'),
    ('fortune-table', 'fortune_booth_artwork', 'commands'),
    ('countdown', 'countdown_artwork', 'reference'),
    ('stall', 'stall_artwork', 'stall_commands'),
    ('shop-interiors', 'shop_interior_artwork', 'reference'),
    ('title', 'title_overlay', 'title'),
)


def canonical(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def source_inventory():
    names = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z',
                            '--', 'tools', 'overlays', 'runtime', 'translations'],
                           cwd=ROOT, check=True, capture_output=True, text=True).stdout.split('\0')
    return {name: sha256((ROOT/name).read_bytes()) for name in sorted(set(names))
            if name and (ROOT/name).is_file()}


def source_state():
    changed = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=all', '--',
                              'tools', 'overlays', 'runtime', 'translations'],
                             cwd=ROOT, check=True, capture_output=True, text=True).stdout
    return {'worktree_modified': bool(changed), 'recipe_sha256': sha256(Path(__file__).read_bytes())}


def read_inputs(base, rom, rel, symbols):
    native = verified_rom(rom.read_bytes())
    image = (base/'animal-forest-halfwidth.z64').read_bytes()
    report = json.loads((base/'build.json').read_text())
    reference, labels = rel.read_bytes(), symbols.read_bytes()
    if (sha256(image) != HARDWARE_FIX_SHA256 or profile_sha256(report) != BASE_REPORT_SHA
            or report.get('output_sha256') != HARDWARE_FIX_SHA256):
        raise ValueError('Rebuild requires the exact corrected v0 cartridge and report')
    if sha256(reference) != REL_SHA256 or sha256(labels) != SYMBOLS_SHA256:
        raise ValueError('Rebuild source REL or symbols changed')
    return native, image, report, reference, labels


def checked_output(path):
    output = path.resolve()
    if path.is_symlink() or output.exists():
        raise ValueError('output must be a fresh directory; previous builds are preserved')
    if not output.is_relative_to(ROOT.resolve()/'build'):
        raise ValueError('output must be inside this source checkout\'s build/ for generated graphics compilation')
    return output


def publish(directory, image, patch, report, *, final=False):
    directory.mkdir(parents=True, exist_ok=False)
    name = 'animal-forest-title-preview' if final else 'replay-only'
    for filename, value in ((name+'.z64', image), (name+'.ups', patch),
                            ('preview.json' if final else 'build.json',
                             (json.dumps(report, indent=2)+'\n').encode())):
        write_new(directory/filename, value)


def check_final(image, patch, report):
    from keyboard_grid_labels import CURSOR_CORRECTED_SHA
    if (sha256(image) != ROM_SHA or sha256(patch) != PATCH_SHA or profile_sha256(report) != REPORT_SHA
            or report['memory']['required_ram_bytes'] != 0x800000
            or report['memory']['ordinary_heap_end'] != 0x80400000
            or sha256(by_vrom(image)[0x3940000].extract(image)) != CURSOR_CORRECTED_SHA):
        raise ValueError('Rebuild differs from the approved complete title/shop-interior/corrected-grid result')


def rebuild(inputs, output):
    output = checked_output(output)
    native, image, report, rel, symbols = inputs
    source_hashes = source_inventory()
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True,
                              capture_output=True, text=True).stdout.strip()
    # Verify the already installed v0 editor before creating any output.
    import apology_overlay
    files = by_vrom(image)
    editor, relocation = files[0x3940000].extract(image), files[0x3948000].extract(image)
    apology_overlay.validate(native, editor, relocation, report['apology_input']['overlay'])
    compiler = verify_toolchain()
    output.mkdir(parents=True, exist_ok=False)
    manifest = {'format': 1, 'source_revision': revision, **source_state(), 'toolchain_image': IMAGE,
                'compiler_verification': compiler,
                'source_sha256': sha256(native), 'base_sha256': sha256(image),
                'base_report_sha256': canonical(report), 'rel_sha256': sha256(rel),
                'symbols_sha256': sha256(symbols), 'sources': source_hashes,
                'scope': 'All post-v0 layers; corrected v0 remains an explicit input',
                'existing_artifacts_overwritten': False, 'native_tests_run': False}
    write_new(output/'inputs.json', (json.dumps(manifest, indent=2)+'\n').encode())
    preceding = output/'compiled/preceding-editor'
    preceding.mkdir(parents=True)
    for name, value in (('overlay.bin', editor), ('relocation.bin', relocation),
                         ('overlay.json', (json.dumps(report['apology_input']['overlay'], indent=2)+'\n').encode())):
        write_new(preceding/name, value)
    completed = []
    try:
        for index, (name, module_name, mode) in enumerate(STAGES, 1):
            started = time.monotonic()
            module = importlib.import_module(module_name)
            extra = []
            compiled = output/'compiled'/name
            if mode in ('reference', 'commands', 'map_commands', 'stall_commands', 'birthday', 'title'):
                extra += [rel, symbols]
            if mode in ('commands', 'map_commands'):
                compile_commands = module.compile_commands if mode == 'map_commands' else module.commands
                extra.append(compile_commands(compiled))
            elif mode == 'stall_commands':
                extra.append(module.compile_model(rel, symbols, compiled)[0])
            elif mode in ('grid1', 'grid2'):
                from build_keyboard_grid import build as build_grid
                build_grid(native, preceding, compiled, version=1 if mode == 'grid1' else 2)
                extra.append(compiled)
            elif mode == 'birthday':
                from build_birthday_draw import compile_draw
                compile_draw(compiled)
                extra.append(compiled)
            elif mode == 'title':
                from build_title_overlay import compile_overlay
                title_report = compile_overlay(native, rel, symbols, compiled)
                extra += [(compiled/'overlay.bin').read_bytes(), (compiled/'relocation.bin').read_bytes(), title_report]
            image, patch, report = module.build(native, image, report, *extra)[:3]
            final = index == len(STAGES)
            if final:
                check_final(image, patch, report)
                if source_inventory() != source_hashes:
                    raise ValueError('Source files changed during the rebuild')
            stage = output/('final' if final else f'replay/{index:02}-{name}')
            publish(stage, image, patch, report, final=final)
            row = {'stage': name, 'module': module_name, 'output_sha256': sha256(image),
                   'patch_sha256': sha256(patch), 'report_sha256': canonical(report),
                   'elapsed_seconds': round(time.monotonic()-started, 3)}
            write_new(output/f'stage-{index:02}.json', (json.dumps(row, indent=2)+'\n').encode())
            completed.append(row)
            print(json.dumps(row), flush=True)
        result = {'complete': True, 'stages': completed, 'output_sha256': ROM_SHA,
                  'patch_sha256': PATCH_SHA, 'report_sha256': canonical(report),
                  'reviewed_profile_sha256': REPORT_SHA,
                  'ordinary_scene_acceptance': False, 'hardware_acceptance': False,
                  'final_directory': 'final', 'clean_clone_base_translation_recipe': False}
        write_new(output/'rebuild.json', (json.dumps(result, indent=2)+'\n').encode())
        return result
    except Exception as error:
        write_new(output/'failure.json', (json.dumps({'complete': False, 'completed': completed,
                  'error': str(error)}, indent=2)+'\n').encode())
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, default=ROOT/'build/v0-hardware-fixes-02')
    p.add_argument('--rom', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    p.add_argument('--rel', type=Path, default=ROOT/'build/gamecube/files/foresta.rel.szs.decoded')
    p.add_argument('--symbols', type=Path, default=ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt')
    p.add_argument('--output', type=Path, default=ROOT/'build/v1-rebuilt-01')
    args = p.parse_args()
    try:
        output = checked_output(args.output)
    except ValueError as error:
        p.error(str(error))
    result = rebuild(read_inputs(args.base, args.rom, args.rel, args.symbols), output)
    print(json.dumps({'output': str(args.output/'final'), 'complete': result['complete']}))


if __name__ == '__main__':
    main()
