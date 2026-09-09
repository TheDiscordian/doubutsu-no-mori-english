"""Complete, source-bound home-gyroid default without changing saved fields."""

from dataclasses import dataclass
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from textbanks import Bank, banks
from textcodec import decode, encode, tokenize

ROOT = Path(__file__).resolve().parents[1]
SLOT, ORIGINAL, DEFAULT = 0x2AE7, 0x0928, 0x055C
ID = f'message:{SLOT:04X}'
SOURCE_SHA256 = 'b3c40cd00dd3610400c2ff42cd922c63b7130720690e8abf30c16048a8eb7900'
RESERVE_SHA256 = '0727aac8e3f598400dccbb8e9a23f39c10b3bc13e0dc1c168b93d03c0aa95609'
INTRO_SOURCE_SHA256 = '863b2176916c9ba3e5c057195d63339ae17145d05a8b943eb7648f3beec995e5'
INTRO_SHA256 = '4fa7828c987f1b1f21e99a0b9faeaa9ffd46a334a4f43e531a34f2438f220f20'
DEFAULT_SHA256 = '8cb503014fe0fdb60f8cb69dc057eabc9931d293c4a38cbfdd3d850b6a25774b'
VARIANT_SHA256 = '06130e75b09b9cf1cec54660524d30ce41e696c41ec334ac19d60ffb173bbdd4'
RESERVE_REFERENCE_SHA256 = 'caf0ad524c17a27a0abe8485e09aba9e0817d93459e5e1a59daee9241401efad'
INITIALIZERS = (
    (0x8009465C, 0x8009467C, '800747fc58b1d07ee52cb7a86190a8f76bb5332ad50a07c0968f15c5fdbc2d6f'),
    (0x800C31D0, 0x800C327C, '1015eaf5fd07824af390ced9a9245c2dc1027de1069266542d76afdfda304cfd'),
)
GC_SYMBOLS = {
    'title_game_haniwa_data_init': (248, '9fa8062669401a0d4fd0f7d32f67d12a0e0d120a86fcf5944d68631a0003d9c5'),
    'mHm_ClearHomeInfo': (404, '6404cdd7ab64390500512e851db95979844d5b3822880baf1587bab1f1f576b3'),
    'haniwa_msg$393': (16, '2289fae58bcd3cdcef80b60480e55525b225967438962a33c41e31f04a2bb2bf'),
    'haniwa_msg$427': (16, '2289fae58bcd3cdcef80b60480e55525b225967438962a33c41e31f04a2bb2bf'),
    'aHNW_set_talk_info_dance': (168, '3cb29237ab2ef9eba78d033517f1acae4af33572e68a64f3a51a48dbc042f4d4'),
}
GC_LINES = (
    (18, '1ce29a8437f9bf90d493c0fb3ecf70cb21acf11418467d5395b2cf2698b79fba'),
    (27, '660598e5f0df373309b3bf0aa9aae222ceaaf006bd82b00a7a390d7aacd54142'),
    (22, '66525a02303e9802d9f89a14af415a5b36af487463128d215f1884cee4256b96'),
    (22, 'c2a179432ae6a51715622dbf60fdf20fe011fd41bf88400412479c8e9c7306f3'),
)


@dataclass(frozen=True)
class GyroidDefaultPermit:
    source_sha256: str = RESERVE_SHA256
    encoded_sha256: str = VARIANT_SHA256


def native_sources(native):
    native = verified_rom(native)
    original = {b.name: b.entries() for b in banks(native) if b.name in ('message', 'string')}
    for value, expected in ((original['string'][DEFAULT], SOURCE_SHA256),
                            (original['message'][ORIGINAL], INTRO_SOURCE_SHA256),
                            (original['message'][SLOT], RESERVE_SHA256)):
        if sha256(value) != expected: raise ValueError('Changed native gyroid default or reserve')
    code = by_vrom(native)[CODE_VROM].extract(native)
    for start, end, digest in INITIALIZERS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM]) != digest:
            raise ValueError('Changed gyroid default initialisation')
    return original


def verify_reserve(native, info):
    from code_sections import code_segments
    from reference_sequences import load_sequences, message_targets
    original = native_sources(native)
    if any(SLOT in message_targets(raw, info) for raw in original['message']):
        raise ValueError('Gyroid reserve has a native script caller')
    if any(m['id'] == ID for g in load_sequences().values() for m in g['members']):
        raise ValueError('Gyroid reserve is allocated to a sequence')
    files = by_vrom(native)
    for vrom, segment in code_segments()[0].items():
        if vrom not in files: continue
        data = files[vrom].extract(native)
        for offset in range(0, len(data)-3, 4):
            word = struct.unpack_from('>I', data, offset)[0]
            if segment.is_text(offset) and word & 65535 == SLOT and word >> 26 in range(8, 15):
                raise ValueError('Gyroid reserve has an executable immediate reference')
        for offset in range(0, len(data)-1, 2):
            if not segment.is_text(offset) and struct.unpack_from('>H', data, offset)[0] == SLOT:
                raise ValueError('Gyroid reserve has an aligned data reference')


