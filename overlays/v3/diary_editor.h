#ifndef AF_V3_DIARY_EDITOR_H
#define AF_V3_DIARY_EDITOR_H
#include "diary_menu.h"
#include "../keyboard_grid/editor.h"

enum { AF_DIARY_EDITOR_MODE=6, AF_DIARY_SESSION_MAGIC=0x41464453 };
/* Owned by the resident diary screen, never by a saved player or keyboard
 * overlay. The submenu passes this pointer through editor menu data3. */
typedef struct {
    unsigned int magic;
    void *submenu;
    AFDiaryMenu *menu;
    AFDiaryMenuAccess *access;
} AFDiaryEditorSession;

void af_diary_editor_init(void *,void *);
void af_diary_editor_update(void *,void *);
int af_diary_editor_active(void *);
/* Bind these to the accepted native keyboard entry points at installation. */
extern void af_diary_keyboard_init(void *,void *);
extern void af_diary_keyboard_update(void *,void *);
extern void af_diary_keyboard_input(void *);
extern void af_diary_keyboard_feedback(void *);
extern int af_diary_keyboard_exchange(struct af_hboard_native_editor *);
extern void af_diary_keyboard_done(void *,void *);
extern void af_diary_keyboard_sound(unsigned int);
#ifndef __mips__
/* Host fixtures model four-byte native pointers without overlapping adjacent
 * fields with the host's wider pointers. */
extern void *af_diary_editor_test_pointer(void *,unsigned int);
extern void af_diary_editor_test_set_pointer(void *,unsigned int,void *);
#endif
#endif
