"""Restore one original mood/timer pair without changing English presentation."""

from textcodec import encode, tokenize

PAIRS = frozenset(('7F090200017F09080001', '7F090200017F09080002'))


def validate_rule(rule):
    if (not isinstance(rule, dict) or set(rule) != {'source_offset', 'reference_offset', 'commands'}
            or any(type(rule.get(key)) is not int or not 0 <= rule[key] < 8192
                   for key in ('source_offset', 'reference_offset'))
            or not isinstance(rule.get('commands'), str) or rule['commands'] not in PAIRS):
        raise ValueError('Native mood restoration requires one exact original mood/timer pair')


def restore(reference_text, source, rule, info):
    validate_rule(rule)
    pair = bytes.fromhex(rule['commands'])
    at = rule['source_offset']
    source_tokens = list(tokenize(source, info))
    def mood(token):
        return token.kind == 'cmd' and len(token.data) == 5 and token.data[1] == 9 and token.data[2] in (2, 8)
    native = [token for token in source_tokens if mood(token)]
    if (len(native) != 2 or [token.offset for token in native] != [at, at+5]
            or b''.join(token.data for token in native) != pair):
        raise ValueError('Mood restoration does not cover the complete exact native pair')
    # The selected native effect starts a page, not an arbitrary phrase. Its
    # corresponding English page is reviewed individually, not matched by count.
    preceding = [token for token in source_tokens if token.offset < at and token.data != b'\xcd']
    if preceding and preceding[-1].data != b'\x7f\x02':
        raise ValueError('Native mood pair must begin a native page')
    reference_info = list(info)+[(0, 0)]*max(0, 0x75-len(info))
    reference_info[0x74] = (2, 0)
    reference = list(tokenize(encode(reference_text, reference_info), reference_info))
    if any(mood(token) for token in reference):
        raise ValueError('English reference already contains mood/timer orders')
    offset = rule['reference_offset']
    tag = '{cmd:7F02}'
    if (offset > len(reference_text)
            or offset != 0 and reference_text[max(0, offset-len(tag)):offset] != tag):
        raise ValueError('Restored mood pair must begin a reviewed English page')
    insertion = ''.join('{cmd:'+pair[n:n+5].hex().upper()+'}' for n in (0, 5))
    result = reference_text[:offset]+insertion+reference_text[offset:]
    actors = lambda tokens: [token.data for token in tokens if token.kind == 'cmd' and 8 <= token.data[1] <= 12]
    # Do not let the ordinary opcode-position adapter permute neighbouring
    # expressions around a pair inserted at the wrong English page.
    if actors(source_tokens) != actors(tokenize(encode(result, reference_info), reference_info)):
        raise ValueError('Restored mood pair changes native actor order or arguments')
    return result, [{'operation': 'restore_complete_native_mood_pair',
                     'source_offset': at, 'reference_offset': offset, 'commands': rule['commands']}]
