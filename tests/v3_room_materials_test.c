#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/room_materials.c"
RoomMaterialTable af_v3_test_room_materials;
static unsigned matrices;
void *_Matrix_to_Mtx_new(void *value) {
    RoomRigGraphics *gfx=value;++matrices;
    gfx->tail-=64;memset(gfx->tail,0x57,64);return gfx->tail;
}
static u32 read_word(FILE *input,unsigned n) {
    u32 value=0;
    for (unsigned i=0;i<n;++i) { int c=fgetc(input);assert(c!=EOF);value=(value<<8)|(unsigned)c; }
    return value;
}
int main(int argc,char **argv) {
    assert(argc==2);FILE *input=fopen(argv[1],"rb");assert(input);
    RoomMaterialTable *table=&af_v3_test_room_materials;
    table->magic=read_word(input,4);table->count=read_word(input,4);
    table->stride=read_word(input,4);table->reserved=read_word(input,4);
    assert(table->count && table->count<=ROOM_MATERIAL_CAPACITY);
    for (u32 i=0;i<table->count;++i) {
        RoomMaterialRecord *r=table->rows+i;
        r->index=read_word(input,2);r->bytes=read_word(input,2);
        r->mode=read_word(input,1);r->segment=read_word(input,1);
        r->frames=read_word(input,1);r->models=read_word(input,1);
        r->divisor=read_word(input,2);r->frame_bytes=read_word(input,2);
        for (unsigned j=0;j<4;++j)r->model_offsets[j]=read_word(input,2);
        for (unsigned j=0;j<8;++j)r->frame_offsets[j]=read_word(input,2);
        r->state_offset=read_word(input,2);r->kind=read_word(input,1);r->reserved=read_word(input,1);
    }
    assert(fgetc(input)==EOF);fclose(input);
    _Alignas(16) u8 model[9216],arena[512];memset(model,0x83,sizeof(model));
    struct { u8 front[16];RoomRig actor;u8 back[16]; } guarded;
    RoomRig *actor=&guarded.actor;RoomRigGraphics gfx={0};RoomMaterialPlay play={.game={.gfx=&gfx}};
    for (u32 n=0;n<table->count;++n) {
        RoomMaterialRecord *r=table->rows+n;
        for (unsigned room=0;room<2;++room) for (unsigned on=0;on<2;++on) {
            memset(&guarded,0xA7,sizeof(guarded));actor->index=r->index+(room ? 0 : 1024);
            ((u8 *)actor)[0x12C]=(u8)on;
            for (unsigned tick=0;tick<300;++tick) {
                /* Last three samples exercise unsigned wrapping and negative
                   signed division without relying on implementation overflow. */
                u32 counter=tick<297 ? tick : tick==297 ? 0x3FFFFFFFu : tick==298 ? 0x40000000u : 0xFFFFFFFFu;
                play.game.frame=counter;play.play_frame=counter+37u;
                actor->joint[0][0]=(s16)(tick-150);
                unsigned long long source_frame=(unsigned long long)(room ? play.play_frame : play.game.frame)*2;
                source_frame&=0xFFFFFFFFu;
                unsigned wanted;
                if (r->mode==2)wanted=(unsigned)(tick-150)&1;
                else if (r->mode==1) {
                    long long signed_frame=(long long)source_frame;
                    if (signed_frame>=0x80000000LL)signed_frame-=0x100000000LL;
                    wanted=room && !on ? 0 : (unsigned)(signed_frame/10)&3;
                } else wanted=(unsigned)(source_frame/r->divisor)%r->frames;
                RoomRig before=*actor;unsigned before_count=matrices;
                gfx.head=(RoomCommand *)arena;gfx.tail=arena+sizeof(arena)-(tick&1)*8;
                u8 *end=gfx.tail;memset(arena,0x42,sizeof(arena));
                af_v3_room_material_dw(actor,room ? actor : NULL,&play.game,model);
                assert(matrices==before_count+1 && gfx.tail==end-64);
                assert(gfx.head==(RoomCommand *)arena+2+r->models);
                RoomCommand *commands=(RoomCommand *)arena;
                assert(commands[0].a==0xDA380003);
                assert(commands[0].b==(u32)(uptr)(end-64));
                assert(commands[1].a==0xDB060000u+4*r->segment);
                assert(commands[1].b==((u32)(uptr)(model+r->frame_offsets[wanted])&0x1FFFFFFFu));
                for (unsigned j=0;j<r->models;++j) {
                    assert(commands[2+j].a==0xDE000000);
                    assert(commands[2+j].b==0x06000000u+r->model_offsets[j]);
                }
                assert(!memcmp(actor,&before,sizeof(before)));
                for (unsigned j=0;j<16;++j)assert(guarded.front[j]==0xA7 && guarded.back[j]==0xA7);
                for (u8 *p=(u8 *)gfx.head;p<gfx.tail;++p)assert(*p==0x42);
            }
        }
    }
    actor->index=table->rows[0].index;
    for (unsigned bad=0;bad<19;++bad) {
        RoomMaterialTable original=*table;RoomMaterialRecord *r=table->rows;
        gfx.head=(RoomCommand *)arena;gfx.tail=arena+sizeof(arena);
        if (bad==0)table->magic^=1;
        if (bad==1)table->count=ROOM_MATERIAL_CAPACITY+1;
        if (bad==2)table->stride++;
        if (bad==3)table->reserved=1;
        if (bad==4)r->bytes=0xFFFF;
        if (bad==5)r->mode=3;
        if (bad==6)r->segment=7;
        if (bad==7)r->frames=9;
        if (bad==8)r->models=5;
        if (bad==9)r->frame_bytes=r->bytes+1;
        if (bad==10)r->model_offsets[0]=r->bytes;
        if (bad==11)r->frame_offsets[0]=r->bytes;
        if (bad==12)r->reserved=1;
        if (bad==13)r->state_offset=0x82C;
        if (bad==14)r->frame_offsets[7]=1; /* Current complete banks use at most seven entries. */
        if (bad==15)gfx.tail=arena+64;
        if (bad==16)gfx.tail=arena+sizeof(arena)-4;
        if (bad==17)gfx.head=NULL;
        if (bad==18)gfx.tail=arena;
        RoomCommand *head=gfx.head;u8 *tail=gfx.tail;unsigned before_count=matrices;
        af_v3_room_material_dw(actor,actor,&play.game,model);
        assert(matrices==before_count && gfx.head==head && gfx.tail==tail);*table=original;
    }
    unsigned before_count=matrices;
    af_v3_room_material_dw(NULL,NULL,&play.game,model);
    af_v3_room_material_dw(actor,NULL,NULL,model);
    af_v3_room_material_dw(actor,NULL,&play.game,NULL);
    af_v3_room_material_dw(actor,NULL,&play.game,model+1);
    assert(matrices==before_count);
    for (unsigned i=0;i<sizeof(model);++i)assert(model[i]==0x83);
    puts("Material frames retain timing, switches, context, complete order, immutable assets, and bounds");
}
