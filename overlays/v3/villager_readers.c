/* Transient letter capture reads complete imported names without new save fields. */
#include "../mail_generation/npc_capture.h"

#ifdef __mips__
#define load_name ((int (*)(unsigned char *, unsigned int, unsigned int))0x80464000u)
#else
extern int af_v3_reader_name(unsigned char *, unsigned int, unsigned int);
#define load_name af_v3_reader_name
#endif

static unsigned int number(const unsigned char *p) {
    return ((unsigned int)p[0] << 8) | p[1];
}

static int overlap(const void *a, unsigned int an, const void *b, unsigned int bn) {
    __UINTPTR_TYPE__ x = (__UINTPTR_TYPE__)a, y = (__UINTPTR_TYPE__)b;
    return x <= y ? y-x < an : x-y < bn;
}

static int valid(AfMailField *out, const AfNpcMailSources *sources) {
    return out && sources && sources->ready == 0x41464353u && sources->words && sources->aliases
        && !overlap(out, sizeof(*out), sources, sizeof(*sources))
        && !overlap(out, sizeof(*out), sources->words, AF_NPC_WORD_BYTES)
        && !overlap(out, sizeof(*out), sources->aliases, AF_NPC_ALIAS_BYTES);
}

static int field(AfMailField *out, const unsigned char *text) {
    AfMailField value;
    unsigned int i;
    value.length = 8; value.article = 0;
    for (i = 0; i < 16; ++i) value.text[i] = i < 8 ? text[i] : 0;
    for (i = 0; i < sizeof(value); ++i) ((unsigned char *)out)[i] = ((const unsigned char *)&value)[i];
    return 1;
}

int af_v3_mail_source_name(AfMailField *out, const AfNpcMailSources *sources, unsigned int npc) {
    unsigned int i;
    unsigned char text[8];
    const unsigned char *row;
    if (!valid(out, sources)) return 0;
    if (npc >= 0xE0DAu && npc < 0xE0EEu)
        return load_name(text, 8, npc) ? field(out, text) : 0;
    if (npc < 0xE000u || npc >= 0xE0D8u) return 0;
    for (i = 0; i < 394; ++i) {
        row = sources->aliases + 64 + i*16;
        if (number(row+6) == npc-0xE000u) return field(out, row+8);
    }
    return 0;
}

int af_v3_mail_source_alias(AfMailField *out, const AfNpcMailSources *sources, const unsigned char *key) {
    unsigned int low = 0, high = 394, mid, i, npc, matches = 0;
    const unsigned char *row;
    unsigned char text[8], selected[8];
    if (!valid(out, sources) || !key) return 0;
    /* Preserve the native sorted alias search and its precedence. */
    while (low < high) {
        mid = low + (high-low)/2;
        row = sources->aliases + 64 + mid*16;
        for (i = 0; i < 6 && row[i] == key[i]; ++i) {}
        if (i == 6) return field(out, row+8);
        if (row[i] < key[i]) low = mid+1;
        else high = mid;
    }
    /* Only installed names can resolve a new six-byte compatibility spelling.
     * Ambiguous imported spellings are rejected, never selected by table order. */
    for (npc = 0xE0DAu; npc < 0xE0EEu; ++npc) {
        if (!load_name(text, 8, npc)) continue;
        for (i = 0; i < 6 && text[i] == key[i]; ++i) {}
        if (i != 6) continue;
        ++matches;
        for (i = 0; i < 8; ++i) selected[i] = text[i];
    }
    return matches == 1 ? field(out, selected) : 0;
}
