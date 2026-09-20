#ifndef AF_V3_SAVE_REWARDS_H
#define AF_V3_SAVE_REWARDS_H
#include "save_codec.h"
#define AF_REWARD_PLAYER_BYTES 12u
/* Donor trophy IDs 0..27 and 28..32 are separate 32-bit fields.
   Celebration bits are independent of trophies and catalogue ownership. */
static inline int af_save_rewards_valid(const af_save_u8 *data) {
    for (af_save_u32 i=0;i<48u;i+=AF_REWARD_PLAYER_BYTES)
        if ((data[i]&0xF0u) || data[i+4] || data[i+5] || data[i+6] ||
                (data[i+7]&0xE0u) || (data[i+8]&0xF0u) || data[i+9] || data[i+10] || data[i+11])
            return 0;
    return 1;
}
int af_v3_reward_data_valid(const af_save_u8 *);
/* category 0 = source trophy ID 0..32; category 1 = celebration type 0..3.
   mark 0 queries, mark 1 records; never aliases an imported catalogue bit. */
int af_v3_reward_flag(af_save_u32 player,af_save_u32 category,af_save_u32 index,af_save_u32 mark);
void af_v3_reward_player_clear(af_save_u8 *);
void af_v3_reward_settle(void *,void *);
#endif
