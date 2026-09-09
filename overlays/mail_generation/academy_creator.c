#include "academy_creator.h"

extern const unsigned char af_npc_word_data[AF_NPC_WORD_BYTES];
extern const unsigned char af_npc_alias_data[AF_NPC_ALIAS_BYTES];

#ifdef __mips__
#define native_clear ((void (*)(unsigned char *))0x8009C384u)
#else
extern void af_npc_creator_test_clear(unsigned char *);
#define native_clear af_npc_creator_test_clear
#endif

int af_academy_mail_create(AfNpcMailCreateWork *work,unsigned char *destination,
                           AfNpcMailSession **active,unsigned int *capital) {
    AfNpcMailSession *session;
    const unsigned char *request,*player;
    unsigned int i,number;
    if (!af_mail_create_guard(work,destination,active,capital,0,0)) return 0;
    session = &work->captured.session;request = session->remail;player = session->player;
    if (!request || request[16] != 251u)
        return af_villager_event_mail_create(work,destination,active,capital);
    if (!player || session->animal || session->condition || session->foreign != 1u
            || (((__UINTPTR_TYPE__)player|(__UINTPTR_TYPE__)request)&1u)
            || request[14] || request[15] || request[17] != 51u) return 0;
    for (i = 0; i < 12u; ++i) if (request[i]) return 0;
    number = ((unsigned int)request[12]<<8)|request[13];
    if (number < 0x1DCu || number > 0x1EFu) return 0;
    for (i = sizeof(*session); i < sizeof(*work); ++i) ((unsigned char *)work)[i] = 0;
    session->initial_capital = *capital;
    native_clear(work->stage);
    for (i = 0; i < 16u; ++i) work->stage[i] = player[i];
    work->stage[16] = 0;
    for (i = 18u; i < 30u; ++i) work->stage[i] = ' ';
    for (i = 30u; i < 35u; ++i) work->stage[i] = 255u;
    work->stage[38] = 0;work->stage[40] = 6u;work->stage[41] = 51u;
    work->captured.capture.capital = *capital;
    work->captured.selection.catalog = AF_MAIL_CREATOR_CATALOG;
    work->captured.selection.templates[0] = (unsigned short)number;
    if (!af_mail_generate(work->stage,164u,&work->captured.capture,&work->captured.selection,&work->generation)) return 0;
    for (i = 0; i < 164u; ++i) destination[i] = work->stage[i];
    *capital = work->captured.capture.capital;
    return 1;
}
