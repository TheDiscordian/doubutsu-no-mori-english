/* Temporary apology input only; this does not grant saved fields new tokens. */
#include "edit.h"

static unsigned int code_size(int code) {
    if (code == AF_APOLOGY_SUN || code == AF_APOLOGY_SKULL) return 2;
    if (code < 0 || code > 255 || code == 0x7F || code == 0x80 || code == 0xCD) return 0;
    return 1;
}

static unsigned int token_size(const unsigned char *text, unsigned int left) {
    if (!left) return 0;
    if (text[0] == 0x80) {
        if (left < 2) return 0;
        return code_size(0x8000 | text[1]);
    }
    return code_size(text[0]);
}

int af_apology_valid(const struct af_apology_draft *draft) {
    unsigned int at=0, size, boundary;
    if (!draft || draft->length > AF_APOLOGY_BYTES || draft->cursor > draft->length) return 0;
    boundary = draft->cursor == draft->length;
    while (at < draft->length) {
        if (at == draft->cursor) boundary=1;
        size=token_size(draft->text+at,draft->length-at);
        if (!size) return 0;
        at+=size;
    }
    for (; at < AF_APOLOGY_BYTES; ++at) if (draft->text[at] != ' ') return 0;
    return (int)boundary;
}

static unsigned int previous(const struct af_apology_draft *draft) {
    unsigned int at=0, next;
    while (at < draft->cursor) {
        next=at+token_size(draft->text+at,draft->length-at);
        if (next == draft->cursor) return at;
        at=next;
    }
    return 0;
}

static int insert(struct af_apology_draft *draft, int code) {
    unsigned int size=code_size(code), at;
    if (code == 0xCD) return AF_APOLOGY_UNCHANGED;
    if (!size) return AF_APOLOGY_ARGUMENT;
    if (draft->length+size > AF_APOLOGY_BYTES) return AF_APOLOGY_FULL;
    at=draft->length;
    while (at > draft->cursor) {
        --at;
        draft->text[at+size]=draft->text[at];
    }
    if (size == 2) draft->text[draft->cursor++]=0x80;
    draft->text[draft->cursor++]=(unsigned char)code;
    draft->length=(unsigned char)(draft->length+size);
    return AF_APOLOGY_CHANGED;
}

int af_apology_edit(struct af_apology_draft *draft, int command, int code) {
    unsigned int at, before, removed;
    if (!af_apology_valid(draft)) return AF_APOLOGY_ARGUMENT;
    switch (command) {
    case AF_APOLOGY_LEFT:
        if (!draft->cursor) return AF_APOLOGY_UNCHANGED;
        draft->cursor=(unsigned char)previous(draft);
        return AF_APOLOGY_CHANGED;
    case AF_APOLOGY_RIGHT:
        if (draft->cursor == draft->length) return insert(draft,' ');
        draft->cursor=(unsigned char)(draft->cursor+token_size(draft->text+draft->cursor,
                                                              draft->length-draft->cursor));
        return AF_APOLOGY_CHANGED;
    case AF_APOLOGY_BACKSPACE:
        if (!draft->cursor) return AF_APOLOGY_UNCHANGED;
        before=previous(draft);
        removed=draft->cursor-before;
        for (at=before; at+removed < draft->length; ++at) draft->text[at]=draft->text[at+removed];
        for (; at < draft->length; ++at) draft->text[at]=' ';
        draft->length=(unsigned char)(draft->length-removed);
        draft->cursor=(unsigned char)before;
        return AF_APOLOGY_CHANGED;
    case AF_APOLOGY_EXCHANGE:
        if (!draft->cursor || code == -1) return AF_APOLOGY_UNCHANGED;
        before=previous(draft);
        if (draft->cursor-before != 1) return AF_APOLOGY_UNCHANGED;
        if (code_size(code) != 1) return AF_APOLOGY_ARGUMENT;
        draft->text[before]=(unsigned char)code;
        return AF_APOLOGY_CHANGED;
    case AF_APOLOGY_INSERT:
        return insert(draft,code);
    case AF_APOLOGY_DONE:
        return AF_APOLOGY_FINISHED;
    case AF_APOLOGY_UP:
    case AF_APOLOGY_DOWN:
        return AF_APOLOGY_UNCHANGED;
    default:
        return AF_APOLOGY_ARGUMENT;
    }
}
