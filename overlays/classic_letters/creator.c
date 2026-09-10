#include "classic.h"

#ifdef __mips__
#define free_strings ((const unsigned char *)0x80140680u)
#else
extern unsigned char af_classic_test_fields[200];
#define free_strings af_classic_test_fields
#endif

int af_classic_mail_create(AfNpcMailCreateWork *work, unsigned char *destination,
                            AfNpcMailSession **active, unsigned int *capital) {
    AfNpcMailSession *session;
    const unsigned char *request;
    unsigned int number, mask, i, j;
    if (!af_mail_create_guard(work, destination, active, capital, free_strings, 200u)) return 0;
    session = &work->captured.session;
    request = session->animal;
    if (!request || session->remail || request[11] != 240u)
        return af_notice_seasonal_create(work, destination, active, capital);
    if (!session->player || (((__UINTPTR_TYPE__)session->player | (__UINTPTR_TYPE__)request) & 1u)
            || session->condition || session->foreign || request[0] != 'A' || request[1] != 'F'
            || request[2] != 'C' || request[3] != 'L' || request[6] || request[7]
            || request[8] || request[9] || request[10]) return 0;
    number = ((unsigned int)request[4] << 8) | request[5];
    mask = af_classic_mask(number);
    if (mask == ~0u) return 0;
    for (i = sizeof(*session); i < sizeof(*work); ++i) ((unsigned char *)work)[i] = 0;
    work->captured.capture.capital = *capital;
    work->captured.selection.catalog = 4u;
    work->captured.selection.templates[0] = (unsigned short)number;
    for (i = 0; i < 20u; ++i) {
        if (!(mask & (1u << i))) continue;
        /* This retained classic ABI supplies ten-byte literal rows. It is not
         * a replacement for live creators that capture full names before the
         * native setter's clamp. Reject non-English data instead of guessing
         * a wider name or interpreting native Japanese as an extended glyph.
         */
        for (j = 0; j < 10u; ++j)
            if (free_strings[10u*i+j] < 32u || free_strings[10u*i+j] >= 127u) return 0;
        if (!af_mail_capture_set(&work->captured.capture, i, free_strings+10u*i, 10u, 0u)) return 0;
    }
    if (!af_mail_generate(work->stage, 164u, &work->captured.capture,
                           &work->captured.selection, &work->generation)) return 0;
    for (i = 0; i < 164u; ++i) destination[i] = work->stage[i];
    *capital = work->captured.capture.capital;
    return 1;
}
