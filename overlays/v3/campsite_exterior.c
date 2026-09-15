/* Additive enterable summer tent. Original igloo profiles/assets stay intact. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef signed short s16;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
typedef struct { float x, y, z; } Position;
typedef struct { u8 value[7]; } Height;
typedef struct { u32 a, b; } Command;
typedef struct {
    u8 before_assets[0x2B8];
    u8 *assets;
    u8 before_fade[0x2C8 - 0x2B8 - sizeof(u8*)];
    float fade;
    u8 rest[12];
} Tent;
typedef struct {
    u8 before_opa[0x298];
    Command *head;
    u8 *tail;
    u8 before_shadow[0x2C8 - 0x298 - sizeof(Command*) - sizeof(u8*)];
    Command *shadow;
    u8 *shadow_tail;
} Graphics;
_Static_assert(sizeof(Tent) == 0x2D8, "Original structure actor pool stride");
_Static_assert(__builtin_offsetof(Tent, fade) == 0x2C8, "Tent window fade");
_Static_assert(__builtin_offsetof(Graphics, shadow) == 0x2C8, "Native shadow arena");
extern u8 campsite_actor_packet[4096], native_descriptors[201 * 32], selected_furniture[1024 * 80];
extern volatile int native_seconds, native_scene;
extern u8 native_exit[20];
extern void *native_malloc(u32);
extern void native_free(void*);
extern int native_dma(void*, u32, u32);
extern void native_delete(void*);
extern int native_fg(u16, Position, int);
extern u16 *native_get_fg(Position);
extern int native_clear_snowman(u16*);
extern u16 native_unbury(u16);
extern void native_keep(u16);
extern void native_deposit_off(Position);
extern void native_height(Position, Height, const char*, int);
extern float native_ground(Position, float);
extern Tent *native_player(void*);
extern int native_block(int*, int*, Position);
extern int native_demo(int, void*);
extern void native_request_door(void*, Position*, s16, int, Tent*);
extern int native_goto(void*, void*, int);
extern void native_bgm(int);
extern Tent *native_make(void*, void*, s16, float, float, float, s16, s16, s16,
                         signed char, signed char, s16, u16, s16, signed char, int);
extern void native_matrix(void*);
extern void native_writeback(void*, int);
extern void native_opaque_state(Graphics*);
extern void native_shadow_state(Graphics*);

static u16 read16(const u8 *p) { return ((u16)p[0] << 8) | p[1]; }
static void write16(u8 *p, u16 v) { p[0] = v >> 8; p[1] = v; }
static Position position(Tent *a, int offset) { return *(Position*)((u8*)a + offset); }
static int enabled(void) {
    static const u16 items[] = {0x335C,0x3360,0x3364,0x336C,0x3370,0x339C,0x33A4,0x33A8,0x33AC,0x33B0};
    for (u32 i = 0; i < 10; ++i) {
        const u8 *r = selected_furniture + ((items[i] - 0x3000) / 4) * 80;
        if (read16(r + 2) == items[i] && r[4] == 0 && r[5] == 0 && r[6] == 0 && r[7] == 1) return 1;
    }
    return 0;
}

__attribute__((section(".entry")))
void *af_v3_campsite_actor_descriptor(int id) {
    if (id == 0xCA) return campsite_actor_packet + 0x20;
    /* Preserve the original table and the engine's existing valid-ID callers.
     * C9 remains the native no-demo sentinel, never the new actor identity. */
    return native_descriptors + id * 32;
}

static void reserve(Tent *a, int on) {
    Position p = position(a, 0x28); p.z += 80.0f;
    if (!on) { native_fg(0, p, 1); return; }
    u16 *fg = native_get_fg(p);
    if (!fg) return;
    if (!native_clear_snowman(fg)) {
        if ((*fg >= 0x2A && *fg <= 0x42) || *fg == 0x5C) {
            native_keep(native_unbury(*fg));
            native_fg(0xFFFF, p, 1);
            native_deposit_off(p);
        } else {
            native_deposit_off(p);
            native_keep(*fg);
            native_fg(0xFFFF, p, 1);
        }
    } else native_fg(0xFFFF, p, 1);
}

