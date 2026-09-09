#ifndef AF_HBOARD_EDITOR_H
#define AF_HBOARD_EDITOR_H

/* Owner-message editing only. These are not Mail_c or player-name fields. */
#define AF_HBOARD_SAVED 64
#define AF_HBOARD_DRAFT 128
#define AF_HBOARD_DEFAULT 92
#define AF_HBOARD_ROWS 4
#define AF_HBOARD_WIDTH 192

enum af_hboard_result {
    AF_HBOARD_OK = 1,
    AF_HBOARD_UNCHANGED = 0,
    AF_HBOARD_ARGUMENT = -1,
    AF_HBOARD_BAD_WIDTH = -2,
    AF_HBOARD_TOO_MANY_ROWS = -3,
    AF_HBOARD_DRAFT_FULL = -4,
    AF_HBOARD_SAVE_FULL = -5,
    AF_HBOARD_SAVE_CHANGED = -6
};

/* Command numbers match the native editor. Done is handled by commit, not
 * command(), so a rejected save cannot start the native closing animation. */
enum af_hboard_command {
    AF_HBOARD_LEFT = 1, AF_HBOARD_DOWN, AF_HBOARD_UP, AF_HBOARD_RIGHT,
    AF_HBOARD_DONE, AF_HBOARD_BACKSPACE, AF_HBOARD_EXCHANGE, AF_HBOARD_INSERT
};

struct af_hboard_point {
    unsigned short column, row, x;
};

struct af_hboard_line {
    unsigned short start, length, width;
};

struct af_hboard_layout {
    struct af_hboard_line lines[AF_HBOARD_ROWS];
    struct af_hboard_point cursor, end;
    unsigned short rows;
};

struct af_hboard_draft {
    unsigned char text[AF_HBOARD_DRAFT];
    unsigned char original[AF_HBOARD_SAVED];
    unsigned short length, cursor;
};

/* Widths are the native proportional font advances, cached by the overlay.
 * No automatic break is inserted into text; manual CD bytes remain in place.
 * Failed operations leave the supplied output/state/save untouched. */
int af_hboard_layout(const unsigned char *text, int length, int cursor,
                     const unsigned char *widths, struct af_hboard_layout *out);
int af_hboard_begin(struct af_hboard_draft *draft, const unsigned char *saved,
                    const unsigned char *native_default, const unsigned char *english_default);
int af_hboard_command(struct af_hboard_draft *draft, int command, int code,
                      const unsigned char *widths);
int af_hboard_pack(const struct af_hboard_draft *draft, const unsigned char *native_default,
                   const unsigned char *english_default, unsigned char *out);
int af_hboard_commit(const struct af_hboard_draft *draft, const unsigned char *native_default,
                     const unsigned char *english_default, unsigned char *saved);

#endif
