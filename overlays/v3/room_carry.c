#include "room_carry.h"
extern float sin_s(s16);
extern float cos_s(s16);

static RoomRig *get_actor(const RoomCarryAccess *access,int id) {
    if (!access || !access->actors || !access->used || access->count<1 || access->count>48 ||
            id<0 || id>=access->count || !access->used[id]) return 0;
    RoomRig *actor=access->actors+id;
    return actor->id==id ? actor : 0;
}

static int cell(float x,float z) {
    /* Comparisons also reject NaNs before any float-to-int conversion. */
    if (!(x>=0 && x<640 && z>=0 && z<640)) return -1;
    return (int)(x/40.0f)+16*(int)(z/40.0f);
}

void af_v3_room_carry_init(RoomCarry *carry) {
    *carry=(RoomCarry){.parent_id=-1};
    for (int i=0;i<4;++i) carry->slots[i].actor_id=-1;
}

int af_v3_room_carry_cells(int *cells,const float *position,u8 shape) {
    static const signed char dx[6][4]={{0,0},{0,-1},{0,0},{0,1},{0},{0,1,0,1}};
    static const signed char dz[6][4]={{0,-1},{0,0},{0,1},{0,0},{0},{0,0,1,1}};
    if (!cells || !position || shape>=6) return 0;
    float x=position[0]-(shape==5 ? 40.0f : 0),z=position[2]-(shape==5 ? 40.0f : 0);
    int first=cell(x,z),count=shape<4 ? 2 : shape==4 ? 1 : 4;
    if (first<0) return 0;
    int result[4];
    for (int i=0;i<count;++i) {
        int cx=(first&15)+dx[shape][i],cz=(first>>4)+dz[shape][i];
        if (cx<0 || cx>=16 || cz<0 || cz>=16) return 0;
        result[i]=cx+16*cz;
    }
    for (int i=0;i<count;++i) cells[i]=result[i];
    return count;
}

static int complete_access(const RoomCarryAccess *access) {
    return access && access->foreground && access->lookup && access->top_height &&
        access->set_furniture && access->set_place && access->get_angle &&
        access->set_angle && access->draw_item;
}

int af_v3_room_carry_request(RoomCarry *carry,const RoomCarryAccess *access,RoomRig *parent) {
    if (!carry || carry->parent_id!=-1 || !complete_access(access) || !parent ||
            get_actor(access,parent->id)!=parent || parent->layer || parent->kept_item) return 0;
    int cells[4],count=af_v3_room_carry_cells(cells,parent->position,parent->shape_type);
    if (!count) return 0;
    RoomCarry next;
    af_v3_room_carry_init(&next);next.parent_id=parent->id;next.angle=parent->s_angle_y;
    int cell_slots[4]={-1,-1,-1,-1},used=0;
    float top=access->top_height(access->opaque,parent);
    for (int i=0;i<count;++i) {
        int at=cells[i];u16 item=access->foreground[at];
        if (!item) continue;
        RoomCarrySlot *slot=next.slots+used;float position[3];
        if ((item>>12)==1 || (item>>12)==3) {
            int id=access->lookup(access->opaque,at);
            RoomRig *child=get_actor(access,id);
            if (!child || child==parent || child->layer!=1) return 0;
            int duplicate=-1;
            for (int n=0;n<used;++n) if (next.slots[n].actor_id==id) duplicate=n;
            if (duplicate!=-1) {cell_slots[i]=duplicate;continue;}
            slot->actor_id=id;
            for (int axis=0;axis<3;++axis) position[axis]=child->position[axis];
        } else {
            slot->item=item;slot->angle=access->get_angle(access->opaque,at);
            position[0]=(at&15)*40.0f+20.0f;position[1]=top;
            position[2]=(at>>4)*40.0f+20.0f;
        }
        slot->active=1;
        for (int axis=0;axis<3;++axis) {
            slot->relative[axis]=position[axis]-(parent->position[axis]+parent->base_position[axis]);
            slot->world[axis]=position[axis];
        }
        cell_slots[i]=used++;
    }
    /* Validate the entire collection first. An unresolved child must not leave
       earlier items removed from the foreground, as a partial transfer would. */
    unsigned detached=0;
    for (int i=0;i<count;++i) {
        int n=cell_slots[i];
        if (n<0) continue;
        RoomCarrySlot *slot=next.slots+n;int at=cells[i];
        access->set_angle(access->opaque,at,0);
        if (slot->actor_id!=-1) {
            if (!(detached&(1u<<n))) access->set_furniture(access->opaque,access->actors+slot->actor_id,0);
            detached|=1u<<n;
            access->set_place(access->opaque,at,-1);
        } else access->foreground[at]=0;
    }
    *carry=next;
    return 1;
}

static int valid_parent(const RoomCarry *carry,const RoomCarryAccess *access,const RoomRig *parent) {
    return carry && parent && carry->parent_id==parent->id && get_actor(access,parent->id)==parent;
}

