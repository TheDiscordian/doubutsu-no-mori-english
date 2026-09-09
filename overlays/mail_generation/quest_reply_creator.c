#include "quest_reply_creator.h"
#include "../../runtime/item_name.h"

extern const unsigned char af_npc_word_data[AF_NPC_WORD_BYTES];
extern const unsigned char af_npc_alias_data[AF_NPC_ALIAS_BYTES];

#ifdef __mips__
#define native_clear ((void (*)(unsigned char *))0x8009C384u)
#define native_name ((void (*)(unsigned char *,const unsigned char *))0x800ACD18u)
#define native_item ((void (*)(unsigned char *,unsigned int))0x80096740u)
#define native_field ((void (*)(unsigned int,const unsigned char *,unsigned int))0x80092D10u)
#define native_sender ((void (*)(unsigned char *,const unsigned char *))0x8009C70Cu)
#else
extern void af_npc_creator_test_clear(unsigned char *);
extern void af_quest_reply_test_name(unsigned char *,const unsigned char *);
extern void af_quest_reply_test_item(unsigned char *,unsigned int);
extern void af_quest_reply_test_field(unsigned int,const unsigned char *,unsigned int);
extern void af_departed_test_sender(unsigned char *,const unsigned char *);
#define native_clear af_npc_creator_test_clear
#define native_name af_quest_reply_test_name
#define native_item af_quest_reply_test_item
#define native_field af_quest_reply_test_field
#define native_sender af_departed_test_sender
#endif

int af_quest_reply_mail_create(AfNpcMailCreateWork *work,unsigned char *destination,
                               AfNpcMailSession **active,unsigned int *capital) {
    AfNpcMailSession *session;
    AfMailField name;
    const unsigned char *request,*player,*animal;
    unsigned int i,rank,npc,number,item,needs_item;
    unsigned char text[16];
    if (!af_mail_create_guard(work,destination,active,capital,0,0)) return 0;
    session = &work->captured.session;request = session->remail;
    if (!request) return af_shop_notice_mail_create(work,destination,active,capital);
    if ((__UINTPTR_TYPE__)request&1u) return 0;
    if (request[16]!=246u) return af_shop_notice_mail_create(work,destination,active,capital);
    player = session->player;animal = session->animal;
    if (!player || !animal || (((__UINTPTR_TYPE__)player|(__UINTPTR_TYPE__)animal)&1u)
            || session->condition || session->foreign!=1u || request[0]!='A' || request[1]!='F'
            || request[2]!='Q' || request[3]!='R' || request[4]>=12u || request[5] || request[17]
            || animal[11]>=6u) return 0;
    for (i = 8u; i < 16u; ++i) if (request[i]) return 0;
    npc = ((unsigned int)animal[0]<<8)|animal[1];
    if (npc<0xE000u || npc>=0xE0D8u) return 0;
    rank = request[4];item = ((unsigned int)request[6]<<8)|request[7];
    number = 0x75u+rank*6u+animal[11];
    needs_item = number==0x8Du || number==0x8Eu || number==0x92u
              || number==0x94u || number==0xB3u || number==0xB6u;
    if (needs_item && !item) return 0;
    for (i = sizeof(*session); i < sizeof(*work); ++i) ((unsigned char *)work)[i] = 0;
    session->initial_capital = *capital;work->captured.capture.capital = *capital;
    if (!af_npc_mail_sources_init(&work->captured.sources,af_npc_word_data,AF_NPC_WORD_BYTES,
                                  af_npc_alias_data,AF_NPC_ALIAS_BYTES)
            || !af_npc_mail_source_name(&name,&work->captured.sources,npc)
            || !af_mail_capture_set(&work->captured.capture,6u,name.text,8u,0u)) return 0;
    if (needs_item && (!af_load_item_name(text,16u,item)
            || !af_mail_capture_set(&work->captured.capture,0u,text,16u,0u))) return 0;
    native_clear(work->stage);
    /* Preserve native temporary fields and metadata call order, independently
     * of the complete display fields captured above. No reward is reselected.
     */
    native_name(text,animal);native_field(6u,text,6u);
    if (item) { native_item(text,item);native_field(0u,text,10u); }
    for (i = 0; i < 16u; ++i) work->stage[i] = player[i];
    work->stage[16] = 0;
    native_sender(work->stage+18u,animal);
    work->stage[36] = request[6];work->stage[37] = request[7];
    work->stage[38] = 0;work->stage[40] = 0;work->stage[41] = 22u;
    work->captured.selection.catalog = AF_MAIL_CREATOR_CATALOG;
    work->captured.selection.templates[0] = (unsigned short)number;
    if (!af_mail_generate(work->stage,164u,&work->captured.capture,&work->captured.selection,&work->generation)) return 0;
    for (i = 0; i < 164u; ++i) destination[i] = work->stage[i];
    *capital = work->captured.capture.capital;
    return 1;
}
