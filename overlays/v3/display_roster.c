/* All imported garments share the original mannequin geometry and callbacks. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
extern int af_v3_item_type(u32);
#ifdef __mips__
#define profile ((const u8 *)0x80460020u)
#else
extern u8 af_v3_display_profile[192];
#define profile af_v3_display_profile
#endif

u32 af_v3_all_display_clothing_index(u32 argument) {
    u32 item=(u16)argument;
    if (item>=0x17ACu && item<0x1BA8u) return (item-0x17ACu)>>2;
    item&=0xFFFCu;
    if (item!=0x3AFCu && item!=0x3868u && item!=0x386Cu) return 0;
    u32 index=(item-0x3800u)>>2;
    if (!(profile[96u+index/8u]&(1u<<(index&7)))) return 0;
    return af_v3_item_type(0x3400u+index)==12 ? 0x1000u+index : 0;
}
