"""Reproduce the base translation in an isolated source checkout, never an old build."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from aflib import sha256, verified_rom
from apply_translation import write_new
from check_keyboard_assembly import IMAGE
from check_references import AF_PIN, GC_PIN
from package_v0 import HARDWARE_FIX_SHA256
from prepare_inputs import LEGACY_UPS_SHA256
from rebuild_v1 import BASE_REPORT_SHA, canonical

ROOT = Path(__file__).resolve().parents[1]
NATIVE = 'local/rom/Doubutsu no Mori (Japan).z64'
LEGACY = 'local/legacy/AFProjectDistro/NAFE-WIP-2_12_2010.ups'
DISC = 'local/gamecube/Animal Crossing (USA, Canada).ciso'
DISC_SHA = 'f6e0e4d5662f1241add7ae1d7a6ddb95476f923cecd50f08c8eada5270427ccc'
MODULE = 'build/notice-seasonal-runtime/module.json'
INPUTS = (NATIVE, LEGACY, DISC)


def stage(name, tool, output, *args):
    return (name, tool, output, args)


# These are source/resource builds, not emulator scenarios. Names retained by
# the existing strict installers are local to the new checkout's empty build/.
STAGES = (
    stage('inspect', 'inspect_inputs', 'build/inspect', '--rom', NATIVE, '--legacy-ups', LEGACY),
    stage('gamecube', 'gamecube', 'build/gamecube', '--disc', DISC, '--extract'),
    stage('inventory', 'inventory', 'build/inventory', '--rom', NATIVE),
    stage('reference-text', 'gc_text', 'build/gamecube/text'),
    stage('reference-names', 'gc_names', 'build/gamecube/names'),
    stage('items', 'extended_items', 'build/design-items-resource', '--rom', NATIVE),
    stage('names', 'display_names', 'build/display-names', '--rom', NATIVE),
    stage('catchphrases', 'catchphrases', 'build/catchphrases', '--rom', NATIVE),
    stage('mail-catalogue', 'mail_catalog', 'build/mail-catalog', '--rom', NATIVE, '--catalog', '2'),
    stage('fortune-resources', 'build_fortune_slips', 'build/fortune-slip-resources', '--rom', NATIVE),
    stage('glyph-catalogue', 'mail_catalog', 'build/mail-glyph-catalog', '--rom', NATIVE, '--catalog', '4'),
    stage('catalogue-bundle', 'build_mail_glyph_catalog', 'build/mail-glyph-resources'),
    stage('mail-glyphs', 'extended_glyphs', 'build/mail-glyphs', '--mail'),
    stage('accent-glyphs', 'extended_glyphs', 'build/accent-glyphs', '--mail', '--accents'),
    stage('word-resources', 'npc_mail_words', 'build/design-items-words', '--native-species'),
    stage('name-aliases', 'npc_mail_names', 'build/npc-mail-names'),
    stage('item-articles', 'item_articles', 'build/design-items-articles', '--names', 'build/design-items-resource'),
    stage('runtime', 'build_runtime_module', 'build/notice-seasonal-runtime', '--rom', NATIVE),
    stage('candidate-font', 'build_extended_font_cartridge', 'build/mail-font-cartridge',
          '--resource', 'build/mail-glyphs/glyphs.bin'),
    stage('world-font', 'build_extended_font_cartridge', 'build/world-names-font',
          '--resource', 'build/mail-glyphs/glyphs.bin', '--world-names'),
    stage('candidates', 'reference_candidates', 'build/gyroid-default-candidates',
          '--rom', NATIVE, '--english-runtime', '--runtime-module', 'build/notice-seasonal-runtime',
          '--extended-font', 'build/mail-font-cartridge', '--english-dialogue-dates',
          '--english-fortunes', '--english-resetti-replies', '--english-shop-units',
          '--english-resident-words', '--english-shared-npc-words', '--english-credits',
          '--english-gyroid-default'),
    stage('mail-grader', 'build_mail_grading', 'build/mail-grading-npc', '--rom', NATIVE),
    stage('letter-creator', 'build_npc_mail_capture', 'build/design-items-creator',
          '--module', MODULE, '--words', 'build/design-items-words/words.bin',
          '--aliases', 'build/npc-mail-names/aliases.bin', '--mother-letters', '--departed-letters',
          '--villager-events', '--academy-letters', '--academy-scores', '--post-office',
          '--museum', '--shop-notices', '--quest-replies', '--notice-treasure',
          '--item-articles', 'build/design-items-articles/articles.bin',
          '--notice-owner', '--notice-seasonal', '--mail-glyphs'),
    stage('fortune-actor', 'build_fortune_actor', 'build/shop-notice-fortune', '--rom', NATIVE, '--module', MODULE),
    stage('leaflet-dates', 'build_leaflet_dates', 'build/leaflet-dates'),
    stage('renewal-code', 'build_mail_generation', 'build/leaflet-letters-probe', '--module', MODULE, '--leaflets'),
    stage('event-code', 'build_mail_generation', 'build/event-leaflet-probe', '--module', MODULE, '--event-leaflets'),
    stage('renewal-actor', 'build_renewal_actor', 'build/shop-notice-renewal', '--rom', NATIVE, '--module', MODULE),
    stage('event-actor', 'build_event_actor', 'build/shop-notice-event', '--rom', NATIVE, '--module', MODULE),
    stage('notice-owners', 'build_shop_notice_owners', 'build/shop-notice-owners', '--module', MODULE),
    stage('snowman', 'build_snowman_actor', 'build/shop-notice-snowman', '--module', MODULE,
          '--items', 'build/design-items-resource/names.bin'),
    stage('secret-letters', 'build_secret_actor', 'build/secret-actor', '--module', MODULE),
    stage('quest-replies', 'build_quest_reply_owners', 'build/quest-reply-owners', '--module', MODULE),
    stage('notice-reader', 'build_notice_overlay', 'build/noticeboard-seasonal/reader',
          '--module', MODULE, '--treasure', '--seasonal'),
    stage('treasure-owner', 'notice_treasure_owner', 'build/noticeboard-treasure/owners', '--module', MODULE),
    stage('seasonal-owner', 'notice_seasonal_owner', 'build/noticeboard-seasonal/owner', '--module', MODULE),
    stage('gyroid-default', 'build_gyroid_default_actor', 'build/gyroid-default-actor'),
    stage('owner-editor', 'build_hboard_overlay', 'build/hboard-editor-overlay'),
    stage('inventory-overlay', 'build_inventory_overlay', 'build/inventory-english-overlay'),
    stage('inventory-menu', 'build_inventory_menu_text', 'build/inventory-menu-text-overlay'),
    stage('inventory-descriptions', 'build_tag_descriptions', 'build/tag-descriptions-overlay'),
    stage('catalogue-overlay', 'build_catalogue_overlay', 'build/catalogue-names-overlay'),
    stage('map-overlay', 'build_map_overlay', 'build/map-names-overlay'),
    stage('map-labels', 'build_map_labels', 'build/map-labels-overlay'),
    stage('fishing-name', 'build_fishing_name', 'build/fishing-name-overlay'),
    stage('letter-names', 'build_letter_names', 'build/letter-names-overlay'),
    stage('text-extension', 'build_text_extension', 'build/text-catchphrases', '--choices', '--identities', '--borrowed'),
    stage('apology-editor', 'build_apology_overlay', 'build/apology-input-overlay'),
    stage('integration', 'build_apology_input_pilot.sh', 'build/apology-input-pilot'),
    stage('accent-items', 'accent_items', 'build/accent-items-candidate'),
    stage('accent-articles', 'accent_item_articles', 'build/accent-item-articles'),
    stage('accent-catalogue', 'accent_mail_catalog', 'build/accent-mail-catalog'),
    stage('accent-font', 'build_extended_font_cartridge', 'build/accent-mail-font',
          '--resource', 'build/accent-glyphs/glyphs.bin', '--world-names', '--mail-literals'),
    stage('accent-adapters', 'accent_mail_overlays', 'build/accent-mail-overlays'),
    stage('accent-install', 'accent_items_install', 'build/accent-items-pilot'),
    stage('unused-names', 'unused_names', 'build/unused-names-pilot'),
    stage('general-strings', 'residual_general', 'build/residual-general-pilot'),
    stage('reserve-letters', 'reserve_letters', 'build/reserve-letters-pilot'),
    stage('classic-adapters', 'build_classic_letters', 'build/classic-letters-candidate'),
    stage('classic-install', 'classic_letters', 'build/classic-letters-pilot'),
    stage('hardware-fixes', 'first_job_progression', 'build/v0-hardware-fixes-02', '--shrine', '--letter-advice'),
)


def file_hash(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def git(path, *args):
    return subprocess.run(['git', '-C', str(path), *args], check=True,
                          capture_output=True, text=True, timeout=120).stdout.strip()


def clean_revision(path, expected=None):
    revision = git(path, 'rev-parse', 'HEAD')
    if expected is not None and revision != expected:
        raise ValueError('Changed source revision: '+str(path))
    if git(path, 'status', '--porcelain', '--untracked-files=no'):
        raise ValueError('Tracked source files are modified: '+str(path))
    return revision


def check_inputs(root):
    verified_rom((root/NATIVE).read_bytes())
    values = {p: file_hash(root/p) for p in INPUTS}
    if values[LEGACY] != LEGACY_UPS_SHA256 or values[DISC] != DISC_SHA:
        raise ValueError('Changed source legacy patch or GAFE01 disc')
    clean_revision(root/'upstream/af', AF_PIN)
    clean_revision(root/'local/ac-decomp', GC_PIN)
    return values


def source_files(root):
    names = git(root, 'ls-files', '-z', '--', 'tools', 'runtime', 'overlays', 'translations').split('\0')
    return {name: file_hash(root/name) for name in sorted(names) if name}


def clone(source, target, revision):
    subprocess.run(['git', 'clone', '--quiet', '--no-hardlinks', '--no-checkout',
                    str(source), str(target)], check=True, capture_output=True, timeout=120)
    git(target, 'checkout', '--quiet', '--detach', revision)
    clean_revision(target, revision)


def initialise(output):
    revision = clean_revision(ROOT)
    if git(ROOT, 'ls-files', '--others', '--exclude-standard', '--', 'tools', 'runtime', 'overlays', 'translations'):
        raise ValueError('Commit build sources before cloning the recipe')
    inputs = check_inputs(ROOT)
    sources = source_files(ROOT)
    subprocess.run(['docker', 'image', 'inspect', IMAGE], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    for tool in ('gcc', 'git'):
        if shutil.which(tool) is None:
            raise ValueError('Missing existing host tool: '+tool)
    output.mkdir(parents=True, exist_ok=False)
    source = output/'source'
    clone(ROOT, source, revision)
    clone(ROOT/'upstream/af', source/'upstream/af', AF_PIN)
    (source/'local').mkdir(exist_ok=True)
    clone(ROOT/'local/ac-decomp', source/'local/ac-decomp', GC_PIN)
    for name in INPUTS:
        target = source/name
        target.parent.mkdir(parents=True, exist_ok=True)
        # Copy, rather than link, so no builder can overwrite the supplied input.
        shutil.copyfile(ROOT/name, target)
        target.chmod(0o444)
    if check_inputs(source) != inputs or source_files(source) != sources or (source/'build').exists():
        raise ValueError('Isolated checkout does not match the clean source/input snapshot')
    manifest = {'version': 1, 'source_revision': revision, 'sources': sources,
                'inputs': inputs, 'af_revision': AF_PIN, 'gc_revision': GC_PIN,
                'toolchain_image': IMAGE, 'recipe': json.loads(json.dumps(STAGES)),
                'retained_build_inputs': [], 'source_directory': 'source',
                'legacy_scope': 'Reference corroboration; legacy output is not the translation base'}
    write_new(output/'inputs.json', (json.dumps(manifest, indent=2)+'\n').encode())
    return manifest


def command(row, source):
    _, tool, destination, arguments = row
    if tool.endswith('.sh'):
        return ['bash', 'tools/'+tool]
    args = [str(source/value) if value.startswith(('build/', 'local/')) else value for value in arguments]
    return [sys.executable, 'tools/'+tool+'.py', *args, '--output', str(source/destination)]


def output_files(source, destination):
    directory = source/destination
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError('Missing or redirected stage output: '+destination)
    files = {}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():
            raise ValueError('Stage output contains a symlink: '+str(path))
        if path.is_file():
            files[path.relative_to(source).as_posix()] = file_hash(path)
    if not files:
        raise ValueError('Empty stage output: '+destination)
    return files


def check_final(source):
    base = source/'build/v0-hardware-fixes-02'
    report = json.loads((base/'build.json').read_text())
    if (file_hash(base/'animal-forest-halfwidth.z64') != HARDWARE_FIX_SHA256
            or canonical(report) != BASE_REPORT_SHA
            or file_hash(base/'animal-forest-halfwidth.ups') != report['patch_sha256']):
        raise ValueError('Clean base rebuild differs from corrected v0 ROM/patch/report')
    from aflib import apply_ups
    if apply_ups((source/NATIVE).read_bytes(), (base/'animal-forest-halfwidth.ups').read_bytes()) != (base/'animal-forest-halfwidth.z64').read_bytes():
        raise ValueError('Clean base UPS does not reconstruct the final ROM')
    return {'rom_sha256': HARDWARE_FIX_SHA256, 'patch_sha256': report['patch_sha256'],
            'canonical_report_sha256': BASE_REPORT_SHA}


def rebuild(output, through, resume=False):
    manifest = json.loads((output/'inputs.json').read_text()) if resume else initialise(output)
    source = output/'source'
    if (manifest['recipe'] != json.loads(json.dumps(STAGES))
            or manifest['sources'] != source_files(ROOT)
            or source_files(source) != manifest['sources']
            or check_inputs(source) != manifest['inputs']):
        raise ValueError('Changed recipe, source snapshot, or input; use a fresh build directory')
    clean_revision(source, manifest['source_revision'])
    completed = []
    expected_files = {}
    for index, row in enumerate(STAGES, 1):
        record = output/f'stage-{index:02}.json'
        if not record.exists():
            break
        saved = json.loads(record.read_text())
        if saved['stage'] != row[0] or saved['command'] != command(row, source):
            raise ValueError('Changed completed stage record')
        expected_files.update(saved['outputs'])
        completed.append(saved)
    for name, digest in expected_files.items():
        path = source/name
        if path.is_symlink() or not path.is_file() or file_hash(path) != digest:
            raise ValueError('Previously completed output changed: '+name)
    end = next(i for i, row in enumerate(STAGES, 1) if row[0] == through)
    if end < len(completed):
        raise ValueError('Requested stage precedes already completed work')
    # Strip inherited feature/output overrides; this recipe supplies its own.
    environment = {key: value for key, value in os.environ.items() if not key.startswith('AF_')}
    for index in range(len(completed)+1, end+1):
        row = STAGES[index-1]
        name, _, destination, _ = row
        if (source/destination).exists():
            raise ValueError('Incomplete output retained; inspect it before a fresh run: '+destination)
        invocation = command(row, source)
        log = output/f'stage-{index:02}.log'
        started = time.monotonic()
        print(json.dumps({'starting': name, 'stage': index, 'total': len(STAGES)}), flush=True)
        with log.open('xb') as stream:
            result = subprocess.run(invocation, cwd=source, env=environment,
                                    stdout=stream, stderr=subprocess.STDOUT, timeout=900)
        if result.returncode:
            raise RuntimeError(f'Stage {name} failed ({result.returncode}); see {log}')
        saved = {'stage': name, 'command': invocation, 'elapsed_seconds': round(time.monotonic()-started, 3),
                 'log_sha256': file_hash(log), 'outputs': output_files(source, destination)}
        write_new(output/f'stage-{index:02}.json', (json.dumps(saved, indent=2)+'\n').encode())
        completed.append(saved)
        print(json.dumps({'completed': name, 'elapsed_seconds': saved['elapsed_seconds']}), flush=True)
    if source_files(source) != manifest['sources'] or check_inputs(source) != manifest['inputs']:
        raise ValueError('Source or input changed during compilation')
    clean_revision(source, manifest['source_revision'])
    complete = end == len(STAGES)
    result = {'complete': complete, 'stages_complete': len(completed), 'stages_total': len(STAGES),
              'last_stage': through, 'retained_build_inputs': [], 'native_tests_run': False,
              'hardware_acceptance': False}
    if complete:
        result.update(check_final(source))
    write_new(output/f'result-{end:02}.json', (json.dumps(result, indent=2)+'\n').encode())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--through', choices=[row[0] for row in STAGES], default=STAGES[-1][0])
    parser.add_argument('--resume', action='store_true', help='Continue a verified successful stage boundary')
    args = parser.parse_args()
    if args.output.is_symlink() or (args.output.exists() and not args.resume):
        parser.error('Choose a fresh directory; existing builds are preserved')
    print(json.dumps(rebuild(args.output.resolve(), args.through, args.resume), indent=2))


if __name__ == '__main__':
    main()
