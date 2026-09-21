/* Shared decision and destination checks; no game state or player's save. */
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/password_policy.c"
extern int ref_decide(const af_v3_password *,int,float);
struct Context {u32 enabled,reads,resolves,rolls;float roll;const u8 *map;u32 map_size;};
static u32 read_enabled(void *p,u32 ram,u32 width) {
    struct Context *c=p;assert(ram>=0x80400000&&ram<=0x80800000-width);
    assert(width==1||width==4);c->reads++;return c->enabled;
}
static u32 resolve(void *p,u32 source) {
    struct Context *c=p;c->resolves++;assert(source<65536);
    if(c->map)return af_v3_password_resolve(c->map,c->map_size,source,read_enabled,c);
    return c->enabled?0x3224:0;
}
static float random_percent(void *p) {struct Context *c=p;c->rolls++;return c->roll;}
static u32 load(const char *path,u8 *data,u32 capacity) {
    FILE *f=fopen(path,"rb");assert(f);u32 n=(u32)fread(data,1,capacity,f);assert(feof(f));fclose(f);return n;
}
static void checksum(af_v3_password *p) {
    u32 total=p->item+p->npc_code;for(u32 i=0;i<8;i++)total+=p->str0[i]+p->str1[i];p->checksum=(u8)(total&3);
}
int main(int argc,char **argv) {
    assert(argc==5);static u8 policy[16384],map[16384],masks[65537],changed[16384],codec[2048];
    u32 n=load(argv[1],policy,sizeof(policy)),m=load(argv[2],map,sizeof(map));
    assert(load(argv[3],masks,sizeof(masks))==65536);
    assert(af_v3_password_policy_valid(policy,n)&&af_v3_password_map_valid(map,m));
    struct Context c={.enabled=1};struct AfPasswordOps ops={&c,resolve,random_percent};
    struct AfPasswordOffer out,untouched;memset(&untouched,0xA5,sizeof(untouched));
    for(u32 i=0;i<65536;i++)for(u32 type=0;type<6;type++)
        assert(af_v3_password_allowed(policy,n,i,type)==!!(masks[i]&(type==0?1:type==4?2:4)));
    u32 count=half(map+6);
    for(u32 i=0;i<count;i++) {
        u32 source=half(map+16+i*12),item=half(map+18+i*12);
        for(u32 enabled=0;enabled<3;enabled++) {
            c.enabled=enabled;c.reads=0;
            assert(af_v3_password_resolve(map,m,source,read_enabled,&c)==(enabled==1?item:0));
            assert(c.reads==1);
        }
    }
    c.reads=0;
    assert(!af_v3_password_resolve(map,m,65535,read_enabled,&c));
    assert(!af_v3_password_resolve(map,m,65536,read_enabled,&c));
    assert(!af_v3_password_resolve(map,m,0,read_enabled,&c));assert(!c.reads);
    af_v3_password p;u8 player[8]={'C','o','d','e',' ',' ',' ',' '},town[8]={'F','o','r','e','s','t',' ',' '};
    const float rolls[]={0.f,29.999f,30.f,59.999f,60.f,79.999f,80.f,99.999f};
    for(u32 type=0;type<6;type++)for(u32 rate=0;rate<8;rate++)for(u32 names=0;names<2;names++)
        for(u32 r=0;r<sizeof(rolls)/sizeof(rolls[0]);r++) {
            memset(&p,0,sizeof(p));p.type=(u8)type;p.hit_rate_index=(u8)rate;
            p.npc_type=(type==1||type==2)?0:255;p.npc_code=(type==1||type==2)?235:255;
            u32 bit=type==0?1:type==4?2:4;u32 item=1;while(item<65535&&!(masks[item]&bit))item++;
            assert(item<65535);p.item=(af_pw_u16)item;
            memcpy(p.str0,player,8);memcpy(p.str1,town,8);if(!names)p.str0[0]='X';checksum(&p);
            c.enabled=1;c.roll=rolls[r];c.rolls=0;out=untouched;
            int expected=ref_decide(&p,(int)names,c.roll);
            int result=af_v3_password_decide(policy,n,&p,player,town,&ops,&out);
            assert(result==expected);assert(c.rolls==((type==3&&rate<=4)?1u:0u));
            if(result)assert(out.item==0x3224&&out.source_item==p.item&&out.result==(u32)result);
            else assert(!memcmp(&out,&untouched,sizeof(out)));
        }
    /* Bounds, source no-award outcomes, and names that contain only spaces. */
    p.type=1;p.hit_rate_index=1;p.npc_type=0;p.npc_code=236;checksum(&p);out=untouched;
    assert(!af_v3_password_decide(policy,n,&p,player,town,&ops,&out));
    p.npc_type=1;p.npc_code=32;checksum(&p);assert(!af_v3_password_decide(policy,n,&p,player,town,&ops,&out));
    p.npc_code=31;memset(p.str0,32,8);checksum(&p);memset(player,32,8);
    assert(af_v3_password_decide(policy,n,&p,player,town,&ops,&out)==AF_PW_WRONG_NAME);
    p.type=3;p.npc_type=p.npc_code=255;p.hit_rate_index=3;checksum(&p);c.roll=0;
    assert(af_v3_password_decide(policy,n,&p,player,town,&ops,&out)==AF_PW_MAGAZINE_LOSE);
    p.hit_rate_index=4;checksum(&p);c.roll=99.999f;
    assert(af_v3_password_decide(policy,n,&p,player,town,&ops,&out)==AF_PW_MAGAZINE_WIN);
    c.enabled=0;c.rolls=0;out=untouched;
    assert(!af_v3_password_decide(policy,n,&p,player,town,&ops,&out)&&!c.rolls);
    c.enabled=1;c.roll=NAN;
    assert(!af_v3_password_decide(policy,n,&p,player,town,&ops,&out));
    c.roll=100;assert(!af_v3_password_decide(policy,n,&p,player,town,&ops,&out));
    c.roll=-1;assert(!af_v3_password_decide(policy,n,&p,player,town,&ops,&out));
    p.checksum^=1;c.rolls=0;assert(!af_v3_password_decide(policy,n,&p,player,town,&ops,&out)&&!c.rolls);
    assert(!memcmp(&out,&untouched,sizeof(out)));
    for(u32 result=0;result<16;result++)assert(af_v3_password_result_gives_item(result)==
        (result==1||result==2||result==3||result==5||result==6));
    for(u32 size=0;size<n;size++)assert(!af_v3_password_policy_valid(policy,size));
    for(u32 size=0;size<m;size++)assert(!af_v3_password_map_valid(map,size));
    assert(!af_v3_password_policy_valid(NULL,n));assert(!af_v3_password_map_valid(NULL,m));
    const u32 bad_policy[]={0,4,6,8,10,12,14,16,21,32,36,37};
    for(u32 i=0;i<sizeof(bad_policy)/sizeof(bad_policy[0]);i++) {
        memcpy(changed,policy,n);changed[bad_policy[i]]=254;
        assert(!af_v3_password_policy_valid(changed,n));
    }
    const u32 bad_map[]={0,4,6,8,10,12,16,20,24,25};
    for(u32 i=0;i<sizeof(bad_map)/sizeof(bad_map[0]);i++) {
        memcpy(changed,map,m);changed[bad_map[i]]=254;c.reads=0;
        assert(!af_v3_password_map_valid(changed,m));
        assert(!af_v3_password_resolve(changed,m,half(map+16),read_enabled,&c)&&!c.reads);
    }
    /* One complete input-code -> current imported identity -> decision chain.
       Codec/reference equivalence is retained from its unchanged batch. */
    u32 codec_size=load(argv[4],codec,sizeof(codec)),candidate=0;
    while(candidate<count&&!(masks[half(map+16+candidate*12)]&4))candidate++;
    assert(candidate<count);u32 source=half(map+16+candidate*12),native=half(map+18+candidate*12);
    memset(&p,0,sizeof(p));p.type=3;p.item=(af_pw_u16)source;p.hit_rate_index=4;
    p.npc_type=p.npc_code=255;memcpy(p.str0,player,8);memcpy(p.str1,town,8);
    u8 text[28];af_v3_password decoded;
    assert(af_v3_password_encode(codec,codec_size,&p,text,28));
    assert(af_v3_password_decode(codec,codec_size,text,28,&decoded));
    c.map=map;c.map_size=m;c.enabled=1;c.roll=99.999f;c.rolls=0;
    assert(af_v3_password_decide(policy,n,&decoded,player,town,&ops,&out)==AF_PW_MAGAZINE_WIN);
    assert(out.item==native&&out.source_item==source&&c.rolls==1);
    c.enabled=0;c.rolls=0;out=untouched;
    assert(!af_v3_password_decide(policy,n,&decoded,player,town,&ops,&out)&&!c.rolls);
    assert(!memcmp(&out,&untouched,sizeof(out)));
    puts("Source decisions, complete permissions, live selections, and no-gift outcomes pass");
    return 0;
}
