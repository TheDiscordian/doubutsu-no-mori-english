"""Lossless Animal Forest text tokens; command sizes come from the source ROM."""

from dataclasses import dataclass
import re

from aflib import CODE_RAM

# Byte-to-glyph correspondence, verified against the supplied character table.
# Multi-byte commands are tokens, never interpreted as Shift-JIS or UTF-8 bytes.
ROWS = [
    "あいうえおかきくけこさしすせそた",
    "ちつてとなにぬねのはひふへほまみ",
    [' ', '!', '"', 'む', 'め', '%', '&', "'", '(', ')', '～', '♥', ',', '-', '.', '♪'],
    "0123456789:◆<=>?",
    "@ABCDEFGHIJKLMNO",
    "PQRSTUVWXYZも+やゆ_",
    "よabcdefghijklmno",
    "pqrstuvwxyzらりるれ\uFFFC",
    "\uFFFD。「」、・ヲァィゥェォャュョッ",
    "ーアイウエオカキクケコサシスセソ",
    "タチツテトナニヌネノハヒフヘホマ",
    "ミムメモヤユヨラリルレロワンヴ☺",
    "ろわをんぁぃぅぇぉゃゅょっ\nガギ",
    "グゲゴザジズゼゾダヂヅデドバビブ",
    "ベボパピプペポがぎぐげござじずぜ",
    "ぞだぢづでどばびぶべぼぱぴぷぺぽ",
]
GLYPHS = {i*16+j: c for i, row in enumerate(ROWS) for j, c in enumerate(row)
          if i*16+j not in (0x7F, 0x80)}
ENCODE = {c: b for b, c in GLYPHS.items()}
LATIN = {b for b, c in GLYPHS.items() if 0x20 <= ord(c) < 0x7F}
TAG = re.compile(r"\{(cmd|glyph|raw):([0-9A-Fa-f]+)\}")


@dataclass(frozen=True)
class Token:
    kind: str
    data: bytes
    offset: int


def command_info(code):
    offset = 0x80106BF4 - CODE_RAM
    info = [tuple(code[offset+i*2:offset+i*2+2]) for i in range(0x61)]
    if len(info) != 0x61 or any(len(row) != 2 or not 2 <= row[0] <= 10 for row in info):
        raise ValueError("Unexpected N64 command-size table")
    return info


def tokenize(data, info, strict=True):
    pos = 0
    while pos < len(data):
        byte = data[pos]
        if byte == 0x7F:
            if pos+1 >= len(data):
                if strict:
                    raise ValueError(f"Truncated command at {pos:#x}")
                yield Token("raw", data[pos:], pos)
                break
            command = data[pos+1]
            if command >= len(info):
                if strict:
                    raise ValueError(f"Unsupported command 7F{command:02X} at {pos:#x}")
                size, kind = 2, "raw"
            else:
                size, kind = info[command][0], "cmd"
        elif byte == 0x80:
            size, kind = 2, "glyph"
        else:
            size, kind = 1, "text"
        if pos + size > len(data):
            if strict:
                raise ValueError(f"Truncated {kind} at {pos:#x}")
            yield Token("raw", data[pos:], pos)
            break
        yield Token(kind, data[pos:pos+size], pos)
        pos += size


def decode(data, info, strict=True):
    return "".join(GLYPHS[t.data[0]] if t.kind == "text"
                   else "{" + t.kind + ":" + t.data.hex().upper() + "}"
                   for t in tokenize(data, info, strict))


def encode(text, info, allow_raw=False):
    out, pos = bytearray(), 0
    while pos < len(text):
        if text[pos] == "{":
            match = TAG.match(text, pos)
            if not match or len(match[2]) % 2:
                raise ValueError(f"Invalid token at character {pos}")
            data = bytes.fromhex(match[2])
            if match[1] == "raw":
                if not allow_raw:
                    raise ValueError("Raw tokens are for lossless extraction, not translation edits")
            else:
                tokens = list(tokenize(data, info))
                if len(tokens) != 1 or tokens[0].kind != match[1]:
                    raise ValueError(f"Token kind/length mismatch: {match[0]}")
            out.extend(data)
            pos = match.end()
        else:
            c = text[pos]
            if c not in ENCODE:
                raise ValueError(f"Unrepresentable character {c!r} (U+{ord(c):04X})")
            out.append(ENCODE[c])
            pos += 1
    return bytes(out)


def control_signature(data, info):
    return [t.data.hex() for t in tokenize(data, info) if t.kind == "cmd"]


def has_japanese(data, info):
    return any(t.kind == "glyph" or
               (t.kind == "text" and (0x3000 <= ord(GLYPHS[t.data[0]]) <= 0x30FF))
               for t in tokenize(data, info, strict=False))
