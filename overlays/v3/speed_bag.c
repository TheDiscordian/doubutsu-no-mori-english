/* Native callbacks for the converted GAFE01-r0 speed bag.
 * The sound entry is an explicit link dependency, not the donor's numeric ID.
 * No actor state, model data, or frame storage is shared between instances.
 */
typedef unsigned char u8;
typedef unsigned int u32;
typedef signed short s16;

typedef union { float f; u32 bits; } FloatWord;
typedef struct {
    float start, end, duration;
    FloatWord speed, current;
    int mode;
    u8 rest[0x58];
} Keyframe;

typedef struct {
    u8 before_position[8];
    float position[3];
    u8 before_state[0x3C - 0x14];
    s16 state;
    u8 before_changed[0x12D - 0x3E];
    u8 changed;
    u8 before_keyframe[6];
    Keyframe keyframe;
    s16 joint[9][3], morph[9][3];
    u8 matrices[2][10][64];
    u8 tail[0x30];
} Furniture;

#define CHECK_OFFSET(field, at) \
    _Static_assert(__builtin_offsetof(Furniture, field) == (at), #field)
CHECK_OFFSET(position, 8);
CHECK_OFFSET(state, 0x3C);
CHECK_OFFSET(changed, 0x12D);
CHECK_OFFSET(keyframe, 0x134);
CHECK_OFFSET(joint, 0x1A4);
CHECK_OFFSET(morph, 0x1DA);
CHECK_OFFSET(matrices, 0x210);
_Static_assert(sizeof(Furniture) == 0x740, "native furniture stride");
_Static_assert(sizeof(Keyframe) == 0x70, "native keyframe size");

extern void cKF_SkeletonInfo_R_ct(Keyframe*, void*, void*, void*, void*);
extern void cKF_SkeletonInfo_R_init_standard_stop(Keyframe*, void*, void*);
extern int cKF_SkeletonInfo_R_play(Keyframe*);
extern void cKF_Si3_draw_R_SV(void*, Keyframe*, void*, void*, void*, void*);
extern void* Lib_SegmentedToVirtual(void*);
extern void* _Matrix_to_Mtx_new(void*);
extern void af_v3_speed_bag_sound(void* position);

void af_v3_speed_bag_ct(Furniture* actor, u8* data) {
    Keyframe* key = &actor->keyframe;
    void* skeleton = Lib_SegmentedToVirtual((void*)0x06000E84);
    void* animation = Lib_SegmentedToVirtual((void*)0x06000E58);
    (void)data;
    cKF_SkeletonInfo_R_ct(key, skeleton, animation, actor->joint, actor->morph);
    cKF_SkeletonInfo_R_init_standard_stop(key, animation, (void*)0);
    cKF_SkeletonInfo_R_play(key);
    key->speed.bits = 0;
    actor->changed = 0;
}

void af_v3_speed_bag_mv(Furniture* actor, void* room, void* game, u8* data) {
    Keyframe* key = &actor->keyframe;
    (void)room; (void)game; (void)data;
    if (cKF_SkeletonInfo_R_play(key) != 1 &&
            (key->speed.bits & 0x7FFFFFFF) != 0) {
        cKF_SkeletonInfo_R_play(key);
        key->speed.bits = 0x3F000000; /* 0.5, without a relocatable constant pool */
    }
    if (actor->changed) {
        /* N64 birth, bye, death, and birth-wait; GC enum values differ. */
        if (actor->state != 5 && actor->state != 6 &&
                actor->state != 13 && actor->state != 15) {
            af_v3_speed_bag_sound(actor->position);
        }
        key->current.bits = 0x3F800000; /* frame 1 */
        cKF_SkeletonInfo_R_play(key);
        key->speed.bits = 0x3F000000;
    }
    /* The room owner clears changed after all furniture callbacks. */
}

void af_v3_speed_bag_dw(Furniture* actor, void* room, void* game, u8* data) {
    u8* gfx = *(u8**)game;
    u32 frame = *(u32*)((u8*)game + 0xA0);
    u32** head = (u32**)(gfx + 0x298);
    u32* command = *head;
    (void)room; (void)data;
    *head = command + 2;
    command[0] = 0xDA380003; /* native F3DEX2 model-view LOAD, NOPUSH */
    command[1] = (u32)_Matrix_to_Mtx_new(gfx);
    cKF_Si3_draw_R_SV(game, &actor->keyframe,
                     actor->matrices[frame & 1], (void*)0, (void*)0, (void*)0);
}
