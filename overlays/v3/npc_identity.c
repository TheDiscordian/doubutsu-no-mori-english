#include "npc_identity.h"
typedef unsigned char u8;
typedef unsigned int u32;
static const AFNpcIdentity *identity(u32 name) {
    const AFNpcIdentities *t=&af_npc_identities;
    if(t->magic!=0x41464E49 || t->version!=1 || t->count>8 || t->stride!=16)return 0;
    for(u32 i=0;i<t->count;i++)if(t->rows[i].name==name)return t->rows+i;
    return 0;
}
static void copy(u8 *dest,const u8 *text) {for(u32 i=0;i<8;i++)dest[i]=text[i];}
int af_npc_identity_name(u8 *dest,u32 capacity,u32 name) {
    const AFNpcIdentity *r=identity(name);
    if(!r)return af_npc_previous_name(dest,capacity,name);
    if(!dest || capacity<8)return 0;
    copy(dest,r->text);return 1;
}
void af_npc_identity_actor_name(u8 *dest,const u8 *actor) {
    const AFNpcIdentity *r=actor?identity((u32)actor[6]*256u+actor[7]):0;
    if(r) {if(dest)copy(dest,r->text);return;}
    af_npc_previous_actor_name(dest,actor);
}
int af_npc_identity_sex(u32 name) {
    const AFNpcIdentity *r=identity((unsigned short)name);
    return r?(int)r->sex:af_npc_previous_sex(name);
}
int af_npc_identity_sound(u32 name) {
    const AFNpcIdentity *r=identity((unsigned short)name);
    return r?(int)r->sound:af_npc_previous_sound(name);
}
