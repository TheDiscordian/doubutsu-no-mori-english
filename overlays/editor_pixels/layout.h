#ifndef AF_EDITOR_PIXELS_H
#define AF_EDITOR_PIXELS_H
#include "../../runtime/mail/view.h"

struct af_edit_point { unsigned int start, column, row, x; };
/* All lengths and indices are saved bytes; only x is a pixel measurement. */
int af_edit_position(const unsigned char *, unsigned int, unsigned int, struct af_edit_point *);
int af_edit_nearest(const unsigned char *, unsigned int, unsigned int, unsigned int);
unsigned int af_edit_width(const unsigned char *, unsigned int);
#endif
