"""Export a static site and a genuine two-game reconstruction recipe."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import struct
import subprocess

from aflib import ROM_SHA256, verified_rom, sha256, yaz0_decode, n64_checksum
from gamecube import Disc

ROOT = Path(__file__).resolve().parents[1]
TARGET_SHA = '08aa1c4418848138803059a68de667f473f9da490d7c0866ee501c58b8d0896b'
DONORS = ('forest_1st.arc', 'forest_2nd.arc', 'foresta.rel.szs')
WEB_FILES = ('index.html', 'style.css', 'app.mjs', 'core.mjs', 'worker.mjs', 'mark.svg')
NOTICE_FILES = ('SOURCE_NOTES.txt', 'LICENSE-tooling.txt', '.nojekyll')
SAVE_NOTE = 'Back up existing saves before playing a patched game. The patcher does not read or change save files.'
DOWNLOAD_NAME = 'Animal Crossing N64 - English.z64'
TRAILER_URL = 'https://www.youtube.com/watch?v=UloFru4K4Q8'


def refresh_web(out):
    """Refresh the live page without regenerating game data or the released video."""
    site = out/'site'
    manifest = json.loads((site/'release/manifest.json').read_text())
    report = json.loads((out/'build.json').read_text())
    if (manifest['output_sha256'] != TARGET_SHA or report['target_sha256'] != TARGET_SHA
            or sha256((site/'release/patch.afwp.gz').read_bytes()) != manifest['recipe']['sha256']
            or report['recipe_sha256'] != manifest['recipe']['sha256']):
        raise ValueError('Refresh requires the verified current portal export')
    for name in WEB_FILES:
        if sha256((site/name).read_bytes()) != report['site_source_sha256'][name]:
            raise ValueError('Preserve unrecorded live-site edits before refreshing: '+name)
    previous_notices = report.get('site_notice_sha256', {
        'SOURCE_NOTES.txt': sha256((ROOT/'docs/SOURCES.md').read_bytes()),
        'LICENSE-tooling.txt': sha256((ROOT/'LICENSE').read_bytes()),
        '.nojekyll': sha256(b''),
    })
    for name in NOTICE_FILES:
        if sha256((site/name).read_bytes()) != previous_notices[name]:
            raise ValueError('Preserve unrecorded live-site edits before refreshing: '+name)
    # Retire only the known redundant export copy; preserve it outside the site.
    old_video, archive = site/'media/trailer.mp4', out/'retired-site-trailer.mp4'
    if old_video.exists():
        if (sha256(old_video.read_bytes()) != '3d3bc78875eefe98b0b0d8ed1499a86222fc44139b8ae1697e9128d87fdaf00a'
                or archive.exists()):
            raise ValueError('Preserve unexpected trailer copies before refreshing')
        old_video.rename(archive)
    for name in WEB_FILES + NOTICE_FILES:
        shutil.copyfile(ROOT/'web'/name, site/name)
    manifest['save_compatibility'] = SAVE_NOTE
    manifest['output_name'] = DOWNLOAD_NAME
    (site/'release/manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    report['site_source_sha256'] = {name: sha256((site/name).read_bytes()) for name in WEB_FILES}
    report['site_notice_sha256'] = {name: sha256((site/name).read_bytes()) for name in NOTICE_FILES}
    report['trailer_url'] = TRAILER_URL
    (out/'build.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'site': str(site.relative_to(ROOT)), 'web_refreshed': True,
                      'patch_sha256': report['recipe_sha256'], 'game_data_changed': False}))


def donor_resources(path):
    manifest, buffers = [], []
    with Disc(path) as disc:
        if disc.header[:6] != b'GAFE01' or disc.header[7] != 0:
            raise ValueError('Expected USA/Canada Animal Crossing, GAFE01 revision 0')
        files = {entry['path']: entry for entry in disc.files()}
        reference = json.loads((ROOT/'build/gamecube/disc.json').read_text())
        hashes = {entry['path']: entry['sha256'] for entry in reference['files']}
        for name in DONORS:
            entry = files[name]
            raw = disc.read(entry['offset'], entry['size'])
            if sha256(raw) != hashes[name]:
                raise ValueError('GameCube donor differs from the translation reference: '+name)
            decoded = yaz0_decode(raw) if raw[:4] == b'Yaz0' else raw
            manifest.append({'path': name, 'size': len(raw), 'sha256': sha256(raw),
                             'decode': 'yaz0' if raw[:4] == b'Yaz0' else 'raw',
                             'decoded_size': len(decoded), 'decoded_sha256': sha256(decoded)})
            buffers.append(decoded)
    return manifest, buffers


def changed_regions(source, target):
    """Coalesce changed 256-byte blocks; retain unchanged original-ROM spans."""
    initial = source.ljust(len(target), b'\0')
    start = None
    for at in range(0, len(target), 256):
        changed = initial[at:at+256] != target[at:at+256]
        if changed and start is None:
            start = at
        elif not changed and start is not None:
            yield start, at
            start = None
    if start is not None:
        yield start, len(target)


def make_recipe(source, target, donors):
    index = {}
    for number, donor in enumerate(donors, 1):
        for at in range(0, len(donor)-31, 16):
            key = donor[at:at+32]
            if len(set(key)) >= 5:
                index.setdefault(key, (number, at))
    print(f'Indexed {len(index):,} donor anchors', flush=True)
    commands, literals = [], bytearray()
    donor_bytes = [0]*len(donors)
    def literal(start, end):
        if end > start:
            commands.append((start, end-start, 0, len(literals)))
            literals.extend(target[start:end])
    for start, end in changed_regions(source, target):
        pending = at = start
        while at+32 <= end:
            match = index.get(target[at:at+32])
            if match is None:
                at += 1
                continue
            number, offset = match
            donor = donors[number-1]
            count, maximum = 32, min(end-at, len(donor)-offset)
            while count+32 <= maximum and target[at+count:at+count+32] == donor[offset+count:offset+count+32]:
                count += 32
            while count < maximum and target[at+count] == donor[offset+count]:
                count += 1
            literal(pending, at)
            commands.append((at, count, number, offset))
            donor_bytes[number-1] += count
            at += count
            pending = at
        literal(pending, end)
    if sum(donor_bytes) < 65536:
        raise ValueError('Insufficient genuine GameCube donor reuse for this recipe')
    recipe = b'AFWP0001'+struct.pack('<II', len(commands), len(literals))
    recipe += b''.join(struct.pack('<4I', *row) for row in commands)+literals
    # Independently apply the emitted command stream to the supplied native ROM.
    restored = bytearray(source.ljust(len(target), b'\0'))
    pools = [literals, *donors]
    for out, count, number, offset in commands:
        restored[out:out+count] = pools[number][offset:offset+count]
    if bytes(restored) != target:
        raise ValueError('Recipe does not recreate the current cartridge')
    return recipe, {'commands': len(commands), 'literal_bytes': len(literals),
                    'gc_copy_bytes': sum(donor_bytes), 'gc_copy_bytes_by_resource': donor_bytes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--refresh-web', action='store_true', help='Refresh an existing verified site without rebuilding its patch or media')
    parser.add_argument('--rom', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--disc', type=Path, default=ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    parser.add_argument('--target', type=Path, default=ROOT/'build/v2-performance-fix-08/Animal Forest English V2.z64')
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT/'build'):
        raise ValueError('Portal exports must be inside ignored build/')
    if args.refresh_web:
        refresh_web(out)
        return
    if out.exists():
        raise ValueError('Choose a fresh directory under ignored build/')
    source = verified_rom(args.rom.read_bytes())
    target = args.target.read_bytes()
    if sha256(target) != TARGET_SHA or struct.unpack_from('>2I', target, 0x10) != n64_checksum(target):
        raise ValueError('Expected the checksummed V2-08 museum/credits correction cartridge')
    resources, buffers = donor_resources(args.disc)
    recipe, stats = make_recipe(source, target, buffers)
    compressed = gzip.compress(recipe, compresslevel=9, mtime=0)
    site = out/'site'
    (site/'release').mkdir(parents=True)
    (site/'media').mkdir()
    for name in WEB_FILES + NOTICE_FILES:
        shutil.copyfile(ROOT/'web'/name, site/name)
    manifest = {'format': 1, 'label': 'V2 · N64 keyboard edition', 'build': 'V2-08',
        'public_release': False, 'source_sha256': ROM_SHA256, 'source_size': len(source),
        'output_sha256': TARGET_SHA, 'output_size': len(target),
        'output_name': DOWNLOAD_NAME,
        'disc_id': 'GAFE01', 'disc_revision': 0, 'resources': resources,
        'recipe': {'file': 'patch.afwp.gz', 'sha256': sha256(compressed), 'size': len(compressed),
                   'decoded_sha256': sha256(recipe), 'decoded_size': len(recipe)},
        'requirements': {'expansion_pak': True, 'save_type': 'FlashRAM', 'save_bytes': 131072, 'rtc': True},
        'save_compatibility': SAVE_NOTE,
        'stats': stats}
    (site/'release/patch.afwp.gz').write_bytes(compressed)
    (site/'release/manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    # The trailer is hosted on YouTube; export only its local poster, never a ROM.
    trailer = ROOT/'build/trailer-cut-05/Animal Forest English - Trailer.mp4'
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', '10', '-i', str(trailer),
                    '-vf', 'crop=1440:1080:240:0,scale=800:600', '-frames:v', '1',
                    str(site/'media/town.webp')], check=True, timeout=30)
    report = {'site': str(site.relative_to(ROOT)), 'target_sha256': TARGET_SHA,
        'trailer_url': TRAILER_URL,
        'recipe_roundtrip': 'passed', 'recipe_sha256': sha256(compressed), **stats,
        'site_source_sha256': {name: sha256((site/name).read_bytes()) for name in WEB_FILES},
        'site_notice_sha256': {name: sha256((site/name).read_bytes()) for name in NOTICE_FILES},
        'public_release': False, 'contains_roms_or_saves': False}
    (out/'build.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
