#include "villager_event_creator.h"
#include "../../runtime/item_name.h"

extern const unsigned char af_npc_word_data[AF_NPC_WORD_BYTES];
extern const unsigned char af_npc_alias_data[AF_NPC_ALIAS_BYTES];

#ifdef __mips__
#define native_clear ((void (*)(unsigned char *))0x8009C384u)
#define native_sender ((void (*)(unsigned char *,const unsigned char *))0x8009C70Cu)
#define current_town ((const unsigned char *)0x80129E00u)
#else
extern void af_npc_creator_test_clear(unsigned char *);
extern void af_departed_test_sender(unsigned char *,const unsigned char *);
extern const unsigned char af_event_card_town[6];
#define native_clear af_npc_creator_test_clear
#define native_sender af_departed_test_sender
#define current_town af_event_card_town
#endif

static int overlaps(const void *a,unsigned int as,const void *b,unsigned int bs) {
    __UINTPTR_TYPE__ x = (__UINTPTR_TYPE__)a,y = (__UINTPTR_TYPE__)b;
    return a && b && (x <= y ? y-x < as : x-y < bs);
}

int af_villager_event_mail_create(AfNpcMailCreateWork *work,unsigned char *destination,
                                  AfNpcMailSession **active,unsigned int *capital) {
    AfNpcMailSession *session;
    AfMailField name;
    unsigned char item_name[16];
    const unsigned char *request,*player;
    const void *outputs[4];
    unsigned int sizes[4],i,j,number,npc,gift,event,birthday,goodbye,christmas;
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
                || overlaps(outputs[i],sizes[i],af_npc_alias_data,AF_NPC_ALIAS_BYTES)
                || overlaps(outputs[i],sizes[i],current_town,6u)) return 0;
    }
    session = &work->captured.session;request = session->remail;player = session->player;
    for (i = 0; i < 4u; ++i) {
        if (overlaps(outputs[i],sizes[i],request,18u)
                || overlaps(outputs[i],sizes[i],player,16u)
                || overlaps(outputs[i],sizes[i],session->animal,12u)) return 0;
    }
    if (*active || *capital > 1u) return 0;
    if (!request || request[16] != 252u)
        return af_departed_mail_create(work,destination,active,capital);
    if (!player || session->animal || session->condition || session->foreign != 1u
            || (((__UINTPTR_TYPE__)player|(__UINTPTR_TYPE__)request)&1u) || request[17] >= 64u) return 0;
    number = ((unsigned int)request[12]<<8)|request[13];
    gift = ((unsigned int)request[14]<<8)|request[15];
    event = number >= 0x60u && number <= 0x71u;
    birthday = number >= 0xEAu && number <= 0xFBu;
    goodbye = number >= 0x20Eu && number <= 0x21Fu;
    christmas = number == 0xD7u;
    if (!event && !birthday && !goodbye && !christmas) return 0;
    npc = ((unsigned int)request[0]<<8)|request[1];
    if (christmas) {
        for (i = 0; i < 12u; ++i) if (request[i]) return 0;
        if (request[17] != 22u || !gift) return 0;
    } else if (npc < 0xE000u || npc >= 0xE0D8u || request[11] >= 6u
            || (number-(event ? 0x60u : birthday ? 0xEAu : 0x20Eu))/3u != request[11]
            || (goodbye ? gift != 0u : !gift)) return 0;
    for (i = sizeof(*session); i < sizeof(*work); ++i) ((unsigned char *)work)[i] = 0;
    session->initial_capital = *capital;
    work->captured.capture.capital = *capital;
    if (!af_npc_mail_sources_init(&work->captured.sources,af_npc_word_data,AF_NPC_WORD_BYTES,
                                  af_npc_alias_data,AF_NPC_ALIAS_BYTES)) return 0;
    if (!christmas) {
        if (!af_npc_mail_source_name(&name,&work->captured.sources,npc)
                || !af_mail_capture_set(&work->captured.capture,0u,player,6u,0u)
                || !af_mail_capture_set(&work->captured.capture,event ? 6u : 1u,name.text,8u,0u)) return 0;
        if (goodbye && !af_mail_capture_set(&work->captured.capture,3u,current_town,6u,0u)) return 0;
        /* Only these complete English birthday bodies use the selected gift
         * name. The other bodies do not depend on an unused item-name load.
         * Set_free_str has no automatic article in the supplied English code.
         */
        if (number == 0xEFu || number == 0xF1u || number == 0xF4u || number == 0xFBu) {
            if (!af_load_item_name(item_name,16u,gift)
                    || !af_mail_capture_set(&work->captured.capture,2u,item_name,16u,0u)) return 0;
        }
    }
    native_clear(work->stage);
    if (christmas) {
        /* Match a freshly cleared native sender, not stale shared staging. */
        for (i = 18u; i < 30u; ++i) work->stage[i] = ' ';
        for (i = 30u; i < 35u; ++i) work->stage[i] = 255u;
    } else native_sender(work->stage+18u,request);
    for (i = 0; i < 16u; ++i) work->stage[i] = player[i];
    work->stage[16] = 0;work->stage[36] = request[14];work->stage[37] = request[15];
    work->stage[38] = 0;work->stage[40] = (unsigned char)christmas;work->stage[41] = request[17];
    work->captured.selection.catalog = 2u;
    work->captured.selection.templates[0] = (unsigned short)number;
    if (!af_mail_generate(work->stage,164u,&work->captured.capture,&work->captured.selection,&work->generation)) return 0;
    for (i = 0; i < 164u; ++i) destination[i] = work->stage[i];
    *capital = work->captured.capture.capital;
    return 1;
}
