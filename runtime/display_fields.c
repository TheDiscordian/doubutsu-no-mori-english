/* Display-only actor names and bounded main-message insertion. */
#include "display_name.h"

#ifdef __mips__
static const unsigned char *animal_data(const unsigned char *actor) {
    return *(const unsigned char *const *)(actor+0x174);
}
static void native_name(unsigned char *destination, const unsigned char *actor) {
    ((void (*)(unsigned char *, const unsigned char *))0x800ACDF8u)(destination, actor);
}
static int code_size(unsigned char *data, int index) {
    return ((int (*)(unsigned char *, int))0x800903A8u)(data, index);
}
static int move_data(unsigned char *data, int to, int from, int length) {
    return ((int (*)(unsigned char *, int, int, int, int))0x8009EA2Cu)(data, to, from, length, 0);
}
static void copy_string(unsigned char *destination, const unsigned char *source, int length) {
    ((void (*)(unsigned char *, const unsigned char *, int))0x8009EB44u)(destination, source, length);
}
#else
extern const unsigned char *af_display_test_animal(const unsigned char *);
extern void af_display_test_native(unsigned char *, const unsigned char *);
extern int af_display_test_code_size(unsigned char *, int);
extern int af_display_test_move(unsigned char *, int, int, int);
extern void af_display_test_copy(unsigned char *, const unsigned char *, int);
#define animal_data af_display_test_animal
#define native_name af_display_test_native
#define code_size af_display_test_code_size
#define move_data af_display_test_move
#define copy_string af_display_test_copy
#endif

static unsigned int id_at(const unsigned char *source) {
    return ((unsigned int)source[0] << 8) | source[1];
}

void af_get_display_name(unsigned char *destination, const unsigned char *actor) {
    unsigned int i, npc;
    const unsigned char *animal = 0;
    int index = -1;
    if (!destination) return;
    if (actor) {
        if (actor[2] == 3) animal = animal_data(actor);
        npc = id_at(animal ? animal : actor+6);
        index = af_display_name_index(npc);
        /* Native animal identities and the special actor table are separate
         * branches. A malformed animal must not become a special character,
         * and a non-NPC actor must not acquire a villager name from fgName. */
        if ((animal && index >= 0 && index < (int)AF_VILLAGER_COUNT)
                || (!animal && index >= (int)AF_VILLAGER_COUNT)) {
            if (af_load_display_name(destination, AF_DISPLAY_NAME_WIDTH, npc)) return;
        }
    }
    for (i = 0; i < AF_DISPLAY_NAME_WIDTH; ++i) destination[i] = ' ';
    native_name(destination, actor);
}

int af_copy_talk_name(const unsigned char *actor, unsigned char *data, int index, int length) {
    unsigned char name[AF_DISPLAY_NAME_WIDTH];
    int size = 0, command, result;
    if (!data || index < 0 || length < 0 || length > 1024 || index >= length-1) return length;
    command = code_size(data, index);
    if (command <= 0 || command > length-index) return length;
    if (actor) {
        af_get_display_name(name, actor);
        for (size = AF_DISPLAY_NAME_WIDTH; size > 0 && name[size-1] == ' '; --size) {}
    }
    if (length-command+size > 1024) return length;
    result = move_data(data, index+size, index+command, length);
    copy_string(data+index, name, size);
    return result;
}
