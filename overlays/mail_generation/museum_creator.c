#include "museum_creator.h"

#ifdef __mips__
#define native_sender ((void (*)(unsigned char *))0x800A3420u)
#else
extern void af_museum_creator_test_sender(unsigned char *);
#define native_sender af_museum_creator_test_sender
#endif

static const unsigned short fossil_templates[25] = {
    0x10E,0x110,0x10F,0x111,0x113,0x112,0x114,0x116,0x115,
    0x117,0x119,0x118,0x11A,0x11B,0x11C,0x11D,0x11E,0x11F,
    0x120,0x121,0x126,0x125,0x123,0x124,0x122
};

int af_museum_mail_create(AfNpcMailCreateWork *work,unsigned char *destination,
                           AfNpcMailSession **active,unsigned int *capital) {
    AfNpcMailSession *session;
    const unsigned char *request,*player;
    unsigned int i,number,gift;
    if (!af_mail_create_guard(work,destination,active,capital,fossil_templates,sizeof(fossil_templates))) return 0;
    session = &work->captured.session;request = session->animal;player = session->player;
    if (session->remail || !request)
        return af_post_office_mail_create(work,destination,active,capital);
    if ((__UINTPTR_TYPE__)request&1u) return 0;
    if (request[11] != 248u)
        return af_post_office_mail_create(work,destination,active,capital);
    if (!player || ((__UINTPTR_TYPE__)player&1u) || session->condition || session->foreign
            || request[0] != 'A' || request[1] != 'F' || request[2] != 'M' || request[3] != 'U'
            || request[8] != 24u || request[9] || request[10]) return 0;
    number = ((unsigned int)request[4]<<8)|request[5];
    gift = ((unsigned int)request[6]<<8)|request[7];
    if (number == 0xBDu || number == 0xBEu) {
        if (gift) return 0;
    } else if (gift < 0x1E3Cu || gift >= 0x1EA0u || number != fossil_templates[(gift-0x1E3Cu)>>2]) return 0;
    for (i = sizeof(*session); i < sizeof(*work); ++i) ((unsigned char *)work)[i] = 0;
    session->initial_capital = *capital;work->captured.capture.capital = *capital;
    for (i = 0; i < 16u; ++i) work->stage[i] = player[i];
    native_sender(work->stage+18u);
    work->stage[36] = request[6];work->stage[37] = request[7];work->stage[41] = 24u;
    work->captured.selection.catalog = AF_MAIL_CREATOR_CATALOG;
    work->captured.selection.templates[0] = (unsigned short)number;
    if (!af_mail_generate(work->stage,164u,&work->captured.capture,&work->captured.selection,&work->generation)) return 0;
    for (i = 0; i < 164u; ++i) destination[i] = work->stage[i];
    *capital = work->captured.capture.capital;
    return 1;
}
