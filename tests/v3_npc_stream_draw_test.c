#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/npc_stream_draw.c"
static AFNpcStreamRecord row;
static unsigned int calls,mode,known;
static void *expected[4];
u32 af_npc_stream_segments[16];
const AFNpcStreamRecord *af_v3_npc_stream_record(unsigned int name) {
    return known && name==row.name?&row:0;
}
static int callback(void *a,void *b,int c,void *d,void *e,void *f,void *h,void *i) {
    (void)a;(void)b;(void)c;(void)d;(void)e;(void)f;(void)h;(void)i;return 1;
}
void af_npc_stream_skeleton(void *game,void *sk,void *mtx,AFNpcDrawCallback before,
        AFNpcDrawCallback after,void *actor) {
    assert(game==expected[0] && sk==expected[1] && mtx==expected[2] && actor==expected[3]);
    assert(before==callback && after==callback);++calls;
    Graphics *g=*(Graphics **)game;
    if(mode==1)g->p=g->d; /* No room for restoring segment state. */
    else {*g->p++=(Command){0xDE000000,0x06000100};*g->xp++=(Command){0xDE000000,0x06000200};}
}
int main(void) {
    union {u32 align;u8 bytes[0x93C];} npc={0};u8 *a=npc.bytes;
    Command opa[32],xlu[32];Graphics graph={0},*g=&graph;
    union {void *align;u8 bytes[0x2000];} play={0};void *game=play.bytes;
    *(Graphics **)game=g;*(u32 *)(play.bytes+0x1904)=1;
    *(u16 *)(play.bytes+0x110)=500;*(u32 *)(play.bytes+0x114)=0x80500000;
    *(u32 *)(play.bytes+0x120)=0x1620;
    *(u16 *)(a+6)=0x1234;row.name=0x1234;row.texture_bytes=0x1620;
    row.body_offset=0x20;row.mouth_count=6;
    *(u32 *)(a+0x750)=0x06000000;
    *(u32 *)(a+0x74C)=0x06000020;
    for(unsigned int i=0;i<8;++i) {
        row.eyes[i]=0x820+i*256;*(u32 *)(a+0x754+4*i)=0x06000000+row.eyes[i];
    }
    for(unsigned int i=0;i<6;++i) {
        row.mouths[i]=0x820+(8+i)*256;*(u32 *)(a+0x774+4*i)=0x06000000+row.mouths[i];
    }
    for(unsigned int i=0;i<16;++i)af_npc_stream_segments[i]=0x1000*i;
    expected[0]=game;expected[1]=a+0x198;expected[2]=opa;expected[3]=a;
    known=1;
    for(unsigned int eyes=0;eyes<8;++eyes)for(unsigned int mouth=0;mouth<6;++mouth) {
        a[0x710]=eyes;a[0x71C]=mouth;
        graph.p=opa;graph.d=opa+32;graph.xp=xlu;graph.xd=xlu+32;
        af_v3_npc_stream_draw(game,a+0x198,opa,callback,callback,a);
        assert(graph.p==opa+7 && graph.xp==xlu+7);
        assert(opa[0].a==0xDB06001C && opa[0].b==0x500020);
        assert(opa[1].b==0x500000u+row.eyes[eyes] && opa[2].b==0x500000u+row.mouths[mouth]);
        for(unsigned int i=0;i<3;++i)assert(opa[4+i].b==af_npc_stream_segments[7+i]);
        assert(!memcmp(opa,xlu,3*sizeof(Command)));
    }
    assert(calls==48);
    row.mouth_count=0;row.texture_bytes=0x1020;
    a[0x71C]=255;
    graph.p=opa;graph.xp=xlu;
    af_v3_npc_stream_draw(game,a+0x198,opa,callback,callback,a);
    assert(calls==49 && graph.p==opa+5 && graph.xp==xlu+5);
    for(unsigned int invalid=0;invalid<9;++invalid) {
        graph.p=opa;graph.xp=xlu;graph.d=opa+32;a[0x710]=0;
        if(invalid==0)a[0x710]=8;
        if(invalid==1)row.texture_bytes=4095;
        if(invalid==2)row.body_offset=0x21;
        if(invalid==3)*(u32 *)(a+0x754)=0x06000024;
        if(invalid==4)graph.d=opa+3;
        if(invalid==5)*(u32 *)(a+0x708)=1;
        if(invalid==6)*(u16 *)(play.bytes+0x110)=(u16)-500;
        if(invalid==7)*(u32 *)(play.bytes+0x120)=0x1000;
        if(invalid==8)*(u32 *)(play.bytes+0x114)=0x807FFFF0;
        af_v3_npc_stream_draw(game,a+0x198,opa,callback,callback,a);
        assert(calls==49 && graph.p==opa && graph.xp==xlu);
        row.texture_bytes=0x1020;row.body_offset=0x20;*(u32 *)(a+0x754)=0x06000820;
        *(u32 *)(a+0x708)=0;*(u16 *)(play.bytes+0x110)=500;
        *(u32 *)(play.bytes+0x120)=0x1620;*(u32 *)(play.bytes+0x114)=0x80500000;
    }
    graph.d=opa+32;mode=1;
    af_v3_npc_stream_draw(game,a+0x198,opa,callback,callback,a);
    assert(calls==50 && graph.p==opa && graph.xp==xlu && graph.d==opa+32);
    known=0;mode=0;
    af_v3_npc_stream_draw(game,a+0x198,opa,callback,callback,a);
    assert(calls==51 && graph.p==opa+1 && graph.xp==xlu+1);
    /* Fixed-face costume models have no eye/mouth expressions. Preserve
     * that absence rather than loading a fake eye at the palette pointer. */
    known=1;memset(row.eyes,0,sizeof row.eyes);memset(a+0x754,0,8*4);
    graph.p=opa;graph.xp=xlu;a[0x710]=255;
    af_v3_npc_stream_draw(game,a+0x198,opa,callback,callback,a);
    assert(calls==52 && graph.p==opa+3 && graph.xp==xlu+3);
    assert(opa[0].a==0xDB06001C && opa[0].b==0x500020);
    assert(opa[2].a==0xDB06001C && opa[2].b==af_npc_stream_segments[7]);
    row.eyes[1]=0x820;graph.p=opa;graph.xp=xlu;
    af_v3_npc_stream_draw(game,a+0x198,opa,callback,callback,a);
    assert(calls==52 && graph.p==opa && graph.xp==xlu);
    row.eyes[1]=0;*(u32 *)(a+0x754)=0x06000820;
    af_v3_npc_stream_draw(game,a+0x198,opa,callback,callback,a);
    assert(calls==52 && graph.p==opa && graph.xp==xlu);
    puts("complete expressions, native fallback, argument forwarding, bounds, and segment restoration pass");
    return 0;
}
