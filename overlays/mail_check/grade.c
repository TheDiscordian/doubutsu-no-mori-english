/* English letter scoring with explicit source and prefix-table bounds. */
#include "mail/grade.h"

#define PREFIX_BYTES 1606u
#define PREFIX_PAIRS 776u
extern const unsigned char af_mail_prefixes[PREFIX_BYTES];

static unsigned int byte_at(const unsigned char *body, unsigned int size, unsigned int at) {
    return at < size ? body[at] : 32u;
}
static int sentence_end(unsigned int c) { return c == '.' || c == '?' || c == '!'; }
static int separator(unsigned int c) {
    return sentence_end(c) || c == ' ' || c == ',' || c == 0x85u || c == 0xCDu;
}
static int upper(unsigned int c) { return c >= 'A' && c <= 'Z'; }
static int alpha(unsigned int c) { return upper(c) || (c >= 'a' && c <= 'z'); }
static unsigned int offset(unsigned int index) {
    return ((unsigned int)af_mail_prefixes[index*2] << 8) | af_mail_prefixes[index*2+1];
}
static int prefix_table_valid(void) {
    unsigned int i, prior = 0;
    if (offset(0) || offset(26) != PREFIX_PAIRS)
        return 0;
    for (i = 1; i <= 26; ++i) {
        unsigned int end = offset(i);
        if (end < prior || end > PREFIX_PAIRS)
            return 0;
        prior = end;
    }
    return 1;
}
static int prefix(const unsigned char *body, unsigned int size, unsigned int pos) {
    unsigned int c = byte_at(body, size, pos), i, end;
    if (upper(c)) c += 'a'-'A';
    if (c < 'a' || c > 'z') return 0;
    i = offset(c-'a');
    end = offset(c-'a'+1);
    for (; i < end; ++i) {
        if (byte_at(body,size,pos+1) == af_mail_prefixes[54+i*2]
            && byte_at(body,size,pos+2) == af_mail_prefixes[55+i*2])
            return 1;
    }
    return 0;
}
static unsigned int trimmed(const unsigned char *body, unsigned int size, unsigned int cap) {
    unsigned int length = cap < size ? cap : size;
    while (length && body[length-1] == ' ') --length;
    return length;
}
static int word_hits(int *words, const unsigned char *body, unsigned int size, int legacy) {
    unsigned int cap = size < 192u ? 192u : size;
    unsigned int end, pos = 0;
    int hits = 0;
    *words = 0;
    if (legacy) {
        /* GAFE01's older helper returns the final non-space index, not
         * its length, and includes index cap-3. Preserve that distinction.
         */
        end = cap-3;
        while (end && byte_at(body,size,end) == ' ') --end;
    } else {
        end = trimmed(body, size, cap-3);
    }
    if (!end) return 0;
    while (pos <= end) {
        ++*words;
        hits += prefix(body, size, pos);
        while (pos < end && !(separator(byte_at(body,size,pos))
                                  && !separator(byte_at(body,size,pos+1)))) ++pos;
        ++pos;
    }
    return hits;
}

int af_mail_word_rate(int *words, const unsigned char *body, unsigned int size) {
    int count, hits;
    if (!words || !body || size > AF_MAIL_GRADE_MAX || !prefix_table_valid())
        return -1;
    hits = word_hits(&count, body, size, 1);
    *words = count;
    return count ? (hits*100)/count : 0;
}

int af_mail_grade(AfMailGrade *output, const unsigned char *body, unsigned int size) {
    AfMailGrade value;
    unsigned int length, cap, i, pos, remain, spaces = 0, nonspaces;
    int words;
    if (!output || !body || size > AF_MAIL_GRADE_MAX || !prefix_table_valid())
        return 0;
    for (i = 0; i < 7; ++i) value.components[i] = 0;
    value.total = 0;
    cap = size < 192u ? 192u : size;
    length = trimmed(body, size, cap);
    /* A: final punctuation, then uppercase within three bytes after .?!.
     * Empty input has no preceding byte; do not reproduce the reference's
     * out-of-bounds body[-1] read.
     */
    if (length && length < cap && sentence_end(body[length-1])) value.components[0] = 20;
    pos = 0;
    remain = length;
    while (remain > 3) {
        while (remain > 3 && !sentence_end(body[pos])) { ++pos; --remain; }
        if (remain > 3) {
            unsigned int left = 3;
            ++pos; --remain;
            while (left && !upper(body[pos])) { --left; ++pos; --remain; }
            value.components[0] += left ? 10 : -10;
        }
    }
    /* B: first-character case is flexible; the next two bytes are exact. */
    value.components[1] = 3*word_hits(&words, body, size, 0);
    /* C: capitalization of the first non-space byte only. */
    for (i = 0; i < length; ++i) {
        if (body[i] != ' ') { value.components[2] = upper(body[i]) ? 20 : -10; break; }
    }
    /* D: three identical consecutive alphabetic bytes, case-sensitive. */
    for (i = 0; i+2 < length; ++i) {
        if (alpha(body[i]) && body[i] == body[i+1] && body[i] == body[i+2]) {
            value.components[3] = -50;
            break;
        }
    }
    /* E uses the spaces/non-spaces ratio, not spaces/total characters. */
    for (i = 0; i < length; ++i) spaces += body[i] == ' ';
    nonspaces = length-spaces;
    value.components[4] = nonspaces && spaces*5 >= nonspaces ? 20 : -20;
    /* F checks a 75-byte run after punctuation, not the first sentence. */
    pos = 0;
    remain = length;
    while (remain > 76) {
        if (sentence_end(body[pos])) {
            unsigned int run = 0;
            ++pos; --remain;
            while (!sentence_end(body[pos])) {
                if (++run >= 75) break;
                ++pos; --remain;
            }
            if (run >= 75) { value.components[5] = -150; break; }
        }
        ++pos; --remain;
    }
    /* G uses complete, fixed 32-byte blocks, not sliding windows. */
    for (pos = 0; pos+32 <= length; pos += 32) {
        for (i = 0; i < 32 && body[pos+i] != ' '; ++i) {}
        if (i == 32) value.components[6] -= 20;
    }
    for (i = 0; i < 7; ++i) value.total += value.components[i];
    value.rank = value.total >= 100 ? 1u : value.total < 50 ? 0u : 2u;
    /* Explicit stores avoid a freestanding memcpy dependency. */
    for (i = 0; i < 7; ++i) output->components[i] = value.components[i];
    output->total = value.total;
    output->rank = value.rank;
    return 1;
}

/* The old native overlay loader calls this fixed two-argument entry. */
int af_mail_word_rate_native(int *words, const unsigned char *body) {
    return af_mail_word_rate(words, body, 96);
}
