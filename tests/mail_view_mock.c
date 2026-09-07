#include <string.h>
#include "../runtime/mail/view.h"

unsigned char af_mail_view_board[192];
int af_mail_view_widths[256];
unsigned int af_mail_view_calls;
struct Draw {
    unsigned int length;
    float x, y;
    unsigned char colour[4], text[128];
} af_mail_view_draws[9];

unsigned char *af_mail_view_test_board(void *submenu) {
    return submenu ? af_mail_view_board : 0;
}
int af_mail_view_test_width(unsigned char code) { return af_mail_view_widths[code]; }
void af_mail_view_test_draw(void *game, const unsigned char *text, unsigned int length,
                            float x, float y, const unsigned char *colour) {
    struct Draw *entry;
    (void)game;
    if (af_mail_view_calls >= 9 || length > 128) {
        af_mail_view_calls = 1000;
        return;
    }
    entry = &af_mail_view_draws[af_mail_view_calls++];
    entry->length = length;
    entry->x = x;
    entry->y = y;
    memcpy(entry->colour, colour, 4);
    memcpy(entry->text, text, length);
}
