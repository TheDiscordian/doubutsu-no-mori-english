"""Translate the native development scene selector without enabling its actions."""
import argparse
import json
from pathlib import Path
import re
import struct
import subprocess

from aflib import CODE_RAM, CODE_VROM, by_vrom, verified_rom, sha256, make_ups, apply_ups
from apply_translation import write_new
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from rebuild_v1 import checked_output, source_state
from title_start_fix import reconstruct

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '3a2e8b4241837daa7cea094deb2f2d229b2fa34755cf9103e493e27b1cf3fd8a'
VROM, RELOC, RAM = 0x73F4D0, 0x741A40, 0x80800000
SECTIONS = (7008, 736, 1840, 0, 274)
OWNER_SHA = '74df018bd0d06fa32f112469292af90ca49a7613d31dcd25448a069850846208'
RELOC_SHA = 'bc96e465cc5cb9483d6822b2c7da52de2624cbff1193c72195d97b3ccc94bc44'
TEXT_START, TEXT_END = 0x1E40, 0x2534
METADATA = bytes.fromhex(
    '000000000073f4d000741a4080800000808025700000000080801a3480801a2800000000000000000000000000000240')
SOURCE_FILES = {
    'upstream/af/src/overlays/gamestates/ovl_select/m_select.c':
        '5d9afab121312db622973569a3ef31c675104babe104f41c0b8076f165686eb0',
    'upstream/af/src/boot/libu64/gfxprint.c':
        '0d52b07cb67b13ce28b0e1f1a1bfa0b01d42a2fede2b894f66ae797ca82a3b89',
    'upstream/af/include/libu64/gfxprint.h':
        '9b095e6e8254aa37158fa897978b39d26e1c108f1c66abcf35d0758a46cbff21',
}
# Original translations of native development labels, not GC dialogue matches.
# The original third field label has a spelling error; retain its course number.
SCENES = (
    ('ﾌｨｰﾙﾄﾞ ｺｰｽ1', 'Field Course 1'), ('ﾌｨｰﾙﾄﾞ ｺｰｽ2', 'Field Course 2'),
    ('ﾌｨｰﾙﾃﾞ ｺｰｽ3', 'Field Course 3'), ('ｵﾐｽﾞﾃｽﾄ ｺｰｽ', 'Water Test Course'),
    ('ｱｼｱﾄﾃｽﾄｺｰｽ', 'Footprint Test Area'), ('npc ﾃｽﾄｺｰｽ', 'NPC Test Course'),
    ('NPCｱﾚﾝｼﾞﾙｰﾑ', 'NPC Arrange Room'), ('NPCﾗﾝﾀﾞﾑｺｰｽ', 'Random NPC Course'),
    ('FGﾂｰﾙ ﾌｨｰﾙﾄﾞﾖｳ', 'FG Tool for Field'), ('ｵﾐｾ', 'Shop'),
    ('BGﾌﾟﾚﾋﾞｭｰ ｶﾜﾅｼ', 'BG Preview No River'), ('BGﾌﾟﾚﾋﾞｭｰ ｶﾜｱﾘ', 'BG Preview (River)'),
    ('ﾔﾐﾌﾞﾛｰｶｰﾉ ｵﾐｾ', 'Black Market Shop'), ('FGﾂｰﾙ ﾍﾔﾉﾅｶﾖｳ', 'FG Tool for Indoors'),
    ('ﾕｳﾋﾞﾝｷｮｸ', 'Post Office'), ('start demo 1', 'start demo 1'),
    ('start demo 2', 'start demo 2'), ('ｺｳﾊﾞﾝ', 'Police Station'),
    ('ﾎﾛﾊﾞｼｬ', 'Covered Wagon'), ('ﾌﾟﾚｰﾔｰ ｾﾚｸﾄ', 'Player Select'),
    ('ﾏｲﾙｰﾑ size S', 'My Room size S'), ('ﾏｲﾙｰﾑ size M', 'My Room size M'),
    ('ﾏｲﾙｰﾑ size L', 'My Room size L'), ('ｺﾝﾋﾞﾆ', 'Convenience Store'),
    ('ｽｰﾊﾟｰ', 'Supermarket'), ('ﾃﾞﾊﾟｰﾄ1F', 'Department Store 1F'),
    ('ﾃｽﾄｺｰｽ 5', 'Test Course 5'), ('ﾌﾟﾚｰﾔｰ ｾﾚｸﾄ 2', 'Player Select 2'),
    ('ﾌﾟﾚｰﾔｰ ｾﾚｸﾄ 3', 'Player Select 3'), ('ﾃﾞﾊﾟｰﾄ2F', 'Department Store 2F'),
    ('ｲﾍﾞﾝﾄ ｺｸﾁ', 'Event Announcement'), ('ｶﾏｸﾗ', 'Igloo'),
    ('for field tool', 'for field tool'), ('ｷｬｸﾏﾁ ﾃﾞﾓ', 'Attract Demo'),
    ('ﾌﾟﾚｰﾔｰ ｾﾚｸﾄ 4', 'Player Select 4'),
)
OTHER = (
    (0x2188, 'ｼﾊﾞﾗｸｵﾏﾁｸﾀﾞｻｲ', 'Please wait a little while.'),
    (0x21A4, 'ﾁｮｯﾄ ﾏｯﾃﾈ', 'Wait a moment, okay?'),
    (0x21B8, 'ｳｪｲﾄ ｱ ﾓｰﾒﾝﾄ', 'Wait a moment.'),
    (0x21D0, 'ﾛｰﾄﾞﾁｭｳ', 'Loading...'),
    (0x21E4, 'ﾅｳ ﾜｰｷﾝｸﾞ', 'Now working.'),
    (0x21F8, 'ｲﾏ ﾂｸｯﾃﾏｽ', 'Making it now.'),
    (0x220C, 'ｺｼｮｳｼﾞｬﾅｲﾖ', "It's not broken!"),
    (0x2224, 'ｺｰﾋｰ ﾌﾞﾚｲｸ', 'Coffee break.'),
    (0x223C, 'Bﾒﾝｦｾｯﾄｼﾃｸﾀﾞｻｲ', 'Please insert Side B.'),
    (0x225C, 'ｼﾞｯﾄｶﾞﾏﾝﾉｺﾃﾞｱｯﾀ', 'I waited patiently.'),
    (0x2280, 'ｲﾏｼﾊﾞﾗｸｵﾏﾁｸﾀﾞｻｲ', 'Please wait a little longer.'),
    (0x22A0, 'ｱﾜﾃﾅｲｱﾜﾃﾅｲ｡ﾋﾄﾔｽﾐﾋﾄﾔｽﾐ｡', 'No rush, no rush.\n          Take a break, take a break.'),
    (0x2370, 'ｽﾃｯﾌﾟ :**m**s', 'Step  :**m**s'),
    (0x2384, 'ﾊﾚ', 'Clear'), (0x238C, 'ｱﾒ', 'Rain'), (0x2394, 'ﾕｷ', 'Snow'),
    (0x239C, 'ｻｸﾗ', 'Blossoms'), (0x23A4, 'ﾗﾝﾀﾞﾑ', 'Random'),
    (0x23B0, 'ﾃﾝｷ   :%s', 'Weather:%s'),
    (0x23C0, 'ｵﾄｺﾉｺ', 'Boy'), (0x23CC, 'ｵﾝﾅﾉｺ', 'Girl'),
    (0x23D8, 'ｾｲﾍﾞﾂ :%s', 'Gender:%s'),
    (0x23E8, 'ﾌｸ    :%03d', 'Shirt :%03d'),
    (0x23F8, 'ﾑｼｻｻﾚ :ｲﾀｸﾅｲ', 'Sting :Painless'),
    (0x2410, 'ﾑｼｻｻﾚ :ｲﾀｿｳ', 'Sting :Painful'),
    (0x2428, 'ﾃﾞｰﾀ  :ﾓﾉﾎﾝ', 'Data:Genuine'),
    (0x243C, 'ﾃﾞｰﾀ  :ｶｹﾞﾑｼｬ', 'Data:Body double'),
    *((0x2454+i*12, f'ﾀｲﾌﾟ{i+1}', f'Type {i+1}') for i in range(8)),
    (0x24B4, 'ｶｵ    :%s', 'Face  :%s'),
    (0x24C8, 'ｻﾞｯｶﾔ', 'General Store'), (0x24D4, 'ﾃﾞｻﾞｲﾅ-', 'Designer'),
    (0x24E4, 'ﾌﾞﾛ-ｶ-', 'Broker'), (0x24F0, 'ｶﾞﾊｸ', 'Artist'),
    (0x24FC, 'ｼﾞｭｳﾀﾝ', 'Carpet'), (0x250C, 'ｸﾛﾋｮｳ', 'Black Panther'),
    (0x2518, 'ｲﾍﾞﾝﾄ :%s', 'Event:\n                       %s'),
    (0x2528, '-ｾｯﾃｲ-', '-Settings-'),
)
# Full left labels fit before the unchanged settings column at x=23.
LAYOUT_WORDS = ((0xF6C, 0x24050005, 0x24050001),)


