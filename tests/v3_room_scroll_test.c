#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/room_scroll.c"
RoomScrollTable af_v3_test_room_scroll;
static unsigned matrices,flushes;
static void *flushed;
static int flushed_bytes;
void *_Matrix_to_Mtx(void *value) { ++matrices;memset(value,0x57,64);return value; }
void osWritebackDCache(void *value,int bytes) { ++flushes;flushed=value;flushed_bytes=bytes; }
static u32 word(FILE *input,unsigned n) {
    u32 value=0;
    for (unsigned i=0;i<n;++i) { int c=fgetc(input);assert(c!=EOF);value=(value<<8)|(unsigned)c; }
    return value;
}
int main(int argc,char **argv) {
    assert(argc==2);FILE *input=fopen(argv[1],"rb");assert(input);
    RoomScrollTable *table=&af_v3_test_room_scroll;
    table->magic=word(input,4);table->count=word(input,4);
    table->stride=word(input,4);table->reserved=word(input,4);
    assert(table->count==5);
    for (u32 i=0;i<table->count;++i) {
        RoomScrollRecord *r=table->rows+i;
        r->index=word(input,2);r->bytes=word(input,2);
        r->models=word(input,1);r->segment=word(input,1);r->tiles=word(input,1);r->colour_mode=word(input,1);
        for (unsigned j=0;j<4;++j)r->model_offsets[j]=word(input,2);
        for (unsigned j=0;j<2;++j)for (unsigned k=0;k<2;++k)r->dimensions[j][k]=word(input,1);
        for (unsigned j=0;j<2;++j)for (unsigned k=0;k<2;++k)r->rates[j][k]=(signed char)word(input,1);
        r->colour_a=word(input,4);r->colour_b=word(input,4);r->state_offset=word(input,2);
        r->preview=word(input,1);r->reserved=word(input,1);
    }
    assert(fgetc(input)==EOF);fclose(input);
    _Alignas(16) u8 data[9216],opa[256],xlu[128];memset(data,0x91,sizeof(data));
    struct { u8 front[16];RoomRig actor;u8 back[16]; } guarded;
    RoomRig *actor=&guarded.actor;RoomRigGraphics gfx={0};
    RoomMaterialPlay play={.game={.gfx=&gfx}};RoomRigGame preview={.gfx=&gfx};
    for (unsigned n=0;n<table->count;++n) for (unsigned room=0;room<2;++room) {
        RoomScrollRecord *r=table->rows+n;
        for (unsigned tick=0;tick<13;++tick) {
            u32 frame=tick==12 ? 0xFFFFFFFFu : tick==11 ? 0x80000000u : tick*997u;
            memset(&guarded,0xA7,sizeof(guarded));actor->index=r->index+(room ? 0 : 1024);
            float level=(float)(tick*17)+0.75f;
            if (r->colour_mode)memcpy((u8 *)actor+r->state_offset,&level,4);
            play.play_frame=frame+13;play.game.frame=7;preview.frame=frame;
            u32 native_frame=room ? play.play_frame : preview.frame;
            gfx.head=(RoomCommand *)opa;gfx.tail=opa+sizeof(opa)-(tick&1)*8;
            gfx.xlu_head=(RoomCommand *)xlu;gfx.xlu_tail=xlu+sizeof(xlu);
            memset(opa,0x42,sizeof(opa));memset(xlu,0x43,sizeof(xlu));
            u8 *end=gfx.tail;unsigned before_count=matrices;RoomRig before=*actor;
            af_v3_room_scroll_dw(actor,room ? actor : NULL,room ? &play.game : &preview,data);
            assert(matrices==before_count+1 && matrices==flushes);
            assert(gfx.head==(RoomCommand *)opa+r->models);
            assert(gfx.xlu_head==(RoomCommand *)xlu+3+(r->colour_mode!=0));
            unsigned scratch=64+(2*r->tiles+1)*8;
            assert(gfx.tail==opa+(((uptr)(end-opa)-scratch)&~(uptr)15));
            assert(flushed==gfx.tail && flushed_bytes==(int)scratch);
            RoomCommand *o=(RoomCommand *)opa,*x=(RoomCommand *)xlu,*scroll=(RoomCommand *)(gfx.tail+64);
            assert(o[0].a==0xDA380003 && o[0].b==(u32)(uptr)gfx.tail);
            for (unsigned j=0;j<r->models-1u;++j) {
                assert(o[j+1].a==0xDE000000 && o[j+1].b==0x06000000u+r->model_offsets[j]);
            }
            assert(x[0].a==o[0].a && x[0].b==o[0].b);++x;
            if (r->colour_mode) {
                unsigned c=room ? (unsigned)level : r->preview;
                assert(x->a==(r->colour_a|(r->colour_mode==2 ? c : 0)));
                assert(x->b==(r->colour_b|(r->colour_mode==1 ? c : 0)));++x;
            }
            assert(x->a==0xDB060000u+4*r->segment && x->b==((u32)(uptr)scroll&0x1FFFFFFFu));++x;
            assert(x->a==0xDE000000 && x->b==0x06000000u+r->model_offsets[r->models-1]);
            for (unsigned j=0;j<r->tiles;++j) {
                /* Independent signed 64-bit reference retains modular origins
                   across negative rates and both native/source wrap points. */
                long long s=(long long)native_frame*2*r->rates[j][0]*2;
                long long t=(long long)native_frame*2*r->rates[j][1]*2;
                u32 left=(u32)(s&16383)/4,top=(u32)(t&16383)/4;
                assert(scroll[j*2].a==0xE8000000 && scroll[j*2].b==0);
                assert(scroll[j*2+1].a==(0xF2000000u|(left<<12)|top));
                assert(scroll[j*2+1].b==((j<<24)|(((left+(r->dimensions[j][0]-1)*4)&4095)<<12)|
                                                        ((top+(r->dimensions[j][1]-1)*4)&4095)));
            }
            assert(scroll[r->tiles*2].a==0xDF000000 && scroll[r->tiles*2].b==0);
            assert(!memcmp(actor,&before,sizeof(before)));
            for (unsigned j=0;j<16;++j)assert(guarded.front[j]==0xA7 && guarded.back[j]==0xA7);
            for (u8 *p=(u8 *)gfx.head;p<gfx.tail;++p)assert(*p==0x42);
            for (u8 *p=(u8 *)gfx.xlu_head;p<gfx.xlu_tail;++p)assert(*p==0x43);
        }
    }
    /* Use a coloured record so malformed state and command paths are covered. */
    unsigned coloured=0;while (!table->rows[coloured].colour_mode)++coloured;
    for (unsigned bad=0;bad<24;++bad) {
        RoomScrollTable original=*table;RoomScrollRecord *r=table->rows+coloured;
        actor->index=r->index;float level=77;memcpy((u8 *)actor+0x1A4,&level,4);
        gfx.head=(RoomCommand *)opa;gfx.tail=opa+sizeof(opa);
        gfx.xlu_head=(RoomCommand *)xlu;gfx.xlu_tail=xlu+sizeof(xlu);
        if (bad==0)table->magic^=1;
        if (bad==1)table->count=ROOM_SCROLL_CAPACITY+1;
        if (bad==2)table->stride++;
        if (bad==3)table->reserved=1;
        if (bad==4)r->bytes=9217;
        if (bad==5)r->models=5;
        if (bad==6)r->segment=7;
        if (bad==7)r->tiles=3;
        if (bad==8)r->colour_mode=3;
        if (bad==9)r->model_offsets[0]=r->bytes;
        if (bad==10)r->dimensions[0][0]=7;
        if (bad==11)r->rates[0][0]=17;
        if (bad==12)r->state_offset=0x834;
        if (bad==13)r->reserved=1;
        if (bad==14)gfx.tail=opa+64;
        if (bad==15)gfx.xlu_tail=xlu+16;
        if (bad==16)gfx.head=NULL;
        if (bad==17)gfx.xlu_head=NULL;
        if (bad==18)gfx.tail=opa+sizeof(opa)-4;
        if (bad==19)gfx.xlu_tail=xlu;
        if (bad==20)r->colour_a=0;
        if (bad>=21) {
            FloatWord value={.bits=bad==21 ? 0x7FC00000u : bad==22 ? 0xBF800000u : 0x43800000u};
            memcpy((u8 *)actor+0x1A4,&value,4);
        }
        memset(opa,0x42,sizeof(opa));memset(xlu,0x43,sizeof(xlu));
        RoomRigGraphics before=gfx;unsigned count=matrices;
        af_v3_room_scroll_dw(actor,actor,&play.game,data);
        assert(matrices==count && !memcmp(&before,&gfx,sizeof(gfx)));
        for (unsigned i=0;i<sizeof(opa);++i)assert(opa[i]==0x42);
        for (unsigned i=0;i<sizeof(xlu);++i)assert(xlu[i]==0x43);
        *table=original;
    }
    unsigned count=matrices;
    af_v3_room_scroll_dw(NULL,NULL,&preview,data);
    af_v3_room_scroll_dw(actor,NULL,NULL,data);
    af_v3_room_scroll_dw(actor,NULL,&preview,NULL);
    af_v3_room_scroll_dw(actor,NULL,&preview,data+1);
    assert(matrices==count);
    for (unsigned i=0;i<sizeof(data);++i)assert(data[i]==0x91);
    puts("Scroll timing, colour, split arenas, immutable frames, and bounded rejection pass");
}
