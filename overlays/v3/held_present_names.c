/* Preserve the native ten-byte getter; only wrapped import identities differ. */
typedef unsigned char u8;
typedef unsigned int u32;
extern void af_v3_present_original_name(u8 *, u32);
#ifdef __mips__
#define decode ((u32 (*)(u32))AF_V3_PRESENT_DECODE)
#else
extern u32 af_test_present_decode(u32);
#define decode af_test_present_decode
#endif

u32 af_v3_present_name_item(u32 item) {
    if (item-0x251Fu<4u) return decode(item) ? 0x251Cu : 0xFFFFu;
    return item;
}

void af_v3_present_legacy_name(u8 *destination,u32 argument) {
    u32 item=(unsigned short)argument;
    if (item-0x251Fu<4u) {
        if (!destination || !decode(item)) return;
        item=0x251Cu;
    }
    af_v3_present_original_name(destination,item);
}
