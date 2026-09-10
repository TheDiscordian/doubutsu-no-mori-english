#include "accent_mail.h"
#include "../../runtime/notice/treasure.h"
#include "../../runtime/crc32.h"
#define af_notice_treasure_valid af_accent_treasure_valid
#define af_notice_treasure_pack af_accent_treasure_pack
#define af_notice_treasure_decode_parts af_accent_treasure_decode_parts

static int overlap(const void *a, unsigned int as, const void *b, unsigned int bs) {
    __UINTPTR_TYPE__ av = (__UINTPTR_TYPE__)a, bv = (__UINTPTR_TYPE__)b;
    return av <= bv ? bv-av < as : av-bv < bs;
}

int af_notice_treasure_valid(const AfMailRecord *record) {
    unsigned int i, j, id, length;
    if (!record || ((__UINTPTR_TYPE__)record & 3u)
            || (record->catalog != AF_MAIL_GLYPH_CATALOG_ID && record->catalog != AF_ACCENT_CATALOG_ID) || record->kind
            || record->flags > 1u) return 0;
    id = record->templates[0];
    if (id < 0x1F0u || id > 0x201u || record->field_mask != af_notice_treasure_mask(id)) return 0;
    for (i = 1; i < 5u; ++i) if (record->templates[i]) return 0;
    for (i = 1; i <= 5u; ++i) {
        const AfMailField *field = &record->fields[i];
        if (!(record->field_mask & (1u << i))) continue;
        if (!field->length || field->length > 16u || field->article > 4u
                || (i != 2u && field->article)) return 0;
        length = field->length;
        while (length && field->text[length-1u] == ' ') --length;
        if (!length) return 0;
        if ((i == 3u || i == 4u) && (field->length != 1u
                || field->text[0] < '1' || field->text[0] > (i == 3u ? '6' : '5'))) return 0;
        if (i == 5u && field->length > 6u) return 0;
        for (j = 0; j < field->length; ++j)
            if (field->text[j] == 0x7Fu || field->text[j] == 0xCDu
                    || (field->text[j] == 0x80u && (record->catalog != AF_ACCENT_CATALOG_ID
                        || i != 2u || !af_accent_item_literal(field->text,field->length))))
                return 0;
    }
    if (record->catalog == AF_ACCENT_CATALOG_ID
            && (!(record->field_mask & 4u) || !af_accent_item_literal(record->fields[2].text,record->fields[2].length)))
        return 0;
    return 1;
}

int af_notice_treasure_pack(unsigned char *output, unsigned int capacity,
                             const AfMailRecord *record) {
    AfMailRecord copy;
    unsigned int i;
    if (!record || ((__UINTPTR_TYPE__)record & 3u)) return 0;
    for (i=0;i<sizeof(copy);++i) ((unsigned char *)&copy)[i]=((const unsigned char *)record)[i];
    if (copy.catalog == AF_MAIL_GLYPH_CATALOG_ID && (copy.field_mask & 4u)
            && af_accent_item_literal(copy.fields[2].text,copy.fields[2].length))
        copy.catalog=AF_ACCENT_CATALOG_ID;
    return af_notice_treasure_valid(&copy) && af_notice_record_pack(output, capacity, &copy);
}

