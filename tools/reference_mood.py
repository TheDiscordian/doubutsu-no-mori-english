"""Restore one original mood/timer pair without changing English presentation."""

from textcodec import encode, tokenize

PAIRS = frozenset(('7F090200017F09080001', '7F090200017F09080002'))
SALE_PAIR = '7F090200017F09080000'


def validate_rule(rule):
    required = {'source_offset', 'reference_offset', 'commands'}
    if (not isinstance(rule, dict) or not required <= set(rule) <= required | {'anchor'}
            or any(type(rule.get(key)) is not int or not 0 <= rule[key] < 8192
                   for key in ('source_offset', 'reference_offset'))
            or not isinstance(rule.get('commands'), str) or rule['commands'] not in PAIRS | {SALE_PAIR}
            or 'anchor' in rule and rule['anchor'] not in ('before_expression_0E', 'before_final_end',
                                                          'after_sale_quest_before_surprise')
            or (rule['commands'] == SALE_PAIR) != (rule.get('anchor') == 'after_sale_quest_before_surprise')):
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
    reference_info = list(info)+[(0, 0)]*max(0, 0x75-len(info))
    reference_info[0x74] = (2, 0)
    reference = list(tokenize(encode(reference_text, reference_info), reference_info))
    if any(mood(token) for token in reference):
        raise ValueError('English reference already contains mood/timer orders')
    offset = rule['reference_offset']
    if offset > len(reference_text):
        raise ValueError('Native mood insertion exceeds the complete English reference')
    tag = '{cmd:7F02}'
    anchor = rule.get('anchor')
    if anchor == 'after_sale_quest_before_surprise':
        if (source[:at] != bytes.fromhex('7F0C020003')
                or source[at+10:at+15] != bytes.fromhex('7F09000002')
                or reference_text[:offset] != '{cmd:7F0C020003}'
                or not reference_text[offset:].startswith('{cmd:7F09000002}')):
            raise ValueError('Zero-duration sale mood requires the exact initial quest and surprise expression')
    elif anchor == 'before_expression_0E':
        if (source[at+10:at+15] != bytes.fromhex('7F0900000E')
                or not reference_text[offset:].startswith('{cmd:7F0900000E}')):
            raise ValueError('Phrase mood anchor must precede the exact original expression')
    elif anchor == 'before_final_end':
        if source[at+10:] != b'\xcd\x7f\x00' or reference_text[offset:] != '\n{cmd:7F00}':
            raise ValueError('Final mood anchor must precede only the original newline and normal end')
    else:
        # Page-start approvals retain their original strict contract. Phrase
        # exceptions require their own source/reference/output-bound anchor.
        preceding = [token for token in source_tokens if token.offset < at and token.data != b'\xcd']
        if preceding and preceding[-1].data != b'\x7f\x02':
            raise ValueError('Native mood pair must begin a native page')
        if offset != 0 and reference_text[max(0, offset-len(tag)):offset] != tag:
            raise ValueError('Restored mood pair must begin a reviewed English page')
    insertion = ''.join('{cmd:'+pair[n:n+5].hex().upper()+'}' for n in (0, 5))
    result = reference_text[:offset]+insertion+reference_text[offset:]
    actors = lambda tokens: [token.data for token in tokens if token.kind == 'cmd' and 8 <= token.data[1] <= 12]
    # Do not let the ordinary opcode-position adapter permute neighbouring
    # expressions around a pair inserted at the wrong English page or phrase.
    if actors(source_tokens) != actors(tokenize(encode(result, reference_info), reference_info)):
        raise ValueError('Restored mood pair changes native actor order or arguments')
    return result, [{'operation': 'restore_complete_native_mood_pair',
                     'source_offset': at, 'reference_offset': offset, 'commands': rule['commands']}]
