/* Select enabled garments from their actual A/B/C season partitions. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#ifdef AF_V3_CLOTHING_BATCH
#include "clothing_batch.h"
#endif
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
#ifdef AF_V3_CLOTHING_BATCH
    if (!index) return 0;
    const struct ClothingStock *stock=0;
    for (u32 i=0;i<3;i++)
        if (list==segment(af_v3_batch_stock[i].pointer)) stock=af_v3_batch_stock+i;
    if (!stock) return native_index(index);
    u32 season=((month+9u)%12u)/3u+1u;
    u32 first=stock->counts[0],last;
    for (u32 i=1;i<season;i++) first+=stock->counts[i];
    last=first+stock->counts[season];
    u32 count=0;
    for (u32 i=0;i<last;i++) {
        if (i>=stock->counts[0] && i<first) continue;
        u32 item=list[i];
        if ((item>=0x2400u && item<0x2500u) || af_v3_roster_clothing_record(item)) count++;
    }
    if (!count) return 0;
    u32 chosen=(u32)(random_float()*(float)count);
    if (chosen>=count) chosen=count-1;
    for (u32 i=0;i<last;i++) {
        if (i>=stock->counts[0] && i<first) continue;
        u32 item=list[i];
        if ((item>=0x2400u && item<0x2500u) || af_v3_roster_clothing_record(item)) {
            if (!chosen) {*index=(int)i;return (int)count;}
            chosen--;
        }
    }
    return 0;
#else
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
#endif
}
