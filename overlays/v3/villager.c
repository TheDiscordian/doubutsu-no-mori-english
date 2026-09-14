/* Imported display names and default catchphrases; no roster activation. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
struct Villager {
    u16 actor, cloth;
    u8 personality, umbrella, growth, present;
    u8 name[8], phrase[10], key[4], reserved[2];
};
_Static_assert(sizeof(struct Villager) == 32, "V3 villager metadata row");
#ifdef __mips__
#define records ((const struct Villager *)0x80462C00u)
#define ready (*(volatile const u32 *)0x8019ACD0u == 1u)
#define name_enabled (*(volatile const u32 *)0x8019491Cu == 0x02C00000u)
#define phrase_enabled (*(volatile const u32 *)0x80194920u == 0x02E00000u)
#define old_name ((int (*)(u8 *, u32, u32))0x80462F00u)
#define old_phrase ((int (*)(u8 *, u32, u32, const u8 *))0x80462F10u)
#define old_short_name ((void (*)(u8 *, u32))0x80462F20u)
#define old_reset ((void (*)(const u8 *))0x80462F30u)
/* The original first branch is the null-destination return. Our wrapper guards
 * that itself, then enters the unchanged complete original prologue at +8. */
#define old_actor_name ((void (*)(u8 *, const u8 *))0x80195D28u)
#define animal_at(actor) (*(u8 *const *)((actor) + 0x174))
#else
extern struct Villager af_v3_villagers[20];
extern int af_v3_ready, af_v3_name_enabled, af_v3_phrase_enabled;
extern int af_v3_old_name(u8 *, u32, u32), af_v3_old_phrase(u8 *, u32, u32, const u8 *);
extern void af_v3_old_short_name(u8 *, u32), af_v3_old_reset(const u8 *), af_v3_old_actor_name(u8 *, const u8 *);
extern u8 *af_v3_animal_at(const u8 *);
#define records af_v3_villagers
#define ready af_v3_ready
#define name_enabled af_v3_name_enabled
#define phrase_enabled af_v3_phrase_enabled
#define old_name af_v3_old_name
#define old_phrase af_v3_old_phrase
#define old_short_name af_v3_old_short_name
#define old_reset af_v3_old_reset
#define old_actor_name af_v3_old_actor_name
#define animal_at af_v3_animal_at
#endif

static u32 actor_id(const u8 *data) { return (u32)data[0] * 256u + data[1]; }
static const struct Villager *lookup(u32 actor) {
    const struct Villager *row;
    if (!ready || actor < 0xE0DAu || actor >= 0xE0EEu) return 0;
    row = records + actor - 0xE0DAu;
    return row->actor == actor && row->present == 1 ? row : 0;
}
static void copy(u8 *out, const u8 *in, u32 length) {
    for (u32 i = 0; i < length; ++i) out[i] = in[i];
}

int af_v3_load_name(u8 *destination, u32 capacity, u32 npc) {
    const struct Villager *row;
    if (!destination || capacity < 8 || !name_enabled) return 0;
    row = lookup(npc);
    if (!row) return old_name(destination, capacity, npc);
    copy(destination, row->name, 8);
    return 1;
}

void af_v3_actor_name(u8 *destination, const u8 *actor) {
    const struct Villager *row;
    const u8 *animal;
    if (!destination) return;
    if (name_enabled && actor && actor[2] == 3 && (animal = animal_at(actor))
            && (row = lookup(actor_id(animal)))) {
        copy(destination, row->name, 8);
        return;
    }
    old_actor_name(destination, actor);
}

void af_v3_short_name(u8 *destination, u32 index_argument) {
    u32 index = (u8)index_argument;
    const struct Villager *row;
    if (!destination || index == 255) return;
    if (index < 218) { old_short_name(destination, index); return; }
    row = lookup(0xE000u + index);
    if (row) copy(destination, row->name, 6);
}

int af_v3_load_phrase(u8 *destination, u32 capacity, u32 npc, const u8 *saved) {
    const struct Villager *row, *owner;
    if (!destination || capacity < 10 || !saved || !phrase_enabled) return 0;
    row = lookup(npc);
    if (!row && (npc < 0xE000u || npc >= 0xE0D8u)) return 0;
    /* FE F3 <stable N64 identity byte> 20 is a V3 default reference. It is
     * four ordinary native glyph bytes, never a partial text control command. */
    if (saved[0] == 0xFE && saved[1] == 0xF3 && saved[3] == 0x20
            && (owner = lookup(0xE000u + saved[2]))) {
        copy(destination, owner->phrase, 10);
        return 1;
    }
    if (row) {
        /* Imported borrowers have no original default-key ownership. Preserve
         * V2's canonical Dozer fallback for its sole ambiguous native key. */
        npc = saved[0] == 0xD0 && saved[1] == 0x90 && saved[2] == 0x20 && saved[3] == 0x20
            ? 0xE014u : 0xE000u;
    }
    return old_phrase(destination, capacity, npc, saved);
}

void af_v3_reset_phrase(const u8 *actor) {
    const struct Villager *row;
    u8 *animal;
    u32 npc;
    if (!actor || actor[2] != 3 || !(animal = animal_at(actor))) return;
    npc = actor_id(animal);
    if (npc >= 0xE0DAu && npc < 0xF000u) {
        row = lookup(npc);
        if (row) copy(animal + 0x4E5, row->key, 4);
        return;
    }
    old_reset(actor);
}
