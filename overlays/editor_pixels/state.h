#ifndef AF_PIXEL_STATE_H
#define AF_PIXEL_STATE_H
#include "../hboard/editor.h"
#ifdef __mips__
static inline void *af_pixel_state(void *submenu, unsigned int at) {
    unsigned char *ovl = submenu ? ((struct af_hboard_submenu_pointer *)submenu)->overlay : 0;
    return ovl ? *(void **)(ovl+at) : 0;
}
#else
/* Host pointers are eight bytes and cannot occupy adjacent native 4-byte slots. */
extern void *af_pixel_state(void *, unsigned int);
#endif
#endif
