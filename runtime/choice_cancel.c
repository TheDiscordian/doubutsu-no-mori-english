/* Original N64 implementation of the English reference's choice sound policy. */
#include "choice_cancel.h"

typedef unsigned char u8;
typedef unsigned int u32;

#define NO_DUPLICATE_CLOSE (1u << 11)
#define GET_WINDOW ((void *(*)(void))0x8009D1F0u)
#define PLAY_SOUND ((void (*)(unsigned))0x800D1A9Cu)

static u32 *message_flags(void *window) {
    return (u32 *)((u8 *)window + 0x28C);
}

void af_choice_no_b_close(void *window) {
    u8 *choice = (u8 *)window + 0x1B0;
    choice[0xB8] = 1;
    choice[0xB9] = 1;
}

unsigned af_choice_close_sound(void *pointer) {
    const u8 *choice = pointer;
    unsigned sound = 0x0D;
    if (choice[0xB8] && *(const int *)(choice + 0x84) == *(const int *)(choice + 0x7C) - 1) {
        sound = choice[0xB9] ? 0x15 : 0x05;
        if (choice[0xB9]) *message_flags(GET_WINDOW()) |= NO_DUPLICATE_CLOSE;
    }
    PLAY_SOUND(sound);
    return sound;
}

static unsigned message_close_sound(unsigned sound) {
    if (*message_flags(GET_WINDOW()) & NO_DUPLICATE_CLOSE) return 0;
    PLAY_SOUND(sound);
    return sound;
}

unsigned af_message_close_short(void) {
    return message_close_sound(0x05);
}

unsigned af_message_close_long(void) {
    return message_close_sound(0x15);
}

void af_message_wait_clear(void *window) {
    *message_flags(window) &= ~NO_DUPLICATE_CLOSE;
}
