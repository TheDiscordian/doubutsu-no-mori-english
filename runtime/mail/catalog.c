#include "catalog.h"

#ifdef __mips__
static unsigned int installed(void) {
    return *(volatile unsigned int *)0x80194924u == AF_MAIL_CATALOG_VROM;
}
static int dma(void *destination, unsigned int source, unsigned int size) {
    return ((int (*)(void *, unsigned int, unsigned int))0x80026B44u)(destination, source, size) == 0;
}
#else
extern unsigned int af_mail_catalog_test_installed(void);
extern int af_mail_catalog_test_dma(void *, unsigned int, unsigned int);
#define installed af_mail_catalog_test_installed
#define dma af_mail_catalog_test_dma
#endif

static unsigned int crc32(const unsigned char *data, unsigned int size) {
    unsigned int crc = 0xFFFFFFFFu, i, bit;
    for (i = 0; i < size; ++i) {
        crc ^= data[i];
        for (bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ ((0u - (crc & 1u)) & 0xEDB88320u);
    }
    return crc ^ 0xFFFFFFFFu;
}

int af_mail_catalog_header_valid(const unsigned int *header, unsigned int catalog) {
    static const unsigned int fingerprint[8] = {
        0xa042bd72u, 0xf6158472u, 0x722717ddu, 0x3f19e761u, 0xea693ce6u, 0x32ae51acu, 0xc9aca26cu, 0x4d99c385u
    };
    unsigned int i;
    if (!header || catalog != AF_MAIL_CATALOG_ID || header[0] != 0x41464D4Cu
            || header[1] != 1u || header[2] != catalog || header[3] != 1u
            || header[4] != AF_MAIL_CATALOG_BYTES || header[5] != 8u
            || header[6] != 128u || header[7] != 16u)
        return 0;
    for (i = 0; i < 8; ++i)
        if (header[8+i] != fingerprint[i])
            return 0;
    for (i = 16; i < 32; ++i)
        if (header[i])
            return 0;
    return 1;
}

static int fields(const unsigned char *data, unsigned int size, unsigned int *mask) {
    unsigned int pos = 0, used = 0, code;
    while (pos < size) {
        code = data[pos++];
        if (code == 0x80u)
            return 0;
        if (code != 0x7Fu)
            continue;
        if (pos == size)
            return 0;
        code = data[pos++];
        if (code >= 0x24u && code <= 0x2Du)
            used |= 1u << (code-0x24u);
        else if (code >= 0x36u && code <= 0x3Fu)
            used |= 1u << (code-0x36u+10u);
        else if (code != 0x74u && code != 0x75u)
            return 0;
    }
    *mask = used;
    return 1;
}

static int overlap(const void *a, unsigned int as, const void *b, unsigned int bs) {
    __UINTPTR_TYPE__ av = (__UINTPTR_TYPE__)a, bv = (__UINTPTR_TYPE__)b;
    return av <= bv ? bv-av < as : av-bv < bs;
}

int af_mail_restore(AfMailText *output, const unsigned char *wire, unsigned int size,
                    AfMailWorkspace *work) {
    unsigned int header[32] __attribute__((aligned(16)));
    unsigned int directory[4] __attribute__((aligned(16)));
    unsigned int row[4] __attribute__((aligned(16)));
    unsigned int part, count, bank, id, offset, length, padded, used = 0, body = 0, mask;
    unsigned int table, entries, i, catalog;
    if (!output || !wire || !work || size != AF_MAIL_RECORD_BYTES || !installed()
            || ((__UINTPTR_TYPE__)work & 15u)
            || overlap(work, sizeof(*work), wire, size)
            || overlap(work, sizeof(*work), output, sizeof(*output))
            || overlap(output, sizeof(*output), wire, size))
        return 0;
    catalog = ((unsigned int)wire[3] << 8) | wire[4];
    if (catalog != AF_MAIL_CATALOG_ID
            || !af_mail_record_unpack(&work->record, wire, size, catalog)
            || !dma(header, AF_MAIL_CATALOG_VROM, sizeof(header))
            || !af_mail_catalog_header_valid(header, catalog))
        return 0;
    work->templates.catalog = catalog;
    work->templates.kind = work->record.kind;
    count = work->record.kind ? 5u : 3u;
    for (part = 0; part < count; ++part) {
        bank = work->record.kind ? part+3u : part;
        id = work->record.templates[work->record.kind ? part : 0u];
        entries = bank < 3u ? 982u : 384u;
        table = 256u+(bank < 3u ? bank*982u : 2946u+(bank-3u)*384u)*16u;
        if (id >= entries || !dma(directory, AF_MAIL_CATALOG_VROM+128u+bank*16u, sizeof(directory))
                || directory[0] != bank || directory[1] != entries || directory[2] != table || directory[3]
                || !dma(row, AF_MAIL_CATALOG_VROM+table+id*16u, sizeof(row)))
            return 0;
        offset = row[0];
        length = row[1] >> 16;
        padded = (length+15u) & ~15u;
        if ((row[1] & 0xFFFFu) || length > AF_MAIL_TEXT_BYTES || (offset & 15u)
                || offset < 78112u || offset > AF_MAIL_CATALOG_BYTES
                || padded > AF_MAIL_CATALOG_BYTES-offset || padded > AF_MAIL_SOURCE_BYTES-used)
            return 0;
        if (padded && !dma(work->source+used, AF_MAIL_CATALOG_VROM+offset, padded))
            return 0;
        for (i = length; i < padded; ++i)
            if (work->source[used+i])
                return 0;
        if (!fields(work->source+used, length, &mask) || mask != row[2]
                || (mask & ~work->record.field_mask) || crc32(work->source+used, length) != row[3])
            return 0;
        work->templates.parts[part].text = work->source+used;
        work->templates.parts[part].length = length;
        work->templates.parts[part].id = (unsigned short)id;
        work->templates.parts[part].reserved = 0;
        used += padded;
        if ((!work->record.kind && part == 1u) || (work->record.kind && part >= 1u && part <= 3u))
            body += length;
    }
    if (body > AF_MAIL_TEXT_BYTES)
        return 0;
    return af_mail_format(output, &work->record, &work->templates);
}
