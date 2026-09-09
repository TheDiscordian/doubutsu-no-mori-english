/* Complete message fields; packed native fields remain compatibility mirrors. */
#include "extension.h"

static unsigned char rows[20][16];
static af_u32 valid;

#ifdef __mips__
#define base_window() ((void *)0x80142410u)
#define message(window) (*(unsigned char **)((unsigned char *)(window)+12))
#define code_word(address) (*(volatile af_u32 *)(address))
extern int af_native_code_size(unsigned char *, int);
extern int af_native_move(unsigned char *, int, int, int, int);
extern void af_native_copy(unsigned char *, const unsigned char *, int);
extern int af_load_item_name(unsigned char *, unsigned int, unsigned int);
extern void af_writeback(void *, unsigned int);
extern void af_invalidate(void *, unsigned int);
#else
extern void *af_free_test_window(void);
extern unsigned char *af_free_test_message(void *);
extern af_u32 *af_free_test_code(af_u32);
#define base_window af_free_test_window
#define message af_free_test_message
#define code_word(address) (*af_free_test_code(address))
extern int af_native_code_size(unsigned char *, int);
extern int af_native_move(unsigned char *, int, int, int, int);
extern void af_native_copy(unsigned char *, const unsigned char *, int);
extern int af_load_item_name(unsigned char *, unsigned int, unsigned int);
extern void af_writeback(void *, unsigned int);
extern void af_invalidate(void *, unsigned int);
#endif

static int colour_offset(int slot) {
    return slot == 1 ? 0x280 : slot == 2 ? 0x281 : slot == 5 ? 0x282 : 0;
}

void af_free_set(void *window, int slot, const unsigned char *source, int length) {
    unsigned char local[16], *native;
    int i, offset, extended;
    if (!window) return;
    offset = colour_offset(slot);
    extended = window == base_window();
    if (slot < 0 || slot >= 20 || !source || length > (extended ? 16 : 10)) goto reset_colour;
    if (length < 0) length = 0;
    for (i=0; i<16; ++i) local[i] = i < length ? source[i] : ' ';
    native = (unsigned char *)window+0x38+slot*10;
    for (i=0; i<10; ++i) native[i] = local[i];
    if (extended) {
        for (i=0; i<16; ++i) rows[slot][i] = local[i];
        valid |= 1u << slot;
    }
reset_colour:
    /* Native reset also occurs for a null source. Coloured setters subsequently
     * replace these flags through the unchanged native wrapper. */
    if (offset) ((unsigned char *)window)[offset] = 0;
}

static const unsigned char *field(void *window, int slot, int *length) {
    const unsigned char *source;
    int size = 10;
    if (slot < 0 || slot >= 20) slot = 0;
    if (window == base_window() && (valid & (1u << slot))) {
        source = rows[slot];
        size = 16;
    } else source = (unsigned char *)window+0x38+slot*10;
    while (size && source[size-1] == ' ') --size;
    *length = size;
    return source;
}

static int insert(void *window, int slot, unsigned char *data, int index, int length,
                  int colour, int *new_index) {
    static const unsigned char colours[5][3] = {
        {0,0,0}, {145,60,145}, {50,130,70}, {75,95,155}, {160,50,75}
    };
    const unsigned char *source;
    unsigned char text[16], control[6];
    int size, command, prefix, result, i;
    if (!window || !data || index < 0 || length < 0 || length > 1024 || index >= length-1
            || colour < 0 || colour >= 5) return length;
    source = field(window, slot, &size);
    command = af_native_code_size(data, index);
    prefix = colour ? 6 : 0;
    if (command <= 0 || command > length-index || length-command+size+prefix > 1024) return length;
    /* Stage before moving the message, including a source that aliases it. */
    for (i=0; i<size; ++i) text[i] = source[i];
    result = af_native_move(data, index+prefix+size, index+command, length, 0);
    if (prefix) {
        control[0]=0x7f; control[1]=0x50;
        for (i=0; i<3; ++i) control[i+2]=colours[colour][i];
        control[5]=(unsigned char)size;
        af_native_copy(data+index, control, 6);
    }
    af_native_copy(data+index+prefix, text, size);
    if (new_index) *new_index = index+prefix;
    return result;
}

int af_free_copy(void *window, int slot, unsigned char *data, int index, int length) {
    return insert(window, slot, data, index, length, 0, 0);
}

int af_free_colour(void *window, int *index, int slot, int colour) {
    unsigned char *data;
    int *length;
    if (!window || !index || !(data=message(window))) return 0;
    length = (int *)(data+8);
    *length = insert(window, slot, data+16, *index, *length, colour, index);
    return 0;
}

void af_free_item(unsigned int item, int slot) {
    unsigned char name[16];
    if (slot < 0 || slot >= 20) return;
    if (af_load_item_name(name, sizeof(name), item & 0xffffu))
        af_free_set(base_window(), slot, name, 16);
}

void af_free_item_nonzero(unsigned int item, int slot) {
    if (item & 0xffffu) af_free_item(item, slot);
}

void af_free_item_colour(unsigned int item, int slot, int colour) {
    int offset = colour_offset(slot);
    af_free_item(item, slot);
    if (offset) ((unsigned char *)base_window())[offset] = (unsigned char)colour;
}

static void hook(af_u32 address, __UINTPTR_TYPE__ target, int link) {
    code_word(address) = (link ? 0x0c000000u : 0x08000000u) | (((af_u32)target >> 2) & 0x03ffffffu);
    if (!link) code_word(address+4) = 0;
    af_writeback((void *)(__UINTPTR_TYPE__)address, 8);
    af_invalidate((void *)(__UINTPTR_TYPE__)address, 8);
}

__attribute__((section(".text.entry")))
int af_text_extension_init(void) {
    /* No patch occurs until all live native reader/bridge entries agree.
     * The setter address contains the currently executing startup loader. */
    if (code_word(0x800A1370u) != 0x0C027C8Cu || code_word(0x800A1394u) != 0x27BDFFD8u
            || code_word(0x800BB6F0u) != 0x27BDFFD8u || code_word(0x800BB6F4u) != 0xAFBF0014u)
        return 0;
    valid = 0;
    hook(0x8009D6D0u, (__UINTPTR_TYPE__)af_free_set, 0);
    hook(0x800A1370u, (__UINTPTR_TYPE__)af_free_copy, 1);
    hook(0x800A1394u, (__UINTPTR_TYPE__)af_free_colour, 0);
    hook(0x800BB6F0u, (__UINTPTR_TYPE__)af_free_item_nonzero, 0);
    hook(0x800BB6F8u, (__UINTPTR_TYPE__)af_free_item, 0);
    hook(0x800BB700u, (__UINTPTR_TYPE__)af_free_item_colour, 0);
    return 1;
}
