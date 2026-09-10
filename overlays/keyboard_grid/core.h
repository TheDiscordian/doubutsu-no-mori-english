#ifndef AF_KEYBOARD_GRID_CORE_H
#define AF_KEYBOARD_GRID_CORE_H

#define AF_GRID_DISABLED 0xFFFFu
#define AF_GRID_SUN 0x80A7u
#define AF_GRID_SKULL 0x80BAu
#define AF_GRID_TABLES 6
#define AF_GRID_KEYS 40

/* This is private input-selection state, never a saved string or native field. */
struct af_grid_state {
    unsigned char column, row, upper, alphabetical, page;
    unsigned char direction, repeat, deleting, delete_repeat;
    unsigned char cursor_direction, cursor_repeat, moved;
};

enum af_grid_command {
    /* Native 8088547C..808854B8: C-right=1, left=2, up=3, down=4. */
    AF_GRID_NONE, AF_GRID_RIGHT, AF_GRID_LEFT, AF_GRID_UP, AF_GRID_DOWN,
    AF_GRID_DONE, AF_GRID_BACKSPACE, AF_GRID_EXCHANGE, AF_GRID_INSERT
};

void af_grid_reset(struct af_grid_state *);
unsigned int af_grid_key(const struct af_grid_state *, const unsigned short *, int, int);
int af_grid_update(struct af_grid_state *, const unsigned short *, unsigned int,
                   unsigned int, int, int, int, int, unsigned short *);

#endif
