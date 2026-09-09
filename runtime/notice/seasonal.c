#include "seasonal.h"
#include "../crc32.h"
#include "seasonal_data.h"

static int overlap(const void *a, unsigned int as, const void *b, unsigned int bs) {
    __UINTPTR_TYPE__ av = (__UINTPTR_TYPE__)a, bv = (__UINTPTR_TYPE__)b;
    return av <= bv ? bv-av < as : av-bv < bs;
}

unsigned int af_notice_seasonal_mask(unsigned int number) {
    return number >= 0x1A4u && number <= 0x1CCu ? af_notice_seasonal_entries[number-0x1A4u].mask : ~0u;
}

int af_notice_seasonal_valid(const AfMailRecord *record) {
    unsigned int mask, index, i, limit, used;
    if (!record || record->catalog != AF_MAIL_GLYPH_CATALOG_ID || record->kind || record->flags > 1u)
        return 0;
    mask = af_notice_seasonal_mask(record->templates[0]);
    if (mask == ~0u || (mask & ~31u) || mask != record->field_mask) return 0;
    for (index = 0; index < 5u; ++index) {
        const AfMailField *field = &record->fields[index];
        if (!(mask & (1u << index))) continue;
        limit = !index ? 6u : index == 1u ? 16u : 14u;
        if (!field->length || field->length > limit || field->article) return 0;
        used = 0;
        for (i = 0; i < field->length; ++i) {
            unsigned int c = field->text[i];
            if (c == 0x7Fu || c == 0x80u || c == 0xCDu) return 0;
            if (c != 32u) used = 1;
        }
        if (!used) return 0;
    }
    return 1;
}

int af_notice_seasonal_pack(unsigned char *output, unsigned int capacity, const AfMailRecord *record) {
    return af_notice_seasonal_valid(record) && af_notice_record_pack(output, capacity, record);
}

int af_notice_seasonal_shop(unsigned char *output, unsigned int capacity, unsigned int level) {
    unsigned int i;
    if (!output || capacity < 16u || level >= 4u
            || af_crc32(af_notice_seasonal_shops, sizeof(af_notice_seasonal_shops)) != AF_NOTICE_SEASONAL_SHOPS_CRC) return 0;
    for (i = 0; i < 16u; ++i) output[i] = af_notice_seasonal_shops[level*16u+i];
    return 1;
}

int af_notice_seasonal_decode_parts(AfMailWorkspace *mail, AfMailText *letter,
                                     unsigned char *wire, const unsigned char *input, unsigned int size) {
    static const unsigned char newline = 0xCDu;
    const AfNoticeSeasonalEntry *entry;
    const unsigned char *body;
    unsigned int i, number;
    if (!mail || !letter || !wire || !input || size != AF_NOTICE_RECORD_BYTES
            || ((__UINTPTR_TYPE__)mail & 15u) || ((__UINTPTR_TYPE__)letter & 3u)
            || overlap(mail, sizeof(*mail), letter, sizeof(*letter))
            || overlap(mail, sizeof(*mail), wire, AF_MAIL_RECORD_BYTES)
            || overlap(letter, sizeof(*letter), wire, AF_MAIL_RECORD_BYTES)
            || overlap(mail, sizeof(*mail), input, size)
            || overlap(letter, sizeof(*letter), input, size)
            || overlap(wire, AF_MAIL_RECORD_BYTES, input, size)
            || !af_notice_record_expand(wire, AF_MAIL_RECORD_BYTES, input, size, AF_MAIL_GLYPH_CATALOG_ID)
            || !af_mail_record_unpack(&mail->record, wire, AF_MAIL_RECORD_BYTES, AF_MAIL_GLYPH_CATALOG_ID)
            || !af_notice_seasonal_valid(&mail->record)) return 0;
    number = mail->record.templates[0];
    entry = &af_notice_seasonal_entries[number-0x1A4u];
    if (!entry->length || entry->length > AF_MAIL_TEXT_BYTES || entry->offset > AF_NOTICE_SEASONAL_DATA_BYTES
            || entry->length > AF_NOTICE_SEASONAL_DATA_BYTES-entry->offset) return 0;
    body = af_notice_seasonal_data+entry->offset;
    if (af_crc32(body, entry->length) != entry->crc) return 0;
    for (i = 0; i < sizeof(mail->templates); ++i) ((unsigned char *)&mail->templates)[i] = 0;
    mail->templates.catalog = AF_MAIL_GLYPH_CATALOG_ID;
    for (i = 0; i < 3u; ++i) {
        mail->templates.parts[i].id = (unsigned short)number;
        mail->templates.parts[i].text = &newline;
    }
    mail->templates.parts[0].length = 1u;
    mail->templates.parts[1].text = body;
    mail->templates.parts[1].length = entry->length;
    return af_mail_format(letter, &mail->record, &mail->templates)
        && !letter->lengths[0] && !letter->lengths[2]
        && letter->offsets[1] <= AF_MAIL_TEXT_BYTES
        && letter->lengths[1] <= AF_MAIL_TEXT_BYTES-letter->offsets[1];
}

int af_notice_seasonal_decode(AfNoticeWorkspace *work, const unsigned char *input, unsigned int size) {
    if (!work || ((__UINTPTR_TYPE__)work & 15u) || overlap(work, sizeof(*work), input, size)) return 0;
    return af_notice_seasonal_decode_parts(&work->mail, &work->letter, work->wire, input, size);
}

int af_notice_seasonal_restore(AfNoticeText *output, const unsigned char *input,
                                unsigned int size, AfNoticeWorkspace *work) {
    unsigned int i, length;
    const unsigned char *body;
    if (!output || !work || ((__UINTPTR_TYPE__)output & 3u)
            || overlap(work, sizeof(*work), output, sizeof(*output))
            || !af_notice_seasonal_decode(work, input, size)) return 0;
    length = work->letter.lengths[1];
    body = work->letter.text+work->letter.offsets[1];
    for (i = 0; i < AF_MAIL_TEXT_BYTES; ++i) output->text[i] = i < length ? body[i] : 0;
    output->length = length;
    return 1;
}