def word(data, at):
    return struct.unpack_from('>I', data, at)[0]


def visible(raw):
    # Gfxprint ignores EUC-JP's 0x8E prefixes; 8C/8D only select kana shape.
    return raw.translate(None, b'\x8c\x8d').decode('euc_jp')


def strings(data):
    result, at = {}, TEXT_START
    while at < TEXT_END:
        end = data.index(b'\0', at, TEXT_END)
        result[at] = data[at:end]
        following = (end+4) & ~3
        if any(data[end:following]):
            raise ValueError('Changed native string alignment padding')
        at = following
    if at != TEXT_END or len(result) != 101:
        raise ValueError('Changed native scene-menu string inventory')
    return result


def references(data, reloc):
    """Read actual native R_MIPS_32 and HI16/LO16 string references."""
    starts, sizes = (0, 0, SECTIONS[0], sum(SECTIONS[:2])), (0, *SECTIONS[:3])
    high, result = {}, []
    for entry, in struct.iter_unpack('>I', reloc[20:20+SECTIONS[4]*4]):
        section, kind, off = entry >> 30, (entry >> 24) & 63, entry & 0xFFFFFF
        if section == 0 or off & 3 or off+4 > sizes[section]:
            raise ValueError('Invalid scene-menu relocation location')
        at = starts[section]+off
        value = word(data, at)
        if kind == 2:
            if RAM+TEXT_START <= value < RAM+TEXT_END:
                result.append((None, at, value-RAM))
        elif kind == 5:
            if value >> 26 != 15:
                raise ValueError('Changed high-half relocation instruction')
            high[(value >> 16) & 31] = at, value
        elif kind == 6:
            register = (value >> 21) & 31
            if register not in high:
                raise ValueError('Unpaired scene-menu low relocation')
            hi_at, hi_word = high[register]
            target = ((hi_word & 65535) << 16)+struct.unpack_from('>h', data, at+2)[0]
            if RAM+TEXT_START <= target < RAM+TEXT_END:
                result.append((hi_at, at, target-RAM))
        elif kind != 4:
            raise ValueError('Unsupported scene-menu relocation kind')
    if len(result) != 101:
        raise ValueError('Changed scene-menu string references')
    return result


