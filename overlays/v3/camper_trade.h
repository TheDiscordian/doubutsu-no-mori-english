#ifndef AF_V3_CAMPER_TRADE_H
#define AF_V3_CAMPER_TRADE_H
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef int (*PocketPicker)(u16 *);
struct TradePrivate {
    u8 prefix[0x14];
    u16 items[15], padding;
    u32 conditions;
    u8 middle[0xA78 - 0x38];
    u16 shirt;
};
struct TradeState {
    u8 prefix[12];
    int item_index;
    u32 unchanged;
    u16 items[5];
};
_Static_assert(__builtin_offsetof(struct TradePrivate, shirt) == 0xA78, "Native worn shirt");
_Static_assert(__builtin_offsetof(struct TradeState, items) == 0x14, "Native trade slots");
extern const struct TradePrivate *native_private;
extern struct TradeState native_trade_state;
extern int native_scene;
extern u16 camper_last_gift, native_rare_item;
extern float native_random(void);
extern u32 native_item_kind(u32, u32);
extern u16 native_house_item(const void *);
extern void native_random_goods(void *, u16 *, int, const u16 *, int, int, int);
extern void native_goods_priority(u8 *, int);
extern void native_item_name(u16, int);
extern u16 native_other_fruit(void);
extern void native_trade_original(PocketPicker, const void *, const int *, int, int);
int af_v3_camper_pocket(u16 *);
void af_v3_camper_trade(PocketPicker, const void *, const int *, int, int);
#endif
