#include "classic.h"

#ifdef __mips__
#define native_sized ((void (*)(unsigned char *, unsigned int, unsigned int *, unsigned char *, unsigned int, unsigned char *, unsigned int))0x80093F54u)
#define native_entry ((volatile unsigned int *)0x80093F04u)
#define writeback ((void (*)(void *, unsigned int))0x8002FE00u)
#define invalidate ((void (*)(void *, unsigned int))0x80034CE0u)
#else
extern void af_classic_test_sized(unsigned char *, unsigned int, unsigned int *, unsigned char *, unsigned int, unsigned char *, unsigned int);
extern volatile unsigned int af_classic_test_entry[2];
extern void af_classic_test_writeback(void *, unsigned int);
extern void af_classic_test_invalidate(void *, unsigned int);
#define native_sized af_classic_test_sized
#define native_entry af_classic_test_entry
#define writeback af_classic_test_writeback
#define invalidate af_classic_test_invalidate
#endif
extern int af_accent_font_install(void);

void af_classic_load(unsigned char *header, unsigned int *split, unsigned char *footer,
                      unsigned char *body, unsigned int number) {
    unsigned char stage[164] __attribute__((aligned(16)));
    unsigned char player[16] __attribute__((aligned(16))) = {0};
    unsigned char request[12] __attribute__((aligned(16))) = {'A', 'F', 'C', 'L', 0, 0, 0, 0, 0, 0, 0, 240};
    __UINTPTR_TYPE__ h = (__UINTPTR_TYPE__)header, s = (__UINTPTR_TYPE__)split;
    unsigned int i;
    if (!header || !split || !body || !footer || (s & 3u)) return;
    if (af_classic_mask(number) != ~0u && h <= ~(__UINTPTR_TYPE__)0-122u
            && (__UINTPTR_TYPE__)body == h+10u && (__UINTPTR_TYPE__)footer == h+106u
            && (s < h ? h-s >= 4u : s-h >= 122u)) {
        request[4] = (unsigned char)(number >> 8);
        request[5] = (unsigned char)number;
        if (af_npc_mail_load(stage, player, request, 0, 0, 0)) {
            /* Contiguous text does not establish ownership of the preceding
             * metadata. Publish only the proven 122-byte text area and the
             * separately supplied split output, never header-42 or a Mail_c.
             */
            for (i = 0; i < 122u; ++i) header[i] = stage[42u+i];
            *split = 128u;
            return;
        }
    }
    /* Preserve the original separate-buffer API and valid native behaviour on
     * allocation/validation failure. No partially generated snapshot escapes.
     */
    native_sized(header, 10u, split, footer, 16u, body, number);
}

int af_classic_install(void) {
    if (native_entry[0] != 0x27BDFFE8u || native_entry[1] != 0xAFA60020u) return 0;
    if (!af_accent_font_install()) return 0;
    native_entry[0] = 0x08000000u | (((unsigned int)(__UINTPTR_TYPE__)af_classic_load >> 2) & 0x03FFFFFFu);
    native_entry[1] = 0;
    writeback((void *)native_entry, 8u);
    invalidate((void *)native_entry, 8u);
    return 1;
}