static int light_on(void) { return native_seconds < 18000 || native_seconds >= 64800; }

void af_v3_campsite_exterior_ct(Tent *a, void *game) {
    (void)game;
    a->assets = native_malloc(0x1E60);
    if (!a->assets) { native_delete(a); return; }
    if (native_dma(a->assets, 0x0248A000, 6960) || native_dma(a->assets + 0x1B30, 0x0248C000, 800)) {
        native_free(a->assets); a->assets = (void*)0; native_delete(a); return;
    }
    for (u32 i = 0x1E50; i < 0x1E60; ++i) a->assets[i] = 0xCD;
    reserve(a, 1);
    const Height *grid = (const Height*)(campsite_actor_packet + 0xA0);
    for (int z = -1; z <= 1; ++z) for (int x = -1; x <= 1; ++x) {
        Position p = position(a, 0x28); p.x += 40.0f * x; p.z += 40.0f * z;
        native_height(p, *grid++, "v3_campsite", 1);
    }
    a->fade = light_on() ? 1.0f : 0.0f;
}

void af_v3_campsite_exterior_dt(Tent *a, void *game) {
    (void)game;
    if (a->assets) { reserve(a, 0); native_free(a->assets); a->assets = (void*)0; }
}

static void leave_door(Tent *a, u8 *game) {
    if (game[0x1EE3]) return;
    Position p = position(a, 0x28); p.z += 86.0f;
    p.y = native_ground(p, 0.0f);
    *(u32*)native_exit = (u32)native_scene;
    native_exit[4] = native_exit[5] = 0;
    write16(native_exit + 6, 3);
    write16(native_exit + 8, (s16)p.x); write16(native_exit + 10, (s16)p.y);
    write16(native_exit + 12, (s16)p.z); write16(native_exit + 14, 0x5849);
    native_exit[16] = 1;
    /* Native igloo uses 028A for the same exterior-entry wipe composition.
     * GC's numeric 2168 belongs to a different BGM command encoding. */
    native_bgm(0x028A);
}

void af_v3_campsite_exterior_mv(Tent *a, void *game) {
    Tent *player = native_player(game);
    if (!a->assets || !player) return;
    Position p = position(a, 0x28), pp = position(player, 0x28);
    int ax, az, px, pz;
    if (native_block(&ax, &az, p) && native_block(&px, &pz, pp) && (ax != px || az != pz)
            && !native_demo(1, player) && !native_demo(5, player)) {
        native_delete(a); return;
    }
#ifdef __mips__
    Tent *(*label)(void*) = *(Tent *(**)(void*))((u8*)player + 0x122C);
    Tent *door = label ? label(game) : (void*)0;
#else
    extern Tent *af_test_door;
    Tent *door = af_test_door;
#endif
    if (door == a) {
        leave_door(a, game);
        native_goto(game, campsite_actor_packet + 0x80, 1);
    } else {
        u16 angle = read16((u8*)player + 0xDE);
        float x = pp.x - p.x, z = pp.z - (p.z + 40.0f);
        if (angle > 0x6000 && angle < 0xA000 && x*x + z*z < 1600.0f) {
            p.y = pp.y; p.z += 68.0f;
            native_request_door(game, &p, -32768, 1, a);
        }
    }
    float target = light_on() ? 1.0f : 0.0f, step = 0.019532442f;
    if (a->fade < target) { a->fade += step; if (a->fade > target) a->fade = target; }
    else if (a->fade > target) { a->fade -= step; if (a->fade < target) a->fade = target; }
}

void af_v3_campsite_exterior_init(Tent *a, void *game) {
    if (!a->assets) return;
    native_fg(0xF127, position(a, 0xC), 0);
    af_v3_campsite_exterior_mv(a, game);
#ifdef __mips__
    /* A deleted actor must stay deleted. */
    if (*(u32*)((u8*)a + 0x164)) *(void (**)(Tent*,void*))((u8*)a + 0x164) = af_v3_campsite_exterior_mv;
#endif
}

