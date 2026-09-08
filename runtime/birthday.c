/* Full ordinary-dialogue birthday fields; saved dates and native RNG stay native. */
#include "dateformat.h"

void af_set_item_str(void *, int, const unsigned char *, int);

static const char animals[12][8] = {
    "Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
    "Horse", "Ram", "Monkey", "Rooster", "Dog", "Boar"
};
static const char signs[12][12] = {
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
};
static const unsigned char last_day[12] = {19,18,20,19,20,21,22,22,22,23,21,21};

#ifdef __mips__
static const unsigned char *current_private(void) {
    return *(const unsigned char *const volatile *)0x80136FD8u;
}
static float random_fraction(void) { return ((float (*)(void))0x8002C9ACu)(); }
static void *message_window(void) { return (void *)0x80142410u; }
#else
extern const unsigned char *af_birthday_test_private(void);
extern float af_birthday_test_random(void);
extern void *af_birthday_test_window(void);
#define current_private af_birthday_test_private
#define random_fraction af_birthday_test_random
#define message_window af_birthday_test_window
#endif

unsigned af_birthday_constellation(unsigned month, unsigned day) {
    unsigned i, selected = 0;
    /* Preserve the cartridge's boundary table, wrap, and invalid-date behaviour. */
    for (i = 0; i < 12; ++i) {
        if (month < i+1 || (month == i+1 && day <= last_day[i])) {
            selected = i;
            break;
        }
    }
    return selected < 3 ? selected+9 : selected-3;
}

static void publish(unsigned slot, const char *value) {
    int length = 0;
    while (value[length]) ++length;
    af_set_item_str(message_window(), (int)slot, (const unsigned char *)value, length);
}

void af_birthday_fields(void) {
    const unsigned char *player = current_private();
    unsigned month, day;
    unsigned char date[10];
    int length, index;
    if (!player) return;
    /* Exactly the original two draws, in the same order, scaled by native 12.0f. */
    index = (int)(random_fraction()*12.0f);
    if (index < 0 || index >= 12) return;
    publish(0, animals[index]);
    index = (int)(random_fraction()*12.0f);
    if (index < 0 || index >= 12) return;
    publish(1, signs[index]);
    month = player[0xA92];
    day = player[0xA93];
    publish(2, signs[af_birthday_constellation(month, day)]);
    length = af_date_format(date, sizeof(date), AF_MONTH, month);
    af_set_item_str(message_window(), 3, date, length);
    length = af_date_format(date, sizeof(date), AF_DAY, day);
    af_set_item_str(message_window(), 4, date, length);
}
