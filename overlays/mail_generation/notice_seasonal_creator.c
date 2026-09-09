#include "notice_seasonal_creator.h"
#include "../../runtime/notice/seasonal.h"
#include "../../runtime/dateformat.h"

typedef struct { unsigned short year; unsigned char month, day; } SeasonalDate;

#ifdef __mips__
#define town ((const unsigned char *)0x80129E00u)
#define shop_level ((unsigned int (*)(void))0x800C165Cu)
#define lunar_date ((int (*)(SeasonalDate *, const SeasonalDate *))0x800D60E4u)
#define weekday ((unsigned int (*)(unsigned int, unsigned int, unsigned int))0x800D5CF8u)
#else
extern const unsigned char af_seasonal_test_town[6];
extern unsigned int af_seasonal_test_shop_level(void);
extern int af_seasonal_test_lunar_date(SeasonalDate *, const SeasonalDate *);
extern unsigned int af_seasonal_test_weekday(unsigned int, unsigned int, unsigned int);
#define town af_seasonal_test_town
#define shop_level af_seasonal_test_shop_level
#define lunar_date af_seasonal_test_lunar_date
#define weekday af_seasonal_test_weekday
#endif

static int date_text(unsigned char *text, unsigned int field, unsigned int year) {
    SeasonalDate lunar, solar;
    unsigned int day, month;
    int month_length, day_length;
    if (field == 2u || field == 3u) {
        lunar.year = (unsigned short)year;
        lunar.month = (unsigned char)(field == 2u ? 8u : 9u);
        lunar.day = (unsigned char)(field == 2u ? 15u : 13u);
        solar = lunar;
        /* Retain the original fallback when the native lunar table cannot
         * convert the year. No writes to the global lunar input table occur.
         */
        if (!lunar_date(&solar, &lunar)) solar = lunar;
        month = solar.month;
        day = solar.day;
    } else if (field == 4u) {
        day = weekday(year, 10u, 14u);
        if (day > 6u) return 0;
        day = day ? 15u-day : 8u;
        month = 10u;
    } else return 0;
    if (!month || month > 12u || !day || day > 31u) return 0;
    month_length = af_format_month(text, month);
    if (month_length < 1 || month_length > 9) return 0;
    text[month_length] = ' ';
    day_length = af_format_day(text+(unsigned int)month_length+1u, day);
    if (day_length < 1 || day_length > 4) return 0;
    return month_length+1+day_length;
}

int af_notice_seasonal_create(AfNpcMailCreateWork *work, unsigned char *destination,
                                AfNpcMailSession **active, unsigned int *capital) {
    AfNpcMailSession *session;
    AfMailRecord *record;
    const unsigned char *request;
    unsigned char text[16];
    unsigned int i, j, number, year, mask, level;
    int length;
    if (!af_mail_create_guard(work, destination, active, capital, town, 6u)) return 0;
    session = &work->captured.session;
    request = session->animal;
    if (!request || session->remail) return af_notice_owner_create(work, destination, active, capital);
    if ((__UINTPTR_TYPE__)request & 1u) return 0;
    if (request[11] != 243u) return af_notice_owner_create(work, destination, active, capital);
    if (!session->player || ((__UINTPTR_TYPE__)session->player & 1u) || session->condition || session->foreign
            || request[0] != 'A' || request[1] != 'F' || request[2] != 'N' || request[3] != 'S'
            || request[8] || request[9] || request[10]) return 0;
    number = ((unsigned int)request[4] << 8) | request[5];
    year = ((unsigned int)request[6] << 8) | request[7];
    mask = af_notice_seasonal_mask(number);
    if (mask == ~0u || !year) return 0;
    for (i = sizeof(*session); i < sizeof(*work); ++i) ((unsigned char *)work)[i] = 0;
    record = &work->generation.catalog.record;
    record->catalog = AF_MAIL_GLYPH_CATALOG_ID;
    record->flags = (unsigned char)*capital;
    record->templates[0] = (unsigned short)number;
    record->field_mask = mask;
    for (i = 0; i < 5u; ++i) {
        if (!(mask & (1u << i))) continue;
        if (!i) {
            length = 6;
            for (j = 0; j < 6u; ++j) text[j] = town[j];
        } else if (i == 1u) {
            level = shop_level();
            if (!af_notice_seasonal_shop(text, sizeof(text), level)) return 0;
            length = 16;
        } else {
            length = date_text(text, i, year);
            if (!length) return 0;
        }
        record->fields[i].length = (unsigned char)length;
        for (j = 0; j < (unsigned int)length; ++j) record->fields[i].text[j] = text[j];
    }
    if (!af_notice_seasonal_pack(work->stage, 96u, record)
            || !af_notice_seasonal_decode_parts(&work->generation.catalog, &work->generation.text,
                                                work->generation.wire, work->stage, 96u)) return 0;
    for (i = 0; i < 164u; ++i) destination[i] = work->stage[i];
    *capital = work->generation.text.final_capital;
    return 1;
}
