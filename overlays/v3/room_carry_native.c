/* Actual relocated room-owner operations for the shared donor carrying core. */
#include "room_carry_native.h"
extern float af_carry_ground(RoomGoodsPoint,float);
extern void Matrix_RotateY(s16,int);
#ifdef __mips__
#define af_v3_goods_get ((s16 (*)(int,int,int))AF_GOODS_GET)
#define af_v3_goods_set ((void (*)(int,int,int,s16))AF_GOODS_SET)
#define af_v3_goods_single ((int (*)(RoomRigGame *,u16,const float *,float,s16))AF_GOODS_SINGLE)
#endif

static u8 *owner_base(RoomCarryOwner *owner) {
    RoomGoodsOverlay *o=owner ? owner->overlay : 0;
    if (!o || o->vrom_start!=0x82D7F0u || o->vram_start!=0x80936710u ||
            o->vram_end<0x8094F610u || !o->loaded) return 0;
    return o->loaded;
}
static void *resolved(u8 *base,u32 address) {
#ifdef __mips__
    return base+(address-0x80936710u);
#else
    (void)base;return af_test_carry_resolve(address);
#endif
}
static RoomCarryNative *live(void) {
    RoomCarryNative *state=carry_native;
    return state->magic==ROOM_CARRY_NATIVE_MAGIC && state->base &&
        owner_base(state->owner)==state->base ? state : 0;
}
static RoomCarryWork *work(RoomCarryNative *state) {
#ifdef __mips__
    return (RoomCarryWork *)(state->base+0x10E50);
#else
    (void)state;return &af_test_carry_work;
#endif
}
static RoomCarryProfile *profile(RoomRig *actor) {
    return actor && actor->index<AF_V3_FURNITURE_CAPACITY ? carry_profiles[actor->index] : 0;
}
static int lookup(void *opaque,int cell) {
    RoomCarryNative *state=opaque;u16 item;int id=-1;
    int ok=((int (*)(u16 *,int *,int,int,s16))resolved(state->base,0x80945ED8))(
        &item,&id,cell&15,cell>>4,1);
    return ok ? id : -1;
}
static float top_height(void *opaque,RoomRig *actor) {
    (void)opaque;RoomCarryProfile *p=profile(actor);
    RoomGoodsPoint point={actor->position[0],actor->position[1],actor->position[2]};
    return p->height+af_carry_ground(point,0);
}
static void set_furniture(void *opaque,RoomRig *actor,int enable) {
    RoomCarryNative *state=opaque;
    RoomGoodsPoint point={actor->position[0],actor->position[1],actor->position[2]};
    ((void (*)(RoomRig *,RoomGoodsPoint,int))resolved(state->base,0x80943C10))(actor,point,enable);
}
static void set_place(void *opaque,int cell,int id) {
    RoomCarryNative *state=opaque;
    ((void (*)(u8,int,int,s16))resolved(state->base,0x80937ABC))(4,cell,id<0 ? 0xC8 : id,1);
}
static s16 get_angle(void *opaque,int cell) {
    (void)opaque;return af_v3_goods_get(cell>>4,cell&15,1);
}
static void set_angle(void *opaque,int cell,s16 angle) {
    (void)opaque;af_v3_goods_set(cell>>4,cell&15,1,angle);
}
static void draw_item(void *opaque,RoomRigGame *game,u16 item,const float *position,float scale,s16 angle) {
    (void)opaque;af_v3_goods_single(game,item,position,scale,angle);
}
static int access(RoomCarryNative *state,RoomCarryAccess *out) {
    if (!state) return 0;
    RoomCarryWork *w=work(state);
    if (!w->actors || !w->used || w->count<1 || w->count>48) return 0;
    u16 *fg=((u16 *(*)(s16))resolved(state->base,0x80936A10))(1);
    if (!fg) return 0;
    *out=(RoomCarryAccess){state,w->actors,w->used,w->count,fg,lookup,top_height,
        set_furniture,set_place,get_angle,set_angle,draw_item};
    return 1;
}
static int request(RoomCarryNative *state,RoomRig *actor,int motion) {
    RoomCarryAccess a;
    if (!access(state,&a) || !actor || !profile(actor) || state->carry.parent_id!=-1 ||
            actor->id<0 || actor->id>=a.count || !a.used[actor->id] || a.actors+actor->id!=actor) return 0;
    /* Furniture on the upper layer has no supported third layer to carry.
       Preserve its own native movement without registering a false parent. */
    if (actor->layer==1) return 1;
    int cells[4],n=af_v3_room_carry_cells(cells,actor->position,actor->shape_type),occupied=0;
    if (!n) return 0;
    for (int i=0;i<n;i++) occupied|=a.foreground[cells[i]];
    if (!occupied) return 1;
    if (room_goods_state->magic!=ROOM_GOODS_MAGIC || !room_goods_state->owner ||
            !room_goods_clip || !room_goods_clip->single_draw) return 0;
    if (!af_v3_room_carry_request(&state->carry,&a,actor)) return 0;
    state->motion=motion;state->failed_restoration=0;return 1;
}

