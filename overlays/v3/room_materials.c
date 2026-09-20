/* Complete frame banks share one renderer. Installing a draw record does not
   install the object's interaction, audio, acquisition, or ordinary profile. */
#include "room_materials.h"

static const RoomMaterialRecord *material_find(u32 index) {
    if (index>=2048u && index<3072u) index-=1024u;
    if (room_material_table->magic!=ROOM_MATERIAL_MAGIC ||
            room_material_table->count>ROOM_MATERIAL_CAPACITY ||
            room_material_table->stride!=sizeof(RoomMaterialRecord) || room_material_table->reserved) return 0;
    for (u32 i=0;i<room_material_table->count;++i) {
        const RoomMaterialRecord *r=room_material_table->rows+i;
        if (r->index!=index) continue;
        if (index<1024 || index>=2048 || r->bytes<32 || r->bytes>9216 || (r->bytes&15) ||
                r->reserved || r->mode>2 || (r->segment!=8 && r->segment!=9) ||
                !r->frames || r->frames>8 || !r->models || r->models>4 ||
                r->kind>1 || !r->frame_bytes || r->frame_bytes>r->bytes ||
                (!r->kind && r->frame_bytes!=32)) return 0;
        if (r->mode==2) {
            /* Private work in non-rig actors, never the donor's 0x82C offset. */
            if (r->state_offset!=0x1A4 || r->frames!=2 || r->divisor) return 0;
        } else if (r->state_offset || !r->divisor ||
                (r->mode==1 && (r->frames!=4 || r->divisor!=10))) return 0;
        for (u32 j=0;j<4;++j)
            if (j<r->models ? ((r->model_offsets[j]&7) || r->model_offsets[j]>r->bytes-8u)
                            : r->model_offsets[j]!=0) return 0;
        for (u32 j=0;j<8;++j)
            if (j<r->frames ? ((r->frame_offsets[j]&7) || r->frame_offsets[j]>r->bytes-r->frame_bytes)
                            : r->frame_offsets[j]!=0) return 0;
        return r;
    }
    return 0;
}

void af_v3_room_material_dw(RoomRig *actor,void *room,RoomRigGame *game,u8 *data) {
    if (!actor || !game || !game->gfx || !data || ((uptr)data&7)) return;
    const RoomMaterialRecord *r=material_find(actor->index);
    if (!r) return;
    u32 frame,index;
    if (r->mode==2) index=(u16)actor->joint[0][0]&1u;
    else {
        /* Donor material counters advance at 60 Hz, native counters at 30 Hz.
           Room ownership distinguishes the play context from menu previews. */
        frame=(room ? ((RoomMaterialPlay *)game)->play_frame : game->frame)*2u;
        if (r->mode==1) {
            /* Signed source division, including wrapping, without signed
               overflow. Only a room instance is stopped by its switch. */
            u32 q=(frame&0x80000000u) ? 0u-((0u-frame)/r->divisor) : frame/r->divisor;
            index=room && !((u8 *)actor)[0x12C] ? 0u : q&3u;
        } else index=(frame/r->divisor)%r->frames;
    }
    RoomRigGraphics *gfx=game->gfx;
    RoomCommand *commands=gfx->head;
    uptr front=(uptr)commands,back=(uptr)gfx->tail;
    u32 count=2u+r->models;
    if (!front || !back || (front&7) || (back&7) || back<front || back-front<64u+8u*count) return;
    /* Reserve all commands before requesting the parent's matrix. No shared
       scratch texture is edited while an earlier frame may still use it. */
    gfx->head=commands+count;
    commands[0]=(RoomCommand){0xDA380003,(u32)(uptr)_Matrix_to_Mtx_new(gfx)};
    commands[1]=(RoomCommand){0xDB060000u+4u*r->segment,
        (u32)(uptr)(data+r->frame_offsets[index])&0x1FFFFFFFu};
    for (u32 i=0;i<r->models;++i)
        commands[2+i]=(RoomCommand){0xDE000000,0x06000000u+r->model_offsets[i]};
}