int af_notice_treasure_decode_parts(AfMailWorkspace *mail, AfMailText *letter,
                                     unsigned char *wire, const unsigned char *input,
                                     unsigned int size) {
    static const unsigned char lengths[18] = {
        120, 140, 108, 137, 95, 119, 139, 134, 132, 121, 104, 130, 110, 142, 129, 138, 146, 112
    };
    static const unsigned int checksums[18] = {
        0x7334755Du, 0x63A193EBu, 0x2B36B149u, 0x663BA9D0u, 0x687B6E73u, 0xF8D339BAu,
        0x3B018450u, 0x06428321u, 0x6FBE9458u, 0xFB3180E2u, 0xBEDF40FDu, 0xF01CD8B0u,
        0x4F5BE5CFu, 0xAB4FCEF5u, 0xAEAE632Bu, 0xB472B085u, 0x54F738EDu, 0x78910646u
    };
    static const unsigned char before[] = "Free \x7F\x74\x7F\x26\xCD" "for whoever finds it! Woo!\xCD";
    static const unsigned char heading[] = "\x7F\x29's Treasure Hunt!\xCD" "Come and join the fun! Woo!\xCD";
    unsigned int id, i, length, catalog;
    AfMailRecord *record;
    AfMailPart *body;
    unsigned char *source;
    if (!mail || !letter || !wire || !input || size != AF_NOTICE_RECORD_BYTES
            || ((__UINTPTR_TYPE__)mail & 15u) || ((__UINTPTR_TYPE__)letter & 3u)
            || overlap(mail, sizeof(*mail), letter, sizeof(*letter))
            || overlap(mail, sizeof(*mail), wire, AF_MAIL_RECORD_BYTES)
            || overlap(letter, sizeof(*letter), wire, AF_MAIL_RECORD_BYTES)
            || overlap(mail, sizeof(*mail), input, size)
            || overlap(letter, sizeof(*letter), input, size)
            || overlap(wire, AF_MAIL_RECORD_BYTES, input, size)) return 0;
    catalog=((unsigned int)input[7]<<8)|input[8];
    if ((catalog!=AF_MAIL_GLYPH_CATALOG_ID && catalog!=AF_ACCENT_CATALOG_ID)
            || !af_notice_record_expand(wire, AF_MAIL_RECORD_BYTES, input, size, catalog)
            || !af_mail_record_unpack(&mail->record, wire, AF_MAIL_RECORD_BYTES, catalog)
            || !af_notice_treasure_valid(&mail->record)) return 0;
    record = &mail->record;
    id = record->templates[0];
    if (id == 0x1F4u) {
        /* Temporary town-as-item data permits the immutable donor source to
         * load and validate. No resulting text is published. The saved mask
         * stays 1/3/5, and the final template never reads an item field.
         */
        record->field_mask |= 1u << 2;
        for (i = 0; i < sizeof(AfMailField); ++i)
            ((unsigned char *)&record->fields[2])[i] = ((const unsigned char *)&record->fields[5])[i];
        if (!af_mail_record_pack(wire, AF_MAIL_RECORD_BYTES, record)) return 0;
    }
    if (!af_mail_restore(letter, wire, AF_MAIL_RECORD_BYTES, mail)) return 0;
    body = &mail->templates.parts[1];
    if (body->length != lengths[id-0x1F0u] || af_crc32(body->text, body->length) != checksums[id-0x1F0u]
            || mail->templates.parts[0].length != 1u
            || mail->templates.parts[0].text[0] != 0xCDu
            || mail->templates.parts[2].length) return 0;
    if (id == 0x1F4u) {
        for (i = 0; i < sizeof(before)-1u; ++i) if (body->text[i] != before[i]) return 0;
        /* The verified source buffer has room beyond this 95-byte body. Move
         * its unmodified remaining four lines before installing the heading.
         */
        source = (unsigned char *)body->text;
        if (source < mail->source || source > mail->source+AF_MAIL_SOURCE_BYTES
                || (unsigned int)(mail->source+AF_MAIL_SOURCE_BYTES-source)
                   < body->length+sizeof(heading)-sizeof(before)) return 0;
        for (i = body->length; i > sizeof(before)-1u; --i)
            source[i-1u+sizeof(heading)-sizeof(before)] = source[i-1u];
        for (i = 0; i < sizeof(heading)-1u; ++i) source[i] = heading[i];
        body->length += sizeof(heading)-sizeof(before);
        record->field_mask &= ~(1u << 2);
        for (i = 0; i < sizeof(AfMailField); ++i) ((unsigned char *)&record->fields[2])[i] = 0;
        if (!af_notice_treasure_valid(record)
                || !af_mail_format(letter, record, &mail->templates)) return 0;
    }
    length = letter->lengths[1];
    return !letter->lengths[0] && !letter->lengths[2]
        && letter->offsets[1] <= AF_MAIL_TEXT_BYTES
        && length <= AF_MAIL_TEXT_BYTES-letter->offsets[1];
}
