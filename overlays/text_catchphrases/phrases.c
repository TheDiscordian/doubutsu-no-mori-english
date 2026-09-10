/* Display-only policy for the one ambiguous four-byte borrowed default. */
#include "extension.h"
extern void af_get_catchphrase(unsigned char *, const unsigned char *);
extern int af_load_catchphrase(unsigned char *, unsigned int, unsigned int, const unsigned char *);
extern int af_text_names_init(void);
extern void af_writeback(void *, unsigned int);
extern void af_invalidate(void *, unsigned int);

#ifdef __mips__
#define word(at) (*(volatile af_u32 *)(at))
static const unsigned char *animal_data(const unsigned char *actor) {
    return *(const unsigned char *const *)(actor+0x174);
}
#else
extern af_u32 *af_borrowed_test_word(af_u32);
extern const unsigned char *af_borrowed_test_animal(const unsigned char *);
#define word(at) (*af_borrowed_test_word(at))
#define animal_data af_borrowed_test_animal
#endif

void af_borrowed_catchphrase(unsigned char *destination, const unsigned char *actor) {
    const unsigned char *animal, *saved;
    unsigned int npc;
    if (!destination) return;
    af_get_catchphrase(destination, actor);
    if (!actor || actor[2] != 3u || !(animal=animal_data(actor))) return;
    npc = ((unsigned int)animal[0] << 8) | animal[1];
    if (npc < 0xE000u || npc >= 0xE0D8u || npc == 0xE014u || npc == 0xE0C5u) return;
    saved = animal+0x4E5;
    if (saved[0] != 0xD0u || saved[1] != 0x90u || saved[2] != ' ' || saved[3] != ' '
            || destination[0] != saved[0] || destination[1] != saved[1]
            || destination[2] != ' ' || destination[3] != ' ') return;
    /* The saved key cannot identify the donor. Use the first native owner's
       complete GC wording, not a guessed donor. Normal loader guards remain. */
    af_load_catchphrase(destination, 10, 0xE014u, saved);
}

__attribute__((section(".text.entry")))
int af_text_extension_init(void) {
    if (word(0x801953C4u) != 0x0C065487u || word(0x801953C8u) != 0x02C02025u) return 0;
    if (!af_text_names_init()) return 0;
    word(0x801953C4u) = 0x0C000000u | (((af_u32)(__UINTPTR_TYPE__)af_borrowed_catchphrase >> 2) & 0x03FFFFFFu);
    af_writeback((void *)0x801953C4u, 4);
    af_invalidate((void *)0x801953C4u, 4);
    return 1;
}
