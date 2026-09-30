/* Borrow the exclusive title workspace between play initialization and cleanup.
 * Native allocation, freeing, and bank data remain complete and unchanged. */
typedef unsigned int u32;
typedef unsigned short u16;
extern void af_scene_native_init(void *, u32);
extern void af_scene_native_cleanup(void);
extern void af_scene_native_add(void *, void *, u32);
extern void af_v3_save_halt(int) __attribute__((noreturn));
#define GUARD 0xAF53434Eu
struct Node { u16 magic, free; u32 size, next, previous; };
#ifdef __mips__
#define detected (*(volatile u32 *)0x80000318u)
#define title_loaded (*(volatile u32 *)0x80102200u)
#define scene_no (*(volatile u32 *)0x80126EB4u)
#define borrowed (*(volatile u32 *)0x804F4900u)
#define arena ((void *)0x80141FA0u)
#define front ((volatile u32 *)0x80400000u)
#define end ((volatile u32 *)0x8044FFF0u)
#else
extern u32 af_scene_test_detected, af_scene_test_title;
extern u32 af_scene_test_number, af_scene_test_borrowed;
extern unsigned char af_scene_test_workspace[0x50000];
#define detected af_scene_test_detected
#define title_loaded af_scene_test_title
#define scene_no af_scene_test_number
#define borrowed af_scene_test_borrowed
#define arena ((void *)0x80141FA0u)
#define front ((volatile u32 *)af_scene_test_workspace)
#define end ((volatile u32 *)(af_scene_test_workspace+0x4FFF0))
#endif

void af_v3_scene_init(void *base, u32 size) {
    if (borrowed) af_v3_save_halt(-3);
    /* m_scene_table.h: only actual town/room gameplay borrows title RAM.
     * Title, resident-selection, introduction, and announcement scenes do not. */
    u32 number=scene_no;
    int gameplay=(number==6 || number==7 || number==9 || number==12 || number==14 ||
        number==17 || number==18 || (number>=20 && number<=25) || number==29 || number==31);
    if (!gameplay) { af_scene_native_init(base, size); return; }
    if (detected != 0x800000u || title_loaded) af_v3_save_halt(-3);
    af_scene_native_init(base, size);
    for (u32 i=0; i<4; ++i) front[i]=end[i]=GUARD;
    /* The native shrink-realloc branch assumes a free successor is adjacent.
     * Keep an allocated sentinel between the lower and upper memory blocks. */
    struct Node *sentinel=(struct Node *)(front+4);
    af_scene_native_add(arena, sentinel, 32);
    if (sentinel->magic != 0x7373u || !sentinel->free || sentinel->size != 16u)
        af_v3_save_halt(-3);
    sentinel->free=0;
    af_scene_native_add(arena, (void *)(front+12), 0x4FFC0u);
    borrowed=1;
}

void af_v3_scene_cleanup(void) {
    if (borrowed) {
        if (title_loaded) af_v3_save_halt(-3);
        for (u32 i=0; i<4; ++i)
            if (front[i]!=GUARD || end[i]!=GUARD) af_v3_save_halt(-3);
        borrowed=0;
    }
    af_scene_native_cleanup();
}
