#include "npc_creator.h"

extern const unsigned char af_npc_word_data[AF_NPC_WORD_BYTES];
extern const unsigned char af_npc_alias_data[AF_NPC_ALIAS_BYTES];

#ifdef __mips__
typedef char creator_size_check[sizeof(AfNpcMailCreateWork) == AF_NPC_MAIL_WORK_BYTES ? 1 : -1];
typedef char creator_stage_check[__builtin_offsetof(AfNpcMailCreateWork,stage) == 448 ? 1 : -1];
typedef char creator_generation_check[__builtin_offsetof(AfNpcMailCreateWork,generation) == 624 ? 1 : -1];
#define native_clear ((void (*)(unsigned char *))0x8009C384u)
#define native_metadata ((void (*)(unsigned char *,const unsigned char *,const unsigned char *,const unsigned char *,unsigned int,unsigned int))0x800A9028u)
#else
extern void af_npc_creator_test_clear(unsigned char *);
extern void af_npc_creator_test_metadata(unsigned char *,const unsigned char *,const unsigned char *,const unsigned char *,unsigned int,unsigned int);
#define native_clear af_npc_creator_test_clear
#define native_metadata af_npc_creator_test_metadata
#endif

static int overlap(const void *a, unsigned int as, const void *b, unsigned int bs) {
    __UINTPTR_TYPE__ x = (__UINTPTR_TYPE__)a, y = (__UINTPTR_TYPE__)b;
    if (!a || !b) return 0;
    return x <= y ? y-x < as : x-y < bs;
}

int af_mail_create_guard(AfNpcMailCreateWork *work, unsigned char *destination,
                         AfNpcMailSession **active, unsigned int *capital,
                         const void *extra, unsigned int extra_bytes) {
    const void *outputs[4], *inputs[3];
    unsigned int sizes[4], lengths[3], i, j;
    if (!work || !destination || !active || !capital || (!extra != !extra_bytes)
            || ((__UINTPTR_TYPE__)work & 15u)
            || ((__UINTPTR_TYPE__)active & (__alignof__(AfNpcMailSession *)-1u))
            || ((__UINTPTR_TYPE__)capital & (__alignof__(unsigned int)-1u))) return 0;
    outputs[0] = work; sizes[0] = sizeof(*work);
    outputs[1] = destination; sizes[1] = 164;
    outputs[2] = active; sizes[2] = sizeof(*active);
    outputs[3] = capital; sizes[3] = sizeof(*capital);
    /* Reject a work pointer aliased to a smaller control object before reading
     * that alleged work object's session fields.
     */
    for (i = 0; i < 4; ++i) {
        for (j = 0; j < i; ++j)
            if (overlap(outputs[i],sizes[i],outputs[j],sizes[j])) return 0;
        if (overlap(outputs[i],sizes[i],af_npc_word_data,AF_NPC_WORD_BYTES)
                || overlap(outputs[i],sizes[i],af_npc_alias_data,AF_NPC_ALIAS_BYTES)
                || overlap(outputs[i],sizes[i],extra,extra_bytes)) return 0;
    }
    inputs[0] = work->captured.session.player; lengths[0] = 16;
    inputs[1] = work->captured.session.animal; lengths[1] = 12;
    inputs[2] = work->captured.session.remail; lengths[2] = 18;
    for (i = 0; i < 4; ++i) {
        for (j = 0; j < 3; ++j)
            if (overlap(outputs[i],sizes[i],inputs[j],lengths[j])) return 0;
    }
    return !*active && *capital <= 1u;
}

int af_npc_mail_create(AfNpcMailCreateWork *work, unsigned char *destination,
                       AfNpcMailSession **active, unsigned int *capital) {
    AfNpcMailCaptureWork *capture;
    AfNpcMailSession *session;
    unsigned int i, owned;
    if (!af_mail_create_guard(work,destination,active,capital,0,0)) return 0;
    capture = &work->captured;
    session = &capture->session;
    if (!session->player || (!session->animal && !session->remail)
            || session->condition > 1u || session->foreign > 1u
            || session->foreign != (session->remail != 0)
            || (session->remail ? session->remail[16]&127u : session->animal[11]) >= 6u)
        return 0;
    /* Preserve input arguments only; no stale fields/phase/metadata can become
     * part of a new letter, including padding untouched by native clear.
     */
    for (i = sizeof(*session); i < sizeof(*work); ++i) ((unsigned char *)work)[i] = 0;
    session->event = af_npc_mail_capture_event;
    session->stage = work->stage;
    session->initial_capital = *capital;
    if (!af_npc_mail_sources_init(&capture->sources,af_npc_word_data,AF_NPC_WORD_BYTES,
                                  af_npc_alias_data,AF_NPC_ALIAS_BYTES)) return 0;
    native_clear(work->stage);
    *active = session;
    native_metadata(work->stage,session->player,session->animal,session->remail,
                    session->condition,session->foreign);
    owned = *active == session;
    *active = 0;
    if (!owned || capture->failed || capture->phase != 3u
            || !af_mail_generate(work->stage,164,&capture->capture,&capture->selection,&work->generation))
        return 0;
    for (i = 0; i < 164u; ++i) destination[i] = work->stage[i];
    *capital = capture->capture.capital;
    return 1;
}
