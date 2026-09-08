"""Complete native diagnostics, separate from the fixed coverage label catalog."""

from dataclasses import dataclass
import re

from textcodec import GLYPHS,encode,tokenize


@dataclass(frozen=True)
class Diagnostic:
    kind: str
    number: str
    translation: str


def definition(text):
    text=' '.join(text.split())
    match=re.fullmatch(r'うわさ\s*パターン([12])',text)
    if match:
        number=match[1]
        return Diagnostic('rumour_pattern',number,f'Rumour pattern {number}\n{{cmd:7F00}}')
    match=re.fullmatch(r'スクリプトバグ コワイあにき ([0-9]+)',text)
    if match:
        number=match[1]
        return Diagnostic('script_bug',number,f'Script bug\nCranky guy\n{number}\n{{cmd:7F00}}')
    match=re.fullmatch(r'このメッセージは ([0-9]+) (?:です|でヒ) デバッグちゅうに '
                      r'このめっせーじがでたら おしらせくださいまヒ By えぐち',text)
    if match:
        number=match[1]
        return Diagnostic('gyroid_debug_notice',number,
                          f'This is message\n{number}.{{cmd:7F04}}\n{{cmd:7F02}}'
                          'If this message appears\nwhile debugging,\n'
                          'please report it.\nBy Eguchi\n{cmd:7F00}')
    return None


def native_definition(data,info):
    tokens=list(tokenize(data,info,strict=False))
    if any(t.kind not in ('text','cmd') for t in tokens):
        return None
    return definition(''.join(GLYPHS[t.data[0]] for t in tokens if t.kind=='text'))


def validate_diagnostic(original,replacement,info):
    diagnostic=native_definition(original,info)
    if diagnostic is None:
        return
    expected=encode(diagnostic.translation,info)
    commands=lambda raw:[t.data for t in tokenize(raw,info) if t.kind=='cmd']
    if commands(original)!=commands(expected):
        raise ValueError('Native diagnostic has an unsupported control structure')
    if replacement!=expected:
        raise ValueError('Native diagnostic requires complete wording, printed number, and controls')
