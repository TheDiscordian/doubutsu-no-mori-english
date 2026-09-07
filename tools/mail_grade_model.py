"""Independent bounded English mail-score model for native test expectations."""

import struct


def word_stats(body, prefixes, *, legacy=False):
    body = body.ljust(192,b' ')
    cap = len(body)
    def char(pos): return body[pos] if pos < cap else 32
    sep = lambda c: c in b' .?!,\x85\xcd'
    end = cap-3 if legacy else len(body[:cap-3].rstrip(b' '))
    if legacy:
        while end and char(end) == 32: end -= 1
    if not end: return 0,0
    offsets = struct.unpack_from('>27H',prefixes)
    words = hits = pos = 0
    while pos <= end:
        words += 1
        c = char(pos)
        if 65 <= c <= 90: c += 32
        if 97 <= c <= 122:
            pair = bytes((char(pos+1),char(pos+2)))
            hits += any(prefixes[54+i*2:56+i*2] == pair for i in range(offsets[c-97],offsets[c-96]))
        while pos < end and not (sep(char(pos)) and not sep(char(pos+1))): pos += 1
        pos += 1
    return words,hits


def grade(body,prefixes):
    if len(body) > 1024: raise ValueError('English mail-score input exceeds its bound')
    body = body.ljust(192,b' ')
    text = body.rstrip(b' ')
    length = len(text)
    scores = [0]*7
    upper = lambda c: 65 <= c <= 90
    end = lambda c: c in b'.?!'
    if text and length < len(body) and end(text[-1]): scores[0] += 20
    pos = 0
    while length-pos > 3:
        while length-pos > 3 and not end(text[pos]): pos += 1
        if length-pos > 3:
            pos += 1
            left = 3
            while left and not upper(text[pos]): pos += 1; left -= 1
            scores[0] += 10 if left else -10
    scores[1] = word_stats(body,prefixes)[1]*3
    first = text.lstrip(b' ')
    if first: scores[2] = 20 if upper(first[0]) else -10
    for pos in range(length-2):
        c = text[pos]
        if (upper(c) or 97 <= c <= 122) and c == text[pos+1] == text[pos+2]:
            scores[3] = -50
            break
    spaces = text.count(32)
    scores[4] = 20 if length-spaces > 0 and spaces*5 >= length-spaces else -20
    pos = 0
    while length-pos > 76:
        if end(text[pos]):
            pos += 1
            run = 0
            while not end(text[pos]):
                run += 1
                if run >= 75: break
                pos += 1
            if run >= 75:
                scores[5] = -150
                break
        pos += 1
    scores[6] = -20*sum(b' ' not in text[pos:pos+32] for pos in range(0,length-31,32))
    total = sum(scores)
    return scores+[total,1 if total >= 100 else 0 if total < 50 else 2]


def legacy_grade(body,prefixes):
    """Native/GAFE01 length grade, including its actual repetition counter."""
    words,hits = word_stats(body,prefixes,legacy=True)
    rate = hits*100//words if words else 0
    length = sum(c != 32 for c in body)
    previous,run,repeated = 32,1,False
    for c in body:
        if c == 32: continue
        if c == previous:
            run += 1
            special = c in (0x21,0x22,0x5F,0x90,0x5C) or 0x25 <= c <= 0x40 or 0x7F <= c <= 0x85
            if run >= (8 if special else 3):
                repeated = True
                break
        else: previous,run = c,0
    rank = 2
    if words < 3:
        if length < 5 or repeated: rank = 0
    elif rate >= 30: rank = 1
    elif repeated: rank = 0
    return rank,length,words,rate