void *af_v3_campsite_structure_setup(void *game, u16 name, float x, float z, s16 params) {
    if (name != 0x5849) {
#ifdef __mips__
        u32 owner = *(u32*)(native_descriptors + 0x45 * 32 + 16);
        return ((void *(*)(void*,u16,float,float,s16))(owner + 0xF54))(game,name,x,z,params);
#else
        extern void *af_test_original_setup(void*,u16,float,float,s16);
        return af_test_original_setup(game,name,x,z,params);
#endif
    }
    if (!enabled()) return (void*)0;
    Position p = {x, 0.0f, z}; p.y = native_ground(p, 0.0f);
    Tent *a = native_make((u8*)game + 0x1C78, game, 0xCA, p.x, p.y, p.z, 0,0,0,
        ((signed char*)game)[0xE4], ((signed char*)game)[0xE5], -1, name, params, -1, -1);
    if (!a || !a->assets) return (void*)0;
    native_fg(0xFFFF, p, 0);
    return a;
}

void af_v3_campsite_exterior_dw(Tent *a, void *game) {
    if (!a->assets) return;
    Graphics *g = *(Graphics**)game;
    uptr head = (uptr)g->head, tail = (uptr)g->tail;
    uptr shadow_head = (uptr)g->shadow, shadow_tail = (uptr)g->shadow_tail;
    /* Immutable matrix, window DL, and all projected vertices share the
     * current frame's checked arena. No partial draw on exhausted storage. */
    if ((head & 7) || (tail & 15) || tail < head || tail - head < 672
            || (shadow_head & 7) || shadow_tail < shadow_head || shadow_tail - shadow_head < 64) return;
    uptr frame = (tail - 528) & ~(uptr)15;
    if (frame < head + 144) return;
    g->tail = (u8*)frame;
    Command *window = (Command*)(frame + 64);
    u8 *projected = (u8*)(frame + 80), *shadow = a->assets + 0x1B30;
    native_matrix((void*)frame);
    u32 brightness = (u32)(a->fade * 255.0f), blue = (u32)(a->fade * 150.0f);
    window[0] = (Command){0xFA0000FF, (brightness << 24) | (brightness << 16) | (blue << 8) | 255};
    window[1] = (Command){0xDF000000,0};
    int shift = (int)(*(float*)((u8*)game + 0x1C50) * 60.0f);
    for (u32 i = 0; i < 28; ++i) {
        for (u32 j = 0; j < 16; ++j) projected[i*16+j] = shadow[0x80+i*16+j];
        if (shadow[0x240+i]) write16(projected+i*16, (u16)((s16)read16(projected+i*16) + shift));
    }
    native_writeback((void*)frame, 528);
    native_opaque_state(g);
    Command *c = g->head;
    c[0]=(Command){0xDA380003,(u32)frame}; c[1]=(Command){0xDB060018,(u32)(uptr)a->assets};
    c[2]=(Command){0xDB060020,(u32)(uptr)window}; c[3]=(Command){0xDE000000,0x060017D0};
    g->head = c + 4;
    native_shadow_state(g);
    const u8 *light = (u8*)game + 0x1C3A;
    u32 alpha = ((u8*)game)[0x1C54];
    c = g->shadow;
    c[0]=(Command){0xE7000000,0}; c[1]=(Command){0xDA380003,(u32)frame};
    c[2]=(Command){0xDB060018,(u32)(uptr)shadow}; c[3]=(Command){0xDB060020,(u32)(uptr)projected};
    c[4]=(Command){0xFA000000 | alpha, (u32)light[0]<<24 | (u32)light[1]<<16 | (u32)light[2]<<8 | alpha};
    c[5]=(Command){0xDE000000,0x06000260};
    g->shadow = c + 6;
}
