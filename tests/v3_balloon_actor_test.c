#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/balloon_actor.c"
#include "../overlays/v3/held_selection.c"

u32 af_test_balloon_segment=0x12345678;
u32 af_test_held_selection[188];
u8 af_test_held_profile[192];
static Balloon b;
static _Alignas(16) u8 player[0x13B0],game[0x1D00];
static int reads,plays,inits,model_index,fail_dma,nature_calls,old_init,makes,fail_make;
static float seed_frame,seed_speed,seed_morph;
static void *lookup(int id) { return (void *)(uptr)(0x1000+32*id); }
static void *get_player(void *g) { assert(g==game);return player; }
static u32 size(int index) { return index<48?5728:index==48?304:1440; }
static u32 pointer(int index) { return 0x6000000+index*4; }
static u32 origin(int index) { return 0x2200000+index*0x2000; }
static int dma(void *dst,u32 rom,u32 n) {
    int index=(rom-0x2200000)/0x2000;reads++;
    assert((index<48 && dst==b.model) || (index>=48 && dst==b.animation));
    if (index<48) model_index=index;
    if (fail_dma && reads==fail_dma) return -1;
    memset(dst,index,n);return 0;
}
static void ct(void *kf,void *skel,void *anim,void *work,void *morph) {
    assert(kf==b.keyframe && skel==((void *)(uptr)pointer(model_index)) && !anim);
    assert(work==b.work && morph==b.morph);
}
static void init(void *kf,void *anim,void *diff,float frame,float speed,float morph) {
    assert(kf==b.keyframe && !diff);
    if (!inits) {
        seed_frame=frame;seed_speed=speed;seed_morph=morph;
        assert(anim==(void *)(uptr)pointer(frame<1?48:49));
    } else { assert(frame==1 && speed==.5f && morph==-5 && anim==(void *)(uptr)pointer(48)); }
    inits++;
}
static int play(void *kf) { assert(kf==b.keyframe);plays++;return 0; }
static void smooth(s16 *angle,s16 target,float ratio,s16 max,s16 min) {
    assert(!target && ratio>.2928f && ratio<.2930f && max==50 && min==5);
    int step=*angle*ratio;
    if (step>max) step=max;
    if (step< -max) step=-max;
    if (*angle>0 && step<min) step=min;
    if (*angle<0 && step> -min) step=-min;
    if (step>*angle && *angle>=0) step=*angle;
    if (step<*angle && *angle<0) step=*angle;
    *angle-=step;
}
static void speed_set(void *actor) {
    assert(actor==&b && BREAL(actor,0x78)==.1f);
    BREAL(actor,0x6C)+=.1f;
    if (BREAL(actor,0x6C)>BREAL(actor,0x7C)) BREAL(actor,0x6C)=BREAL(actor,0x7C);
}
static void nature(void *actor) { assert(actor==&b);nature_calls++; }
static void original(void *p,void *g) { assert(p==player && g==game);old_init++; }
static Balloon *make(void *info,void *g,s16 id,float x,float y,float z,s16 ax,s16 ay,s16 az,
                     signed char bx,signed char bz,s16 q,u16 fg,s16 p,signed char n,int bank) {
    assert(info==game+0x1C78 && g==game && id==0xCB);
    assert(x==1 && y==2 && z==3 && !ax && !ay && !az);
    assert(bx==-1 && bz==-1 && q==-1 && !fg && p==-1 && n==-1 && bank==-1);
    makes++;return fail_make?0:&b;
}
void *af_test_balloon_function(u32 at) {
    switch (at) {
    case 0x804A0360:return lookup;case 0x800B1C84:return get_player;
    case 0x800B131C:return size;case 0x800B12C8:return pointer;case 0x800B1650:return origin;
    case 0x80026B44:return dma;case 0x80052228:return ct;case 0x800531F0:return init;
    case 0x800528D4:return play;case 0x8009A974:return smooth;case 0x8005652C:return speed_set;
    case 0x808BCC48:return original;case 0x80057E24:return make;
    default:assert(0);return 0;
    }
}
static void reset(void) {
    memset(&b,0,sizeof(b));reads=plays=inits=nature_calls=0;fail_dma=0;
    BPOS(player,0x28)=(BalloonPosition){1,2,3};
    *(void (**)(void *))(game+0x1C58)=nature;
    af_v3_balloon_ct(&b,game);
}
int main(void) {
    af_test_held_selection[0]=0x41464853;af_test_held_selection[1]=1;
    af_test_held_selection[2]=92;af_test_held_selection[3]=8;
    Entry *rows=(Entry *)(af_test_held_selection+4);
    for (int i=0;i<8;++i) rows[68+i]=(Entry){0x2244+i,91+i,1,32,1<<i,1};
    af_test_held_profile[32]=255;
    BalloonAngle a={400,1234,-200};BalloonPosition p={10,20,30};
    reset();af_v3_balloon_main(&b,game);
    assert(!b.mode && b.pending==-1 && !memcmp(&BPOS(&b,0x28),&BPOS(player,0x28),12));
    assert(!reads && !plays);
    for (int shape=0;shape<8;++shape) {
        reset();float frame=shape&1?12:-1;
        assert(af_v3_balloon_fly(&b,game,shape,&a,100,&p,frame,7));
        af_v3_balloon_main(&b,game);
        assert(b.ready && b.mode==1 && b.pending==-1 && b.saved_type==shape);
        assert(model_index==40+shape && reads==3 && plays==3 && inits==2 && nature_calls==2);
        assert(seed_frame==frame && seed_speed==0 && seed_morph==0);
        assert(BREAL(&b,0x2C)>20.149f && BREAL(&b,0x2C)<20.151f && BSHORT(&b,0xDE)==1234);
        assert(af_test_balloon_segment==0x12345678 && b.model[5727]==40+shape && b.animation[1439]==(frame<1?0:49));
        for (int i=0;i<100 && b.mode;++i) af_v3_balloon_main(&b,game);
        assert(!b.mode && b.pending==-1 && !memcmp(&BPOS(&b,0x28),&BPOS(player,0x28),12));
    }
    for (int failure=1;failure<=3;failure++) {
        reset();fail_dma=failure;
        assert(af_v3_balloon_fly(&b,game,0,&a,0,&p,-1,7));af_v3_balloon_main(&b,game);
        assert(!b.mode && !b.ready && b.pending==-1 && !nature_calls && af_test_balloon_segment==0x12345678);
    }
    reset();af_test_held_profile[32]=0;
    assert(!af_v3_balloon_fly(&b,game,0,&a,0,&p,-1,7));assert(b.pending==0);
    af_v3_balloon_player_init(player,game);assert(old_init==1 && !makes && !*(Balloon **)(player+0x13A0));
    af_test_held_profile[32]=0x80;af_v3_balloon_player_init(player,game);
    assert(old_init==2 && makes==1 && *(Balloon **)(player+0x13A0)==&b);
    fail_make=1;af_v3_balloon_player_init(player,game);
    assert(old_init==3 && makes==2 && !*(Balloon **)(player+0x13A0));
    assert(!af_v3_balloon_fly(0,game,7,&a,0,&p,-1,7));
    af_test_held_profile[32]=1;reset();assert(af_v3_balloon_fly(&b,game,-3,&a,0,&p,-1,7));
    af_v3_balloon_main(&b,game);assert(model_index==40 && b.saved_type==-3);
    assert(af_v3_balloon_descriptor(0xCA)==(void *)(uptr)(0x1000+32*0xCA));
    puts("shared balloon actor pass");return 0;
}
