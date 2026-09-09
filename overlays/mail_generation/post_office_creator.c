#include "post_office_creator.h"
#include "../../runtime/dateformat.h"
#include "../../runtime/item_name.h"

int af_post_office_mail_create(AfNpcMailCreateWork *work,unsigned char *destination,
                               AfNpcMailSession **active,unsigned int *capital) {
    AfNpcMailSession *session;
    const unsigned char *request,*player;
    unsigned int i,number,gift;
    unsigned char text[16];
    if (!af_mail_create_guard(work,destination,active,capital,0,0)) return 0;
    session = &work->captured.session;request = session->animal;player = session->player;
    if (session->remail || !request)
        return af_academy_score_mail_create(work,destination,active,capital);
    if ((__UINTPTR_TYPE__)request&1u) return 0;
    if (request[11] != 249u)
        return af_academy_score_mail_create(work,destination,active,capital);
    if (!player || ((__UINTPTR_TYPE__)player&1u) || session->condition || session->foreign
            || request[0] != 'A' || request[1] != 'F' || request[2] != 'P' || request[3] != 'O'
            || request[8] != 55u || request[9] || request[10]) return 0;
    number = ((unsigned int)request[4]<<8)|request[5];
    gift = ((unsigned int)request[6]<<8)|request[7];
    if (number == 0x57u) {
        if (gift < 0x2C00u || gift > 0x2C5Cu || (gift&7u) >= 5u) return 0;
    } else if (number < 0x49u || number > 0x4Cu || !gift) return 0;
    for (i = sizeof(*session); i < sizeof(*work); ++i) ((unsigned char *)work)[i] = 0;
    session->initial_capital = *capital;work->captured.capture.capital = *capital;
    if (number == 0x57u) {
        if (af_format_month(text,((gift-0x2C00u)>>3)+1u) < 1
                || !af_mail_capture_set(&work->captured.capture,4u,text,9u,0u)) return 0;
    } else if (!af_load_item_name(text,16u,gift)
            || !af_mail_capture_set(&work->captured.capture,0u,text,16u,0u)) return 0;
    for (i = 0; i < 16u; ++i) work->stage[i] = player[i];
    for (i = 18u; i < 30u; ++i) work->stage[i] = ' ';
    for (i = 30u; i < 35u; ++i) work->stage[i] = 255u;
    work->stage[36] = request[6];work->stage[37] = request[7];
    work->stage[40] = 7u;work->stage[41] = 55u;
    work->captured.selection.catalog = AF_MAIL_CREATOR_CATALOG;
    work->captured.selection.templates[0] = (unsigned short)number;
    if (!af_mail_generate(work->stage,164u,&work->captured.capture,&work->captured.selection,&work->generation)) return 0;
    for (i = 0; i < 164u; ++i) destination[i] = work->stage[i];
    *capital = work->captured.capture.capital;
    return 1;
}
