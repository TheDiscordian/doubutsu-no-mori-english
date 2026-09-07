/* Complete English item values without changing the native message structure. */
#include "item_name.h"

static unsigned char item_rows[5][AF_ITEM_WIDTH];
static unsigned int item_valid;

#ifdef __mips__
static void *base_window(void) { return (void *)0x80142410u; }
static int code_size(unsigned char *data, int index) {
    return ((int (*)(unsigned char *, int))0x800903A8u)(data, index);
}
static int move_data(unsigned char *data, int to, int from, int length) {
    return ((int (*)(unsigned char *, int, int, int, int))0x8009EA2Cu)(data, to, from, length, 0);
}
static void copy_string(unsigned char *destination, const unsigned char *source, int length) {
    ((void (*)(unsigned char *, const unsigned char *, int))0x8009EB44u)(destination, source, length);
}
static void native_name(unsigned char *destination, unsigned int item) {
    ((void (*)(unsigned char *, unsigned short))0x80096740u)(destination, (unsigned short)item);
}
#else
extern void *af_item_test_window(void);
extern int af_item_test_code_size(unsigned char *, int);
extern int af_item_test_move(unsigned char *, int, int, int);
extern void af_item_test_copy(unsigned char *, const unsigned char *, int);
extern void af_item_test_native_name(unsigned char *, unsigned int);
#define base_window af_item_test_window
#define code_size af_item_test_code_size
#define move_data af_item_test_move
#define copy_string af_item_test_copy
#define native_name af_item_test_native_name
#endif

void af_set_item_str(void *window, int slot, const unsigned char *source, int length) {
    unsigned char local[AF_ITEM_WIDTH];
    unsigned char *native;
    int i, extended = window == base_window();
    if (!window || slot < 0 || slot >= 5 || !source || length > (extended ? 16 : 10)) return;
    if (length < 0) length = 0;
    /* Stage first: source may be the destination or another resident row. */
    for (i = 0; i < 16; ++i) local[i] = i < length ? source[i] : ' ';
    native = (unsigned char *)window+0x100+slot*10;
    for (i = 0; i < 10; ++i) native[i] = local[i];
    if (extended) {
        for (i = 0; i < 16; ++i) item_rows[slot][i] = local[i];
        item_valid |= 1u << slot;
    }
}

int af_copy_item_string(void *window, int slot, unsigned char *data, int index, int length) {
    const unsigned char *source;
    int width = 10, size, command, result;
    if (!window || !data || index < 0 || length < 0 || length > 1024 || index >= length-1) return length;
    if (slot < 0 || slot >= 5) slot = 0;
    if (window == base_window() && (item_valid & (1u << slot))) {
        source = item_rows[slot];
        width = 16;
    } else {
        source = (const unsigned char *)window+0x100+slot*10;
    }
    command = code_size(data, index);
    if (command <= 0 || command > length-index) return length;
    for (size = width; size > 0 && source[size-1] == ' '; --size) {}
    if (length-command+size > 1024) return length;
    result = move_data(data, index+size, index+command, length);
    copy_string(data+index, source, size);
    return result;
}

void af_quest_set_item(unsigned int item, int slot) {
    unsigned char name[AF_ITEM_WIDTH];
    int width = 16;
    item &= 0xFFFFu;
    if (!item || slot < 0 || slot >= 5 || af_item_name_index(item) < 0) return;
    if (!af_load_item_name(name, sizeof(name), item)) {
        int i;
        for (i = 0; i < 16; ++i) name[i] = ' ';
        native_name(name, item);
        width = 10;
    }
    af_set_item_str(base_window(), slot, name, width);
}
