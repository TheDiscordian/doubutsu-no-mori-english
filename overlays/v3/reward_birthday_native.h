#ifndef AF_V3_REWARD_BIRTHDAY_NATIVE_H
#define AF_V3_REWARD_BIRTHDAY_NATIVE_H
#include "reward_event.h"
/* Native 800A9C48/70 passes animal+10 to the seven-memory reader.
 * Native 800A74E4 reads friendship at 28 and advances by B0. Header
 * comments from the incomplete decompilation describe different offsets. */
typedef struct {u8 bytes[0x10];} AFRewardPersonalID;
typedef struct {u16 npc_id;u8 rest[10];} AFRewardAnimalID;
typedef struct {
    AFRewardPersonalID memory_player_id;
    u8 before_friendship[0x18];
    s8 friendship;
    u8 rest[0x87];
} AFRewardMemory;
typedef struct {
    AFRewardAnimalID id;
    u8 before_memories[4];
    AFRewardMemory memories[7];
    u8 rest[0x48];
} AFRewardAnimal;
_Static_assert(sizeof(AFRewardMemory)==0xB0,"Native resident memory stride");
_Static_assert(__builtin_offsetof(AFRewardMemory,friendship)==0x28,"Native friendship byte");
_Static_assert(__builtin_offsetof(AFRewardAnimal,memories)==0x10,"Native animal memories");
_Static_assert(sizeof(AFRewardAnimal)==0x528,"Native animal stride");
AFRewardAnimal *af_rw_birthday_animals(void);
int af_rw_birthday_friendship(void);
u16 af_rw_birthday_choose(void);
int af_rw_native_highest_friendship(AFRewardMemory *,int);
int af_rw_native_compare_player(AFRewardPersonalID *,AFRewardPersonalID *);
int af_rw_native_free_animal(AFRewardAnimalID *);
#endif
