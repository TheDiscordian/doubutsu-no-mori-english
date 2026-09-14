/* Preserve native B/C seasons while adding the selected all-season A garment. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#ifdef __mips__
#define segment ((const void *(*)(u32))0x8009ADA8u)
#define native_index ((int (*)(int *))0x800BFAA8u)
#define random_float ((float (*)(void))0x8002C9ACu)
#define month (*(const u8 *)0x80136FC1u)
#define selected (((const u8 *)0x80460020u)[183] & 0x80)
#else
extern const void *af_stock_segment(u32);
extern int af_stock_native_index(int *);
extern float af_stock_random_float(void);
extern u8 af_stock_month, af_stock_selected;
#define segment af_stock_segment
#define native_index af_stock_native_index
#define random_float af_stock_random_float
#define month af_stock_month
#define selected af_stock_selected
#endif
extern u32 af_v3_clothing_source(int, u32);

int af_v3_clothing_stock_index(int *index, const u16 *list) {
    if (!index) return 0;
    if (list != segment(0x06000230u)) return native_index(index);
    if (!selected || !af_v3_clothing_source(0x10BF, 0)) {
        int count = native_index(index);
        if (*index >= 32) ++*index; /* Skip the inserted item in the expanded A list. */
        return count;
    }
    const u8 *counts = (const u8 *)list-0x14; /* Retained native counts at 21C. */
    u32 season = ((month+9u)%12u)/3u+1u;
    u32 any = counts[0]+1u, count = any+counts[season];
    int chosen = (int)(random_float()*(float)count);
    if ((u32)chosen >= any)
        for (u32 i = 1; i < season; ++i) chosen += counts[i];
    *index = chosen;
    return (int)count;
}
