/* Only the main-message catchphrase caller receives the wider display string. */
#include "catchphrase.h"

#ifdef __mips__
static const unsigned char *animal_data(const unsigned char *actor) {
    return *(const unsigned char *const *)(actor+0x174);
}
static const unsigned char *native_ending(const unsigned char *actor) {
    return ((const unsigned char *(*)(const unsigned char *))0x800A9E7Cu)(actor);
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
extern const unsigned char *af_catchphrase_test_animal(const unsigned char *);
extern const unsigned char *af_catchphrase_test_native(const unsigned char *);
extern int af_catchphrase_test_code_size(unsigned char *, int);
extern int af_catchphrase_test_move(unsigned char *, int, int, int);
extern void af_catchphrase_test_copy(unsigned char *, const unsigned char *, int);
#define animal_data af_catchphrase_test_animal
#define native_ending af_catchphrase_test_native
#define code_size af_catchphrase_test_code_size
#define move_data af_catchphrase_test_move
#define copy_string af_catchphrase_test_copy
#endif

void af_get_catchphrase(unsigned char *destination, const unsigned char *actor) {
    const unsigned char *animal = 0, *saved;
    unsigned int i, npc;
    if (!destination) return;
    if (actor && actor[2] == 3) animal = animal_data(actor);
    if (animal) {
        npc = ((unsigned int)animal[0] << 8) | animal[1];
        if (af_load_catchphrase(destination, AF_CATCHPHRASE_WIDTH, npc, animal+0x4E5)) return;
    }
    for (i = 0; i < AF_CATCHPHRASE_WIDTH; ++i) destination[i] = ' ';
    if (actor) {
        saved = native_ending(actor);
        for (i = 0; i < 4; ++i) destination[i] = saved[i];
    }
}

int af_copy_catchphrase(const unsigned char *actor, unsigned char *data, int index, int length) {
    unsigned char phrase[AF_CATCHPHRASE_WIDTH];
    int size = 0, command, result;
    if (!data || index < 0 || length < 0 || length > 1024 || index >= length-1) return length;
    command = code_size(data, index);
    if (command <= 0 || command > length-index) return length;
    if (actor) {
        af_get_catchphrase(phrase, actor);
        for (size = AF_CATCHPHRASE_WIDTH; size > 0 && phrase[size-1] == ' '; --size) {}
    }
    if (length-command+size > 1024) return length;
    result = move_data(data, index+size, index+command, length);
    copy_string(data+index, phrase, size);
    return result;
}
