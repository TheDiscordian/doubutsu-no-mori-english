#include "accent_mail.h"

typedef struct {
    AfMailText *out;
    const AfMailRecord *record;
    unsigned int used, capital, forced;
} Formatter;

typedef struct {
    const AfMailPart *parts;
    unsigned int count, part, pos;
} Cursor;

static int next(Cursor *cursor) {
    while (cursor->part < cursor->count) {
        const AfMailPart *part = &cursor->parts[cursor->part];
        if (cursor->pos < part->length)
            return part->text[cursor->pos++];
        cursor->part++;
        cursor->pos = 0;
    }
    return -1;
}

static unsigned char upper(unsigned int byte) {
    return (unsigned char)((byte >= 'a' && byte <= 'z') ? byte - ('a' - 'A') : byte);
}

static int append(Formatter *formatter, unsigned int byte) {
    if (formatter->used == AF_MAIL_TEXT_BYTES)
        return 0;
    formatter->out->text[formatter->used++] = (unsigned char)byte;
    return 1;
}

static int expand(Formatter *f, const AfMailPart *parts, unsigned int count, unsigned int section) {
    static const unsigned char articles[5][6] = {"", "a ", "an ", "the ", "some "};
    static const unsigned char article_lengths[5] = {0, 2, 3, 4, 5};
    Cursor cursor = {parts, count, 0, 0};
    unsigned int begin = f->used, markers = 0, pending = 0, input = 0, i;
    int byte;
    for (i = 0; i < count; ++i) {
        if (parts[i].length > AF_MAIL_TEXT_BYTES-input)
            return 0;
        input += parts[i].length;
    }
    f->out->offsets[section] = (unsigned short)begin;
    while ((byte = next(&cursor)) >= 0) {
        int opcode;
        unsigned int index, length, article, j;
        const AfMailField *field;
        if (section == 0 && byte == 0xCD) {
            f->out->header_split = (unsigned short)(f->used - begin);
            markers++;
            continue;
        }
        if (byte == 0x80) {
            if ((f->record->catalog != AF_MAIL_GLYPH_CATALOG_ID && f->record->catalog != AF_ACCENT_CATALOG_ID)
                    || cursor.pos == cursor.parts[cursor.part].length
                    || f->used > AF_MAIL_TEXT_BYTES-2u)
                return 0;
            opcode = next(&cursor);
            if (!af_accent_glyph_width((unsigned int)opcode,f->record->catalog))
                return 0;
            f->out->text[f->used++] = 0x80;
            f->out->text[f->used++] = (unsigned char)(pending ?
                af_accent_glyph_upper((unsigned int)opcode) : (unsigned int)opcode);
            pending = 0;
            continue;
        }
        if (byte != 0x7F) {
            if (!append(f, pending ? upper((unsigned int)byte) : (unsigned int)byte))
                return 0;
            pending = 0;
            continue;
        }
        pending = 0;
        opcode = next(&cursor);
        if (opcode == 0x74) {
            f->forced = 1;
            continue;
        }
        if (opcode == 0x75) {
            f->capital = 1;
            continue;
        }
        if (opcode >= 0x24 && opcode <= 0x2D)
            index = (unsigned int)opcode - 0x24;
        else if (opcode >= 0x36 && opcode <= 0x3F)
            index = (unsigned int)opcode - 0x36 + 10;
        else
            return 0;
        if (!(f->record->field_mask & (1u << index)))
            return 0;
        field = &f->record->fields[index];
        length = field->length;
        while (length && field->text[length-1] == ' ')
            --length;
        article = f->forced ? 0 : field->article;
        f->forced = 0;
        for (j = 0; j < article_lengths[article]; ++j) {
            unsigned char c = articles[article][j];
            if (!append(f, f->capital && !j ? upper(c) : c))
                return 0;
        }
        for (j = 0; j < length; ++j) {
            unsigned char c = field->text[j];
            if (c==0x80u) {
                unsigned int code=field->text[j+1u];
                if (!append(f,0x80u) || !append(f,f->capital && !j && !article ? af_accent_glyph_upper(code) : code))
                    return 0;
                ++j;
            } else if (!append(f, f->capital && !j && !article ? upper(c) : c))
                return 0;
        }
        pending = f->capital && !length && !article;
    }
    if (section == 0 && markers != 1) {
        for (i = 0; i < markers; ++i)
            if (!append(f, ' '))
                return 0;
        f->out->header_split = (unsigned short)(f->used-begin);
    }
    f->out->lengths[section] = (unsigned short)(f->used-begin);
    return 1;
}

int af_accent_mail_format(AfMailText *output, const AfMailRecord *record, const AfMailTemplates *templates) {
    AfMailText value;
    unsigned char encoded[AF_MAIL_RECORD_BYTES];
    unsigned char *bytes = (unsigned char *)&value;
    Formatter f;
    unsigned int i, j, count;
    if (!output || !record || !templates || !af_mail_record_pack(encoded, sizeof(encoded), record)
        || templates->catalog != record->catalog || templates->kind != record->kind)
        return 0;
    count = record->kind ? 5 : 3;
    for (i = 0; i < count; ++i) {
        const AfMailPart *part = &templates->parts[i];
        if (part->reserved || part->length > AF_MAIL_TEXT_BYTES || (!part->text && part->length)
            || part->id != record->templates[record->kind ? i : 0])
            return 0;
    }
    for (i = 0; i < AF_MAIL_FIELD_COUNT; ++i)
        if (record->field_mask & (1u << i))
            for (j = 0; j < record->fields[i].length; ++j) {
                unsigned int code=record->fields[i].text[j];
                if (code==0x7Fu) return 0;
                if (code==0x80u) {
                    if (record->catalog!=AF_ACCENT_CATALOG_ID || j+1u==record->fields[i].length
                            || !af_accent_glyph_width(record->fields[i].text[j+1u],record->catalog)) return 0;
                    ++j;
                }
            }
    for (i = 0; i < sizeof(value); ++i)
        bytes[i] = 0;
    f.out = &value;
    f.record = record;
    f.used = f.forced = 0;
    f.capital = record->flags;
    if (!expand(&f, templates->parts, 1, 0))
        return 0;
    if (record->kind) {
        if (!expand(&f, templates->parts+1, 3, 1) || !expand(&f, templates->parts+4, 1, 2))
            return 0;
    } else {
        if (!expand(&f, templates->parts+2, 1, 2) || !expand(&f, templates->parts+1, 1, 1))
            return 0;
    }
    value.final_capital = (unsigned char)f.capital;
    for (i = 0; i < sizeof(value); ++i)
        ((unsigned char *)output)[i] = bytes[i];
    return 1;
}
