/* Accept native allocations only in the ordinary heap or the exclusively
 * borrowed, guarded title workspace. This changes no letter/reward rules. */
typedef unsigned int u32;
#ifdef __mips__
#define detected (*(volatile u32 *)0x80000318u)
#define title_loaded (*(volatile u32 *)0x80102200u)
#define borrowed (*(volatile u32 *)0x804F4900u)
#define front ((volatile u32 *)0x80400000u)
#define end ((volatile u32 *)0x8044FFF0u)
#else
extern u32 af_mail_heap_test_detected, af_mail_heap_test_title;
extern u32 af_mail_heap_test_borrowed;
extern u32 af_mail_heap_test_front[4], af_mail_heap_test_end[4];
#define detected af_mail_heap_test_detected
#define title_loaded af_mail_heap_test_title
#define borrowed af_mail_heap_test_borrowed
#define front af_mail_heap_test_front
#define end af_mail_heap_test_end
#endif

int af_v3_npc_mail_heap_range(u32 address, u32 size) {
    if (address >= 0x8019C8E0u && address <= 0x80400000u
            && size <= 0x80400000u-address) return 1;
    if (address < 0x80400040u || address > 0x8044FFF0u
            || size > 0x8044FFF0u-address || detected != 0x800000u
            || title_loaded || borrowed != 1u) return 0;
    for (u32 i=0; i<4; ++i)
        if (front[i] != 0xAF53434Eu || end[i] != 0xAF53434Eu) return 0;
    return 1;
}
