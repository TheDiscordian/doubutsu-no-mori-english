/* Complete scrolling layers share immutable, frame-owned commands and matrix. */
#include "room_scroll.h"

static const RoomScrollRecord *scroll_find(u32 index) {
    if (index>=2048u && index<3072u) index-=1024u;
    if (room_scroll_table->magic!=ROOM_SCROLL_MAGIC || room_scroll_table->reserved ||
            room_scroll_table->count>ROOM_SCROLL_CAPACITY ||
            room_scroll_table->stride!=sizeof(RoomScrollRecord)) return 0;
    for (u32 i=0;i<room_scroll_table->count;++i) {
        const RoomScrollRecord *r=room_scroll_table->rows+i;
        if (r->index!=index) continue;
        if (index<1024 || index>=2048 || r->bytes<32 || r->bytes>9216 || (r->bytes&15) ||
                r->models<2 || r->models>4 || (r->segment!=8 && r->segment!=9) ||
                !r->tiles || r->tiles>2 || r->colour_mode>4 || r->reserved ||
                !r->opaque_models || r->opaque_models>=r->models) return 0;
        if (r->colour_mode==4) {
            if (r->state_offset || r->preview || (r->colour_a&0xFFFFFF00u)!=0xFA000000u ||
                    r->colour2_a!=0xFB000000u || (r->debug_offset&1) ||
                    r->debug_offset<0x14 || r->debug_offset>0x1C94-18) return 0;
        } else {
            if (r->colour2_a || r->colour2_b || r->debug_offset) return 0;
            if (r->colour_mode ? (r->state_offset!=0x1A4 ||
                    (r->colour_mode!=2 ? ((r->colour_a!=0xFB000000u &&
                        (r->colour_a&0xFFFFFF00u)!=0xFA000000u) || (r->colour_b&255u))
                        : r->colour_a!=0xFA000000u))
                    : (r->colour_a || r->colour_b || r->state_offset || r->preview)) return 0;
            if (r->colour_mode==3 && r->preview) return 0;
        }
        for (u32 j=0;j<4;++j)
            if (j<r->models ? ((r->model_offsets[j]&7) || r->model_offsets[j]>r->bytes-8u)
                            : r->model_offsets[j]!=0) return 0;
        for (u32 j=0;j<2;++j) for (u32 k=0;k<2;++k) {
            u32 n=r->dimensions[j][k];
            if (j<r->tiles ? (n<8 || n>64 || (n&(n-1)) ||
                    r->rates[j][k]<-16 || r->rates[j][k]>16)
                    : (n || r->rates[j][k])) return 0;
        }
        return r;
    }
    return 0;
}

void af_v3_room_scroll_dw(RoomRig *actor,void *room,RoomRigGame *game,u8 *data) {
    if (!actor || !game || !game->gfx || !data || ((uptr)data&7)) return;
    const RoomScrollRecord *r=scroll_find(actor->index);
    if (!r) return;
    u32 colour=r->preview,a=r->colour_a,b=r->colour_b,environment=r->colour2_b;
    if ((room && (r->colour_mode==1 || r->colour_mode==2)) || r->colour_mode==3) {
        FloatWord value;
        u8 *to=(u8 *)&value;const u8 *from=(u8 *)actor+r->state_offset;
        to[0]=from[0];to[1]=from[1];to[2]=from[2];to[3]=from[3];
        /* Reject NaNs and unsafe float-to-integer conversions as well as
           uninitialised lifecycle state. Source fades stay in this interval. */
        float maximum=r->colour_mode==3 ? 1.0f : 255.0f;
        if (!(value.f>=0.0f && value.f<=maximum)) return;
        colour=(u32)(r->colour_mode==3 ? value.f*255.0f : value.f);
    }
    if (r->colour_mode==4) {
        uptr debug=(uptr)af_v3_room_debug;
        if (!debug || (debug&1)) return;
#ifdef __mips__
        if (debug<0x80000000u || debug>0x80800000u-0x1C94u) return;
#endif
        const s16 *registers=(const s16 *)(debug+r->debug_offset);
        a=(a&0xFFFFFF00u)|((a+(u32)(int)registers[0])&255u);
        b=environment=0;
        for (u32 i=0;i<4;++i) {
            u32 shift=24u-8u*i;
            b|=(((r->colour_b>>shift)+(u32)(int)registers[i+1])&255u)<<shift;
            environment|=(((r->colour2_b>>shift)+(u32)(int)registers[i+5])&255u)<<shift;
        }
    }
    RoomRigGraphics *gfx=game->gfx;
    uptr opa=(uptr)gfx->head,end=(uptr)gfx->tail;
    uptr xlu=(uptr)gfx->xlu_head,xend=(uptr)gfx->xlu_tail;
    u32 ocommands=1u+r->opaque_models;
    u32 xcommands=2u+r->models-r->opaque_models+(r->colour_mode!=0)+(r->colour_mode==4);
    u32 scratch=64u+(2u*r->tiles+1u)*8u;
    if (!opa || !end || !xlu || !xend || ((opa|end|xlu|xend)&7) || end<opa || xend<xlu ||
            end-opa<scratch+8u*ocommands || xend-xlu<8u*xcommands) return;
    uptr allocation=(end-scratch)&~(uptr)15;
    if (allocation<opa+8u*ocommands) return;
    /* Reserve both draw streams and all temporary state before any write. */
    RoomCommand *o=gfx->head,*x=gfx->xlu_head;
    gfx->tail=(u8 *)allocation;gfx->head+=ocommands;gfx->xlu_head+=xcommands;
    RoomCommand *scroll=(RoomCommand *)(allocation+64);
    u32 frame=(room ? ((RoomMaterialPlay *)game)->play_frame : game->frame)*2u;
    for (u32 i=0;i<r->tiles;++i) {
        /* Source origins are doubled then masked to 14 fractional bits;
           Dolphin uses 1/16 texel, native RDP 1/4. Unsigned math retains
           negative scrolling and wrap without undefined signed shifts. */
        u32 s=(((frame*(u32)(int)r->rates[i][0])<<1)&0x3FFFu)>>2;
        u32 t=(((frame*(u32)(int)r->rates[i][1])<<1)&0x3FFFu)>>2;
        u32 right=(s+4u*(r->dimensions[i][0]-1u))&0xFFFu;
        u32 bottom=(t+4u*(r->dimensions[i][1]-1u))&0xFFFu;
        scroll[i*2]=(RoomCommand){0xE8000000,0};
        scroll[i*2+1]=(RoomCommand){0xF2000000u|(s<<12)|t,(i<<24)|(right<<12)|bottom};
    }
    scroll[r->tiles*2]=(RoomCommand){0xDF000000,0};
    _Matrix_to_Mtx((void *)allocation);
    *o++=(RoomCommand){0xDA380003,(u32)allocation};
    for (u32 i=0;i<r->opaque_models;++i)
        *o++=(RoomCommand){0xDE000000,0x06000000u+r->model_offsets[i]};
    *x++=(RoomCommand){0xDA380003,(u32)allocation};
    if (r->colour_mode)
        *x++=(RoomCommand){a|(r->colour_mode==2 ? colour : 0),
                          b|(r->colour_mode==1 || r->colour_mode==3 ? colour : 0)};
    if (r->colour_mode==4) *x++=(RoomCommand){r->colour2_a,environment};
    *x++=(RoomCommand){0xDB060000u+4u*r->segment,(u32)(uptr)scroll&0x1FFFFFFFu};
    for (u32 i=r->opaque_models;i<r->models;++i)
        *x++=(RoomCommand){0xDE000000,0x06000000u+r->model_offsets[i]};
    osWritebackDCache((void *)allocation,(int)scratch);
}

