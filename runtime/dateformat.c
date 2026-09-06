/* English calendar forms matching the English GameCube message formatters. */
#include "dateformat.h"

static const char months[12][10] = {
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
};
static const char weekdays[7][10] = {
    "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
};

int af_date_format(unsigned char *out, unsigned capacity, unsigned part, unsigned value) {
    char number[4];
    const char *source = number;
    unsigned length = 0, i, tens;

    switch (part) {
        case AF_YEAR:
            if (value < 1901 || value > 2099) value = 2000;
            number[0] = '0' + value / 1000;
            number[1] = '0' + (value / 100) % 10;
            number[2] = '0' + (value / 10) % 10;
            number[3] = '0' + value % 10;
            length = 4;
            break;
        case AF_MONTH:
            if (value < 1 || value > 12) value = 1;
            source = months[value - 1];
            break;
        case AF_WEEKDAY:
            if (value > 6) value = 0;
            source = weekdays[value];
            break;
        case AF_DAY:
            if (value < 1 || value > 31) value = 1;
            if (value >= 10) number[length++] = '0' + value / 10;
            number[length++] = '0' + value % 10;
            i = value % 10;
            if (value >= 11 && value <= 13) i = 0;
            number[length++] = i == 1 ? 's' : i == 2 ? 'n' : i == 3 ? 'r' : 't';
            number[length++] = i == 1 ? 't' : i == 2 || i == 3 ? 'd' : 'h';
            break;
        case AF_HOUR:
            if (value > 23) value = 0;
            value %= 12;
            if (!value) value = 12;
            if (value >= 10) number[length++] = '1';
            number[length++] = '0' + value % 10;
            break;
        case AF_MINUTE:
        case AF_SECOND:
            if (value > 59) value = 0;
            tens = value / 10;
            number[0] = '0' + tens;
            number[1] = '0' + value - tens * 10;
            length = 2;
            break;
        case AF_AMPM:
            if (value > 23) value = 0;
            source = value < 12 ? "AM" : "PM";
            break;
        default:
            return -1;
    }
    if (!length) {
        while (source[length]) ++length;
    }
    if (!out || length > capacity) return -1;
    for (i = 0; i < length; ++i) out[i] = source[i];
    for (; i < capacity; ++i) out[i] = ' ';
    return (int)length;
}

#define FORMATTER(name, width, part) \
    int af_format_##name(unsigned char *out, unsigned value) { \
        return af_date_format(out, width, part, value); \
    }
FORMATTER(year, 6, AF_YEAR)
FORMATTER(month, 9, AF_MONTH)
FORMATTER(weekday, 9, AF_WEEKDAY)
FORMATTER(day, 4, AF_DAY)
FORMATTER(hour, 2, AF_HOUR)
FORMATTER(minute, 2, AF_MINUTE)
FORMATTER(second, 2, AF_SECOND)
