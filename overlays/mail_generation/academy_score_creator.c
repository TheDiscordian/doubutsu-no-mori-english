#include "academy_score_creator.h"
#include "../../runtime/dateformat.h"
#include "../../runtime/item_name.h"

extern const unsigned char af_npc_word_data[AF_NPC_WORD_BYTES];
extern const unsigned char af_npc_alias_data[AF_NPC_ALIAS_BYTES];
extern const unsigned char af_academy_series_data[AF_ACADEMY_SERIES_BYTES];

static int overlaps(const void *a,unsigned int as,const void *b,unsigned int bs) {
    __UINTPTR_TYPE__ x = (__UINTPTR_TYPE__)a,y = (__UINTPTR_TYPE__)b;
    return a && b && (x <= y ? y-x < as : x-y < bs);
}

static unsigned int half(const unsigned char *p) { return ((unsigned int)p[0]<<8)|p[1]; }

static unsigned int points_text(unsigned char *out,unsigned int value) {
    unsigned char reverse[16];
    unsigned int n = 0,digits = 0,i,width;
    do {
        if (digits && !(digits%3u)) reverse[n++] = ',';
        reverse[n++] = (unsigned char)('0'+value%10u);value /= 10u;++digits;
    } while (value);
    width = n < 10u ? 10u : n;
    for (i = 0; i < width-n; ++i) out[i] = ' ';
    while (n) out[i++] = reverse[--n];
    return width;
}

int af_academy_score_mail_create(AfNpcMailCreateWork *work,unsigned char *destination,
                                 AfNpcMailSession **active,unsigned int *capital) {
    AfNpcMailSession *session;
    const unsigned char *request,*player,*series;
    const void *outputs[4];
    unsigned int sizes[4],i,j,number,points,year,month,day,days,index,length;
    unsigned char text[16];
    if (!work || !destination || !active || !capital || ((__UINTPTR_TYPE__)work&15u)
            || ((__UINTPTR_TYPE__)active&(__alignof__(AfNpcMailSession *)-1u))
            || ((__UINTPTR_TYPE__)capital&(__alignof__(unsigned int)-1u))) return 0;
    outputs[0] = work;sizes[0] = sizeof(*work);outputs[1] = destination;sizes[1] = 164u;
    outputs[2] = active;sizes[2] = sizeof(*active);outputs[3] = capital;sizes[3] = sizeof(*capital);
    for (i = 0; i < 4u; ++i) {
        for (j = 0; j < i; ++j) if (overlaps(outputs[i],sizes[i],outputs[j],sizes[j])) return 0;
        if (overlaps(outputs[i],sizes[i],af_npc_word_data,AF_NPC_WORD_BYTES)
                || overlaps(outputs[i],sizes[i],af_npc_alias_data,AF_NPC_ALIAS_BYTES)
                || overlaps(outputs[i],sizes[i],af_academy_series_data,AF_ACADEMY_SERIES_BYTES)) return 0;
    }
    session = &work->captured.session;request = session->remail;player = session->player;series = session->animal;
    for (i = 0; i < 4u; ++i)
        if (overlaps(outputs[i],sizes[i],request,18u) || overlaps(outputs[i],sizes[i],player,16u)
                || overlaps(outputs[i],sizes[i],series,12u)) return 0;
    if (*active || *capital > 1u) return 0;
    if (!request || request[16] != 250u) return af_academy_mail_create(work,destination,active,capital);
    if (!player || session->condition || session->foreign != 1u
            || (((__UINTPTR_TYPE__)player|(__UINTPTR_TYPE__)request|(__UINTPTR_TYPE__)series)&1u)
            || request[6] || request[7] || request[14] || request[15] || request[17] != 51u) return 0;
    number = half(request+12u);points = (half(request)<<16)|half(request+2u);
    year = half(request+8u);month = request[10];day = request[11];
    if (number < 0x34u || number > 0x48u || points > 0x7FFFFFFFu
            || year < 1901u || year > 2099u || !month || month > 12u) return 0;
    days = month == 2u ? 28u+(!(year%4u) && (year%100u || !(year%400u)))
         : month == 4u || month == 6u || month == 9u || month == 11u ? 30u : 31u;
    if (!day || day > days) return 0;
    index = 55u;
    if (number == 0x3Au || number == 0x3Bu) {
        if (!series) return 0;
        for (i = 0; i < 55u; ++i) {
            for (j = 0; j < 10u && series[j] == af_academy_series_data[i*26u+j]; ++j) {}
            if (j == 10u) { if (index != 55u) return 0; index = i; }
        }
        if (index == 55u) return 0;
    }
    for (i = sizeof(*session); i < sizeof(*work); ++i) ((unsigned char *)work)[i] = 0;
    session->initial_capital = *capital;work->captured.capture.capital = *capital;
    length = points_text(text,points);
    if (!af_mail_capture_set(&work->captured.capture,0u,text,length,0u)
            || af_format_year(text,year) != 4 || !af_mail_capture_set(&work->captured.capture,3u,text,4u,0u)
            || af_format_month(text,month) < 1 || !af_mail_capture_set(&work->captured.capture,4u,text,9u,0u)
            || af_format_day(text,day) < 1 || !af_mail_capture_set(&work->captured.capture,5u,text,4u,0u)) return 0;
    if (number == 0x37u && (!af_load_item_name(text,16u,half(request+4u))
            || !af_mail_capture_set(&work->captured.capture,1u,text,16u,0u))) return 0;
    if (index < 55u && !af_mail_capture_set(&work->captured.capture,2u,
            af_academy_series_data+index*26u+10u,16u,0u)) return 0;
    for (i = 0; i < 16u; ++i) work->stage[i] = player[i];
    for (i = 18u; i < 30u; ++i) work->stage[i] = ' ';
    for (i = 30u; i < 35u; ++i) work->stage[i] = 255u;
    work->stage[40] = 6u;work->stage[41] = 51u;
    work->captured.selection.catalog = 2u;work->captured.selection.templates[0] = (unsigned short)number;
    if (!af_mail_generate(work->stage,164u,&work->captured.capture,&work->captured.selection,&work->generation)) return 0;
    for (i = 0; i < 164u; ++i) destination[i] = work->stage[i];
    *capital = work->captured.capture.capital;
    return 1;
}
