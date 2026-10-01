#include "academy_score_creator.h"
#include "../../runtime/dateformat.h"
#include "../../runtime/item_name.h"

extern const unsigned char af_npc_word_data[AF_NPC_WORD_BYTES];
extern const unsigned char af_npc_alias_data[AF_NPC_ALIAS_BYTES];
#ifdef AF_V3_HRA_REWARDS
#ifndef AF_V3_HRA_SERIES_COUNT
#define AF_V3_HRA_SERIES_COUNT 55u
#endif
#define AF_SCORE_SERIES_COUNT AF_V3_HRA_SERIES_COUNT
#define AF_SCORE_SERIES_BYTES ((AF_SCORE_SERIES_COUNT*26u+15u)&~15u)
extern const unsigned char af_academy_series_data[AF_SCORE_SERIES_BYTES];
#else
#define AF_SCORE_SERIES_COUNT 55u
#define AF_SCORE_SERIES_BYTES AF_ACADEMY_SERIES_BYTES
extern const unsigned char af_academy_series_data[AF_ACADEMY_SERIES_BYTES];
#endif

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
    unsigned int i,j,number,points,year,month,day,days,index,length;
#ifdef AF_V3_HRA_REWARDS
    unsigned int gift;
#endif
    unsigned char text[16];
    if (!af_mail_create_guard(work,destination,active,capital,af_academy_series_data,AF_SCORE_SERIES_BYTES)) return 0;
    session = &work->captured.session;request = session->remail;player = session->player;series = session->animal;
    if (!request || request[16] != 250u) return af_academy_mail_create(work,destination,active,capital);
    if (!player || session->condition || session->foreign != 1u
            || (((__UINTPTR_TYPE__)player|(__UINTPTR_TYPE__)request|(__UINTPTR_TYPE__)series)&1u)
            || request[6] || request[7]
#ifndef AF_V3_HRA_REWARDS
            || request[14] || request[15]
#endif
            || request[17] != 51u) return 0;
    number = half(request+12u);points = (half(request)<<16)|half(request+2u);
    year = half(request+8u);month = request[10];day = request[11];
#ifdef AF_V3_HRA_REWARDS
    /* The original HRA selector supplies the two model presents. Selection,
     * earned-once flags, and successful delivery belong to that caller. Never
     * accept a present on an ordinary score letter or invent a replacement.
     */
    gift = half(request+14u);
    if (!((number >= 0x34u && number <= 0x48u && !gift)
            || (number == 0x221u && gift == 0x3024u && points >= 70000u)
            || (number == 0x222u && gift == 0x3028u && points >= 100000u))) return 0;
    if (points > 0x7FFFFFFFu
#else
    if (number < 0x34u || number > 0x48u || points > 0x7FFFFFFFu
#endif
            || year < 1901u || year > 2099u || !month || month > 12u) return 0;
    days = month == 2u ? 28u+(!(year%4u) && (year%100u || !(year%400u)))
         : month == 4u || month == 6u || month == 9u || month == 11u ? 30u : 31u;
    if (!day || day > days) return 0;
    index = AF_SCORE_SERIES_COUNT;
    if (number == 0x3Au || number == 0x3Bu) {
        if (!series) return 0;
        for (i = 0; i < AF_SCORE_SERIES_COUNT; ++i) {
            for (j = 0; j < 10u && series[j] == af_academy_series_data[i*26u+j]; ++j) {}
            if (j == 10u) { if (index != AF_SCORE_SERIES_COUNT) return 0; index = i; }
        }
        if (index == AF_SCORE_SERIES_COUNT) return 0;
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
    if (index < AF_SCORE_SERIES_COUNT && !af_mail_capture_set(&work->captured.capture,2u,
            af_academy_series_data+index*26u+10u,16u,0u)) return 0;
    for (i = 0; i < 16u; ++i) work->stage[i] = player[i];
    for (i = 18u; i < 30u; ++i) work->stage[i] = ' ';
    for (i = 30u; i < 35u; ++i) work->stage[i] = 255u;
#ifdef AF_V3_HRA_REWARDS
    work->stage[36] = (unsigned char)(gift>>8);work->stage[37] = (unsigned char)gift;
#endif
    work->stage[40] = 6u;work->stage[41] = 51u;
    work->captured.selection.catalog = AF_MAIL_CREATOR_CATALOG;work->captured.selection.templates[0] = (unsigned short)number;
    if (!af_mail_generate(work->stage,164u,&work->captured.capture,&work->captured.selection,&work->generation)) return 0;
    for (i = 0; i < 164u; ++i) destination[i] = work->stage[i];
    *capital = work->captured.capture.capital;
    return 1;
}
