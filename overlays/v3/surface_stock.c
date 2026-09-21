/* Keep native rarity/selection and compact only disabled additive surfaces. */
typedef unsigned short u16;
typedef unsigned int u32;
extern int af_v3_surface_item_type(u32);
extern int af_surface_prior_shop_category(u32);
extern u16 *af_surface_prior_stock_list(void *, void *, int);

static int added(u32 item) {
    return (item >> 8)-0x26u < 2u && (item & 255u) >= 64u;
}

int af_v3_surface_shop_category(u32 argument) {
    u32 item=(u16)argument;
    if (!added(item)) return af_surface_prior_shop_category(argument);
    return af_v3_surface_item_type(item)==12 ? (int)(item >> 8)-0x23 : -1;
}

u16 *af_v3_surface_stock_list(void *lists, void *priorities, int type) {
    u16 *list=af_surface_prior_stock_list(lists,priorities,type);
    if (!list || !*list || ((*list >> 8)-0x26u >= 2u)) return list;
    /* Native goods lists are disposable, size-derived DMA allocations. Validate
       the full short surface list before filtering it in place. Other goods
       categories do not enter this loop or change their season/rarity rules. */
    u32 count=0,kind=*list >> 8;
    while (count<69u && list[count]) {
        if ((list[count] >> 8)!=kind) return 0;
        ++count;
    }
    if (count==69u) return 0;
    u32 out=0;
    for (u32 i=0;i<count;++i) {
        u32 item=list[i];
        if (!added(item) || af_v3_surface_item_type(item)==12) list[out++]=(u16)item;
    }
    list[out]=0;
    return list;
}
