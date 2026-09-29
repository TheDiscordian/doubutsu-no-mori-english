#include "creature_carried.h"
#include "creature_insect_manager.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

u32 af_carried_field_info[8],af_carried_segments[16];
static AfNativeInsectClip clip;
AfNativeInsectClip *af_insect_native_clip=&clip;
static u32 graph[0x300/4],game[0x2000/4],commands[64];
static u8 artwork[1440] __attribute__((aligned(16)));
static u8 destination[0xC00] __attribute__((aligned(16)));
static int faults,fallbacks,shadows,matrix_puts,positions,rotations;
static aINS_INSECT_ACTOR insect;
int af_carried_creature_graphics_load(void *,u32,u32,const char *,int);
void af_carried_insect_draw(void *,aINS_INSECT_ACTOR *,GAME *,int,int);

int af_carried_prior_graphics_load(void *out,u32 vrom,u32 n,const char *file,int line) {
    (void)out;(void)n;(void)file;(void)line;assert(vrom!=af_carried_field_info[1]);fallbacks++;return 77;
}
void af_carried_fault(const char *a,const char *b) {(void)a;(void)b;faults++;}
void af_carried_matrix_put(const void *matrix) {assert(matrix==insect.tools_actor.work+4);matrix_puts++;}
void af_carried_matrix_position(const xyz_t *zero,xyz_t *out) {
    assert(!zero->x && !zero->y && !zero->z);*out=(xyz_t){10,20,30};positions++;
}
void af_carried_matrix_translate(f32 x,f32 y,f32 z,int mode) {
    assert(x==10 && y==22 && z==30 && !mode);
}
void af_carried_matrix_scale(f32 x,f32 y,f32 z,int mode) {assert(x==.01f && y==.01f && z==.01f && mode==1);}
void af_carried_matrix_x(s16 v,int mode) {assert(!v && mode==1);rotations++;}
void af_carried_matrix_y(s16 v,int mode) {assert(!v && mode==1);rotations++;}
void af_carried_matrix_z(s16 v,int mode) {assert(!v && mode==1);rotations++;}
void *af_carried_matrix_new(void *g) {assert(g==graph);return (void *)0x80403000u;}
void af_carried_shadow(ACTOR *a,GAME *g,f32 scale) {assert(a==(ACTOR *)&insect && g==(GAME *)game && scale==1);shadows++;}
static void native_draw(void *g,aINS_INSECT_ACTOR *i,GAME *play,int frame,int alpha) {
    assert(g==graph && i==&insect && play==(GAME *)game && frame==3 && alpha==91);fallbacks++;
}

int main(void) {
    assert((uintptr_t)artwork<=0xFFFFFFFFu);
    af_carried_field_info[0]=0x41464351;af_carried_field_info[1]=0x113F000;
    af_carried_field_info[2]=sizeof artwork;af_carried_field_info[3]=(u32)(uintptr_t)artwork;
    af_carried_field_info[4]=0x06012300;af_carried_field_info[5]=0x06012400;
    memset(artwork,0xAB,sizeof artwork);memset(destination,0xCD,sizeof destination);
    assert(af_carried_creature_graphics_load(destination,0x113F000,sizeof artwork,"fixture",1)==0);
    assert(!memcmp(destination,artwork,sizeof artwork) && destination[sizeof artwork]==0xCD);
    assert(af_carried_creature_graphics_load(destination,0x113D000,100,"fixture",1)==77);
    assert(af_carried_creature_graphics_load(destination+1,0x113F000,sizeof artwork,"fixture",1)==-1);
    assert(af_carried_creature_graphics_load(destination,0x113F000,sizeof artwork-1,"fixture",1)==-1);
    assert(faults==2 && fallbacks==1);
    insect.type=40;insect.native_1F0=0x00400000;
    insect.tools_actor.actor_class.world.position=(xyz_t){10,20,30};
    insect.tools_actor.actor_class.scale=(xyz_t){.01f,.01f,.01f};
    game[0x1E9C/4]=0x80405000;
    for (int held=0;held<2;held++)for (int pose=0;pose<2;pose++) {
        insect.tools_actor.init_matrix=held;insect._1E0=(float)pose+.5f;
        *(u32 **)((u8 *)graph+0x2A8)=commands;rotations=0;
        af_carried_insect_draw(graph,&insect,(GAME *)game,held?0:pose*2,91);
        assert(*(u32 **)((u8 *)graph+0x2A8)==commands+12);
        const u32 expected[]={0xE7000000,0,0xDB060018,0x00400000,
            0xDA380003,0x80403000,0xDA380001,0x80405000,
            0xFB000000,0xFFFFFF5B,0xDE000000,af_carried_field_info[4+pose]};
        assert(!memcmp(commands,expected,sizeof expected));
        assert(rotations==(held?2:3) && af_carried_segments[6]==0x80400000);
        af_carried_insect_draw(graph,&insect,(GAME *)game,(held?0:pose*2)+1,91);
        assert(*(u32 **)((u8 *)graph+0x2A8)==commands+12);
    }
    assert(shadows==4 && matrix_puts==2 && positions==2);
    insect._1E0=2;af_carried_insect_draw(graph,&insect,(GAME *)game,0,91);assert(faults==3);
    clip.release=(void *)((uintptr_t)native_draw-(0x11264u-0x102B8u));
    insect.type=27;af_carried_insect_draw(graph,&insect,(GAME *)game,3,91);assert(fallbacks==2);
    puts("Carried field: full bounded copy, animated held/wild billboard, single pass, native delegation");
}
