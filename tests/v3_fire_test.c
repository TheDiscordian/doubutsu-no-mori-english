#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/fire.c"

static _Alignas(32) u8 opaque[4096], translucent[1024], model[8000];
static FireGfx graphics;
static FireGame game;
static Fire actors[2];
static unsigned kind, stage, sounds, evaluations, draws, flushes, converted;
static u32 expected_frame;
static void *expected_matrices;

void *Lib_SegmentedToVirtual(void *address) { return address; }
void cKF_SkeletonInfo_R_ct(Keyframe *key, void *rig, void *animation, void *joint, void *morph) {
    assert(stage++ == 0 && key == &actors[kind].keyframe);
    assert((uptr)rig == (kind ? 0x06001780u : 0x06001F38u));
    assert((uptr)animation == (kind ? 0x06001748u : 0x06001F00u));
    assert(joint == actors[kind].joint && morph == actors[kind].morph);
    memset(key, 0, sizeof *key);
}
void cKF_SkeletonInfo_R_init_standard_repeat(Keyframe *key, void *animation, void *unused) {
    assert(stage++ == 1 && key == &actors[kind].keyframe && !unused);
    assert((uptr)animation == (kind ? 0x06001748u : 0x06001F00u));
}
int cKF_SkeletonInfo_R_play(Keyframe *key) {
    assert(key == &actors[kind].keyframe);
    if (stage == 2) { assert(key->speed.f == 0.5f); ++stage; }
    ++evaluations; return 0;
}
void sAdo_OngenPos(u32 identity, u8 sound, float *position) {
    assert(identity == (u32)(uptr)&actors[kind]);
    assert(sound == (kind ? 0x5C : 0x5D) && position == actors[kind].position);
    ++sounds;
}
void Matrix_Position_Zero(float *position) {
    assert(stage++ == 10); position[0] = 7; position[1] = 11; position[2] = 13;
}
void Matrix_push(void) { assert(stage++ == 11); }
void Matrix_translate(float x, float y, float z, u8 mode) {
    assert(stage++ == 12 && !mode && x == 7 && y == 11 && z == 13);
}
void Matrix_mult(float *matrix, int mode) { assert(stage++ == 13 && matrix == game.billboard && mode == 1); }
void Matrix_RotateY(s16 angle, int mode) { assert(stage++ == 14 && angle == 0x4000 && mode == 1); }
void Matrix_scale(float x, float y, float z, u8 mode) {
    assert(stage++ == 15 && mode == 1);
    assert(x == actors[kind].scale[0] * 0.01f && y == actors[kind].scale[1] * 0.01f
           && z == actors[kind].scale[2] * 0.01f);
}
void *_Matrix_to_Mtx(void *matrix) {
    assert(!((uptr)matrix & 15));
    if (stage == 16) { assert(matrix == graphics.opa_tail + 64); ++stage; }
    else assert(stage == 3 && matrix == graphics.opa_tail);
    memset(matrix, stage == 17 ? 0xBB : 0xAA, 64); ++converted; return matrix;
}
void Matrix_pull(void) { assert(stage++ == 17); }
void osWritebackDCache(void *address, int bytes) {
    assert(stage == 18);
    if (bytes == 168) assert(address == graphics.opa_tail);
    else assert(bytes == 128 && address == expected_matrices);
    ++flushes;
}
void cKF_Si3_draw_R_SV(FireGame *g, Keyframe *key, void *matrices,
        JointCallback before, JointCallback after, void *arg) {
    assert(g == &game && key == &actors[kind].keyframe && matrices == expected_matrices);
    /* Exercise the native three-joint callback order and both display heads.
     * Native traversal itself is pinned separately, not reimplemented as proof. */
    *graphics.opa_head++ = (Command){0xDB060034, (u32)(uptr)matrices};
    *graphics.xlu_head++ = (Command){0xDB060034, (u32)(uptr)matrices};
    for (int j = 0; j < 3; ++j) {
        Command *shape = j == 1 ? 0 : (Command*)(uptr)(j ? 0x06001660 : 0x06001070);
        Command *original = shape;
        u8 flags = kind && j == 2;
        s16 rotation[3] = {1, 2, 3}; float translation[3] = {4, 5, 6};
        assert(before(g, key, j, &shape, &flags, arg, rotation, translation) == 1);
        assert(shape == (j == 2 ? 0 : original) && flags == (kind && j == 2));
        assert(rotation[0] == 1 && rotation[1] == 2 && rotation[2] == 3);
        assert(translation[0] == 4 && translation[1] == 5 && translation[2] == 6);
        if (original) {
            *graphics.opa_head++ = (Command){0xDA380003, (u32)(uptr)matrices + (j ? 64 : 0)};
            if (shape) *graphics.opa_head++ = (Command){0xDE000000, (u32)(uptr)shape};
        }
        if (j == 2) stage = 10;
        assert(after(g, key, j, &shape, &flags, arg, rotation, translation) == 1);
    }
    memset(matrices, 0xCC, 128); ++draws;
}
static void reset_arena(void) {
    memset(opaque, 0xA5, sizeof opaque); memset(translucent, 0xA5, sizeof translucent);
    graphics.opa_head = (Command*)(opaque + 32); graphics.opa_tail = opaque + sizeof opaque - 32;
    graphics.xlu_head = (Command*)(translucent + 32); graphics.xlu_tail = translucent + sizeof translucent - 32;
    game.gfx = &graphics;
}
static void draw_one(void *room) {
    Command *opa = graphics.opa_head, *xlu = graphics.xlu_head;
    u8 *tail = graphics.opa_tail;
    Fire old = actors[kind];
    expected_frame = room ? game.play_frame : game.frame;
    expected_matrices = actors[kind].matrices[game.frame & 1];
    stage = 3; unsigned n = draws, f = flushes, m = converted;
    if (kind) af_v3_bonfire_dw(actors + kind, room, &game, model);
    else af_v3_campfire_dw(actors + kind, room, &game, model);
    assert(draws == n + 1 && flushes == f + 2 && converted == m + 2);
    assert(graphics.opa_head == opa + 5 && graphics.xlu_head == xlu + 5
           && (uptr)graphics.opa_tail == (((uptr)tail - 176) & ~(uptr)15));
    assert(opa[0].a == 0xDA380003 && opa[0].b == (u32)(uptr)graphics.opa_tail);
    assert(xlu[0].a == opa[0].a && xlu[0].b == opa[0].b);
    assert(xlu[1].a == 0xDB060024 && xlu[1].b == (u32)(uptr)(graphics.opa_tail + 128));
    assert(xlu[3].a == 0xDA380003 && xlu[3].b == (u32)(uptr)(graphics.opa_tail + 64));
    assert(xlu[4].a == 0xDE000000 && xlu[4].b == (kind ? 0x06001660u : 0x06001E20u));
    const Command *scroll = (const Command*)(graphics.opa_tail + 128);
    /* Independent signed rational reference, including negative odd rounding. */
    long long donor_y = -(long long)expected_frame * (kind ? 6 : 12);
    u32 sy = (u32)((donor_y - 3) / 4) & 4095;
    u32 sx = kind ? (u32)(-(long long)expected_frame) & 4095 : 0;
    assert(scroll[0].a == 0xE8000000 && !scroll[0].b && scroll[2].a == 0xE8000000 && !scroll[2].b);
    assert(scroll[1].a == (0xF2000000 | sy));
    assert(scroll[1].b == ((124u << 12) | ((sy + 252u) & 4095)));
    assert(scroll[3].a == (0xF2000000 | sx << 12));
    assert(scroll[3].b == (0x01000000 | ((sx + (kind ? 252 : 124)) & 4095) << 12 | 124));
    assert(scroll[4].a == 0xDF000000 && !scroll[4].b);
    memset(old.matrices[game.frame & 1], 0xCC, 128);
    assert(!memcmp(&old, actors + kind, sizeof old));
}
int main(void) {
    for (kind = 0; kind < 2; ++kind) {
        memset(actors + kind, 0xA5, sizeof(Fire)); Fire old = actors[kind]; stage = 0;
        if (kind) af_v3_bonfire_ct(actors + kind, model); else af_v3_campfire_ct(actors + kind, model);
        assert(stage == 3); old.keyframe = actors[kind].keyframe;
        assert(!memcmp(&old, actors + kind, sizeof old));
        for (int state = 0; state < 18; ++state) {
            actors[kind].state = state; actors[kind].keyframe.speed.f = 1;
            old = actors[kind]; unsigned n = sounds, e = evaluations;
            if (kind) af_v3_bonfire_mv(actors + kind, 0, &game, model);
            else af_v3_campfire_mv(actors + kind, 0, &game, model);
            assert(evaluations == e + 1 && actors[kind].keyframe.speed.f == 0.5f);
            assert(sounds == n + (state != 5 && state != 6 && state != 13 && state != 15));
            old.keyframe = actors[kind].keyframe; assert(!memcmp(&old, actors + kind, sizeof old));
        }
        actors[kind].scale[0] = 1.5f; actors[kind].scale[1] = 2.5f; actors[kind].scale[2] = 3.5f;
        const u32 frames[] = {0, 1, 2, 3, 63, 64, 127, 128, 1023, 1024, 5461, 0x7FFFFFFF, 0xFFFFFFFE, 0xFFFFFFFF};
        for (unsigned i = 0; i < sizeof frames / sizeof *frames; ++i) {
            reset_arena(); game.frame = frames[i]; game.play_frame = frames[i] ^ 0xFFFFFFFFu;
            draw_one(0); u8 retained[176]; u8 *first = graphics.opa_tail; memcpy(retained, first, sizeof retained);
            draw_one(actors); assert(!memcmp(retained, first, sizeof retained));
        }
        for (unsigned opa_room = 0; opa_room <= 240; ++opa_room) {
            for (unsigned xlu_room = 32; xlu_room <= 48; ++xlu_room) {
                reset_arena(); graphics.opa_tail = opaque + 32 + opa_room;
                graphics.xlu_tail = translucent + 32 + xlu_room;
                uptr allocation = opa_room >= 176 ? ((uptr)graphics.opa_tail - 176) & ~(uptr)15 : 0;
                if (opa_room >= 216 && allocation >= (uptr)graphics.opa_head + 40 && xlu_room >= 40) {
                    draw_one(0); continue;
                }
                FireGfx before = graphics; unsigned n = draws, f = flushes;
                if (kind) af_v3_bonfire_dw(actors + kind, 0, &game, model);
                else af_v3_campfire_dw(actors + kind, 0, &game, model);
                assert(!memcmp(&graphics, &before, sizeof graphics) && draws == n && flushes == f);
                for (unsigned j = 0; j < sizeof opaque; ++j) assert(opaque[j] == 0xA5);
                for (unsigned j = 0; j < sizeof translucent; ++j) assert(translucent[j] == 0xA5);
            }
        }
    }
    puts("Fire rig callbacks, sound identities, billboard order, scroll phases, frame lifetime, and arena bounds pass");
}
