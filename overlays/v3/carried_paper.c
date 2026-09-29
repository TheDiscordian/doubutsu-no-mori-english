/* One ROM-build policy for every stationery style. Apply obtain() only at
 * actual creation/purchase/reward boundaries: moving, picking up, splitting,
 * merging, attaching, and consuming an existing sheet never creates paper. */
#include "carried_paper.h"
#ifdef __mips__
const AFCarryWord af_carried_paper_mode=0; /* N64 singles; GameCube packs is 1. */
#endif
extern int af_carried_category(AFCarryWord);

int af_carried_paper_packs_enabled(void) {
    return *(const volatile AFCarryWord *)&af_carried_paper_mode==1;
}
int af_carried_paper_reserved(AFCarryWord item) {
    return item-AF_PAPER_PACK_FIRST<AF_PAPER_PACK_COUNT;
}
int af_carried_paper_style(AFCarryWord item) {
    if(item-0x2000u<64u)return (int)(item-0x2000u);
    if(item-0x2040u<4u)return af_carried_category(item)==49?64:-1;
    if(af_carried_paper_reserved(item))return (int)((item-AF_PAPER_PACK_FIRST)%64u);
    return -1;
}
AFCarryWord af_carried_paper_quantity(AFCarryWord item) {
    if(item-0x2000u<64u)return 1;
    if(item-0x2040u<4u)return af_carried_paper_style(item)==64?item-0x203Fu:0;
    if(af_carried_paper_reserved(item))return (item-AF_PAPER_PACK_FIRST)/64u+2u;
    return 0;
}
AFCarryHalf af_carried_paper_with_quantity(AFCarryWord item,AFCarryWord quantity) {
    int style=af_carried_paper_style(item);
    if(style<0 || !quantity || quantity>4)return 0;
    if(style==64)return (AFCarryHalf)(0x203Fu+quantity);
    return (AFCarryHalf)(quantity==1 ? 0x2000u+(unsigned)style :
        AF_PAPER_PACK_FIRST+(quantity-2u)*64u+(unsigned)style);
}
AFCarryHalf af_carried_paper_obtain(AFCarryWord item) {
    unsigned mode=*(const volatile AFCarryWord *)&af_carried_paper_mode;
    if(mode>1)return 0;
    return af_carried_paper_with_quantity(item,mode?4u:1u);
}
AFCarryHalf af_carried_paper_catalogue_item(AFCarryWord index) {
    /* Catalogue indices are stable style/collection identities, not quantities.
     * Index 67 is the existing additive orange catalogue row. */
    if(index<64u)return af_carried_paper_obtain(0x2000u+index);
    if(index==67u)return af_carried_paper_obtain(0x2040u);
    return 0;
}
AFCarryHalf af_carried_paper_create_item(AFCarryWord item) {
    /* Only creation callers use this adapter. Inventory setters and native mail
     * attachment transfers must retain the exact existing item/quantity. */
    if(item-0x2000u<68u || af_carried_paper_reserved(item))
        return af_carried_paper_obtain(item);
    return (AFCarryHalf)item;
}
AFCarryHalf af_cw_paper_stack(AFCarryHalf item,unsigned source_quantity) {
    if(!source_quantity || source_quantity>4)return 0;
    return af_carried_paper_obtain(item);
}