def patch_owner(old, reloc):
    if (sha256(old) != OWNER_SHA or sha256(reloc) != RELOC_SHA
            or struct.unpack_from('>5I', reloc) != SECTIONS):
        raise ValueError('Changed native scene-menu owner or relocation')
    source = strings(old)
    translations = {at: (before, after) for at, before, after in OTHER}
    for i, (before, after) in enumerate(SCENES):
        at, action, scene = struct.unpack_from('>3I', old, 0x1B60+i*12)
        if action != RAM or scene != i or len(after)+3 > 22:
            raise ValueError('Changed scene destination/action table')
        translations[at-RAM] = (f'{i+1:2}:'+before, f'{i+1:2}:'+after)
    changed = bytearray(old)
    changed[TEXT_START:TEXT_END] = bytes(TEXT_END-TEXT_START)
    mapping, records, cursor = {}, [], TEXT_START
    for at, raw in source.items():
        before = visible(raw)
        if at in translations:
            expected, after = translations[at]
            if before != expected:
                raise ValueError('Changed native source label')
        else:
            after = before
        if (any(not (32 <= ord(c) <= 126 or c == '\n') for c in after)
                or '%' in after.replace('%03d', '').replace('%04d', '').replace('%02d', '').replace('%s', '')):
            raise ValueError('Untranslated or unsafe scene-menu string')
        if re.findall(r'%(?:0\d+)?[ds]', before) != re.findall(r'%(?:0\d+)?[ds]', after):
            raise ValueError('Changed printf arguments in translated text')
        encoded = after.encode('ascii')+b'\0'
        if cursor+len(encoded) > TEXT_END:
            raise ValueError('Complete English scene-menu text exceeds native allocation')
        mapping[at] = cursor
        changed[cursor:cursor+len(encoded)] = encoded
        records.append({'original_offset': at, 'offset': cursor, 'source': before,
                        'english': after, 'translated': any(ord(c) > 127 for c in before)})
        cursor = (cursor+len(encoded)+3) & ~3
    if not set(translations) <= set(source) or cursor > TEXT_END:
        raise ValueError('Missing translated record or exhausted aligned storage')
    refs = references(old, reloc)
    if {target for _, _, target in refs} != set(source):
        raise ValueError('String inventory and installed references disagree')
    allowed = set(range(TEXT_START, TEXT_END))
    for hi, at, original in refs:
        target = RAM+mapping[original]
        if hi is None:
            struct.pack_into('>I', changed, at, target)
            allowed.update(range(at, at+4))
        else:
            struct.pack_into('>I', changed, hi, (word(old, hi) & 0xFFFF0000)|((target+0x8000) >> 16))
            struct.pack_into('>I', changed, at, (word(old, at) & 0xFFFF0000)|(target & 65535))
            allowed.update(range(hi, hi+4))
            allowed.update(range(at, at+4))
    for at, before, after in LAYOUT_WORDS:
        if word(old, at) != before or at in allowed:
            raise ValueError('Changed scene-list coordinate instruction')
        struct.pack_into('>I', changed, at, after)
        allowed.update(range(at, at+4))
    if len(changed) != len(old) or any(a != b and i not in allowed for i, (a, b) in enumerate(zip(old, changed))):
        raise ValueError('Scene translation changes unrelated owner bytes')
    for base in (0x801A6010, 0x802F8010, 0x803D0010):
        shifted = relocate_verified_data(Image(RAM, len(old), SECTIONS), bytes(changed), reloc, base)
        for hi, at, original in refs:
            actual = word(shifted, at) if hi is None else (
                (word(shifted, hi) & 65535) << 16)+struct.unpack_from('>h', shifted, at+2)[0]
            if actual != base+mapping[original]:
                raise ValueError('Relocated scene-menu reader selects the wrong string')
    return bytes(changed), records, cursor


