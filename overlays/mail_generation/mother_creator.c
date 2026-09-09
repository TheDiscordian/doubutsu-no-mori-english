#include "mother_creator.h"

int af_system_mail_create(AfNpcMailCreateWork *work,unsigned char *destination,
                           AfNpcMailSession **active,unsigned int *capital) {
    AfNpcMailSession *session;
    const unsigned char *request,*player;
    unsigned int i,template_id;
    if (!af_mail_create_guard(work,destination,active,capital,0,0)) return 0;
    session = &work->captured.session;request = session->animal;player = session->player;
    if (!request || request[11] != 254u)
        return af_npc_mail_create(work,destination,active,capital);
    if (!player || session->condition || session->foreign || session->remail
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
    work->captured.selection.catalog = AF_MAIL_CREATOR_CATALOG;
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