void af_v3_carry_ctor(RoomCarryOwner *owner) {
    u8 *base=owner_base(owner);
    if (!base) return;
    ((void (*)(RoomCarryOwner *))resolved(base,0x8093B498))(owner);
    RoomCarryNative *state=carry_native;
    *state=(RoomCarryNative){.owner=owner,.base=base};
    af_v3_room_carry_init(&state->carry);state->magic=ROOM_CARRY_NATIVE_MAGIC;
}
int af_v3_carry_blocked(const int *contact) {
    RoomCarryNative *state=live();RoomCarryAccess a;
    if (!access(state,&a) || !contact) return 1;
    int id=contact[1];
    if (contact[0]!=1 || id<0 || id>=a.count || !a.used[id]) return 1;
    if (state->carry.parent_id!=-1) return 1;
    /* Registration still validates every child after destination permission.
       The separate native stored-item tests remain in the caller. */
    return 0;
}
int af_v3_carry_permit_move(int shape,int destination,RoomRig *actor) {
    RoomCarryNative *state=live();
    return state && ((int (*)(u8,int))resolved(state->base,0x8093CAF8))(shape,destination) &&
        request(state,actor,1);
}
int af_v3_carry_permit_rotate_b(RoomRig *actor,void *contact,void *player,int rotation) {
    RoomCarryNative *state=live();
    return state && ((int (*)(RoomRig *,void *,void *,s16))resolved(state->base,0x8093FBE0))(
        actor,contact,player,rotation) && request(state,actor,2);
}
int af_v3_carry_permit_rotate_ac(RoomRig *actor) {
    RoomCarryNative *state=live();
    return state && ((int (*)(RoomRig *))resolved(state->base,0x8093FD14))(actor) && request(state,actor,2);
}
static int finish(RoomCarryNative *state,RoomCarryAccess *a,RoomRig *actor) {
    if (!af_v3_room_carry_update(&state->carry,a,actor)) return 0;
    if (actor->state==0) {
        if (!af_v3_room_carry_release(&state->carry,a,actor)) {state->failed_restoration=1;return 0;}
        state->motion=0;state->failed_restoration=0;
    }
    return 1;
}
int af_v3_carry_after_move(RoomRig *actor,RoomCarryOwner *owner) {
    RoomCarryNative *state=live();RoomCarryAccess a;
    if (!state || state->owner!=owner) return 0;
    if (access(state,&a) && actor && state->carry.parent_id==actor->id) finish(state,&a,actor);
    /* Replaces exactly the original count reload at the loop tail. */
    return work(state)->count;
}
RoomRig *af_v3_carry_parent(RoomRig *actor) {
    RoomCarryNative *state=live();RoomCarryAccess a;
    return access(state,&a) ? af_v3_room_carry_parent(&state->carry,&a,actor) : 0;
}
s16 af_v3_carry_angle(RoomRig *actor) {
    RoomCarryNative *state=live();RoomCarryAccess a;
    return access(state,&a) ? af_v3_room_carry_angle(&state->carry,&a,actor) : 0;
}
void af_v3_carry_draw_rotation(s16 angle,int mode,RoomRig *actor) {
    Matrix_RotateY((s16)((int)angle+af_v3_carry_angle(actor)),mode);
}
void af_v3_carry_draw(RoomRig *actor,RoomCarryOwner *owner,void *p,RoomRigGame *game) {
    u8 *base=owner_base(owner);
    if (!base) return;
    ((void (*)(RoomRig *,RoomCarryOwner *,void *,RoomRigGame *))resolved(base,0x80946F40))(actor,owner,p,game);
    RoomCarryNative *state=live();RoomCarryAccess a;
    if (state && state->owner==owner && access(state,&a)) af_v3_room_carry_draw(&state->carry,&a,actor,game);
}
void af_v3_carry_destruct(RoomCarryOwner *owner) {
    u8 *base=owner_base(owner);
    if (!base) return;
    RoomCarryNative *state=live();RoomCarryAccess a;
    if (state && state->owner==owner && state->carry.parent_id>=0 && access(state,&a)) {
        int id=state->carry.parent_id;
        if (id<a.count && a.used[id]) {
            RoomRig *parent=a.actors+id;
            /* The native action has already reserved the destination. Finish
               that accepted move before the owner persists its foreground. */
            if (state->motion==1)
                for (int axis=0;axis<3;axis++) parent->position[axis]=parent->target_position[axis];
            else if (state->motion==2) {
                parent->angle_y=parent->angle_y_target;
                parent->s_angle_y=(s16)(int)(parent->angle_y*0.01745329238474369f*10430.3779296875f);
            }
            parent->state=0;finish(state,&a,parent);
        }
    }
    ((void (*)(void))resolved(base,0x80937140))();
    if (carry_native->owner==owner) {carry_native->magic=0;carry_native->owner=0;}
}
