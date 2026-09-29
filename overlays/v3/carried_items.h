#ifndef AF_V3_CARRIED_ITEMS_H
#define AF_V3_CARRIED_ITEMS_H
typedef unsigned char AFCarryByte;
typedef unsigned short AFCarryHalf;
typedef unsigned int AFCarryWord;
typedef struct {
    AFCarryHalf item,source,parent;
    AFCarryByte family,state,category,reserved;
    AFCarryHalf price;
    AFCarryWord icon;
    AFCarryByte name[16];
} AFCarryItem;
_Static_assert(sizeof(AFCarryItem)==32,"Carried item record width");
#define AF_CARRY_TABLE 0x80773800u
#define AF_CARRY_ICON 0x80774000u
#define AF_CARRY_ICON_END 0x80775F80u
#define AF_CARRY_COUNT 26u
int af_carried_reserved(AFCarryWord item);
int af_carried_category(AFCarryWord item);
AFCarryWord af_carried_quantity(AFCarryWord item);
AFCarryHalf af_carried_with_quantity(AFCarryWord item,AFCarryWord quantity);
#endif
