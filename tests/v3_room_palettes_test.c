#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/room_rigs.c"

RoomRigTable af_v3_test_room_rigs;
RoomRigClip *af_v3_test_room_clip;
u16 af_v3_test_room_hour,af_v3_test_room_minute;
u8 af_v3_test_roof_common[0x10004];
const u16 *af_v3_test_roof_field;
static _Alignas(32) u8 bank[9216],arena[32768];
static RoomRigGraphics graphics;
static unsigned matrices,flushes,frames;
typedef struct {u32 magic;u16 bytes,count;u32 on,off,models[3],colours;} Layout;
int mHS_get_arrange_idx(int player) {
    assert(player>=0 && player<4);
    return af_v3_test_roof_common[0xEF5A]>>(player*2)&3;
}
void *_Matrix_to_Mtx(void *p) {assert(p==graphics.tail);memset(p,0xAA,64);++matrices;return p;}
void osWritebackDCache(void *p,int n) {assert(p==graphics.tail && n==96);++flushes;}
/* Any skeleton path is an incorrect dispatch for these non-rig profiles. */
void *Lib_SegmentedToVirtual(void *p) {(void)p;abort();}
void *_Matrix_to_Mtx_new(void *p) {(void)p;abort();}
void cKF_SkeletonInfo_R_ct(RoomKeyframe *p,void *a,void *b,void *c,void *d) {
    (void)p;(void)a;(void)b;(void)c;(void)d;abort();
}
void cKF_SkeletonInfo_R_init_standard_repeat(RoomKeyframe *p,void *a,void *b) {(void)p;(void)a;(void)b;abort();}
void cKF_SkeletonInfo_R_init_standard_stop(RoomKeyframe *p,void *a,void *b) {(void)p;(void)a;(void)b;abort();}
int cKF_SkeletonInfo_R_play(RoomKeyframe *p) {(void)p;abort();}
void cKF_Si3_draw_R_SV(void *p,RoomKeyframe *a,void *b,void *c,void *d,void *e) {
    (void)p;(void)a;(void)b;(void)c;(void)d;(void)e;abort();
}
static u32 be(const u8 *p,int n) {u32 v=0;while(n--)v=v*256+*p++;return v;}
static float fade(const RoomRig *a) {float f;memcpy(&f,(const u8 *)a+0x1A4,4);return f;}
static u32 roof(const RoomRig *a) {u32 n;memcpy(&n,(const u8 *)a+0x1A8,4);return n;}
static void colour(int home,int n) {af_v3_test_roof_common[0x3588+home*0xB48+0x24]=(u8)n;}
static void guard(const RoomRig *a,RoomRig before) {
    memcpy((u8 *)&before+0x1A4,(const u8 *)a+0x1A4,8);
    assert(!memcmp(a,&before,sizeof(before)));
}
static void palette(const u16 *p,const Layout *layout,int n,float t) {
    const u16 *on=(const u16 *)(bank+layout->on+n*32),*off=(const u16 *)(bank+layout->off+n*32);
    for(int i=0;i<16;++i) {
        unsigned result=off[i]&1;
        for(int shift=1;shift<16;shift+=5) {
            int a=off[i]>>shift&31,b=on[i]>>shift&31;
            result|=((unsigned)(a+t*(b-a))&31)<<shift;
        }
        assert(p[i]==result);
    }
}
static const u16 *draw(RoomRig *a,RoomRigGame *game,const Layout *layout) {
    RoomCommand *head=graphics.head;unsigned before=matrices;
    af_v3_room_rig_dw(a,0,game,bank);
    assert(matrices==before+1 && flushes==matrices && graphics.head==head+5);
    assert(head[0].a==0xDA380003 && head[1].a==0xDB060020);
    for(int i=0;i<3;++i)assert(head[i+2].a==0xDE000000 && head[i+2].b==layout->models[i]);
    const u16 *p=(u16 *)(graphics.tail+64);palette(p,layout,roof(a),fade(a));++frames;return p;
}
int main(int argc,char **argv) {
    assert(argc==3);
    RoomRigGame game={.gfx=&graphics};
    for(int f=1;f<argc;++f) {
        FILE *file=fopen(argv[f],"rb");assert(file);
        size_t n=fread(bank,1,sizeof(bank),file);assert(n && fgetc(file)==EOF && !fclose(file));
        Layout layout={be(bank,4),be(bank+4,2),be(bank+6,2),be(bank+8,4),be(bank+12,4),{0},be(bank+28,4)};
        for(int i=0;i<3;++i)layout.models[i]=be(bank+16+i*4,4);
        assert(layout.bytes==n && layout.colours==12);memcpy(bank,&layout,sizeof(layout));
        for(int role=0;role<2;++role)for(int i=0;i<384;i+=2) {
            u8 *p=bank+(role?layout.on:layout.off)+i;u16 v=be(p,2);memcpy(p,&v,2);
        }
        af_v3_test_room_rigs=(RoomRigTable){ROOM_RIG_MAGIC,1,24,0,{{0}}};
        af_v3_test_room_rigs.rows[0]=(RoomRigRecord){.index=1100,.bytes=n,.mode=7,.first={.bits=12}};
        /* All colours, all four room identities, both ordinary/menu indices,
           all player-home arrangements, and the source's other-place fallback. */
        for(int c=0;c<12;++c)for(int home=0;home<4;++home)for(int preview=0;preview<2;++preview) {
            memset(arena,0xA5,sizeof arena);
            graphics.head=(RoomCommand *)(arena+32);graphics.tail=arena+sizeof(arena)-32;
            RoomRig a;memset(&a,0xA5,sizeof(a));a.index=1100+(preview?1024:0);a.ctr_type=preview?0:1;a.switched=0;
            u16 field=0x6000+home;af_v3_test_roof_field=&field;
            af_v3_test_roof_common[0x10003]=home;
            af_v3_test_roof_common[0xEF5A]=(u8)(preview?0x1B:0xE4);
            for(int j=0;j<4;++j)colour(j,(c+j)%12);
            int selected=preview?3-home:home,expected=(c+selected)%12;
            RoomRig before=a;af_v3_room_rig_ct(&a,bank);guard(&a,before);
            assert(roof(&a)==(u32)expected && fade(&a)==0);
            const u16 *first=draw(&a,&game,&layout);u16 saved[16];memcpy(saved,first,32);
            float t=0;
            for(int tick=0;tick<24;++tick) {
                a.switched=tick<4||tick>=8;float target=a.switched;
                if(t>target){t-=.1f;if(t<target)t=target;}
                else if(t<target){t+=.1f;if(t>target)t=target;}
                expected=(expected+1)%12;colour(selected,expected);
                before=a;af_v3_room_rig_mv(&a,0,&game,bank);guard(&a,before);
                assert(fade(&a)==t && roof(&a)==(u32)expected);draw(&a,&game,&layout);
                assert(!memcmp(first,saved,32));
            }
            colour(selected,255);af_v3_room_rig_mv(&a,0,&game,bank);assert(roof(&a)==0);
            if(preview)af_v3_test_roof_common[0x10003]=255;else field=0x5000;
            af_v3_room_rig_ct(&a,bank);assert(roof(&a)==0 && fade(&a)==1);
            af_v3_test_roof_field=0;af_v3_room_rig_ct(&a,bank);assert(roof(&a)==0);
            for(int i=0;i<32;++i)assert(arena[i]==0xA5 && arena[sizeof(arena)-1-i]==0xA5);
        }
        RoomRig a={.index=1100};af_v3_room_rig_ct(&a,bank);
        for(int test=0;test<9;++test) {
            Layout bad=layout;
            switch(test) {
            case 0:bad.magic^=1;break;case 1:bad.bytes-=16;break;case 2:bad.count=4;break;
            case 3:bad.on=layout.bytes-32;break;case 4:bad.off=0;break;case 5:bad.colours=1;break;
            case 6:bad.models[2]=0x06000001;break;case 7:bad.models[1]=0x08000000;break;
            case 8:bad.off=33;break;
            }
            memcpy(bank,&bad,sizeof(bad));unsigned before=matrices;
            graphics.head=(RoomCommand *)(arena+32);graphics.tail=arena+sizeof(arena)-32;
            af_v3_room_rig_dw(&a,0,&game,bank);assert(matrices==before);
        }
        memcpy(bank,&layout,sizeof layout);
        for(int available=0;available<=192;available+=8) {
            graphics.head=(RoomCommand *)(arena+32);graphics.tail=arena+32+available;
            RoomCommand *head=graphics.head;u8 *tail=graphics.tail;unsigned before=matrices;
            af_v3_room_rig_dw(&a,0,&game,bank);
            uptr allocation=available>=96?((uptr)tail-96)&~(uptr)31:0;
            int fits=available>=136 && allocation>=(uptr)head+40;
            if(!fits)assert(matrices==before && graphics.head==head && graphics.tail==tail);
            else assert(matrices==before+1 && (uptr)graphics.head<=(uptr)graphics.tail);
        }
    }
    printf("Selected roof dispatcher: %u frames, all colours/homes/previews, fades, retained palettes, and bounds pass\n",frames);
}
