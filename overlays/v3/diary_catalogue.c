/* Only the upper-layer HRA clutter query exempts selected carried diaries.
 * Floor diaries remain loose objects, and all ordinary furniture queries keep
 * their existing result. This follows the donor's EvaluateLetsClean branch. */
#include "diary_items.h"
extern unsigned int af_diary_prior_room_value(unsigned int,unsigned int);
unsigned int af_diary_clutter_value(unsigned int item,unsigned int mode) {
    if(!mode && item-AF_DIARY_ITEM_FIRST<AF_DIARY_ITEM_COUNT && af_diary_item_collection(item))return 1;
    return af_diary_prior_room_value(item,mode);
}