#ifdef AF_V3_ROOM_SCROLL_LIFECYCLE
static const RoomScrollLife *life_find(u32 index) {
    if (index>=2048u && index<3072u) index-=1024u;
    if (room_scroll_lives->magic!=ROOM_SCROLL_LIFE_MAGIC || room_scroll_lives->reserved ||
            room_scroll_lives->stride!=sizeof(RoomScrollLife) ||
            room_scroll_lives->count>ROOM_SCROLL_LIFE_CAPACITY) return 0;
    for (u32 i=0;i<room_scroll_lives->count;++i) {
        const RoomScrollLife *r=room_scroll_lives->rows+i;
        if (r->index!=index) continue;
        if (index<1024 || index>=2048 || r->mode<1 || r->mode>2 || r->flags>1 ||
                r->sound<68 || r->sound>=96 ||
                (r->on ? (!r->off || r->on>=128 || r->off>=128) : r->off!=0)) return 0;
        if (r->mode==1 ? (r->flags || r->maximum || r->step || r->on || r->off)
                       : (!r->maximum || !r->step || r->step>r->maximum)) return 0;
        return r;
    }
    return 0;
}

void af_v3_room_scroll_ct(RoomScrollActor *actor,u8 *data) {
    (void)data;
    const RoomScrollLife *r=actor ? life_find(actor->index) : 0;
    if (!r || r->mode!=2) return;
    actor->private_switch=actor->saved_switch==1;
    actor->colour.f=actor->private_switch ? (float)r->maximum : 0.0f;
}

void af_v3_room_scroll_mv(RoomScrollActor *actor,void *room,RoomRigGame *game,u8 *data) {
    (void)room;(void)game;(void)data;
    const RoomScrollLife *r=actor ? life_find(actor->index) : 0;
    if (!r) return;
    int audible=actor->state<12 || actor->state>15;
    if (r->mode==1) {
        if (audible) sAdo_OngenPos((u32)(uptr)actor,(u8)r->sound,actor->position);
        return;
    }
    if ((unsigned)actor->private_switch>1 ||
            !(actor->colour.f>=0.0f && actor->colour.f<=(float)r->maximum)) return;
    /* The native update replaces two source updates. A switch edge occurs
       only in the first half; do not repeat it or clear the owner's flag. */
    for (u32 half=0;half<2;++half) {
        float target=actor->private_switch ? (float)r->maximum : 0.0f;
        if (audible && actor->private_switch)
            sAdo_OngenPos((u32)(uptr)actor,(u8)r->sound,actor->position);
        if (actor->colour.f>target) {
            actor->colour.f-=(float)r->step;
            if (actor->colour.f<target) actor->colour.f=target;
        } else if (actor->colour.f<target) {
            actor->colour.f+=(float)r->step;
            if (actor->colour.f>target) actor->colour.f=target;
        } else if (!half && actor->changed) {
            actor->private_switch^=1;
            if (r->on) sAdo_OngenTrgStart(actor->private_switch ? r->on : r->off,actor->position);
        }
    }
}

void af_v3_room_scroll_dt(RoomScrollActor *actor,u8 *data) {
    (void)data;
    const RoomScrollLife *r=actor ? life_find(actor->index) : 0;
    if (r && (r->flags&1) && (unsigned)actor->private_switch<=1)
        actor->saved_switch=(u8)actor->private_switch;
}
#endif
