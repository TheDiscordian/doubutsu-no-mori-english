/* Quest creatures share the native field buffer and draw loop. Original
 * insects delegate to the complete relocated native draw helper. */
#include "creature_carried.h"
#include "creature_insect_manager.h"
extern const u32 af_carried_field_info[8];
extern u32 af_carried_segments[];
extern int af_carried_prior_graphics_load(void *,u32,u32,const char *,int);
extern void *memcpy(void *,const void *,size_t);
extern void af_carried_matrix_put(const void *);
extern void af_carried_matrix_position(const xyz_t *,xyz_t *);
extern void af_carried_matrix_translate(f32,f32,f32,int);
extern void af_carried_matrix_scale(f32,f32,f32,int);
extern void af_carried_matrix_x(s16,int),af_carried_matrix_y(s16,int),af_carried_matrix_z(s16,int);
extern void *af_carried_matrix_new(void *);
extern void af_carried_shadow(ACTOR *,GAME *,f32);
extern void af_carried_fault(const char *,const char *);

int af_carried_creature_graphics_load(void *destination,u32 vrom,u32 bytes,const char *file,int line) {
    const u32 *info=af_carried_field_info;
    if (vrom!=info[1])return af_carried_prior_graphics_load(destination,vrom,bytes,file,line);
    if (info[0]!=0x41464351 || !destination || (uintptr_t)destination&7 ||
            bytes!=info[2] || !bytes || bytes>0xC00 || bytes&15) {
        af_carried_fault("Carried creature","Invalid complete field resource");
        return -1;
    }
    memcpy(destination,(const void *)(uintptr_t)info[3],bytes);
    return 0;
}

void af_carried_insect_draw(void *graph,aINS_INSECT_ACTOR *insect,GAME *game,int frame,int alpha) {
    if (insect->type!=aINS_INSECT_TYPE_SPIRIT) {
        typedef void (*Draw)(void *,aINS_INSECT_ACTOR *,GAME *,int,int);
        /* The checked release callback is part of this same native overlay. */
        Draw original=(Draw)((uintptr_t)af_insect_native_clip->release+0x11264u-0x102B8u);
        original(graph,insect,game,frame,alpha);
        return;
    }
    /* The original caller makes a material+shadow pair. Spirits have one
     * billboard pass; their animation continues even while held in the net. */
    if (frame&1)return;
    ACTOR *actor=(ACTOR *)insect;
    s16 x=actor->shape_info.rotation.x,y=actor->shape_info.rotation.y,z=actor->shape_info.rotation.z;
    if (insect->tools_actor.init_matrix) {
        static const xyz_t zero={0,0,0};
        af_carried_matrix_put(insect->tools_actor.work+4);
        af_carried_matrix_position(&zero,&actor->world.position);
        x=y=z=0;
    }
    af_carried_matrix_translate(actor->world.position.x,actor->world.position.y+2.0f,
        actor->world.position.z,0);
    af_carried_matrix_x(x,1);af_carried_matrix_y(y,1);
    if (!insect->tools_actor.init_matrix)af_carried_matrix_z(z,1);
    af_carried_matrix_scale(actor->scale.x,actor->scale.y,actor->scale.z,1);
    int pose=(int)insect->_1E0;
    if ((unsigned)pose>=2 || af_carried_field_info[0]!=0x41464351) {
        af_carried_fault("Carried creature","Invalid complete animation frame");return;
    }
    /* Native segment six and graph arena retain their original conventions. */
    u32 segment=(u32)insect->native_1F0;
    af_carried_segments[6]=segment+0x80000000u;
    u32 *gfx=*(u32 **)((u8 *)graph+0x2A8);
    *gfx++=0xE7000000;*gfx++=0;
    *gfx++=0xDB060018;*gfx++=segment;
    *gfx++=0xDA380003;*gfx++=(u32)(uintptr_t)af_carried_matrix_new(graph);
    *gfx++=0xDA380001;*gfx++=*(const u32 *)((const u8 *)game+0x1E9C);
    *gfx++=0xFB000000;*gfx++=0xFFFFFF00u|((u32)alpha&255u);
    *gfx++=0xDE000000;*gfx++=af_carried_field_info[4+pose];
    *(u32 **)((u8 *)graph+0x2A8)=gfx;
    af_carried_shadow(actor,game,1.0f);
}
