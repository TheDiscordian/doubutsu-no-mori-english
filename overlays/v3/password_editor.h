#ifndef AF_PASSWORD_EDITOR_H
#define AF_PASSWORD_EDITOR_H
#include "../keyboard_grid/editor.h"

#define AF_PW_EDITOR_MODE 5
#define AF_PW_EDITOR_BYTES 28
/* Runtime input only: never stored in a town or a native name field. */
struct AfPasswordDraft {
    unsigned char text[AF_PW_EDITOR_BYTES];
    unsigned char line, cursor, finished;
};
enum { AF_PW_EDIT_NONE, AF_PW_EDIT_CHANGED, AF_PW_EDIT_DONE, AF_PW_EDIT_REJECT };
int af_pw_edit(struct AfPasswordDraft *, int, unsigned int);
int af_pw_editor_active(void *);
unsigned int af_pw_editor_key(const struct af_grid_state *, const unsigned short *, int, int);
void af_pw_editor_init(void *, void *);
void af_pw_editor_update(void *, void *);
void af_pw_editor_draw(void *, void *, void *);
#endif
