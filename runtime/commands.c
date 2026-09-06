/* Preserve native commands while adding explicit English-only operations. */
#include "dateformat.h"
#include "choice_cancel.h"

typedef unsigned char u8;
typedef unsigned int u32;

struct MessageData {
    int loaded, id, length, cut;
    u8 text[1024];
};

struct MessageWindow {
    u8 prefix[12];
    struct MessageData *data;
    u8 before_flags[0x28C-16];
    u32 flags;
    float unknown_timer, cursor_timer;
    u8 before_cancel[0x2BC-0x298];
    int cancel, cancelable;
};

typedef char check_data_offset[__builtin_offsetof(struct MessageWindow, data) == 12 ? 1 : -1];
typedef char check_flags_offset[__builtin_offsetof(struct MessageWindow, flags) == 0x28C ? 1 : -1];
typedef char check_text_offset[__builtin_offsetof(struct MessageData, text) == 16 ? 1 : -1];
typedef char check_timer_offset[__builtin_offsetof(struct MessageWindow, cursor_timer) == 0x294 ? 1 : -1];
typedef char check_cancel_offset[__builtin_offsetof(struct MessageWindow, cancel) == 0x2BC ? 1 : -1];
typedef int (*NativeCommand)(struct MessageWindow *, int *);

#define NATIVE_COUNT 0x61u
#define NATIVE_INFO ((const u8 (*)[2])0x80106BF4u)
#define NATIVE_HANDLERS ((const NativeCommand *)0x80107CB8u)
#define RTC_HOUR (*(volatile const u8 *)0x80136FBEu)
#define USE_AM (1u << 17)
#define CAPITALIZE (1u << 16)
#define PACING_LOCK (1u << 14)
#define FAST_TEXT (1u << 8)
#define BUTTON_TRIGGER ((int (*)(unsigned))0x80078DACu)

int af_cancel_order(struct MessageWindow *window) {
    if ((window->flags & PACING_LOCK) || !window->cancelable || window->cancel) return 0;
    return BUTTON_TRIGGER(0x8000) || BUTTON_TRIGGER(0x4000);
}

int af_fast_button(struct MessageWindow *window) {
    return (window->flags & PACING_LOCK) ? 0 : BUTTON_TRIGGER(0x4000);
}

void af_cursor_timer(struct MessageWindow *window) {
    if (!(window->flags & PACING_LOCK) && (window->cancel || (window->flags & FAST_TEXT))) {
        window->cursor_timer = 0.0f;
    } else {
        window->cursor_timer -= 1.0f;
        if (window->cursor_timer <= 0.0f) window->cursor_timer = 0.0f;
    }
}

int af_code_size(const u8 *text) {
    if (text[0] == 0x7F) {
        unsigned command = text[1];
        return command < NATIVE_COUNT ? NATIVE_INFO[command][0] : 2;
    }
    return text[0] == 0x80 ? 2 : 1;
}

int af_code_attribute(unsigned command) {
    if (command < NATIVE_COUNT) return NATIVE_INFO[command][1];
    if (command == 0x76) return 2; /* Read-only string insertion. */
    return 0;
}

int af_dispatch_command(struct MessageWindow *window, int *index) {
    struct MessageData *data = window->data;
    unsigned command;
    if (*index < 0 || data->length > 1024 || *index >= data->length - 1
            || data->text[*index] != 0x7F) return 0;
    command = data->text[*index + 1];
    if (command < NATIVE_COUNT) {
        NativeCommand handler = NATIVE_HANDLERS[command];
        int consumes_capital = (command >= 0x1A && command <= 0x1C)
            || (command >= 0x24 && command <= 0x2D) || command == 0x2F
            || (command >= 0x31 && command <= 0x40);
        int capitalize = consumes_capital && (window->flags & CAPITALIZE);
        int result;
        if (consumes_capital) window->flags &= ~CAPITALIZE;
        if (command == 0x21) {
            /* Match GameCube: latch AM/PM when the hour field is inserted. */
            if (RTC_HOUR < 12) window->flags |= USE_AM;
            else window->flags &= ~USE_AM;
        }
        result = handler ? handler(window, index) : 0;
        /* Native colour wrappers can advance the index before inserting a name.
           Use that index, not a preceding colour command. Consume once even for
           an empty field, matching the GameCube insertion routine. */
        data = window->data;
        if (capitalize && *index >= 0 && *index < data->length && *index < 1024) {
            u8 first = data->text[*index];
            if (first >= 'a' && first <= 'z') data->text[*index] = first - ('a' - 'A');
        }
        return result;
    }
    if (command == 0x62) {
        *index += 2;
        af_choice_no_b_close(window);
    }
    if (command == 0x75) {
        *index += 2;
        window->flags |= CAPITALIZE;
    }
    if (command == 0x72 || command == 0x73) {
        *index += 2;
        if (command == 0x72) window->flags |= PACING_LOCK;
        else window->flags &= ~PACING_LOCK;
    }
    if (command == 0x76) {
        /* Both command and result occupy two bytes; no move or length change. */
        af_date_format(data->text + *index, 2, AF_AMPM, (window->flags & USE_AM) ? 0 : 12);
    }
    return 0; /* Native mMsg_RESULT_VOID: process inserted text at the same index. */
}