def feature_matches(matches):
    """Reconcile only the exact reserve-label approval in an enabled build."""
    expected = {'id': ID, 'source_sha256': RESERVE_SHA256, 'reference_id': ID,
                'reference_sha256': RESERVE_REFERENCE_SHA256,
                'complete_reference': {'adapted_sha256': RESERVE_REFERENCE_SHA256}}
    row = matches.get(ID, {})
    if {k: v for k, v in row.items() if k != 'evidence'} != expected:
        raise ValueError('Changed gyroid reserve-label approval')
    return {k: v for k, v in matches.items() if k != ID}


def reference_payloads(native, info):
    from gc_names import symbol_data
    from gc_text import decode_gc, decoder_tables
    from gc_adapter import adapt_reference
    from mail_reference import BANK_HASHES, DECODER_SHA256, transcode
    original = native_sources(native)
    rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    decoder = ROOT/'local/ac-decomp/tools/msg_tool.py'
    if (sha256(rel) != '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837'
            or sha256(decoder.read_bytes()) != DECODER_SHA256):
        raise ValueError('Changed supplied gyroid executable or decoder')
    for name, expected in GC_SYMBOLS.items():
        raw = symbol_data(rel, symbols, name)
        if (len(raw), sha256(raw)) != expected: raise ValueError('Changed gyroid donor: '+name)
        if name.startswith('haniwa_msg$') and struct.unpack('>4I', raw) != tuple(range(0x76A, 0x76E)):
            raise ValueError('Changed actual gyroid line selection')
    tables = decoder_tables(decoder)
    sources = {}
    for name, arc, hashes in (
            ('string', 'forest_1st', BANK_HASHES['string']),
            ('message', 'forest_2nd', ('57e0971900ab944d24beb9b93f800cebda5177ca4200223d75601ef2d2a1d8ce',
                                     'e4962174ef139a28c6d2ff7dc5541ee8ec093944576eb6f0555c3719d0db4a2a'))):
        path = ROOT/f'build/gamecube/files/{arc}.arc.unpacked/data'
        data, table = [(path/(name+suffix+'.bin')).read_bytes() for suffix in ('_data', '_data_table')]
        if (sha256(data), sha256(table)) != hashes: raise ValueError('Changed English gyroid bank')
        sources[name] = Bank(name, 0, 0, data, table).entries()
    lines = sources['string'][0x76A:0x76E]
    if [(len(v), sha256(v)) for v in lines] != list(GC_LINES):
        raise ValueError('Changed complete gyroid reference lines')
    full = b'\xcd'.join(transcode(line, tables) for line in lines)
    raw = sources['message'][ORIGINAL]
    if sha256(raw) != INTRO_SHA256: raise ValueError('Changed complete gyroid introduction')
    text, _ = adapt_reference(decode_gc(raw, tables), original['message'][ORIGINAL], info,
                             'presentation', resident_runtime=True)
    intro = encode(text, info)
    commands = [t.data for t in tokenize(intro, info) if t.kind == 'cmd']
    if sha256(intro) != INTRO_SHA256 or commands.count(b'\x7f\x40') != 1:
        raise ValueError('Changed gyroid introduction adaptation or insertion')
    variant = intro.replace(b'\x7f\x40', full)
    if (len(full), sha256(full), len(variant), sha256(variant)) != (92, DEFAULT_SHA256, 206, VARIANT_SHA256):
        raise ValueError('Changed full gyroid default presentation')
    return full, intro, variant


def candidate(native, info):
    verify_reserve(native, info)
    _, _, variant = reference_payloads(native, info)
    return {'id': ID, 'source_sha256': RESERVE_SHA256, 'translation': decode(variant, info),
            'control_policy': 'gyroid_default', 'gyroid_default': True,
            'provenance': {'source': 'user-supplied GAFE01 revision 0 disc',
                           'reference_ids': ['message:0928', *[f'string:{i:04X}' for i in range(0x76A, 0x76E)]],
                           'reference_sha256': INTRO_SHA256, 'default_sha256': DEFAULT_SHA256},
            'status': 'source_bound_default_variant_requires_actor_and_editor_acceptance',
            'adaptations': [{'operation': 'substitute_exact_saved_default', 'command': '7F40'}]}


def permits(native, edits, info, *, enabled):
    special = [r for r in edits if 'gyroid_default' in r or r.get('control_policy') == 'gyroid_default']
    if not enabled:
        if special: raise ValueError('Gyroid variant requires its actor installation')
        return {}
    expected = candidate(native, info)
    if special != [expected] or sum(r['id'] == ID for r in edits) != 1:
        raise ValueError('Missing or changed complete gyroid variant')
    intro = [r for r in edits if r['id'] == 'message:0928']
    if len(intro) != 1 or sha256(encode(intro[0]['translation'], info)) != INTRO_SHA256:
        raise ValueError('Gyroid custom-message introduction must remain complete and unchanged')
    return {ID: GyroidDefaultPermit()}
