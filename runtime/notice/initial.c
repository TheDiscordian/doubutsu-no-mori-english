#include "initial.h"
#include "../crc32.h"

static int overlap(const void *a, unsigned int as, const void *b, unsigned int bs) {
    __UINTPTR_TYPE__ av = (__UINTPTR_TYPE__)a, bv = (__UINTPTR_TYPE__)b;
    return av <= bv ? bv-av < as : av-bv < bs;
}

int af_notice_initial_pack(unsigned char *output, unsigned int capacity,
                            unsigned int template_id, unsigned int capital) {
    AfMailRecord record;
    unsigned int i;
    if (template_id < 0x1Eu || template_id > 0x21u || capital > 1u)
        return 0;
    for (i = 0; i < sizeof(record); ++i)
        ((unsigned char *)&record)[i] = 0;
    record.catalog = AF_MAIL_GLYPH_CATALOG_ID;
    record.templates[0] = (unsigned short)template_id;
    record.flags = (unsigned char)capital;
    return af_notice_record_pack(output, capacity, &record);
}

int af_notice_initial_restore(AfNoticeText *output, const unsigned char *input,
                               unsigned int size, AfNoticeWorkspace *work) {
    static const unsigned int lengths[4] = {141u, 166u, 137u, 154u};
    static const unsigned int checksums[4] = {
        0x11065B6Bu, 0x8987D0B9u, 0x2F99A590u, 0xA7883698u
    };
    static const unsigned char original[] = "C Stick";
    static const unsigned char replacement[] = "C Buttons";
    unsigned int id, length, i, extra;
    const unsigned char *body;
    if (!output || !input || !work || size != AF_NOTICE_RECORD_BYTES
            || ((__UINTPTR_TYPE__)output & 3u) || ((__UINTPTR_TYPE__)work & 15u)
            || overlap(work, sizeof(*work), input, size)
            || overlap(work, sizeof(*work), output, sizeof(*output))
            || !af_notice_record_expand(work->wire, sizeof(work->wire), input,
                                         size, AF_MAIL_GLYPH_CATALOG_ID))
        return 0;
    id = ((unsigned int)work->wire[8] << 8) | work->wire[9];
    /* No ignored extra fields: initial bodies are fixed, independent of names. */
    if (id < 0x1Eu || id > 0x21u || (work->wire[5] & 15u)
            || work->wire[6] || work->wire[7]
            || !af_mail_restore(&work->letter, work->wire, sizeof(work->wire), &work->mail))
        return 0;
    length = work->letter.lengths[1];
    if (work->letter.lengths[0] || work->letter.lengths[2]
            || work->letter.offsets[1] > AF_MAIL_TEXT_BYTES
            || length > AF_MAIL_TEXT_BYTES-work->letter.offsets[1]
            || length != lengths[id-0x1Eu])
        return 0;
    body = work->letter.text+work->letter.offsets[1];
    if (af_crc32(body, length) != checksums[id-0x1Eu])
        return 0;
    extra = id == 0x21u ? 2u : 0u;
    if (extra)
        for (i = 0; i < sizeof(original)-1u; ++i)
            if (body[81u+i] != original[i])
                return 0;
    /* All validation and cartridge reads precede publication. */
    for (i = 0; i < AF_MAIL_TEXT_BYTES; ++i) {
        if (i >= length+extra)
            output->text[i] = 0;
        else if (extra && i >= 81u && i < 90u)
            output->text[i] = replacement[i-81u];
        else
            output->text[i] = body[i-(extra && i >= 90u ? extra : 0u)];
    }
    output->length = length+extra;
    return 1;
}