int af_v3_room_carry_update(RoomCarry *carry,const RoomCarryAccess *access,RoomRig *parent) {
    if (!valid_parent(carry,access,parent)) return 0;
    for (int i=0;i<4;++i) {
        RoomCarrySlot *slot=carry->slots+i;
        if (slot->active && slot->actor_id!=-1 && !get_actor(access,slot->actor_id)) return 0;
    }
    s16 delta=(s16)((int)parent->s_angle_y-carry->angle);
    float sine=delta ? sin_s(delta) : 0,cosine=delta ? cos_s(delta) : 1;
    /* T(parent) R(delta) T(base) T(relative). Keep the source matrix's order
       of float operations instead of rotating a rounded combined offset. */
    float origin[3]={parent->position[0]+(cosine*parent->base_position[0]+sine*parent->base_position[2]),
        parent->position[1]+parent->base_position[1],
        parent->position[2]+(-sine*parent->base_position[0]+cosine*parent->base_position[2])};
    for (int i=0;i<4;++i) {
        RoomCarrySlot *slot=carry->slots+i;
        if (!slot->active) continue;
        slot->world[0]=origin[0]+(cosine*slot->relative[0]+sine*slot->relative[2]);
        slot->world[1]=origin[1]+slot->relative[1];
        slot->world[2]=origin[2]+(-sine*slot->relative[0]+cosine*slot->relative[2]);
        if (slot->actor_id!=-1)
            for (int axis=0;axis<3;++axis) access->actors[slot->actor_id].position[axis]=slot->world[axis];
    }
    return 1;
}

RoomRig *af_v3_room_carry_parent(const RoomCarry *carry,const RoomCarryAccess *access,const RoomRig *child) {
    if (!carry || !child || child->layer!=1 || get_actor(access,child->id)!=child) return 0;
    RoomRig *parent=get_actor(access,carry->parent_id);
    if (!parent) return 0;
    for (int i=0;i<4;++i)
        if (carry->slots[i].active && carry->slots[i].actor_id==child->id) return parent;
    return 0;
}

s16 af_v3_room_carry_angle(const RoomCarry *carry,const RoomCarryAccess *access,const RoomRig *child) {
    RoomRig *parent=af_v3_room_carry_parent(carry,access,child);
    return parent ? (s16)((int)parent->s_angle_y-carry->angle) : 0;
}

int af_v3_room_carry_release(RoomCarry *carry,const RoomCarryAccess *access,RoomRig *parent) {
    if (!valid_parent(carry,access,parent) || !complete_access(access)) return 0;
    int cells[4];
    /* The adapter updates carrying after the final position/angle snap, before
       release. Do not discard state on a failed restoration. */
    for (int i=0;i<4;++i) {
        RoomCarrySlot *slot=carry->slots+i;
        if (!slot->active) continue;
        cells[i]=cell(slot->world[0],slot->world[2]);
        if (cells[i]<0 || access->foreground[cells[i]] ||
                (slot->actor_id!=-1 && !get_actor(access,slot->actor_id))) return 0;
        for (int n=0;n<i;++n) if (carry->slots[n].active && cells[n]==cells[i]) return 0;
    }
    s16 delta=(s16)((int)parent->s_angle_y-carry->angle);
    for (int i=0;i<4;++i) {
        RoomCarrySlot *slot=carry->slots+i;
        if (!slot->active) continue;
        int at=cells[i];
        if (slot->actor_id!=-1) {
            RoomRig *child=access->actors+slot->actor_id;
            child->s_angle_y=(s16)((int)child->s_angle_y+delta);
            child->angle_y=57.2957763671875f*(child->s_angle_y*0.00009587380161928013f);
            child->angle_y_target=child->angle_y;
            child->position[0]=(at&15)*40.0f+20.0f;child->position[1]=slot->world[1];
            child->position[2]=(at>>4)*40.0f+20.0f;
            access->set_furniture(access->opaque,child,1);
            access->set_place(access->opaque,at,child->id);
        }
        if (slot->item) {
            access->foreground[at]=slot->item;
            access->set_angle(access->opaque,at,(s16)((int)slot->angle+delta));
        }
        slot->active=0;slot->actor_id=-1;
    }
    carry->parent_id=-1;
    return 1;
}

int af_v3_room_carry_draw(const RoomCarry *carry,const RoomCarryAccess *access,RoomRig *parent,RoomRigGame *game) {
    if (!valid_parent(carry,access,parent) || !game || !access->draw_item) return 0;
    s16 delta=(s16)((int)parent->s_angle_y-carry->angle);
    for (int i=0;i<4;++i) {
        const RoomCarrySlot *slot=carry->slots+i;
        if (slot->active && slot->item)
            access->draw_item(access->opaque,game,slot->item,slot->world,.01f,(s16)((int)slot->angle+delta));
    }
    return 1;
}
