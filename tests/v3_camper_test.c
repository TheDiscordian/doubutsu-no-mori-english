#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/camper.h"
AfCamper camper;
volatile camp_u32 native_installed;
const camp_u8 *native_private;
static AfCamperAlias aliases[5];
static unsigned char enabled[238], actor[0x180], private_data[16];
static camp_u8 *attached;
static int cleared, defaults, memories, previous;
AfCamperAlias *native_event(camp_u32 id) {
    for (int i=0;i<5;i++) if (aliases[i].event==id) return aliases+i;
    return NULL;
}
int native_free_event(void) {
    for (int i=0;i<5;i++) if (!aliases[i].use) return i;
    return -1;
}
int native_register(camp_u32 mask,camp_u32 texture,camp_u32 id,camp_u32 cloth) {
    int i=native_free_event(); if (i<0) return 0;
    aliases[i]=(AfCamperAlias){mask,texture,id,cloth,0,1,0}; return 1;
}
int selected_villager(int i) { return i>=0 && i<238 && i!=216 && i!=217 && enabled[i]; }
int selected_outfit(camp_u32 cloth) { return (cloth>=0x2400 && cloth<0x2500) || cloth==0x341A; }
void native_clear_animal(camp_u8 *p) { assert(p==camper.animal); memset(p,0,0x528); cleared++; }
void native_set_index(camp_u8 *p,int i) {
    assert(p==camper.animal); defaults++;
    p[0]=0xE0; p[1]=i; p[0x520]=0x34; p[0x521]=0x1A;
}
void native_set_memory(const camp_u8 *p,camp_u8 *m) {
    assert(p==native_private && m==camper.animal+16); memcpy(m,p,16); memories++;
}
void original_npc_info(camp_u8 *a,int i) { assert(a==actor && i==7); previous++; }
void camper_test_set_info(camp_u8 *a,camp_u8 *animal) { assert(a==actor); attached=animal; }
static void reset(void) {
    memset(&camper,0,sizeof(camper)); memset(aliases,0,sizeof(aliases));
    memset(enabled,1,sizeof(enabled)); memset(actor,0,sizeof(actor));
    camper.magic=0x41464341; camper.guard[0]=0xAFCA11ED;
    native_installed=1; native_private=private_data; cleared=defaults=memories=previous=0;
    actor[2]=3; actor[6]=0xD0; actor[7]=0x8F; attached=NULL;
}
int main(void) {
    assert(offsetof(AfCamper,animal)==0x20 && offsetof(AfCamper,guard)==0x550);
    reset(); assert(af_v3_camper_register(0xD08F,0xE0DA,0)==1);
    assert(cleared==1 && defaults==1 && !memories && aliases[0].cloth==0x341A);
    assert(aliases[0].texture==0xE0DA && aliases[0].npc==0xE0DA);
    camper.animal[32]=0xAB;
    assert(af_v3_camper_register(0xD08F,0xE0DA,0)==1 && cleared==1 && camper.animal[32]==0xAB);
    assert(!af_v3_camper_register(0xD08F,0xE0ED,0) && cleared==1);
    af_v3_camper_npc_info(actor,7); assert(attached==camper.animal && !previous);
    aliases[0].npc=0xE0ED; af_v3_camper_npc_info(actor,7); assert(!attached);
    actor[7]=0x8E; af_v3_camper_npc_info(actor,7); assert(previous==1);
    reset(); for (int i=0;i<5;i++) aliases[i]=(AfCamperAlias){0xD000+i,0,0,0,0,1,0};
    assert(!af_v3_camper_register(0xD08F,0xE0DA,0) && !cleared);
    reset(); enabled[218]=0; assert(!af_v3_camper_register(0xD08F,0xE0DA,0) && !cleared);
    for (int i=216;i<=217;i++) assert(!af_v3_camper_register(0xD08F,0xE000+i,0));
    assert(!af_v3_camper_register(0xD08F,0xE0EE,0));
    assert(!af_v3_camper_register(0xD08E,0xE000,0));
    reset(); camper.greeted=1; native_private=NULL;
    assert(!af_v3_camper_register(0xD08F,0xE000,0) && !cleared);
    native_private=private_data; memset(private_data,0xA5,16);
    assert(af_v3_camper_register(0xD08F,0xE000,0xFFFF)==1 && aliases[0].cloth==0x2400);
    assert(memories==1 && !memcmp(camper.animal+16,private_data,16));
    assert(!memcmp(camper.animal+12,"\0\0\0\0",4));
    reset(); assert(af_v3_camper_register(0xD08F,0xE000,0xFE20)==1 && aliases[0].cloth==0xFE20);
    reset(); camper.guard[0]=0; assert(!af_v3_camper_register(0xD08F,0xE000,0));
    reset(); native_installed=0; assert(!af_v3_camper_register(0xD08F,0xE000,0));
    af_v3_camper_npc_info(actor,7); assert(previous==1);
    puts("camper ownership, aliases, selection, defaults, memory, and reader pass");
}
