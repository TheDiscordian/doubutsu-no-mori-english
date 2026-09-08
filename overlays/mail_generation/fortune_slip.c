#include "fortune_slip.h"

#ifdef __mips__
typedef char choice_size_check[sizeof(AfFortuneSlipChoice) == 8 ? 1 : -1];
typedef char fortune_work_check[sizeof(AfFortuneSlipWork) == 5280 ? 1 : -1];
typedef char fortune_generation_check[__builtin_offsetof(AfFortuneSlipWork,generation) == 560 ? 1 : -1];
#endif

static int overlap(const void *a, unsigned int as, const void *b, unsigned int bs) {
    __UINTPTR_TYPE__ av = (__UINTPTR_TYPE__)a, bv = (__UINTPTR_TYPE__)b;
    return av <= bv ? bv-av < as : av-bv < bs;
}

int af_fortune_slip_create(unsigned char *mail, unsigned int size,
    const AfFortuneSlipChoice *choice, const unsigned char *words,
    unsigned int word_bytes, unsigned int *capital, AfFortuneSlipWork *work) {
    unsigned int i, slot, row;
    if (!mail || size != 164u || !choice || !words || word_bytes != AF_FORTUNE_WORD_BYTES
            || !capital || ((__UINTPTR_TYPE__)capital & 3u) || !work
            || ((__UINTPTR_TYPE__)work & 15u)
            || overlap(work,sizeof(*work),mail,size)
            || overlap(work,sizeof(*work),choice,sizeof(*choice))
            || overlap(work,sizeof(*work),words,word_bytes)
            || overlap(work,sizeof(*work),capital,sizeof(*capital))
            || overlap(mail,size,choice,sizeof(*choice))
            || overlap(mail,size,words,word_bytes)
            || overlap(mail,size,capital,sizeof(*capital))
            || overlap(capital,sizeof(*capital),choice,sizeof(*choice))
            || overlap(capital,sizeof(*capital),words,word_bytes)
            || *capital > 1u || choice->outcome >= 4u || choice->template_index >= 3u
            || choice->reserved[0] || choice->reserved[1])
        return 0;
    for (i = 0; i < 4u; ++i)
        if (choice->phrases[i] >= 16u)
            return 0;
    af_mail_capture_reset(&work->capture);
    work->capture.capital = *capital;
    for (slot = 0; slot < 5u; ++slot) {
        row = slot < 4u ? slot*16u+choice->phrases[slot] : 64u+choice->outcome;
        if (!af_mail_capture_set(&work->capture,slot,words+row*16u,16u,0u))
            return 0;
    }
    for (i = 0; i < sizeof(work->selection); ++i)
        ((unsigned char *)&work->selection)[i] = 0;
    work->selection.catalog = AF_MAIL_FORTUNE_CATALOG_ID;
    work->selection.templates[0] = (unsigned short)(0x72u+choice->template_index);
    for (i = 0; i < size; ++i)
        work->mail[i] = mail[i];
    if (!af_mail_generate(work->mail,size,&work->capture,&work->selection,&work->generation))
        return 0;
    work->mail[0x26] = 0u;
    work->mail[0x28] = 5u;
    work->mail[0x29] = 25u;
    for (i = 0; i < size; ++i)
        mail[i] = work->mail[i];
    *capital = work->capture.capital;
    return 1;
}
