/* Synthetic host-only player and RNG inputs for the real birthday/item code. */
#include <stddef.h>
extern unsigned char af_test_window[0x300];
unsigned char af_birthday_player[0xB00];
unsigned char af_birthday_first_row_before_second_draw[10];
float af_birthday_draws[2];
unsigned af_birthday_draw_count;
unsigned af_birthday_player_enabled;

const unsigned char *af_birthday_test_private(void) {
    return af_birthday_player_enabled ? af_birthday_player : NULL;
}
void *af_birthday_test_window(void) { return af_test_window; }
float af_birthday_test_random(void) {
    unsigned i, n = af_birthday_draw_count++;
    if (n == 1) {
        for (i = 0; i < 10; ++i)
            af_birthday_first_row_before_second_draw[i] = af_test_window[0x100+i];
    }
    return n < 2 ? af_birthday_draws[n] : -1.0f;
}