def build(native, base):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Scene-menu text requires the exact RC7 baseline')
    if any(sha256((ROOT/path).read_bytes()) != digest for path, digest in SOURCE_FILES.items()):
        raise ValueError('Changed native scene-menu or graphics-print source')
    files = by_vrom(base)
    code = files[CODE_VROM].extract(base)
    if code[0x80106E50-CODE_RAM:0x80106E80-CODE_RAM] != METADATA:
        raise ValueError('Changed scene-menu registration or instance size')
    data, records, used = patch_owner(files[VROM].extract(base), files[RELOC].extract(base))
    image = reconstruct(native, base, {VROM: data})
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Scene-menu UPS reconstruction differs')
    return image, patch, {
        'version': 1, 'source_sha256': sha256(native), 'baseline_sha256': BASE_SHA,
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'source_builder_sha256': sha256(Path(__file__).read_bytes()), 'source_definitions': SOURCE_FILES,
        'changed_files': {f'{VROM:08X}': sha256(data)}, 'records': records,
        'translated_records': sum(row['translated'] for row in records),
        'text_bytes_available': TEXT_END-TEXT_START, 'text_bytes_used': used-TEXT_START,
        'allocation_changed': False, 'relocation_changed': False, 'menu_access_changed': False,
        'menu_actions_changed': False, 'saved_format_changed': False, 'save_readers_writers_changed': False,
        'saved_names_changed': False, 'required_ram_bytes': 0x800000,
        'native_execution_verified': False, 'ordinary_reachability_verified': False,
        'original_hardware_verified': False, 'prior_rc7_corrections_retained': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=ROOT/'build/v1rc7/Animal Forest English V1RC7.z64')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = checked_output(args.output)
    state = source_state()
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True,
                              capture_output=True, text=True).stdout.strip()
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(), args.base.read_bytes())
    if state['worktree_modified'] != source_state()['worktree_modified']:
        raise ValueError('Source state changed during scene-menu construction')
    report.update(source_revision=revision, worktree_modified=state['worktree_modified'])
    out.mkdir(parents=True, exist_ok=False)
    for name, value in {'animal-forest-scene-text.z64': image, 'animal-forest-scene-text.ups': patch,
                         'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        write_new(out/name, value)
    print(json.dumps({key: value for key, value in report.items() if key != 'records'}, indent=2))


if __name__ == '__main__':
    main()
