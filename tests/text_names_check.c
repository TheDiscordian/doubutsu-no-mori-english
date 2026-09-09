#include <assert.h>
#include <string.h>
#include "extension.h"
extern void af_identity_name(unsigned char *, const unsigned char *);
static af_u32 words[2];
static int ready, initials, flushes, invalidates, native_calls, full_calls, enabled = 1;

af_u32 *af_identity_test_word(af_u32 at) {
    assert(at == 0x800BB708u || at == 0x800BB70Cu);
    return words + (at - 0x800BB708u) / 4;
}
int af_text_choices_init(void) { ++initials; return ready; }
void af_writeback(void *at, unsigned int size) {
    assert((__UINTPTR_TYPE__)at == 0x800BB708u && size == 8); ++flushes;
}
void af_invalidate(void *at, unsigned int size) {
    assert((__UINTPTR_TYPE__)at == 0x800BB708u && size == 8); ++invalidates;
}
void af_native_identity_name(unsigned char *out, const unsigned char *id) {
    (void)id; ++native_calls; memcpy(out, "native", 6);
}
int af_load_display_name(unsigned char *out, unsigned int size, unsigned int id) {
    assert(size == 8 && id >= 0xE000 && id <= 0xE0D7); ++full_calls;
    if (!enabled) return 0;
    memcpy(out, "LongName", 8); return 1;
}

int main(void) {
    unsigned char out[10], id[12], saved[12];
    const unsigned int ids[] = {0, 0xD008, 0xDFFF, 0xE000, 0xE014, 0xE0D7, 0xE0D8, 0xEFFF, 0xFFFF};
    assert(!af_text_extension_init() && !initials && !flushes);
    words[0] = 0x27A4001C; words[1] = 0;
    assert(!af_text_extension_init() && !initials && !flushes);
    words[1] = 0x0C0259D0;
    assert(!af_text_extension_init() && initials == 1 && !flushes);
    assert(words[0] == 0x27A4001C && words[1] == 0x0C0259D0);
    ready = 1;
    assert(af_text_extension_init() && initials == 2 && flushes == 1 && invalidates == 1);
    assert(words[0] >> 26 == 2 && words[1] == 0);
    assert(!af_text_extension_init() && initials == 2 && flushes == 1);
    memset(id, 0xA5, sizeof id);
    for (unsigned int i = 0; i < sizeof ids / sizeof ids[0]; ++i) {
        int calls = full_calls;
        int valid = ids[i] >= 0xE000 && ids[i] <= 0xE0D7;
        id[0] = ids[i] >> 8; id[1] = ids[i]; memcpy(saved, id, sizeof id);
        memset(out, '!', sizeof out); af_identity_name(out + 1, id);
        assert(!memcmp(out + 1, valid ? "LongName" : "native  ", 8));
        assert(out[0] == '!' && out[9] == '!' && !memcmp(saved, id, sizeof id));
        assert(full_calls == calls + valid);
    }
    enabled = 0; id[0] = 0xE0; id[1] = 0;
    af_identity_name(out + 1, id); assert(!memcmp(out + 1, "native  ", 8));
    af_identity_name(out + 1, 0); assert(!memcmp(out + 1, "native  ", 8));
    int calls = native_calls;
    af_identity_name(0, id); assert(native_calls == calls);
    return 0;
}
