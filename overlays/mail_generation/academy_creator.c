#include "academy_creator.h"

extern const unsigned char af_npc_word_data[AF_NPC_WORD_BYTES];
extern const unsigned char af_npc_alias_data[AF_NPC_ALIAS_BYTES];

#ifdef __mips__
#define native_clear ((void (*)(unsigned char *))0x8009C384u)
#else
extern void af_npc_creator_test_clear(unsigned char *);
#define native_clear af_npc_creator_test_clear
#endif

static int overlaps(const void *a,unsigned int as,const void *b,unsigned int bs) {
    __UINTPTR_TYPE__ x = (__UINTPTR_TYPE__)a,y = (__UINTPTR_TYPE__)b;
    return a && b && (x <= y ? y-x < as : x-y < bs);
}

int af_academy_mail_create(AfNpcMailCreateWork *work,unsigned char *destination,
                           AfNpcMailSession **active,unsigned int *capital) {
    AfNpcMailSession *session;
    const unsigned char *request,*player;
    const void *outputs[4];
    unsigned int sizes[4],i,j,number;
    if (!work || !destination || !active || !capital || ((__UINTPTR_TYPE__)work&15u)
            || ((__UINTPTR_TYPE__)active&(__alignof__(AfNpcMailSession *)-1u))
            || ((__UINTPTR_TYPE__)capital&(__alignof__(unsigned int)-1u))) return 0;
    outputs[0] = work;sizes[0] = sizeof(*work);
    outputs[1] = destination;sizes[1] = 164u;
    outputs[2] = active;sizes[2] = sizeof(*active);
    outputs[3] = capital;sizes[3] = sizeof(*capital);
    for (i = 0; i < 4u; ++i) {
        for (j = 0; j < i; ++j)
            if (overlaps(outputs[i],sizes[i],outputs[j],sizes[j])) return 0;
        if (overlaps(outputs[i],sizes[i],af_npc_word_data,AF_NPC_WORD_BYTES)
                || overlaps(outputs[i],sizes[i],af_npc_alias_data,AF_NPC_ALIAS_BYTES)) return 0;
    }
    session = &work->captured.session;request = session->remail;player = session->player;
    for (i = 0; i < 4u; ++i)
        if (overlaps(outputs[i],sizes[i],request,18u)
                || overlaps(outputs[i],sizes[i],player,16u)
                || overlaps(outputs[i],sizes[i],session->animal,12u)) return 0;
    if (*active || *capital > 1u) return 0;
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
    work->captured.selection.catalog = 2u;
    work->captured.selection.templates[0] = (unsigned short)number;
    if (!af_mail_generate(work->stage,164u,&work->captured.capture,&work->captured.selection,&work->generation)) return 0;
    for (i = 0; i < 164u; ++i) destination[i] = work->stage[i];
    *capital = work->captured.capture.capital;
    return 1;
}
