#include "mother_creator.h"

static int overlaps(const void *a,unsigned int as,const void *b,unsigned int bs) {
    __UINTPTR_TYPE__ x = (__UINTPTR_TYPE__)a,y = (__UINTPTR_TYPE__)b;
    return x <= y ? y-x < as : x-y < bs;
}

int af_system_mail_create(AfNpcMailCreateWork *work,unsigned char *destination,
                           AfNpcMailSession **active,unsigned int *capital) {
    AfNpcMailSession *session;
    const unsigned char *request,*player;
    const void *outputs[4];
    unsigned int sizes[4],i,j,template_id;
    if (!work || !destination || !active || !capital || ((__UINTPTR_TYPE__)work&15u)
            || ((__UINTPTR_TYPE__)active&(__alignof__(AfNpcMailSession *)-1u))
            || ((__UINTPTR_TYPE__)capital&(__alignof__(unsigned int)-1u))) return 0;
    outputs[0] = work;sizes[0] = sizeof(*work);
    outputs[1] = destination;sizes[1] = 164u;
    outputs[2] = active;sizes[2] = sizeof(*active);
    outputs[3] = capital;sizes[3] = sizeof(*capital);
    for (i = 0; i < 4u; ++i)
        for (j = 0; j < i; ++j)
            if (overlaps(outputs[i],sizes[i],outputs[j],sizes[j])) return 0;
    session = &work->captured.session;request = session->animal;player = session->player;
    /* Reject inputs pointing into smaller output objects before reading even
     * the dispatch marker. Ordinary NPC creation applies its remaining checks.
     */
    for (i = 0; i < 4u; ++i)
        if ((request && overlaps(outputs[i],sizes[i],request,12u))
                || (player && overlaps(outputs[i],sizes[i],player,16u))) return 0;
    if (!request || request[11] != 254u)
        return af_npc_mail_create(work,destination,active,capital);
    if (*active || *capital > 1u || !player || session->condition || session->foreign || session->remail
            || (((__UINTPTR_TYPE__)player|(__UINTPTR_TYPE__)request)&1u)
            || request[0] != 'A' || request[1] != 'F' || request[2] != 'M' || request[3] != 'O'
            || request[8] >= 64u || request[9] || request[10]) return 0;
    template_id = ((unsigned int)request[4]<<8)|request[5];
    if (!((template_id >= 0x12Cu && template_id <= 0x181u)
            || template_id == 0x184u || template_id == 0x185u
            || (template_id >= 0x18Au && template_id <= 0x1A3u))) return 0;
    for (i = sizeof(*session); i < sizeof(*work); ++i) ((unsigned char *)work)[i] = 0;
    session->initial_capital = *capital;
    for (i = 0; i < 16u; ++i) work->stage[i] = player[i];
    for (i = 18u; i < 30u; ++i) work->stage[i] = ' ';
    for (i = 30u; i < 35u; ++i) work->stage[i] = 255u;
    work->stage[36] = request[6];work->stage[37] = request[7];
    work->stage[40] = 4u;work->stage[41] = request[8];
    work->captured.capture.capital = *capital;
    work->captured.selection.catalog = 2u;
    work->captured.selection.templates[0] = (unsigned short)template_id;
    /* Every selected Mom template has no free-string fields. The catalogue and
     * complete formatter validate that contract before publication. A currently
     * unavailable glyph row fails intact; it is never silently shortened.
     */
    if (!af_mail_generate(work->stage,164u,&work->captured.capture,&work->captured.selection,&work->generation)) return 0;
    for (i = 0; i < 164u; ++i) destination[i] = work->stage[i];
    *capital = work->captured.capture.capital;
    return 1;
}
