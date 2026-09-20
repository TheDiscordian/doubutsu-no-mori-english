/* Wrapped field identities resolve to selected parents plus pocket condition.
   This table does not enable acquisition, reward demos, or profile bits. */
typedef unsigned short u16;
typedef unsigned int u32;
typedef struct { u16 wrapped, parent; } Present;
#ifdef __mips__
#define header ((const u32 *)0x804B4F00u)
#define selected ((int (*)(u32))AF_V3_HELD_SELECTED)
#else
extern u32 af_test_present_table[8];
extern int af_test_present_selected(u32);
#define header af_test_present_table
#define selected af_test_present_selected
#endif

static u32 mapped(u32 item, int decode) {
    if (item>65535u || header[0]!=0x41465057u || header[1]!=1u ||
            header[2]!=4u || header[3]!=sizeof(Present)) return 0;
    const Present *rows=(const Present *)(header+4);
    for (u32 i=0;i<4u;++i) {
        const Present *r=rows+i;
        if (r->wrapped!=0x251Fu+i || r->parent!=0x2239u+i) return 0;
        if (item==(decode?r->wrapped:r->parent))
            return selected(r->parent)>=36 ? (decode?r->parent:r->wrapped) : 0;
    }
    return 0;
}

u32 af_v3_present_decode(u32 item) { return mapped(item,1); }
u32 af_v3_present_encode(u32 item,u32 condition) {
    u32 wrapped=condition==1u ? mapped(item,0) : 0;
    return wrapped ? wrapped : item;
}
