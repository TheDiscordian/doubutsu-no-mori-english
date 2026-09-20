/* Complete ac_balloon state machine. Every balloon owns both of its banks;
   releasing the player's held banks cannot invalidate a flying balloon. */
#include "balloon_actor.h"

void *af_v3_balloon_descriptor(int id) {
#ifdef __mips__
    if (id==0xCB) return (void *)0x804AEA40u;
#endif
    return BFN(0x804A0360u,void *,int)(id);
}

void af_v3_balloon_hide(Balloon *b,void *game) {
    (void)game;
    b->pending=0;
}

int af_v3_balloon_fly(Balloon *b,void *game,int type,const BalloonAngle *angle,s16 lean,
                     const BalloonPosition *pos,float frame,float speed) {
    (void)game;
    int shape=(unsigned)type<8u?type:0;
    if (!b || !angle || !pos || af_v3_player_selected_equipment((u32)(0x2244+shape))!=91+shape) return 0;
    b->pending=1;b->type=type;b->angle=*angle;b->lean=lean;
    b->frame=frame;b->speed=speed;b->position=*pos;
    return 1;
}

/* Return a segment-six pointer only after the entire resource is transferred. */
static u32 load(u8 *bank,u32 capacity,int index) {
    u32 n=BFN(0x800B131Cu,u32,int)(index);
    u32 p=BFN(0x800B12C8u,u32,int)(index);
    u32 rom=BFN(0x800B1650u,u32,int)(index);
    if (!n || n>capacity || !p || rom<0x02200000u || rom>=0x025F0000u || n>0x025F0000u-rom ||
            BFN(0x80026B44u,int,void *,u32,u32)(bank,rom,n)) return 0;
    BSEG=(u32)(uptr)bank&0x1FFFFFFFu;
    return p;
}

static void setup_fly(Balloon *b) {
    int shape=(unsigned)b->type<8u?b->type:0;
    u32 saved=BSEG,p;
    b->ready=0;
    p=load(b->model,sizeof(b->model),40+shape);
    if (!p) goto failed;
    BFN(0x80052228u,void,void *,void *,void *,void *,void *)
        (b->keyframe,(void *)(uptr)p,0,b->work,b->morph);
    p=load(b->animation,sizeof(b->animation),b->frame<1.0f?48:49);
    if (!p) goto failed;
    BFN(0x800531F0u,void,void *,void *,void *,float,float,float)
        (b->keyframe,(void *)(uptr)p,0,b->frame,0.0f,0.0f);
    BFN(0x800528D4u,int,void *)(b->keyframe);
    p=load(b->animation,sizeof(b->animation),48);
    if (!p) goto failed;
    BFN(0x800531F0u,void,void *,void *,void *,float,float,float)
        (b->keyframe,(void *)(uptr)p,0,1.0f,.5f,-5.0f);
    *(BalloonAngle *)(b->actor+0xDC)=b->angle;
    BREAL(b,0x6C)=0.0f;BREAL(b,0x7C)=b->speed;
    /* Native speed_set has no donor half-step, so supply gravity/2. */
    BREAL(b,0x78)=.1f;BPOS(b,0x28)=b->position;
    b->saved_type=b->type;b->mode=1;b->pending=-1;b->ready=1;
    BSEG=saved;return;
failed:
    b->mode=0;b->pending=-1;BSEG=saved;
}

static void source_step(Balloon *b,void *game) {
    if (b->pending==0) { b->mode=0;b->pending=-1; }
    else if (b->pending==1) setup_fly(b);
    void *player=BFN(0x800B1C84u,void *,void *)(game);
    if (b->mode==0) {
        if (player) BPOS(b,0x28)=BPOS(player,0x28);
    } else if (b->mode==1 && b->ready) {
        u32 saved=BSEG;
        BSEG=(u32)(uptr)b->animation&0x1FFFFFFFu;
        BFN(0x800528D4u,int,void *)(b->keyframe);
        BSEG=saved;
        BFN(0x8009A974u,void,s16 *,s16,float,s16,s16)(&BSHORT(b,0xDC),0,.2928932309f,50,5);
        BFN(0x8009A974u,void,s16 *,s16,float,s16,s16)(&BSHORT(b,0xE0),0,.2928932309f,50,5);
        BFN(0x8009A974u,void,s16 *,s16,float,s16,s16)(&b->lean,0,.2928932309f,50,5);
        BFN(0x8005652Cu,void,void *)(b);
        /* Source Actor_position_move: preserve the native environment callback
           and displacement, but apply the donor's 60-Hz velocity half-step. */
        (*(void (**)(void *))((u8 *)game+0x1C58))(b);
        for (unsigned o=0;o<12;o+=4)
            BREAL(b,0x28+o)+=.5f*BREAL(b,0x68+o)+BREAL(b,0xC4+o);
        if (player && BREAL(b,0x2C)-BREAL(player,0x2C)>200.0f) b->pending=0;
    }
}

void af_v3_balloon_main(Balloon *b,void *game) {
    source_step(b,game);source_step(b,game);
}

void af_v3_balloon_ct(Balloon *b,void *game) {
    b->ready=0;b->mode=0;af_v3_balloon_hide(b,game);
}

void af_v3_balloon_dt(Balloon *b,void *game) { (void)b;(void)game; }

void af_v3_balloon_player_init(void *player,void *game) {
    BFN(0x808BCC48u,void,void *,void *)(player,game);
    Balloon **slot=(Balloon **)((u8 *)player+0x13A0);
    *slot=0;
    for (int shape=0;shape<8;++shape) {
        if (af_v3_player_selected_equipment((u32)(0x2244+shape))!=91+shape) continue;
        BalloonPosition p=BPOS(player,0x28);
        *slot=BFN(0x80057E24u,Balloon *,void *,void *,s16,float,float,float,s16,s16,s16,
                   signed char,signed char,s16,u16,s16,signed char,int)
            ((u8 *)game+0x1C78,game,0xCB,p.x,p.y,p.z,0,0,0,-1,-1,-1,0,-1,-1,-1);
        break;
    }
}
