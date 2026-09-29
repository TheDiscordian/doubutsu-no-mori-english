/* Whole donor giver selection over the verified N64 save view. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "reward_birthday_native.h"
#include "../overlays/v3/reward_birthday_native.c"
#include "reward_birthday_source.c"
u8 af_hp_native_animals[15][0x528] __attribute__((aligned(8)));
static AFRewardPersonalID player;
static u16 giver;
void *af_rw_private(void) {return &player;}
u16 af_rw_birthday_giver(void) {return giver;}
int af_rw_native_free_animal(AFRewardAnimalID *id) {return !id->npc_id;}
int af_rw_native_compare_player(AFRewardPersonalID *a,AFRewardPersonalID *b) {
    return !memcmp(a,b,sizeof(*a));
}
int af_rw_native_highest_friendship(AFRewardMemory *memory,int count) {
    assert(count==7);
    int best=-1,max=0;
    for(int i=0;i<count;i++)if(memory[i].memory_player_id.bytes[0] &&
            memory[i].friendship>=max) {max=memory[i].friendship;best=i;}
    return best;
}
static void friend(int animal,int memory,int score,int person) {
    AFRewardAnimal *a=af_rw_birthday_animals()+animal;
    a->id.npc_id=(u16)(0xE010+animal);
    a->memories[memory].friendship=(s8)score;
    a->memories[memory].memory_player_id.bytes[0]=(u8)person;
}
int main(void) {
    player.bytes[0]=1;
    assert(!af_rw_birthday_friendship());
    friend(0,0,12,1);friend(14,6,30,1);
    assert(af_rw_birthday_friendship() && af_rw_birthday_choose()==0xE01E);
    /* First animal wins equal maximum values, while the highest-memory
     * service chooses the last equal player memory within that animal. */
    friend(3,2,30,1);
    assert(af_rw_birthday_choose()==0xE013);
    giver=0xE013;assert(af_rw_birthday_choose()==0xE01E);
    /* Being friendly is insufficient when someone else is the best friend. */
    friend(14,0,31,2);
    assert(af_rw_birthday_choose()==0xE010);
    friend(0,6,12,2);
    assert(!af_rw_birthday_friendship());
    giver=0;friend(3,0,29,2);
    assert(af_rw_birthday_choose()==0xE013);
    friend(3,6,31,2);
    assert(!af_rw_birthday_friendship());
    /* A vacated animal slot cannot supply its old memories. */
    af_rw_birthday_animals()[3].id.npc_id=0;
    assert(!af_rw_birthday_friendship());
    memset(af_hp_native_animals,0,sizeof(af_hp_native_animals));
    for(int i=0;i<15;i++)friend(i,6,i+1,1);
    assert(af_rw_birthday_choose()==0xE01E);
    puts("Birthday giver: verified native offsets, all fifteen animals and seven memories, best-friend identity, equal scores, previous giver, and vacant slots pass.");
}
