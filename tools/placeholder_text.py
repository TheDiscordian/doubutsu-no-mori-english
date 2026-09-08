"""Exact native development labels; recognition never establishes reachability."""

from dataclasses import dataclass
import re

from aflib import sha256
from textcodec import GLYPHS, decode, encode, tokenize


@dataclass(frozen=True)
class Placeholder:
    kind: str
    english: str
    alternatives: tuple = ()


FIXED = {
    'よび': 'Reserved',
    'おみせようの、よびだポコ!': 'Shop reserve, poko!',
    'セイウチようの、よびだぎゃ!': 'Walrus reserve, gyah!',
    'ラクダのよびですもん!': "It's a camel reserve!",
    'オープニングの よび': 'Opening reserve',
    'アルバイトのうけこたえ よび': 'Part-time job\nResponse reserve',
    'ハニワくんの よび': 'Gyroid reserve',
    'えきいんさんの よび': 'Station staff reserve',
    'いちおう よび': 'Extra reserve',
    'おてがみ みせる よび': 'Letter display reserve',
    'たかびーねぇさんの トレードのよび': 'Snooty woman\nTrade reserve',
    'タカビーねえさんの プレゼント よび': 'Snooty woman\nGift reserve',
    'たかびーねえさんの セールスのよび': 'Snooty woman\nSales reserve',
    'うれしいときの プレゼント よび': 'Happy gift reserve',
    'うれしい トレードのよび': 'Happy trade reserve',
    'タカビーねえさんの うれしいセールスのよび': 'Snooty woman\nHappy sales reserve',
    'コワイあにき よびメッセージ': 'Cranky guy\nReserve message',
    'マメダヌキ よび': 'Young raccoon reserve',
    'イベントこくち よび': 'Event announcement\nReserve',
    'ごみとった よび': 'Trash collection reserve',
    'コワイあにきの トレードのよび': 'Cranky guy\nTrade reserve',
    'コワイあにきの セールスのよび': 'Cranky guy\nSales reserve',
}
NUMBERED = (
    ('イノシシの よびメッセージ', '', 'Boar\nReserve message {}'),
    ('くろひょう よびメッセージ', '', 'Black panther\nReserve message {}'),
    ('ハロウィン よびメッセージ', '', 'Halloween\nReserve message {}'),
    ('タカビーねえさんの トレード', 'のよび', 'Snooty woman\nTrade {} reserve'),
    ('ビーバーの よびメッセージ', '', 'Beaver\nReserve message {}'),
    ('おみくじ よびメッセージ', '', 'Fortune slip\nReserve message {}'),
    ('ふつうのおんなのこ いっぱんかいわよう よび', '', 'Normal girl\nGeneral chat reserve {}'),
    ('げんきギャル いっぱんかいわよう よび', '', 'Peppy girl\nGeneral chat reserve {}'),
)


def normalise(text):
    return ' '.join(text.split())


def label(text):
    text = normalise(text)
    match = re.fullmatch(r'ダミー\s*([0-9０-９]*)', text)
    if match:
        number = str(int(match[1])) if match[1] else ''
        return Placeholder('dummy', 'Dummy'+(' '+number if number else ''), ('Dummy'+number,))
    if text == 'きしゃのデモ よびのエリア':
        return Placeholder('train_demo_reserve', 'Train Demo\nExtra Area', ('Train Demo Extra Space',))
    if text in FIXED:
        alternatives = ('extra',) if text == 'イベントこくち よび' else ()
        return Placeholder('reserved', FIXED[text], alternatives)
    for prefix, suffix, english in NUMBERED:
        match = re.fullmatch(re.escape(prefix)+r'([0-9０-９]+)'+re.escape(suffix), text)
        if match:
            return Placeholder('numbered_reserve', english.format(int(match[1])))
    return None


def native_label(data, info):
    tokens = list(tokenize(data, info, strict=False))
    if any(t.kind in ('raw', 'glyph') for t in tokens):
        return None
    return label(''.join(GLYPHS[t.data[0]] for t in tokens if t.kind == 'text'))


def validate_placeholder(original, replacement, info):
    """Unallocated labels cannot become unrelated English dialogue or actions."""
    definition = native_label(original, info)
    if not definition:
        return
    native = list(tokenize(original, info))
    candidate = list(tokenize(replacement, info))
    visible = normalise(''.join(GLYPHS[t.data[0]] for t in candidate if t.kind == 'text'))
    allowed = {normalise(text) for text in (definition.english, *definition.alternatives)}
    if (any(t.kind not in ('text', 'cmd') for t in candidate) or visible not in allowed
            or [t.data for t in native if t.kind == 'cmd'] !=
               [t.data for t in candidate if t.kind == 'cmd']):
        raise ValueError('Native placeholder requires its English label or an approved complete sequence')


def placeholder_edit(id, original, info):
    definition = native_label(original, info)
    if not definition:
        return None
    commands = [t.data for t in tokenize(original, info) if t.kind == 'cmd']
    prefix = b'\x7f\x09\x00\x00\xff'
    if (not commands or commands[-1] not in (b'\x7f\x00', b'\x7f\x01')
            or not original.endswith(commands[-1])
            or commands[:-1] not in ([], [prefix])
            or commands[:-1] and not original.startswith(prefix)):
        raise ValueError('Placeholder fallback requires a native ending and optional leading expression reset')
    text = ''.join(decode(c, info) for c in commands[:-1])+definition.english+'\n'+decode(commands[-1], info)
    validate_placeholder(original, encode(text, info), info)
    return {'id': id, 'source_sha256': sha256(original), 'translation': text,
            'control_policy': 'exact', 'status': 'draft',
            'provenance': 'Original translation of an exact Japanese N64 development label',
            'placeholder_kind': definition.kind,
            'notes': 'Translate the complete native label, retaining its final command. '
                     'This is not gameplay dialogue, a new continuation allocation, '
                     'or evidence that the record is unreachable.'}
