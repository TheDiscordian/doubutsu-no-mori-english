#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/campsite_exterior.c"

u8 campsite_actor_packet[4096], native_descriptors[201 * 32], selected_furniture[1024 * 80];
volatile int native_seconds, native_scene;
u8 native_exit[20];
Tent *af_test_door;
static Tent actor, player;
static _Alignas(16) u8 game[0x2000], opaque[2048], shadow_arena[256];
static u8 exterior[6960], shadow_art[800];
static Graphics graphics;
static int allocation_fail, dma_fail, dma_calls, deleted, freed, heights, writes, keeps, deposits;
static int snowman, missing_fg, unburied, requests, entered, sounds, make_calls, original_calls;
static int blocks_differ, demo, no_player, matrix_calls, flushes, opaque_calls, shadow_calls;
static u16 ground_item, last_kept, last_fg;
static Position last_position, requested;
static Height actual_heights[9];
static Position actual_positions[9];

void *native_malloc(u32 size) { assert(size == 0x1E60); return allocation_fail ? NULL : malloc(size); }
void native_free(void *p) { assert(p); ++freed; free(p); }
int native_dma(void *p, u32 address, u32 size) {
    ++dma_calls;
    assert((address == 0x0248A000 && size == sizeof exterior) ||
           (address == 0x0248C000 && size == sizeof shadow_art));
    if (dma_calls == dma_fail) return -1;
    memcpy(p, address == 0x0248A000 ? exterior : shadow_art, size); return 0;
}
void native_delete(void *p) { assert(p == &actor); ++deleted; }
int native_fg(u16 item, Position p, int mode) {
    assert(mode == 0 || mode == 1); last_fg = item; last_position = p; ++writes; return 1;
}
u16 *native_get_fg(Position p) { assert(p.z == 280); return missing_fg ? NULL : &ground_item; }
int native_clear_snowman(u16 *p) { assert(p == &ground_item); return snowman; }
u16 native_unbury(u16 item) { assert(item == ground_item); ++unburied; return 0x33A4; }
void native_keep(u16 item) { last_kept = item; ++keeps; }
void native_deposit_off(Position p) { assert(p.z == 280); ++deposits; }
void native_height(Position p, Height h, const char *file, int line) {
    assert(heights < 9 && !strcmp(file, "v3_campsite") && line == 1);
    actual_heights[heights] = h; actual_positions[heights++] = p;
}
float native_ground(Position p, float add) { (void)p; assert(add == 0); return 12; }
Tent *native_player(void *g) { assert(g == game); return no_player ? NULL : &player; }
int native_block(int *x, int *z, Position p) { *x = blocks_differ && p.z != 200; *z = 0; return 1; }
int native_demo(int kind, void *p) { assert(p == &player); return demo == kind; }
void native_request_door(void *g, Position *p, s16 angle, int kind, Tent *a) {
    assert(g == game && angle == -32768 && kind == 1 && a == &actor); requested = *p; ++requests;
}
int native_goto(void *g, void *door, int mode) {
    assert(g == game && door == campsite_actor_packet + 0x80 && mode == 1); ++entered; return 1;
}
void native_bgm(int id) { assert(id == 0x028A); ++sounds; }
Tent *native_make(void *info, void *g, s16 id, float x, float y, float z, s16 rx, s16 ry, s16 rz,
                  signed char bx, signed char bz, s16 arg, u16 fg, s16 params, signed char npc, int bank) {
    assert(info == game + 0x1C78 && g == game && id == 0xCA && x == 100 && y == 12 && z == 200);
    assert(!rx && !ry && !rz && bx == 2 && bz == 3 && arg == -1 && fg == 0x5849
           && params == 7 && npc == -1 && bank == -1);
    ++make_calls; return &actor;
}
void *af_test_original_setup(void *g, u16 fg, float x, float z, s16 p) {
    assert(g == game && fg == 0x5829 && x == 100 && z == 200 && p == 7); ++original_calls; return &player;
}
void native_matrix(void *p) { assert(p == graphics.tail); memset(p, 0x5A, 64); ++matrix_calls; }
void native_writeback(void *p, int bytes) { assert(p == graphics.tail && bytes == 528); ++flushes; }
void native_opaque_state(Graphics *g) { assert(g == &graphics); *g->head++ = (Command){0xDE000000,1}; ++opaque_calls; }
void native_shadow_state(Graphics *g) { assert(g == &graphics); *g->shadow++ = (Command){0xDE000000,2}; ++shadow_calls; }
static void reset(void) {
    memset(&actor, 0, sizeof actor); memset(&player, 0, sizeof player); memset(game, 0, sizeof game);
    *(Position*)((u8*)&actor + 0x28) = (Position){100,12,200};
    *(Position*)((u8*)&actor + 0xC) = (Position){100,12,200};
    *(Position*)((u8*)&player + 0x28) = (Position){100,19,245};
    write16((u8*)&player + 0xDE, 0x8000); native_seconds = 0; native_scene = 0;
    allocation_fail = dma_fail = dma_calls = deleted = freed = heights = writes = keeps = deposits = 0;
    snowman = missing_fg = unburied = requests = entered = sounds = make_calls = original_calls = 0;
    blocks_differ = demo = no_player = matrix_calls = flushes = opaque_calls = shadow_calls = 0;
    af_test_door = NULL; ground_item = 0x335C;
}
static void arena(void) {
    memset(opaque, 0xA5, sizeof opaque); memset(shadow_arena, 0xA5, sizeof shadow_arena);
    graphics.head = (Command*)(opaque + 16); graphics.tail = opaque + sizeof opaque - 16;
    graphics.shadow = (Command*)(shadow_arena + 16); graphics.shadow_tail = shadow_arena + sizeof shadow_arena - 16;
    *(Graphics**)game = &graphics;
    game[0x1C3A] = 11; game[0x1C3B] = 22; game[0x1C3C] = 33; game[0x1C54] = 44;
    *(float*)(game + 0x1C50) = -0.25f;
}
static void load(const char *path, void *out, size_t size) {
    FILE *f = fopen(path, "rb"); assert(f); assert(fread(out, 1, size, f) == size);
    assert(fgetc(f) == EOF); fclose(f);
}
int main(int argc, char **argv) {
    assert(argc == 4); load(argv[1], campsite_actor_packet, 0x1F0);
    load(argv[2], exterior, sizeof exterior); load(argv[3], shadow_art, sizeof shadow_art);
    for (int i = 0; i < 201; ++i) assert(af_v3_campsite_actor_descriptor(i) == native_descriptors + i * 32);
    assert(af_v3_campsite_actor_descriptor(0xCA) == campsite_actor_packet + 0x20);
    for (int fail = 1; fail <= 3; ++fail) {
        reset(); allocation_fail = fail == 1; dma_fail = fail - 1;
        af_v3_campsite_exterior_ct(&actor, game);
        assert(!actor.assets && deleted == 1 && !writes && !heights && freed == (fail != 1));
        af_v3_campsite_exterior_dt(&actor, game); assert(freed == (fail != 1));
    }
    const u16 items[] = {0x335C,0x2A,0x42,0x5C,0};
    for (unsigned i = 0; i < sizeof items / sizeof *items; ++i) {
        reset(); ground_item = items[i]; snowman = i == 4;
        af_v3_campsite_exterior_ct(&actor, game);
        assert(actor.assets && dma_calls == 2 && heights == 9 && writes == 1 && actor.fade == 1);
        assert(!memcmp(actor.assets, exterior, sizeof exterior));
        assert(!memcmp(actor.assets + 0x1B30, shadow_art, sizeof shadow_art));
        for (int b = 0x1E50; b < 0x1E60; ++b) assert(actor.assets[b] == 0xCD);
        assert(keeps == !snowman && deposits == !snowman && unburied == (i >= 1 && i <= 3));
        if (!snowman) assert(last_kept == (i ? 0x33A4 : 0x335C));
        for (int cell = 0; cell < 9; ++cell) {
            assert(!memcmp(actual_heights + cell, campsite_actor_packet + 0xA0 + cell * 7, 7));
            assert(actual_positions[cell].x == 100 + (cell % 3 - 1) * 40
                   && actual_positions[cell].y == 12 && actual_positions[cell].z == 200 + (cell / 3 - 1) * 40);
        }
        af_v3_campsite_exterior_dt(&actor, game); assert(!actor.assets && freed == 1 && last_fg == 0);
        af_v3_campsite_exterior_dt(&actor, game); assert(freed == 1);
    }
    reset(); missing_fg = 1; native_seconds = 18000; af_v3_campsite_exterior_ct(&actor, game);
    assert(!writes && !keeps && !deposits && actor.fade == 0);
    game[0xE4] = 2; game[0xE5] = 3;
    assert(af_v3_campsite_structure_setup(game,0x5829,100,200,7) == &player && original_calls == 1);
    assert(!af_v3_campsite_structure_setup(game,0x5849,100,200,7) && !make_calls);
    u8 *row = selected_furniture + ((0x335C - 0x3000) / 4) * 80;
    write16(row + 2, 0x335C); row[7] = 1;
    assert(af_v3_campsite_structure_setup(game,0x5849,100,200,7) == &actor && make_calls == 1 && last_fg == 0xFFFF);
    af_v3_campsite_exterior_init(&actor, game); assert(last_fg == 0xF127 && requests == 1);
    assert(requested.x == 100 && requested.y == 19 && requested.z == 268);
    native_seconds = 64800;
    for (int i = 0; i < 60; ++i) af_v3_campsite_exterior_mv(&actor, game);
    assert(actor.fade == 1); native_seconds = 64799;
    for (int i = 0; i < 60; ++i) af_v3_campsite_exterior_mv(&actor, game);
    assert(actor.fade == 0);
    for (int i = 0; i < 2; ++i) {
        write16((u8*)&player + 0xDE, i ? 0xA000 : 0x6000);
        int before = requests; af_v3_campsite_exterior_mv(&actor, game); assert(requests == before);
    }
    af_test_door = &actor; native_scene = 7; memset(native_exit, 0xA5, sizeof native_exit);
    af_v3_campsite_exterior_mv(&actor, game);
    assert(entered == 1 && sounds == 1 && *(u32*)native_exit == 7 && !native_exit[4] && !native_exit[5]);
    assert(read16(native_exit + 6) == 3 && read16(native_exit + 8) == 100
           && read16(native_exit + 10) == 12 && read16(native_exit + 12) == 286
           && read16(native_exit + 14) == 0x5849 && native_exit[16] == 1 && native_exit[17] == 0xA5);
    game[0x1EE3] = 1; af_v3_campsite_exterior_mv(&actor, game); assert(entered == 2 && sounds == 1);
    af_test_door = NULL; blocks_differ = 1; af_v3_campsite_exterior_mv(&actor, game); assert(deleted == 1);
    demo = 1; af_v3_campsite_exterior_mv(&actor, game); assert(deleted == 1);
    demo = 5; af_v3_campsite_exterior_mv(&actor, game); assert(deleted == 1);
    arena(); actor.fade = 1; Command *opa = graphics.head, *sha = graphics.shadow;
    af_v3_campsite_exterior_dw(&actor, game);
    assert(graphics.head == opa + 5 && graphics.shadow == sha + 7 && matrix_calls == 1 && flushes == 1);
    assert(opa[4].a == 0xDE000000 && opa[4].b == 0x060017D0 && sha[6].b == 0x06000260);
    const Command *window = (const Command*)(graphics.tail + 64);
    assert(window[0].a == 0xFA0000FF && window[0].b == 0xFFFF96FF && window[1].a == 0xDF000000);
    assert(sha[5].a == 0xFA00002C && sha[5].b == 0x0B16212C);
    u8 projected[448]; memcpy(projected, shadow_art + 0x80, sizeof projected);
    for (int i = 0; i < 28; ++i) if (shadow_art[0x240+i]) write16(projected + i*16, read16(projected+i*16) - 15);
    assert(!memcmp(graphics.tail + 80, projected, sizeof projected));
    u8 retained[528]; u8 *first = graphics.tail; memcpy(retained, first, sizeof retained);
    af_v3_campsite_exterior_dw(&actor, game); assert(!memcmp(first, retained, sizeof retained));
    for (int kind = 0; kind < 5; ++kind) {
        arena();
        if (kind == 0) graphics.tail = (u8*)graphics.head + 656;
        if (kind == 1) graphics.tail -= 1;
        if (kind == 2) graphics.head = (Command*)((u8*)graphics.head + 4);
        if (kind == 3) graphics.shadow_tail = (u8*)graphics.shadow + 56;
        if (kind == 4) graphics.shadow = (Command*)((u8*)graphics.shadow + 4);
        Graphics before = graphics; int calls = matrix_calls;
        af_v3_campsite_exterior_dw(&actor, game);
        assert(!memcmp(&before, &graphics, sizeof before) && calls == matrix_calls);
    }
    af_v3_campsite_exterior_dt(&actor, game);
    puts("campsite full assets, nine-cell collision, recovery, doors, fades, selection, lifetime, and drawing pass");
}
