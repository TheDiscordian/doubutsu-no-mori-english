#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/villager.c"

struct Villager af_v3_villagers[20];
int af_v3_ready = 1, af_v3_name_enabled = 1, af_v3_phrase_enabled = 1;
static u8 actor[0x180], animal[0x540];
static u8 *actor_animal = animal;
static u32 old_npc;
static int calls;
u8 af_v3_land_info[10];
u32 af_v3_old_looks(u32 npc) { assert(npc >= 0xE000 && npc < 0xE0DA); return 3; }
void af_v3_old_defaults(u8 *out, u32 npc, const u8 *data) {
    assert(out && data && npc >= 0xE000 && npc < 0xE0DA); ++calls;
}
void af_v3_old_info(u8 *out, u32 npc, u32 looks, const u8 *data) {
    assert(out && data && npc >= 0xE000 && npc < 0xE0DA && looks < 256); ++calls;
}
void af_v3_old_index(u8 *out, int index) { assert(out && index >= 0 && index < 216); ++calls; }
u8 *af_v3_animal_at(const u8 *value) { assert(value == actor); return actor_animal; }
int af_v3_old_name(u8 *out, u32 capacity, u32 npc) {
    assert(out && capacity >= 8); ++calls;
    if (npc == 0xE000 || npc == 0xD008) { memcpy(out, "Native  ", 8); return 1; }
    return 0;
}
int af_v3_old_phrase(u8 *out, u32 capacity, u32 npc, const u8 *saved) {
    assert(out && capacity >= 10 && saved); old_npc = npc; ++calls;
    if (!memcmp(saved, "old!", 4) || (npc == 0xE014 && !memcmp(saved, "\xD0\x90  ", 4))) {
        memcpy(out, "Original  ", 10); return 1;
    }
    return 0;
}
void af_v3_old_short_name(u8 *out, u32 npc) {
    assert(out && npc < 218); old_npc = npc; ++calls; memcpy(out, "Native", 6);
}
void af_v3_old_reset(const u8 *value) { assert(value == actor); ++calls; }
void af_v3_old_actor_name(u8 *out, const u8 *value) {
    assert(out && (!value || value == actor)); ++calls; memcpy(out, "Fallback", 8);
}
static void reset(void) {
    memset(af_v3_villagers, 0, sizeof(af_v3_villagers));
    for (int i = 0; i < 2; ++i) {
        int slot = i ? 19 : 16;
        struct Villager *row = af_v3_villagers + slot;
        row->actor = 0xE0DA + slot; row->present = 1;
        memcpy(row->name, i ? "Punchy  " : "Cheri   ", 8);
        memcpy(row->phrase, i ? "mrmpht    " : "tralala   ", 10);
        row->key[0] = 0xFE; row->key[1] = 0xF3; row->key[2] = row->actor; row->key[3] = 0x20;
    }
    memset(actor, 0, sizeof(actor)); actor[2] = 3;
    memset(animal, 0xA5, sizeof(animal)); animal[0] = 0xE0; animal[1] = 0xEA;
    actor_animal = animal; af_v3_ready = af_v3_name_enabled = af_v3_phrase_enabled = 1;
    calls = 0; old_npc = 0;
}
int main(void) {
    u8 buffer[32], before[sizeof(animal)], *out = buffer + 1;
    reset(); memset(buffer, 0xA5, sizeof(buffer));
    assert(af_v3_load_name(out, 8, 0xE0EA) == 1 && !memcmp(out, "Cheri   ", 8));
    assert(af_v3_load_name(out, 8, 0xE0ED) == 1 && !memcmp(out, "Punchy  ", 8));
    assert(!calls && buffer[0] == 0xA5 && buffer[9] == 0xA5);
    const u32 missing[] = {0xE0D8, 0xE0D9, 0xE0DA, 0xE0EE, 0x100E0EA, 0xFFFFFFFF};
    for (u32 i = 0; i < sizeof(missing) / sizeof(*missing); ++i) {
        assert(!af_v3_load_name(out, 8, missing[i]) && !memcmp(out, "Punchy  ", 8));
    }
    assert(!af_v3_load_name(0, 8, 0xE0EA));
    assert(!af_v3_load_name(out, 7, 0xE0EA));
    af_v3_name_enabled = 0; assert(!af_v3_load_name(out, 8, 0xE0EA)); af_v3_name_enabled = 1;
    af_v3_ready = 0; assert(!af_v3_load_name(out, 8, 0xE0EA)); af_v3_ready = 1;
    af_v3_villagers[16].actor = 0xE0ED; assert(!af_v3_load_name(out, 8, 0xE0EA));
    reset(); assert(af_v3_load_name(out, 8, 0xD008) && calls == 1);
    af_v3_actor_name(out, actor); assert(!memcmp(out, "Cheri   ", 8));
    actor[2] = 2; af_v3_actor_name(out, actor); assert(!memcmp(out, "Fallback", 8));
    actor[2] = 3; actor_animal = 0; af_v3_actor_name(out, actor); assert(!memcmp(out, "Fallback", 8));
    reset(); memset(buffer, 0xA5, sizeof(buffer));
    af_v3_short_name(out, 0x1234EA); assert(!memcmp(out, "Cheri ", 6) && buffer[7] == 0xA5 && !calls);
    af_v3_short_name(out, 217); assert(!memcmp(out, "Native", 6) && old_npc == 217 && calls == 1);
    af_v3_short_name(out, 218); af_v3_short_name(out, 255); af_v3_short_name(0, 0);
    assert(calls == 1 && !memcmp(out, "Native", 6));
    reset(); memset(buffer, 0xA5, sizeof(buffer)); memcpy(before, animal, sizeof(before));
    af_v3_reset_phrase(actor);
    memcpy(before + 0x4E5, "\xFE\xF3\xEA ", 4);
    assert(!memcmp(before, animal, sizeof(animal)) && !calls);
    assert(af_v3_load_phrase(out, 10, 0xE0EA, animal + 0x4E5) && !memcmp(out, "tralala   ", 10));
    assert(af_v3_load_phrase(out, 10, 0xE000, animal + 0x4E5) && !memcmp(out, "tralala   ", 10));
    assert(af_v3_load_phrase(out, 10, 0xE0EA, af_v3_villagers[19].key) && !memcmp(out, "mrmpht    ", 10));
    assert(buffer[0] == 0xA5 && buffer[11] == 0xA5 && !calls);
    assert(af_v3_load_phrase(out, 10, 0xE0EA, (const u8 *)"old!") && old_npc == 0xE000);
    assert(af_v3_load_phrase(out, 10, 0xE0EA, (const u8 *)"\xD0\x90  ") && old_npc == 0xE014);
    assert(!af_v3_load_phrase(out, 10, 0xE0EA, (const u8 *)"Yup!") && !memcmp(out, "Original  ", 10));
    assert(!af_v3_load_phrase(out, 9, 0xE0EA, animal + 0x4E5));
    assert(!af_v3_load_phrase(out, 10, 0xD008, animal + 0x4E5));
    assert(!af_v3_load_phrase(out, 10, 0xE0DA, animal + 0x4E5));
    assert(!af_v3_load_phrase(0, 10, 0xE0EA, animal + 0x4E5));
    assert(!af_v3_load_phrase(out, 10, 0xE0EA, 0));
    af_v3_phrase_enabled = 0; assert(!af_v3_load_phrase(out, 10, 0xE0EA, animal + 0x4E5));
    reset(); animal[1] = 0xDA; memcpy(before, animal, sizeof(before)); af_v3_reset_phrase(actor);
    assert(!calls && !memcmp(before, animal, sizeof(before)));
    animal[1] = 0; af_v3_reset_phrase(actor); assert(calls == 1);
    actor[2] = 2; af_v3_reset_phrase(actor); af_v3_reset_phrase(0); assert(calls == 1);
    reset(); calls = 0;
    af_v3_villagers[16].personality = 1; af_v3_villagers[19].personality = 2;
    af_v3_villagers[16].native_cloth = 0x2498;
    memcpy(af_v3_land_info, "Forest!!\x12\x34", 10);
    memcpy(before, animal, sizeof(before));
    before[0] = 0xE0; before[1] = 0xEA; before[0xB] = 1;
    memcpy(before + 2, "\x12\x34" "Forest", 8);
    memcpy(before + 0x4E5, "\xFE\xF3\xEA ", 4);
    before[0x520] = 0x24; before[0x521] = 0x98;
    for (int route = 0; route < 3; ++route) {
        memset(animal, 0xA5, sizeof(animal));
        if (route == 0) af_v3_set_defaults(animal, 0x1234E0EA, NULL);
        if (route == 1) af_v3_set_info(animal, 0xE0EA, 255, NULL);
        if (route == 2) af_v3_set_index(animal, 234);
        assert(!memcmp(before, animal, sizeof(before)) && !calls);
    }
    assert(af_v3_get_looks(0x1234E0EA) == 1 && af_v3_get_looks(0xE0ED) == 2);
    assert(af_v3_get_looks(0xE0D9) == 3 && af_v3_get_looks(0xD008) == 0);
    assert(af_v3_get_looks(0xE0DA) == 0 && af_v3_get_looks(0xEFFF) == 0);
    for (u32 i = 0; i < 2; ++i) {
        u32 npc = i ? 0xE0ED : 0xE0DA;
        af_v3_set_defaults(animal, npc, animal);
        af_v3_set_info(animal, npc, 0, animal);
        af_v3_set_index(animal, npc & 255);
        assert(!memcmp(before, animal, sizeof(before)) && !calls);
    }
    af_v3_ready = 0;
    af_v3_set_info(animal, 0xE0EA, 1, animal);
    assert(!memcmp(before, animal, sizeof(before)) && !calls && af_v3_get_looks(0xE0EA) == 0);
    af_v3_ready = 1;
    af_v3_set_defaults(NULL, 0xE0EA, animal);
    af_v3_set_info(NULL, 0xE0EA, 1, animal);
    af_v3_set_index(NULL, 234);
    af_v3_set_defaults(animal, 0xE000, NULL);
    af_v3_set_info(animal, 0xE000, 0, NULL);
    af_v3_set_index(animal, -1); af_v3_set_index(animal, 216); af_v3_set_index(animal, 238);
    assert(!calls && !memcmp(before, animal, sizeof(before)));
    af_v3_set_defaults(animal, 0xE0D9, animal);
    af_v3_set_info(animal, 0xE000, 0x123401, animal);
    af_v3_set_index(animal, 215);
    assert(calls == 3);
    puts("V3 names, borrowed/default phrases, initial defaults, personality, native fallback, and guards pass");
    return 0;
}
