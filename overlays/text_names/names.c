/* Display-only identity adapter; the native six-byte saved APIs stay intact. */
#include "extension.h"
extern void af_native_identity_name(unsigned char *, const unsigned char *);
extern int af_load_display_name(unsigned char *, unsigned int, unsigned int);
extern int af_text_choices_init(void);
extern void af_writeback(void *, unsigned int);
extern void af_invalidate(void *, unsigned int);

#ifdef __mips__
#define word(at) (*(volatile af_u32 *)(at))
#else
extern af_u32 *af_identity_test_word(af_u32);
#define word(at) (*af_identity_test_word(at))
#endif

void af_identity_name(unsigned char *destination, const unsigned char *identity) {
    unsigned int id;
    if (!destination) return;
    af_native_identity_name(destination, identity);
    destination[6] = destination[7] = ' ';
    if (!identity) return;
    id = ((unsigned int)identity[0] << 8) | identity[1];
    if (id >= 0xE000 && id < 0xE0D8) af_load_display_name(destination, 8, id);
}

__attribute__((section(".text.entry")))
int af_text_extension_init(void) {
    /* All new rejection checks precede the preceding initializer's writes. */
    if (word(0x800BB708u) != 0x27A4001Cu || word(0x800BB70Cu) != 0x0C0259D0u)
        return 0;
    if (!af_text_choices_init()) return 0;
    word(0x800BB708u) = 0x08000000u | (((af_u32)(__UINTPTR_TYPE__)af_identity_name >> 2) & 0x03FFFFFFu);
    word(0x800BB70Cu) = 0;
    af_writeback((void *)0x800BB708u, 8);
    af_invalidate((void *)0x800BB708u, 8);
    return 1;
}
