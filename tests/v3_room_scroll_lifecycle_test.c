#define AF_V3_ROOM_SCROLL_LIFECYCLE 1
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/room_scroll.c"
RoomScrollTable af_v3_test_room_scroll;
RoomScrollLives af_v3_test_room_scroll_lives;
u8 *af_v3_room_debug;
void *_Matrix_to_Mtx(void *p) { return p; }
void osWritebackDCache(void *p,int n) { (void)p;(void)n; }
static RoomScrollActor *active;
static unsigned loops,clicks,last_sound,last_click;
void sAdo_OngenPos(u32 handle,u8 sound,float *position) {
    assert(handle==(u32)(uptr)active && position==active->position);
    ++loops;last_sound=sound;
}
void sAdo_OngenTrgStart(u32 sound,float *position) {
    assert(position==active->position);++clicks;last_click=sound;
}
static u32 word(FILE *f,unsigned n) {
    u32 v=0;
    while (n--) { int c=fgetc(f);assert(c!=EOF);v=(v<<8)|(unsigned)c; }
    return v;
}
int main(int argc,char **argv) {
    assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);
    RoomScrollLives *t=&af_v3_test_room_scroll_lives;
    t->magic=word(f,4);t->count=word(f,4);t->stride=word(f,4);t->reserved=word(f,4);
    assert(t->count==4 && t->stride==12);
    for (unsigned i=0;i<t->count;++i) {
        RoomScrollLife *r=t->rows+i;
        r->index=word(f,2);r->mode=word(f,1);r->flags=word(f,1);
        r->sound=word(f,2);r->on=word(f,2);r->off=word(f,2);
        r->maximum=word(f,1);r->step=word(f,1);
    }
    assert(fgetc(f)==EOF);fclose(f);
    struct { u8 front[16];RoomScrollActor actor;u8 back[16]; } guarded;
    active=&guarded.actor;
    for (unsigned n=0;n<t->count;++n) for (unsigned alias=0;alias<2;++alias) {
        RoomScrollLife *r=t->rows+n;
        for (unsigned saved=0;saved<3;++saved) {
            memset(&guarded,0xA7,sizeof(guarded));
            active->index=r->index+alias*1024;active->state=0;
            active->saved_switch=saved;active->changed=0;
            RoomScrollActor before=*active;
            af_v3_room_scroll_ct(active,NULL);
            if (r->mode==1)assert(!memcmp(active,&before,sizeof(before)));
            else {
                assert(active->private_switch==(saved==1));
                assert(active->colour.f==(saved==1 ? r->maximum : 0));
            }
            loops=clicks=0;
            af_v3_room_scroll_mv(active,NULL,NULL,NULL);
            assert(loops==(r->mode==1 ? 1u : saved==1 ? 2u : 0u));
            if (loops)assert(last_sound==r->sound);
            if (r->mode==2) {
                /* One edge; the second source half advances the new fade. */
                active->changed=1;loops=clicks=0;
                int on=saved!=1;
                af_v3_room_scroll_mv(active,NULL,NULL,NULL);
                assert(active->private_switch==on && active->changed==1);
                assert(active->colour.f==(on ? r->step : r->maximum-r->step));
                assert(loops==1 && clicks==(r->on!=0));
                if (clicks)assert(last_click==(on ? r->on : r->off));
                /* An edge during a fade is ignored, including a first half
                   that arrives at the target. It cannot reappear in half two. */
                for (unsigned tick=0;tick<70;++tick) {
                    float old=active->colour.f,target=on ? r->maximum : 0;
                    active->changed=old!=target;loops=clicks=0;
                    af_v3_room_scroll_mv(active,NULL,NULL,NULL);
                    float want=old+(on ? 2*r->step : -2*(int)r->step);
                    if (on && want>target)want=target;
                    if (!on && want<target)want=target;
                    assert(active->colour.f==want && active->private_switch==on);
                    assert(loops==(on ? 2u : 0u) && clicks==0);
                }
                active->saved_switch=2;
                af_v3_room_scroll_dt(active,NULL);
                assert(active->saved_switch==(r->flags ? on : 2));
                active->private_switch=1;active->colour.f=r->maximum;
            }
            for (int state=0;state<=16;++state) {
                active->state=state;active->changed=0;loops=clicks=0;
                af_v3_room_scroll_mv(active,NULL,NULL,NULL);
                assert(loops==((state==5 || state==6 || state==13 || state==15) ? 0u : r->mode==1 ? 1u : 2u));
            }
            if (r->on) {
                active->state=5;active->changed=1;loops=clicks=0;
                af_v3_room_scroll_mv(active,NULL,NULL,NULL);
                assert(!loops && clicks==1 && last_click==r->off);
            }
            for (unsigned i=0;i<16;++i)assert(guarded.front[i]==0xA7 && guarded.back[i]==0xA7);
            /* All owner fields except the explicitly mapped private/save
               fields are immutable across the complete lifecycle. */
            assert(!memcmp(active->before_position,before.before_position,sizeof(before.before_position)));
            assert(!memcmp(active->before_private,before.before_private,sizeof(before.before_private)));
        }
    }
    for (unsigned bad=0;bad<18;++bad) {
        RoomScrollLives original=*t;RoomScrollLife *r=t->rows;
        memset(active,0,sizeof(*active));active->index=r->index;
        active->private_switch=1;active->colour.f=r->maximum;
        if (bad==0)t->magic^=1;
        if (bad==1)t->count=65;
        if (bad==2)t->stride=13;
        if (bad==3)t->reserved=1;
        if (bad==4)r->mode=3;
        if (bad==5)r->flags=2;
        if (bad==6)r->sound=96;
        if (bad==7)r->sound=67;
        if (bad==8)r->on=128;
        if (bad==9)r->off=1;
        if (bad==10)r->maximum=1; /* loop-only row cannot carry fade data */
        if (bad>=11 && bad<=13) {
            r->mode=2;r->maximum=100;r->step=4;
            if (bad==11)active->private_switch=2;
            if (bad==12)active->colour.bits=0x7FC00000;
            if (bad==13)active->colour.f=101;
        }
        if (bad==14)active->index=0;
        if (bad==15)active->index=1024; /* absent lifecycle stays a no-op */
        if (bad==16) { r->mode=2;r->maximum=0;r->step=1; }
        if (bad==17) { r->mode=2;r->maximum=1;r->step=2; }
        RoomScrollActor before=*active;loops=clicks=0;
        af_v3_room_scroll_mv(active,NULL,NULL,NULL);
        assert(!loops && !clicks && !memcmp(active,&before,sizeof(before)));
        *t=original;
    }
    af_v3_room_scroll_ct(NULL,NULL);af_v3_room_scroll_mv(NULL,NULL,NULL,NULL);af_v3_room_scroll_dt(NULL,NULL);
    puts("Source-shaped fades, switch edges, positioned sounds, persistence, and bounded rejection pass");
}
