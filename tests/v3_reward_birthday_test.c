/* Whole donor giver selection over the verified N64 save view. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "reward_birthday_native.h"
#include "../overlays/v3/reward_birthday_native.c"
#include "reward_birthday_source.c"
u8 af_hp_native_animals[15][0x528] __attribute__((aligned(8)));
static AFRewardPersonalID player;
static u16 giver;
static u8 cards[64];
static AFRewardBirthday birthdays[4];
static lbRTC_time_c clock_data={.year=2026,.month=9,.day=29};
static int native_mails,mail_count,mail_result=1,same_town=1;
static u16 mail_givers[15];
volatile s32 af_rw_birthday_mode;
u8 *af_v3_card_data(void) {return cards;}
lbRTC_time_c *af_cw_clock(void) {return &clock_data;}
int af_reward_birthday_get(const u8 *p,unsigned slot,AFRewardBirthday *out) {
    assert(p==cards && slot<4);*out=birthdays[slot];return 1;
}
int af_reward_birthday_set(u8 *p,unsigned slot,const AFRewardBirthday *value) {
    assert(p==cards && slot<4);birthdays[slot]=*value;return 1;
}
int af_rw_native_birthday_mail(AFRewardPersonalID *pid,int slot) {
    assert(pid==&player && slot==3);native_mails++;return 23;
}
int af_rw_native_same_town(const u8 *town,u16 id) {
    assert(town==player.bytes+6 && id==0x1234);return same_town;
}
int af_rw_native_birthday_card(AFRewardPersonalID *pid,int slot,AFRewardAnimalID *id) {
    assert(pid==&player && slot==3 && mail_count<15);
    mail_givers[mail_count++]=id->npc_id;return mail_result;
}
void af_v3_save_halt(int error) {(void)error;abort();}
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
    a->memories[memory].memory_player_id=player;
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
    memset(af_hp_native_animals,0,sizeof(af_hp_native_animals));
    player.bytes[14]=0x12;player.bytes[15]=0x34;friend(0,0,30,1);friend(1,0,20,1);
    assert(af_rw_birthday_mail(&player,3)==23 && native_mails==1 && !mail_count);
    af_rw_birthday_mode=1;birthdays[3]=(AFRewardBirthday){0xE010,2026};giver=0xE011;
    assert(af_rw_birthday_mail(&player,3)==1 && mail_count==1 && mail_givers[0]==0xE011);
    assert(birthdays[3].giver==0xE010 && birthdays[3].year==2026);
    assert(af_rw_birthday_current_giver()==giver);
    birthdays[3].year=2025;mail_count=0;
    assert(af_rw_birthday_mail(&player,3)==1 && mail_count==1);
    assert(!birthdays[3].giver && birthdays[3].year==2026);
    mail_count=0;same_town=0;birthdays[3]=(AFRewardBirthday){0xE010,2025};
    assert(!af_rw_birthday_mail(&player,3) && !mail_count && birthdays[3].year==2025);
    same_town=1;mail_result=0;mail_count=0;
    assert(!af_rw_birthday_mail(&player,3) && mail_count==1 && birthdays[3].year==2026);
    for(unsigned i=0;i<3;i++)assert(!birthdays[i].giver && !birthdays[i].year);
    puts("Birthday: verified native giver selection, N64 mail delegation, whole donor birthday mail, per-player giver exclusion/year update, refused delivery, and restored active-player context pass. Native services are doubled.");
}
