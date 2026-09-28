/* Shared native services for complete source moon/meteor callbacks. No
 * additional effect pool, saved state, or substitute participant behaviour. */
#include "holiday_sky.h"
int af_sky_ready(void *game) {
    AFSkyClip *c=af_sky_native_clip;
    AFSkyClock t=af_sky_native_rtc;
    return game && c && c->request && c->create && c->continuous && c->adjust && c->lookat &&
        af_sky_player(game) && t.hour<24 && t.min<60 && t.sec<60;
}
AFSkyClock af_sky_clock(void) {return af_sky_native_rtc;}
int af_sky_seconds(void) {
    AFSkyClock t=af_sky_native_rtc;return t.hour*3600+t.min*60+t.sec;
}
s16 af_sky_debug(unsigned int i) {
    uptr p=(uptr)af_sky_native_debug;
    if(!p || p&1u || i>=96)return 0;
#ifdef __mips__
    if(p<0x80000000u || p>0x80800000u-0x1C94u)return 0;
#endif
    return *(const s16 *)(p+0x14+2*(33*96+i));
}
void af_sky_request(int id,EffectPosition p,int prio,s16 angle,void *g,u16 name,s16 a,s16 b) {
    if(id>=AF_SKY_MOON && id<=AF_SKY_KIRA && af_sky_ready(g))
        af_sky_native_clip->request(id,p,prio,angle,g,name,a,b);
}
RoomEffect *af_sky_create(s16 id,EffectPosition p,EffectPosition *offset,void *g,void *arg,
        u16 name,int prio,s16 a,s16 b) {
    return id>=AF_SKY_MOON && id<=AF_SKY_KIRA && af_sky_ready(g) ?
        af_sky_native_clip->create(id,p,offset,g,arg,name,prio,a,b):0;
}
void af_sky_continuous(RoomEffect *e,s16 unused,s16 timer) {
    af_sky_native_clip->continuous(e,unused,timer);
}
float af_sky_adjust(s16 n,s16 start,s16 end,float a,float b) {
    return af_sky_native_clip->adjust(n,start,end,a,b);
}
int af_sky_lookat(EffectPosition p) {return af_sky_native_clip->lookat(p);}
void af_sky_attention(int kind,void *actor,EffectPosition *pos) {
    if(kind!=aNPC_ATTENTION_TYPE_POSITION || actor || !pos || !af_sky_native_npc_clip)return;
    void (*call)(int,void *,EffectPosition *)=*(void (**)(int,void *,EffectPosition *))
        ((u8 *)af_sky_native_npc_clip+0x18);
    if(call)call(kind,actor,pos);
}
