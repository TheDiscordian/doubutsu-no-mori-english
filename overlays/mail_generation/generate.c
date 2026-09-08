#include "generate.h"

#ifdef __mips__
typedef char capture_size_check[sizeof(AfMailCapture) == 368 ? 1 : -1];
typedef char selection_size_check[sizeof(AfMailSelection) == 14 ? 1 : -1];
typedef char work_size_check[sizeof(AfMailGenerateWork) == 4720 ? 1 : -1];
typedef char text_offset_check[__builtin_offsetof(AfMailGenerateWork,text) == 3552 ? 1 : -1];
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

static int overlap(const void *a, unsigned int as, const void *b, unsigned int bs) {
    __UINTPTR_TYPE__ av = (__UINTPTR_TYPE__)a, bv = (__UINTPTR_TYPE__)b;
    return av <= bv ? bv-av < as : av-bv < bs;
}

void af_mail_capture_reset(AfMailCapture *capture) {
    unsigned int i;
    if (capture)
        for (i = 0; i < sizeof(*capture); ++i)
            ((unsigned char *)capture)[i] = 0;
}

int af_mail_capture_set(AfMailCapture *capture, unsigned int slot,
                        const unsigned char *text, unsigned int length, unsigned int article) {
    AfMailField value;
    unsigned int i;
    if (!capture || slot >= AF_MAIL_FIELD_COUNT)
        return 0;
    if ((!text && length) || length > AF_MAIL_FIELD_BYTES || article > 4)
        goto invalid;
    for (i = 0; i < length; ++i)
        if (text[i] == 0x7Fu || text[i] == 0x80u)
            goto invalid;
    value.length = (unsigned char)length;
    value.article = (unsigned char)article;
    for (i = 0; i < AF_MAIL_FIELD_BYTES; ++i)
        value.text[i] = i < length ? text[i] : 0;
    for (i = 0; i < sizeof(value); ++i)
        ((unsigned char *)&capture->fields[slot])[i] = ((unsigned char *)&value)[i];
    capture->valid |= 1u << slot;
    return 1;
invalid:
    capture->valid &= ~(1u << slot);
    return 0;
}

int af_mail_generate(unsigned char *mail, unsigned int mail_size, AfMailCapture *capture,
                      const AfMailSelection *selection, AfMailGenerateWork *work) {
    unsigned int header[32] __attribute__((aligned(16)));
    unsigned int row[4] __attribute__((aligned(16)));
    unsigned int part, count, bank, id, table, entries, mask = 0, i, j, vrom;
    AfMailRecord *record;
    if (!mail || mail_size != 164u || !capture || !selection || !work
            || ((__UINTPTR_TYPE__)capture & 3u) || ((__UINTPTR_TYPE__)selection & 1u)
            || ((__UINTPTR_TYPE__)work & 15u)
            || overlap(work,sizeof(*work),mail,mail_size)
            || overlap(work,sizeof(*work),capture,sizeof(*capture))
            || overlap(work,sizeof(*work),selection,sizeof(*selection))
            || overlap(mail,mail_size,capture,sizeof(*capture))
            || overlap(mail,mail_size,selection,sizeof(*selection))
            || overlap(capture,sizeof(*capture),selection,sizeof(*selection))
            || capture->capital > 1u || capture->valid >> AF_MAIL_FIELD_COUNT
            || !af_mail_catalog_vrom(selection->catalog) || selection->kind > 1u
            || selection->reserved || !installed())
        return 0;
    if (!selection->kind)
        for (i = 1; i < 5; ++i)
            if (selection->templates[i])
                return 0;
    vrom = af_mail_catalog_vrom(selection->catalog);
    if (!dma(header,vrom,sizeof(header))
            || !af_mail_catalog_header_valid(header,selection->catalog))
        return 0;
    count = selection->kind ? 5u : 3u;
    for (part = 0; part < count; ++part) {
        bank = selection->kind ? part+3u : part;
        id = selection->templates[selection->kind ? part : 0u];
        entries = bank < 3u ? 982u : 384u;
        table = 256u+(bank < 3u ? bank*982u : 2946u+(bank-3u)*384u)*16u;
        if (id >= entries || !dma(row,vrom+table+id*16u,sizeof(row))
                || (row[1] & 0xFFFFu) || row[2] >> AF_MAIL_FIELD_COUNT)
            return 0;
        mask |= row[2];
    }
    if (mask & ~capture->valid)
        return 0;
    record = &work->catalog.record;
    for (i = 0; i < sizeof(*record); ++i)
        ((unsigned char *)record)[i] = 0;
    record->catalog = selection->catalog;
    record->kind = selection->kind;
    record->flags = (unsigned char)capture->capital;
    record->field_mask = mask;
    for (i = 0; i < 5; ++i)
        record->templates[i] = selection->templates[i];
    for (i = 0; i < AF_MAIL_FIELD_COUNT; ++i)
        if (mask & (1u << i))
            for (j = 0; j < sizeof(AfMailField); ++j)
                ((unsigned char *)&record->fields[i])[j] = ((unsigned char *)&capture->fields[i])[j];
    /* Directory, payload CRC, exact field masks, glyph/control domain, padding,
     * full formatting, and output bounds are validated by the resident reader.
     * The row masks above are hints for pruning capture state, never approval.
     */
    if (!af_mail_record_pack(work->wire,AF_MAIL_RECORD_BYTES,record)
            || !af_mail_restore(&work->text,work->wire,AF_MAIL_RECORD_BYTES,&work->catalog))
        return 0;
    for (i = 0; i < AF_MAIL_RECORD_BYTES; ++i)
        mail[42u+i] = work->wire[i];
    mail[39] = 0x80u;
    capture->capital = work->text.final_capital;
    return 1;
}
