#include <string.h>

typedef struct { unsigned short year; unsigned char month, day; } SeasonalDate;
const unsigned char af_seasonal_test_town[6] = {'T', 'o', 'w', 'n', ' ', ' '};
unsigned int af_seasonal_level, af_seasonal_shop_calls, af_seasonal_lunar_calls, af_seasonal_weekday_calls;
unsigned int af_seasonal_lunar_mode = 1, af_seasonal_month = 9, af_seasonal_day = 30;
unsigned int af_seasonal_weekday_value, af_seasonal_lunar_input[3], af_seasonal_weekday_input[3];

unsigned int af_seasonal_test_shop_level(void) { ++af_seasonal_shop_calls; return af_seasonal_level; }

int af_seasonal_test_lunar_date(SeasonalDate *out, const SeasonalDate *in) {
    ++af_seasonal_lunar_calls;
    af_seasonal_lunar_input[0] = in->year;
    af_seasonal_lunar_input[1] = in->month;
    af_seasonal_lunar_input[2] = in->day;
    /* Contract-only fixture, not a model or proof of the native lunar table. */
    if (!af_seasonal_lunar_mode) { memset(out, 0xFF, sizeof(*out)); return 0; }
    out->year = in->year;
    out->month = (unsigned char)af_seasonal_month;
    out->day = (unsigned char)af_seasonal_day;
    return 1;
}

unsigned int af_seasonal_test_weekday(unsigned int year, unsigned int month, unsigned int day) {
    ++af_seasonal_weekday_calls;
    af_seasonal_weekday_input[0] = year;
    af_seasonal_weekday_input[1] = month;
    af_seasonal_weekday_input[2] = day;
    return af_seasonal_weekday_value;
}
