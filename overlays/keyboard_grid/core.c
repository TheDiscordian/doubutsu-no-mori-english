/* GameCube-style selection and native commands, independent of saved text. */
#include "core.h"

#define BTN_A 0x8000u
#define BTN_B 0x4000u
#define BTN_Z 0x2000u
#define BTN_START 0x1000u
#define BTN_UP 0x0800u
#define BTN_DOWN 0x0400u
#define BTN_LEFT 0x0200u
#define BTN_RIGHT 0x0100u
#define BTN_L 0x0020u
#define BTN_R 0x0010u

void af_grid_reset(struct af_grid_state *s) {
    unsigned int i;
    if (s) for (i=0;i<sizeof(*s);++i) ((unsigned char *)s)[i]=0;
}

static int valid(const struct af_grid_state *s) {
    return s && s->column<10 && s->row<4 && s->upper<2 && s->alphabetical<2 && s->page<3
        && s->direction<=4 && s->repeat<8 && s->deleting<2 && s->delete_repeat<8
        && s->cursor_direction<=4 && s->cursor_repeat<8;
}

unsigned int af_grid_key(const struct af_grid_state *s, const unsigned short *tables,
                         int newline, int apology) {
    unsigned int table, code;
    if (!valid(s) || !tables) return AF_GRID_DISABLED;
    table = s->page ? s->page+3u : s->upper*2u+s->alphabetical;
    code=tables[table*AF_GRID_KEYS+s->row*10u+s->column];
    if (code==0xCD && !newline) return AF_GRID_DISABLED;
    if (code>255 && !(apology && (code==AF_GRID_SUN || code==AF_GRID_SKULL)))
        return AF_GRID_DISABLED;
    if (code==0x7F || code==0x80) return AF_GRID_DISABLED;
    return code;
}

static int repeat(unsigned int direction, unsigned char *old, unsigned char *frames) {
    if (!direction) { *old=*frames=0; return 0; }
    if (direction!=*old) { *old=(unsigned char)direction; *frames=0; return 1; }
    if (++*frames>=8) { *frames=6; return 1; }
    return 0;
}

static unsigned int direction(unsigned int buttons, int x, int y) {
    unsigned int horizontal=buttons&(BTN_LEFT|BTN_RIGHT), vertical=buttons&(BTN_UP|BTN_DOWN);
    int ax, ay;
    if (horizontal || vertical) {
        if (horizontal==(BTN_LEFT|BTN_RIGHT) || vertical==(BTN_UP|BTN_DOWN)) return 0;
        if (vertical) return vertical==BTN_UP ? AF_GRID_UP : AF_GRID_DOWN;
        return horizontal==BTN_LEFT ? AF_GRID_LEFT : AF_GRID_RIGHT;
    }
    /* Joystick accessors are bounded by the native signed controller range. */
    if (x < -128 || x > 127 || y < -128 || y > 127) return 0;
    ax=x<0 ? -x : x; ay=y<0 ? -y : y;
    if (ax<25 && ay<25) return 0;
    if (ay>=ax) return y>0 ? AF_GRID_UP : AF_GRID_DOWN;
    return x>0 ? AF_GRID_RIGHT : AF_GRID_LEFT;
}

int af_grid_update(struct af_grid_state *s, const unsigned short *tables,
        unsigned int held, unsigned int pressed, int x, int y, int newline,
        int apology, unsigned short *out) {
    unsigned int d, cursor=0, key;
    unsigned char old_column, old_row;
    int erase;
    if (!s || !out || !tables) return AF_GRID_NONE;
    *out=AF_GRID_DISABLED;
    if (!valid(s)) { af_grid_reset(s); return AF_GRID_NONE; }
    held |= pressed;
    s->moved=0;
    d=direction(held,x,y);
    if (repeat(d,&s->direction,&s->repeat)) {
        old_column=s->column;old_row=s->row;
        if (d==AF_GRID_LEFT && s->column) --s->column;
        if (d==AF_GRID_RIGHT && s->column<9) ++s->column;
        if (d==AF_GRID_UP && s->row) --s->row;
        if (d==AF_GRID_DOWN && s->row<3) ++s->row;
        s->moved=(s->column!=old_column || s->row!=old_row);
    }
    if ((held&15)==1) cursor=AF_GRID_RIGHT;
    if ((held&15)==2) cursor=AF_GRID_LEFT;
    if ((held&15)==4) cursor=AF_GRID_DOWN;
    if ((held&15)==8) cursor=AF_GRID_UP;
    if (!repeat(cursor,&s->cursor_direction,&s->cursor_repeat)) cursor=0;
    erase=repeat((held&BTN_B)!=0,&s->deleting,&s->delete_repeat);
    if (pressed&BTN_START) return AF_GRID_DONE;
    if ((held&BTN_L) && (pressed&BTN_A)) return AF_GRID_EXCHANGE;
    if ((held&(BTN_L|BTN_Z))==(BTN_L|BTN_Z) && (pressed&(BTN_L|BTN_Z))) {
        s->alphabetical^=1u;return AF_GRID_NONE;
    }
    if (pressed&BTN_L) { s->upper^=1u;return AF_GRID_NONE; }
    if (pressed&BTN_Z) { s->page=(unsigned char)((s->page+1u)%3u);return AF_GRID_NONE; }
    if (erase) return AF_GRID_BACKSPACE;
    if (cursor) return (int)cursor;
    if (pressed&BTN_R) { *out=' ';return AF_GRID_INSERT; }
    if (pressed&BTN_A) {
        key=af_grid_key(s,tables,newline,apology);
        if (key!=AF_GRID_DISABLED) { *out=(unsigned short)key;return AF_GRID_INSERT; }
    }
    return AF_GRID_NONE;
}
