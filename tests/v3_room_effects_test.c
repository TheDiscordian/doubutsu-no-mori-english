#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/room_effects.c"

RoomEffectClip *af_test_effect_clip;
u32 af_test_effect_scene;
static int random_calls,requests,creates,lights,matrix_calls,writebacks;
static float random_values[2];
static int expected_width;
static void *expected_game;
static RoomEffect result;
static s16 light_length,light_peak;
float af_effect_random(void) { return random_values[random_calls++&1]; }
static void request(int id,EffectPosition p,int priority,s16 angle,void *game,u16 item,s16 a,s16 b) {
    assert(id==ROOM_EFFECT_FLASH && priority==2 && !angle && game==expected_game && item==0xFFFF);
    assert(a==(requests&1) && !b);
    assert(p.x==40.0f+0.5f*(float)expected_width*40.0f && p.y==80.0f && p.z==43.0f);
    ++requests;
}
static RoomEffect *create(s16 id,EffectPosition p,EffectPosition *offset,void *game,void *arg,
                          u16 item,int priority,s16 a,s16 b) {
    assert(id==(creates ? ROOM_EFFECT_FLASH_CONTROLLER : ROOM_EFFECT_FLASH));
    assert(p.x==1 && p.y==2 && p.z==3 && !offset && !arg);
    assert(game==expected_game && item==0xFFFF && priority==2 && a==1 && b==17);
    ++creates;return &result;
}
static float adjust(s16 now,s16 start,s16 end,float a,float b) {
    if (start==end || now<=start) return a;
    if (now>=end) return b;
    return a+(float)(now-start)*((b-a)/(float)(end-start));
}
static void light(EffectColour c,s16 length,s16 peak,int shadow) {
    assert(c.r==27 && c.g==27 && c.b==27 && c.a==255 && shadow==1);
    light_length=length;light_peak=peak;++lights;
}
void Matrix_translate(float x,float y,float z,u8 mode) {
    assert(x==1 && y==2 && z==3 && mode==0);++matrix_calls;
}
void Matrix_mult(float *p,int mode) {
    assert(p==(float *)((u8 *)expected_game+0x1E5C) && mode==1);++matrix_calls;
}
void Matrix_scale(float x,float y,float z,u8 mode) {
    assert(x==0.01f && x==y && x==z && mode==1);++matrix_calls;
}
void *_Matrix_to_Mtx(void *p) { assert(!((uptr)p&15));memset(p,0x42,64);++matrix_calls;return p; }
void osWritebackDCache(void *p,int size) { assert(!((uptr)p&15) && size==64);++writebacks; }
void _texture_z_light_fog_prim_xlu(void *p) {
    RoomRigGraphics *g=p;*g->xlu_head++=(RoomCommand){0xDE000000,0x8010CB90};
}

int main(void) {
    RoomEffectClip clip={.request=request,.adjust=adjust,.create=create,.light=light};
    af_test_effect_clip=&clip;
    _Alignas(16) u8 game_mem[0x1EA0]={0};expected_game=game_mem;
    af_v3_flash_init((EffectPosition){1,2,3},2,17,game_mem,0xFFFF,1,99);
    af_v3_flash_controller_init((EffectPosition){1,2,3},2,17,game_mem,0xFFFF,1,99);
    assert(creates==2);
    /* Every native room, full controller lifetime, alternating light requests. */
    const u32 scenes[]={6,20,21,22,7,0xFFFFFFFFu};
    const int widths[]={6,4,6,8,-1,-1};
    for (unsigned s=0;s<sizeof(scenes)/sizeof(scenes[0]);++s) {
        struct { u32 before[4];RoomEffect effect;u32 after[4]; } guarded;
        memset(&guarded,0xA5,sizeof(guarded));RoomEffect *e=&guarded.effect;
        e->item=0xFFFF;e->priority=2;
        af_test_effect_scene=scenes[s];expected_width=widths[s];
        requests=random_calls=0;random_values[0]=0.5f;random_values[1]=0.75f;
        af_v3_flash_controller_ct(e,game_mem,0);
        int frames=0;
        while(e->timer>0) { af_v3_flash_controller_mv(e,game_mem);--e->timer;++frames; }
        assert(frames==120 && requests==(expected_width>0 ? 30:0));
        assert(e->specific[0]==requests && random_calls==2*requests);
        for (int i=0;i<4;++i) assert(guarded.before[i]==0xA5A5A5A5 && guarded.after[i]==0xA5A5A5A5);
    }
    /* All seven random lifetimes, both lighting branches, full scale/lifetime. */
    for(int length=3;length<=9;++length) for(int enabled=0;enabled<=1;++enabled) {
        RoomEffect e={.arg0=enabled};random_calls=lights=0;
        random_values[0]=((float)(length-3)+0.25f)/7.0f;random_values[1]=0.5f;
        af_v3_flash_ct(&e,game_mem,0);
        assert(e.timer==5 && random_calls==2 && lights==enabled);
        if (enabled) assert(light_length==(length+1)/2 && light_peak==((length>>1)+1)/2);
        for(int frame=0;frame<3;++frame) {
            af_v3_flash_mv(&e,game_mem);--e.timer;
            float expected=frame ? 0.01f : e.acceleration.x*0.005f;
            assert(e.scale.x==expected && e.scale.y==expected && e.scale.z==expected);
        }
        assert(e.timer==-1);
    }
    /* Exact display commands and matrix bounds; a full arena does no work. */
    RoomRigGraphics gfx={0};RoomRigGame *game=(RoomRigGame *)game_mem;game->gfx=&gfx;
    _Alignas(16) u8 arena[256];memset(arena,0xA5,sizeof(arena));
    gfx.xlu_head=(RoomCommand *)(arena+16);gfx.xlu_tail=arena+240;
    RoomEffect e={.position={1,2,3},.scale={0.01f,0.01f,0.01f}};
    af_v3_flash_dw(&e,game);
    assert(matrix_calls==4 && writebacks==1 && (u8 *)gfx.xlu_head==arena+48);
    RoomCommand *commands=(RoomCommand *)(arena+16);
    assert(commands[1].a==0xDA380003 && commands[1].b==(u32)(uptr)(arena+176));
    assert(commands[2].a==0xFA0000FF && commands[2].b==0xFFFFFFC8);
    assert(commands[3].a==0xDE000000 && commands[3].b==0x06000140);
    for(int i=0;i<16;++i) assert(arena[i]==0xA5 && arena[240+i]==0xA5);
    gfx.xlu_head=(RoomCommand *)(arena+16);gfx.xlu_tail=arena+96;
    af_v3_flash_dw(&e,game);assert(matrix_calls==4 && writebacks==1);
    af_test_effect_clip=0;
    af_v3_flash_init((EffectPosition){1,2,3},2,17,game_mem,0xFFFF,1,0);
    assert(creates==2);
    puts("complete flash lifecycle, lighting, drawing, and guards pass");
    return 0;
}
