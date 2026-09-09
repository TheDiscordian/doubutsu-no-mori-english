#include "departed_creator.h"

extern const unsigned char af_npc_word_data[AF_NPC_WORD_BYTES];
extern const unsigned char af_npc_alias_data[AF_NPC_ALIAS_BYTES];

#ifdef __mips__
#define native_looks ((unsigned int (*)(unsigned int))0x800AA1E0u)
#define native_random ((float (*)(void))0x8002C9ACu)
#define native_name ((void (*)(unsigned char *,unsigned int))0x800ACC38u)
#define native_field ((void (*)(unsigned int,const unsigned char *,unsigned int))0x80092D10u)
#define native_paper ((unsigned int (*)(void))0x800A9364u)
#define native_sender ((void (*)(unsigned char *,const unsigned char *))0x8009C70Cu)
#define native_clear ((void (*)(unsigned char *))0x8009C384u)
#else
extern unsigned int af_departed_test_looks(unsigned int);
extern float af_departed_test_random(void);
extern void af_departed_test_name(unsigned char *,unsigned int);
extern void af_departed_test_field(unsigned int,const unsigned char *,unsigned int);
extern unsigned int af_departed_test_paper(void);
extern void af_departed_test_sender(unsigned char *,const unsigned char *);
extern void af_npc_creator_test_clear(unsigned char *);
#define native_looks af_departed_test_looks
#define native_random af_departed_test_random
#define native_name af_departed_test_name
#define native_field af_departed_test_field
#define native_paper af_departed_test_paper
#define native_sender af_departed_test_sender
#define native_clear af_npc_creator_test_clear
#endif

int af_departed_mail_create(AfNpcMailCreateWork *work,unsigned char *destination,
                            AfNpcMailSession **active,unsigned int *capital) {
    AfNpcMailSession *session;
    AfMailField name;
    const unsigned char *request,*player;
    unsigned int i,npc,looks,number,paper;
    unsigned char identity[12] __attribute__((aligned(2))),short_name[6];
    float draw;
    if (!af_mail_create_guard(work,destination,active,capital,0,0)) return 0;
    session = &work->captured.session;request = session->animal;player = session->player;
    if (!request || session->foreign || session->remail || request[11] != 253u)
        return af_system_mail_create(work,destination,active,capital);
    if (!player || session->condition || (((__UINTPTR_TYPE__)player|(__UINTPTR_TYPE__)request)&1u)
            || request[0] != 'D' || request[1] != 'M' || request[10]) return 0;
    npc = ((unsigned int)request[2]<<8)|request[3];
    if (npc < 0xE000u || npc >= 0xE0D8u) return 0;
    for (i = sizeof(*session); i < sizeof(*work); ++i) ((unsigned char *)work)[i] = 0;
    session->initial_capital = *capital;
    if (!af_npc_mail_sources_init(&work->captured.sources,af_npc_word_data,AF_NPC_WORD_BYTES,
                                  af_npc_alias_data,AF_NPC_ALIAS_BYTES)
            || !af_npc_mail_source_name(&name,&work->captured.sources,npc)) return 0;
    work->captured.capture.capital = *capital;
    if (!af_mail_capture_set(&work->captured.capture,0u,player,6u,0u)
            || !af_mail_capture_set(&work->captured.capture,1u,name.text,8u,0u)
            || !af_mail_capture_set(&work->captured.capture,2u,request+4u,6u,0u)
            || !af_mail_capture_set(&work->captured.capture,3u,player+6u,6u,0u)) return 0;
    native_clear(work->stage);
    looks = native_looks(npc);
    if (looks >= 6u) return 0;
    draw = native_random();
    if (!(draw >= 0.0f && draw < 1.0f)) return 0;
    number = 0xFCu+looks*3u+(int)(draw*3.0f);
    /* Keep the original native temporary fields and selected-source call order.
     * The snapshot captures the full English name independently of this buffer.
     */
    native_field(0u,player,6u);
    native_name(short_name,npc&255u);
    native_field(1u,short_name,6u);
    native_field(2u,request+4u,6u);
    native_field(3u,player+6u,6u);
    paper = native_paper();
    if (paper >= 64u) return 0;
    identity[0] = request[2];identity[1] = request[3];identity[2] = 0x30u;identity[3] = 0;
    for (i = 0; i < 6u; ++i) identity[4u+i] = request[4u+i];
    identity[10] = (unsigned char)npc;identity[11] = (unsigned char)looks;
    native_sender(work->stage+18u,identity);
    for (i = 0; i < 16u; ++i) work->stage[i] = player[i];
    work->stage[16] = 0;work->stage[36] = 0;work->stage[37] = 0;
    work->stage[38] = 0;work->stage[40] = 0;work->stage[41] = (unsigned char)paper;
    work->captured.selection.catalog = AF_MAIL_CREATOR_CATALOG;
    work->captured.selection.templates[0] = (unsigned short)number;
    if (!af_mail_generate(work->stage,164u,&work->captured.capture,&work->captured.selection,&work->generation)) return 0;
    for (i = 0; i < 164u; ++i) destination[i] = work->stage[i];
    *capital = work->captured.capture.capital;
    return 1;
}
