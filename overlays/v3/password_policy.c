/* Shared source eligibility and Nook result rules. Acquisition is an engine
 * state machine; this module deliberately cannot write inventory or saves. */
#include "password_policy.h"
typedef af_pw_u8 u8;
typedef af_pw_u32 u32;
static u32 half(const u8 *p) { return (u32)p[0]*256+p[1]; }
static u32 word(const u8 *p) { return (half(p)<<16)|half(p+2); }
int af_v3_password_map_valid(const u8 *p,u32 n) {
    u32 i,count,last=0;
    if(!p||n<16||n>65535||p[0]!='A'||p[1]!='F'||p[2]!='P'||p[3]!='M'
        ||half(p+4)!=1||half(p+8)!=12||half(p+10)!=n||word(p+12)) return 0;
    count=half(p+6);if(n!=16+count*12) return 0;
    for(i=0;i<count;i++) {
        const u8 *r=p+16+i*12;u32 source=half(r),item=half(r+2),ram=word(r+4),width=r[8];
        if(!source||source==65535||!item||item==65535||(i&&source<=last)
            ||(width!=1&&width!=4)||ram<0x80400000u||ram>0x80800000u-width
            ||(width==4&&(ram&3))||r[9]||r[10]||r[11])return 0;
        last=source;
    }
    return 1;
}
u32 af_v3_password_resolve(const u8 *p,u32 n,u32 item,u32 (*read)(void *,u32,u32),void *context) {
    u32 lo=0,hi,mid;
    if(item>65535||!read||!af_v3_password_map_valid(p,n))return 0;
    hi=half(p+6);
    while(lo<hi) {
        const u8 *r;mid=lo+(hi-lo)/2;r=p+16+mid*12;
        if(item<half(r))hi=mid;
        else if(item>half(r))lo=mid+1;
        else return read(context,word(r+4),r[8])==1?half(r+2):0;
    }
    return 0;
}
int af_v3_password_policy_valid(const u8 *p,u32 n) {
    u32 i,count,last=0,mask=0;
    if(!p||n<32||n>65535||p[0]!='A'||p[1]!='F'||p[2]!='P'||p[3]!='E'
        ||half(p+4)!=1||half(p+8)!=n||half(p+10)!=236||half(p+12)!=32
        ||half(p+14)!=65535||p[16]!=80||p[17]!=60||p[18]!=30||p[19]!=0||p[20]!=100) return 0;
    count=half(p+6);if(!count||32+count*6!=n) return 0;
    for(i=21;i<32;i++) if(p[i]) return 0;
    for(i=0;i<count;i++) {
        const u8 *r=p+32+i*6;u32 a=half(r),b=half(r+2);
        if(a>b||!r[4]||r[4]>7||r[5]||(i&&(a<=last||(a==last+1&&mask==r[4])))) return 0;
        last=b;mask=r[4];
    }
    return last==65535&&mask==7;
}
int af_v3_password_allowed(const u8 *p,u32 n,u32 item,u32 type) {
    u32 lo=0,hi,mid,bit=type==0?1:type==4?2:4;
    if(item>65535||type>=6||!af_v3_password_policy_valid(p,n)) return 0;
    hi=half(p+6);
    while(lo<hi) {
        const u8 *r;mid=lo+(hi-lo)/2;r=p+32+mid*6;
        if(item<half(r)) hi=mid;
        else if(item>half(r+2)) lo=mid+1;
        else return !!(r[4]&bit);
    }
    return 0;
}
static int equal_name(const u8 *a,const u8 *b) {
    u32 i,nonspace=0;if(!a||!b)return 0;
    for(i=0;i<8;i++) { if(a[i]!=b[i])return 0;nonspace|=a[i]!=32; }
    return !!nonspace;
}
static int descriptor_ok(const af_v3_password *v) {
    u32 sum,i;
    if(!v||v->type>=6||v->checksum>3||v->hit_rate_index>7||v->reserved) return 0;
    if(v->type!=1&&v->type!=2&&(v->npc_type!=255||v->npc_code!=255)) return 0;
    sum=v->item+v->npc_code;
    for(i=0;i<8;i++) sum+=v->str0[i]+v->str1[i];
    return (sum&3)==v->checksum;
}
int af_v3_password_result_gives_item(u32 result) {
    return result==AF_PW_FAMICOM||result==AF_PW_NPC||result==AF_PW_MAGAZINE_WIN
        ||result==AF_PW_USER||result==AF_PW_CARD_E_MINI;
}
int af_v3_password_decide(const u8 *p,u32 n,const af_v3_password *v,
    const u8 *player,const u8 *town,const struct AfPasswordOps *ops,struct AfPasswordOffer *out) {
    u32 item,result=0;
    if(!out||!ops||!ops->resolve||!descriptor_ok(v)||!af_v3_password_allowed(p,n,v->item,v->type)) return 0;
    item=ops->resolve(ops->context,v->item);
    if(!item||item>=65535) return 0;
    switch(v->type) {
    case 0:case 1:case 4:
        if(v->hit_rate_index!=1) return 0;
        if(v->type==1&&!((v->npc_type==0&&v->npc_code<half(p+10))
                         ||(v->npc_type==1&&v->npc_code<half(p+12)))) return 0;
        result=v->type==0?AF_PW_FAMICOM:v->type==1?AF_PW_NPC:AF_PW_USER;
        if(!equal_name(player,v->str0)||!equal_name(town,v->str1)) result=AF_PW_WRONG_NAME;
        break;
    case 2:result=AF_PW_CARD_E;break;
    case 3: {
        float roll;
        if(v->hit_rate_index>4||!ops->random_percent) return 0;
        roll=ops->random_percent(ops->context);
        if(!(roll>=0.0f&&roll<100.0f)) return 0;
        result=roll<(float)p[16+v->hit_rate_index]?AF_PW_MAGAZINE_WIN:AF_PW_MAGAZINE_LOSE;
        break;
    }
    case 5:if(v->hit_rate_index==1)result=AF_PW_CARD_E_MINI;break;
    }
    if(!result) return 0;
    out->source_item=v->item;out->item=item;out->result=result;
    return (int)result;
}
