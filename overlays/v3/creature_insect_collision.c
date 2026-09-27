/* Exclude only the hiding tile's cylinder, not the tile's terrain or any
 * surrounding obstacles. Foreground items and collision maps stay untouched. */
#include "creature_insect_collision.h"
static int directed,hidden_x,hidden_z;

void af_insect_columns(AfInsectColumn *columns,int *count,void *units,int side,
                       int grounded,u16 mask0,u16 mask1) {
    af_insect_native_columns(columns,count,units,side,grounded,mask0,mask1);
    if (!directed) return;
    /* Native WallCheck clears the complete array before filling it. Its
     * generator counts empty records too, so keep that ordering and stride. */
    for (int i=0;i<*count && i<16;i++)
        if (columns[i].x==hidden_x && columns[i].z==hidden_z)
            columns[i]=(AfInsectColumn){0};
}

void af_insect_directed_bg(ACTOR *actor,f32 radius,f32 height,int attribute,int x,int z) {
    int was_directed=directed,was_x=hidden_x,was_z=hidden_z;
    directed=x>=0 && z>=0;hidden_x=x;hidden_z=z;
    af_insect_native_bg(NULL,actor,radius,height,attribute,0,1);
    directed=was_directed;hidden_x=was_x;hidden_z=was_z;
}

void af_insect_acre_wall(ACTOR *actor,f32 radius) {
    AfInsectBgContext *ctx=&af_insect_bg_context;
    ctx->reverse=(xyz_t){0};ctx->centre=actor->world.position;
    ctx->old_centre=actor->last_world_position;
    ctx->speed[0]=ctx->centre.x-ctx->old_centre.x;
    ctx->speed[1]=ctx->centre.z-ctx->old_centre.z;
    int bx,bz;
    if (!af_insect_world_block(&bx,&bz,ctx->old_centre) ||
            (ctx->speed[0]==0.0f && ctx->speed[1]==0.0f)) return;
    f32 base_x,base_z;
    if (!mFI_BkNum2WposXZ(&base_x,&base_z,bx,bz)) return;
    /* Source intro-demo mode excludes one tile around the player acre. */
    f32 inset=af_insect_acre_inset(bx,bz)?40.0f:0.0f;
    f32 left=base_x+inset+radius,right=base_x+640.0f-inset-radius;
    f32 top=base_z+inset+radius,bottom=base_z+640.0f-inset-radius;
    if (ctx->centre.x<left) ctx->reverse.x=left-ctx->centre.x;
    else if (ctx->centre.x>right) ctx->reverse.x=right-ctx->centre.x;
    if (ctx->centre.z<top) ctx->reverse.z=top-ctx->centre.z;
    else if (ctx->centre.z>bottom) ctx->reverse.z=bottom-ctx->centre.z;
    af_insect_ground_check(&ctx->reverse,ctx,actor,0.0f,&actor->bg_collision_check.result,NULL,0);
    af_insect_apply_reverse(actor,ctx->reverse,0);
}
