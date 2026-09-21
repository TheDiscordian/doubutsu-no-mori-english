/* Surface pages use independent ownership; retain the native debug-bit reader. */
typedef unsigned char u8;
typedef unsigned int u32;
typedef int (*NativeBit)(const u32 *, int);
#ifdef __mips__
#define active (*(u8 *volatile *)0x80136FD8u)
#else
extern u8 *af_surface_menu_active;
#define active af_surface_menu_active
#endif
extern int af_v3_catalogue_owned(const u8 *,u32);

int af_v3_surface_catalogue_bit(const u32 *bits,int index,NativeBit original) {
    const u8 *player=active;
    if (player && ((const u8 *)bits==player+0xB68 || (const u8 *)bits==player+0xB70)) {
        if ((u32)index>=256u) return 0;
        if (index>=64) {
            u32 base=(const u8 *)bits==player+0xB68 ? 0x2700u : 0x2600u;
            return af_v3_catalogue_owned(player,base+(u32)index);
        }
    }
    if (index<2048) return original(bits,index);
    if (index>3071 || !player || (const u8 *)bits!=player+0xAF0) return 0;
    return af_v3_catalogue_owned(player,0x1000u+(u32)index*4u);
}
