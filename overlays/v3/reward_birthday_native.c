/* The complete source friendship and giver-selection routines use a native
 * sparse view, never a cast to the donor's larger save record. */
#include "reward_birthday_native.h"
extern u8 af_hp_native_animals[15][0x528];
AFRewardAnimal *af_rw_birthday_animals(void) {
    return (AFRewardAnimal *)af_hp_native_animals;
}
