#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/room_carry.c"

float sin_s(s16 angle) { return sinf(angle*(6.2831853071795864769f/65536.0f)); }
float cos_s(s16 angle) { return cosf(angle*(6.2831853071795864769f/65536.0f)); }
typedef float f32;
typedef u16 mActor_name_t;
typedef struct {float x,y,z;} xyz_t;
typedef struct {
    int id;u16 name;s16 s_angle_y,layer,state;u8 shape_type;
    float angle_y,angle_y_target;
    xyz_t position,base_position;
} FTR_ACTOR;
typedef struct {int exist_flag;xyz_t pos;int ftr_ID;u16 item_no;s16 angle_y;xyz_t ut_pos;} aMR_fit_ftr_c;
typedef struct {int ftrID;s16 angle_y;aMR_fit_ftr_c fit_ftr_table[4];} aMR_parent_ftr_c;
typedef struct {aMR_parent_ftr_c parent_ftr;} MY_ROOM_ACTOR;
typedef MY_ROOM_ACTOR ACTOR;
typedef struct {void *graph;} GAME;
typedef struct {float height;} aFTR_PROFILE;
static struct {FTR_ACTOR *ftr_actor_list;} l_aMR_work;
#define UT_X_NUM 16
#define UT_Z_NUM 16
#define aFTR_SHAPE_TYPE_NUM 6
#define aFTR_SHAPE_TYPEA 4
#define aFTR_SHAPE_TYPEC 5
#define aMR_FIT_FTR_MAX 4
#define mCoBG_LAYER1 1
#define aMR_NO_FTR_ID -1
#define EMPTY_NO 0
#define FALSE 0
#define TRUE 1
#define mFI_UT_WORLDSIZE_X_F 40.0f
#define mFI_UT_WORLDSIZE_Z_F 40.0f
#define mFI_UT_WORLDSIZE_HALF_X_F 20.0f
#define mFI_UT_WORLDSIZE_HALF_Z_F 20.0f
#define ITEM_IS_FTR(item) (((item)>>12)==1 || ((item)>>12)==3)
#define DEG2SHORT_ANGLE(deg) ((s16)((deg)*(65536.0f/360.0f)))
#define SHORT2RAD_ANGLE2(angle) ((float)(angle)*((2.0f*3.14159265358979323846f)/65536.0f))
#define RAD2DEG(rad) ((180.0f/3.14159265358979323846f)*(rad))
#define MTX_LOAD 0
#define MTX_MULT 1
#define Common_Get(name) name
#define OPEN_DISP(graph) ((void)(graph))
#define CLOSE_DISP(graph) ((void)(graph))
#define NEXT_POLY_OPA_DISP 0
#define NEXT_POLY_XLU_DISP 1
#define gDPSetTexEdgeAlpha(stream,alpha) do {assert((stream)==0 || (stream)==1);assert((alpha)==144);} while(0)

typedef struct {u16 item;s16 angle;float pos[3],scale;} Draw;
typedef struct {
    u16 foreground[256];int place[256];s16 angles[256];
    Draw drawn[4];int draws,writes;
} Grid;
typedef struct {Grid grid;RoomRig actors[5];u8 used[5];RoomCarryAccess access;} World;
static World native;
static Grid donor;
static FTR_ACTOR donor_actors[5];
static aFTR_PROFILE profile={37.0f};
static unsigned cases,frames;

static int at(float x,float z) {return (int)(x/40.0f)+16*(int)(z/40.0f);}
static void write_furniture(Grid *grid,int id,u16 name,int cell_no,int put) {
    assert(cell_no>=0 && cell_no<256);grid->foreground[cell_no]=put ? name : 0;
    if (!put) for (int i=0;i<256;++i) if (grid->place[i]==id) grid->foreground[i]=0;
    ++grid->writes;
}
static void write_place(Grid *grid,int cell_no,int id) {
    assert(cell_no>=0 && cell_no<256);grid->place[cell_no]=id;++grid->writes;
}
static void record_draw(Grid *grid,u16 item,const float *pos,float scale,s16 angle) {
    if (!item) return;
    assert(grid->draws<4);Draw *draw=grid->drawn+grid->draws++;
    draw->item=item;draw->angle=angle;draw->scale=scale;memcpy(draw->pos,pos,12);
}
static int lookup(void *ctx,int cell_no) {return ((World *)ctx)->grid.place[cell_no];}
static float top_height(void *ctx,RoomRig *actor) {(void)ctx;(void)actor;return 43.0f;}
static void set_furniture(void *ctx,RoomRig *actor,int put) {
    write_furniture(&((World *)ctx)->grid,actor->id,actor->index,at(actor->position[0],actor->position[2]),put);
}
static void set_place(void *ctx,int cell_no,int id) {write_place(&((World *)ctx)->grid,cell_no,id);}
static s16 get_angle(void *ctx,int cell_no) {return ((World *)ctx)->grid.angles[cell_no];}
static void set_angle(void *ctx,int cell_no,s16 angle) {((World *)ctx)->grid.angles[cell_no]=angle;}
static void draw_item(void *ctx,RoomRigGame *game,u16 item,const float *pos,float scale,s16 angle) {
    assert(game);record_draw(&((World *)ctx)->grid,item,pos,scale,angle);
}
static u16 *aMR_GetLayerTopFg(int layer) {assert(layer==1);return donor.foreground;}
static aFTR_PROFILE *aMR_GetFurnitureProfile(u16 name) {assert(name);return &profile;}
static float mCoBG_GetBgY_OnlyCenter_FromWpos2(xyz_t pos,float offset) {(void)pos;assert(offset==0);return 6.0f;}
static int aMR_UnitNum2FtrItemNoFtrID(u16 *item,int *id,int x,int z,int layer) {
    assert(layer==1);*id=donor.place[x+16*z];*item=donor.foreground[x+16*z];return *id>=0;
}
static void aMR_SetFurniture2FG(FTR_ACTOR *actor,xyz_t pos,int put) {
    write_furniture(&donor,actor->id,actor->name,at(pos.x,pos.z),put);
}
static void aMR_SetInfoFurnitureTable(int shape,int cell_no,int id,int layer) {
    assert(shape==4 && layer==1);write_place(&donor,cell_no,id);
}
static void mFI_Wpos2UtCenterWpos(xyz_t *pos,xyz_t source) {
    *pos=(xyz_t){(int)(source.x/40.0f)*40.0f+20.0f,source.y,(int)(source.z/40.0f)*40.0f+20.0f};
}
static s16 single_get(int z,int x,int layer) {assert(layer==1);return donor.angles[x+16*z];}
static void single_set(int z,int x,int layer,s16 angle) {assert(layer==1);donor.angles[x+16*z]=angle;}
static void single_draw(GAME *game,u16 item,xyz_t *pos,float scale,s16 angle,int layer) {
    assert(game && layer==1);float point[3]={pos->x,pos->y,pos->z};record_draw(&donor,item,point,scale,angle);
}
typedef struct {
    void (*single_draw_proc)(GAME*,u16,xyz_t*,float,s16,int);
    s16 (*single_get_angle_y_proc)(int,int,int);
    void (*single_set_angle_y_proc)(int,int,int,s16);
} Shop;
static Shop shop={single_draw,single_get,single_set};
static struct {Shop *shop_goods_clip;struct {ACTOR *my_room_actor_p;} *my_room_clip;} clip;

/* Independent ordinary matrix operations for the unchanged donor transform. */
static float matrix[3][4];
static void Matrix_translate(float x,float y,float z,int mode) {
    if (!mode) {
        memset(matrix,0,sizeof(matrix));for(int i=0;i<3;++i)matrix[i][i]=1;
        matrix[0][3]=x;matrix[1][3]=y;matrix[2][3]=z;
    } else for(int i=0;i<3;++i)matrix[i][3]+=matrix[i][0]*x+matrix[i][1]*y+matrix[i][2]*z;
}
static void Matrix_RotateY(s16 angle,int mode) {
    assert(mode==1);if(!angle)return;
    float sine=sin_s(angle),cosine=cos_s(angle);
    for(int i=0;i<3;++i) {
        float x=matrix[i][0],z=matrix[i][2];
        matrix[i][0]=x*cosine-z*sine;matrix[i][2]=x*sine+z*cosine;
    }
}
static void Matrix_Position(xyz_t *src,xyz_t *out) {
    float result[3];
    for(int i=0;i<3;++i)result[i]=matrix[i][3]+(matrix[i][0]*src->x+matrix[i][1]*src->y+matrix[i][2]*src->z);
    *out=(xyz_t){result[0],result[1],result[2]};
}

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#include "donor_carry.inc"
#pragma GCC diagnostic pop

static void close_float(float actual,float expected) {assert(fabsf(actual-expected)<0.0002f);}
static void compare_grid(void) {
    assert(!memcmp(native.grid.foreground,donor.foreground,sizeof(donor.foreground)));
    assert(!memcmp(native.grid.place,donor.place,sizeof(donor.place)));
    assert(!memcmp(native.grid.angles,donor.angles,sizeof(donor.angles)));
    assert(native.grid.writes==donor.writes);
}
static void compare(const RoomCarry *carry,const MY_ROOM_ACTOR *owner,int live) {
    assert(carry->parent_id==owner->parent_ftr.ftrID && carry->angle==owner->parent_ftr.angle_y);
    for(int i=0;i<4;++i) {
        const RoomCarrySlot *slot=carry->slots+i;const aMR_fit_ftr_c *fit=owner->parent_ftr.fit_ftr_table+i;
        assert(slot->active==fit->exist_flag && slot->actor_id==fit->ftr_ID && slot->item==fit->item_no);
        assert(slot->angle==fit->angle_y);
        close_float(slot->relative[0],fit->pos.x);close_float(slot->relative[1],fit->pos.y);close_float(slot->relative[2],fit->pos.z);
        if(live && slot->active) {
            close_float(slot->world[0],fit->ut_pos.x);close_float(slot->world[1],fit->ut_pos.y);close_float(slot->world[2],fit->ut_pos.z);
        }
    }
    for(int i=1;i<5;++i) {
        RoomRig *a=native.actors+i;FTR_ACTOR *b=donor_actors+i;
        close_float(a->position[0],b->position.x);close_float(a->position[1],b->position.y);close_float(a->position[2],b->position.z);
        assert(a->s_angle_y==b->s_angle_y);close_float(a->angle_y,b->angle_y);close_float(a->angle_y_target,b->angle_y_target);
    }
    compare_grid();
}
static void setup(int shape,unsigned mask,RoomCarry *carry,MY_ROOM_ACTOR *owner) {
    memset(&native,0,sizeof(native));memset(&donor,0,sizeof(donor));memset(donor_actors,0,sizeof(donor_actors));
    memset(owner,0,sizeof(*owner));owner->parent_ftr.ftrID=-1;clip.shop_goods_clip=&shop;
    l_aMR_work.ftr_actor_list=donor_actors;
    for(int i=0;i<256;++i)native.grid.place[i]=donor.place[i]=-1;
    native.access=(RoomCarryAccess){&native,native.actors,native.used,5,native.grid.foreground,
        lookup,top_height,set_furniture,set_place,get_angle,set_angle,draw_item};
    af_v3_room_carry_init(carry);
    for(int i=0;i<5;++i) {
        RoomRig *a=native.actors+i;FTR_ACTOR *b=donor_actors+i;
        a->id=b->id=i;a->index=b->name=(u16)(0x3000+i*4);native.used[i]=1;
        a->shape_type=b->shape_type=(u8)(i ? 4 : shape);a->layer=b->layer=i ? 1 : 0;
        a->s_angle_y=b->s_angle_y=(s16)(i ? 2300*i : 30000);
        a->angle_y=a->angle_y_target=b->angle_y=b->angle_y_target=0;
    }
    RoomRig *parent=native.actors;FTR_ACTOR *other=donor_actors;
    parent->position[0]=other->position.x=240;parent->position[1]=other->position.y=6;
    parent->position[2]=other->position.z=240;
    parent->base_position[0]=other->base_position.x=7;
    parent->base_position[1]=other->base_position.y=-3;
    parent->base_position[2]=other->base_position.z=11;
    int cells[4];int count=af_v3_room_carry_cells(cells,parent->position,(u8)shape);
    assert(count==(shape<4 ? 2 : shape==4 ? 1 : 4));
    for(int i=0;i<count;++i) {
        int cell_no=cells[i];RoomRig *a=native.actors+i+1;FTR_ACTOR *b=donor_actors+i+1;
        a->position[0]=b->position.x=(cell_no&15)*40.0f+20.0f;a->position[1]=b->position.y=43.0f;
        a->position[2]=b->position.z=(cell_no>>4)*40.0f+20.0f;
        if(!(mask&(1u<<(i+4))))continue;
        u16 item=(mask&(1u<<i)) ? a->index : (u16)(0x2200+i);
        native.grid.foreground[cell_no]=donor.foreground[cell_no]=item;
        native.grid.angles[cell_no]=donor.angles[cell_no]=(s16)(30000-i*5000);
        if(mask&(1u<<i))native.grid.place[cell_no]=donor.place[cell_no]=i+1;
    }
}
static void motion_case(int shape,unsigned mask,int direction) {
    struct {u32 before;RoomCarry carry;u32 after;} guarded={.before=0x12345678,.after=0x9ABCDEF0};
    RoomCarry *carry=&guarded.carry;MY_ROOM_ACTOR owner;setup(shape,mask,carry,&owner);
    RoomRig *parent=native.actors;FTR_ACTOR *source=donor_actors;
    assert(af_v3_room_carry_request(carry,&native.access,parent)==aMR_RequestItemToFitFurniture(&owner,source));
    compare(carry,&owner,0);
    for(int frame=0;frame<=20;++frame) {
        parent->s_angle_y=source->s_angle_y=(s16)(30000+direction*frame*16384/20);
        parent->position[0]=source->position.x=240+frame*2.0f;
        parent->position[2]=source->position.z=240-frame*2.0f;
        assert(af_v3_room_carry_update(carry,&native.access,parent));
        aMR_GetItemPosOnMovingFurniture(&owner,source);compare(carry,&owner,1);
        for(int i=1;i<5;++i) {
            RoomRig *p=af_v3_room_carry_parent(carry,&native.access,native.actors+i);
            FTR_ACTOR *q=aMR_GetParentFactor(donor_actors+i,&owner);
            assert((p ? p->id : -1)==(q ? q->id : -1));
            assert(af_v3_room_carry_angle(carry,&native.access,native.actors+i)==aMR_GetParentAngleOffset(donor_actors+i,&owner));
        }
        native.grid.draws=donor.draws=0;GAME game={0};RoomRigGame native_game={0};
        assert(af_v3_room_carry_draw(carry,&native.access,parent,&native_game));
        aMR_DrawItemOnMovingFurniture(&owner,source,&game);
        assert(native.grid.draws==donor.draws);
        for(int i=0;i<donor.draws;++i) {
            Draw *a=native.grid.drawn+i,*b=donor.drawn+i;
            assert(a->item==b->item && a->angle==b->angle && a->scale==b->scale);
            for(int axis=0;axis<3;++axis)close_float(a->pos[axis],b->pos[axis]);
        }
        ++frames;
    }
    assert(af_v3_room_carry_release(carry,&native.access,parent));
    aMR_RequestItemToUnFitFurniture(&owner,source);compare(carry,&owner,1);
    assert(guarded.before==0x12345678 && guarded.after==0x9ABCDEF0);++cases;
}

static void rejection_cases(void) {
    RoomCarry carry;MY_ROOM_ACTOR owner;setup(5,0xFF,&carry,&owner);
    RoomRig *parent=native.actors;
    for(int reason=0;reason<12;++reason) {
        setup(5,0xFF,&carry,&owner);int first=5+16*5;
        if(reason==0)native.used[3]=0;
        if(reason==1)native.actors[3].id=9;
        if(reason==2)native.actors[3].layer=0;
        if(reason==3)native.grid.place[first+16]=0;
        if(reason==4)parent->kept_item=0x2A00;
        if(reason==5)parent->layer=1;
        if(reason==6)parent->shape_type=6;
        if(reason==7)parent->position[0]=-0.1f;
        if(reason==8)parent->position[0]=NAN;
        if(reason==9)native.access.draw_item=NULL;
        if(reason==10)native.access.foreground=NULL;
        if(reason==11)carry.parent_id=0;
        World before=native;RoomCarry before_carry=carry;
        assert(!af_v3_room_carry_request(&carry,&native.access,parent));
        assert(!memcmp(&before,&native,sizeof(native)) && !memcmp(&before_carry,&carry,sizeof(carry)));
    }
    /* Refuse an incomplete restoration without forgetting any detached item. */
    for(int reason=0;reason<5;++reason) {
        setup(5,0xFF,&carry,&owner);assert(af_v3_room_carry_request(&carry,&native.access,parent));
        assert(af_v3_room_carry_update(&carry,&native.access,parent));
        if(reason==0)carry.slots[2].world[0]=-1;
        if(reason==1)native.grid.foreground[at(carry.slots[2].world[0],carry.slots[2].world[2])]=0x2222;
        if(reason==2)native.used[3]=0;
        if(reason==3)memcpy(carry.slots[2].world,carry.slots[1].world,12);
        if(reason==4)native.access.set_place=NULL;
        World before=native;RoomCarry before_carry=carry;
        assert(!af_v3_room_carry_release(&carry,&native.access,parent));
        assert(!memcmp(&before,&native,sizeof(native)) && !memcmp(&before_carry,&carry,sizeof(carry)));
    }
    /* A repeated occupied cell must not register the same actor twice. */
    setup(5,0xFF,&carry,&owner);native.grid.place[6+16*6]=2;
    native.grid.foreground[6+16*6]=native.actors[2].index;
    assert(af_v3_room_carry_request(&carry,&native.access,parent));
    assert(carry.slots[0].actor_id==1 && carry.slots[1].actor_id==2 && carry.slots[2].actor_id==3 && !carry.slots[3].active);
    assert(native.grid.place[6+16*6]==-1 && !native.grid.foreground[6+16*6]);
    int cells[4]={-9,-9,-9,-9};float point[3]={0,0,0};
    assert(!af_v3_room_carry_cells(cells,point,1) && cells[0]==-9);
    assert(!af_v3_room_carry_cells(cells,point,0) && cells[0]==-9);
    point[0]=639;assert(!af_v3_room_carry_cells(cells,point,3) && cells[0]==-9);
    point[0]=0;point[2]=639;assert(!af_v3_room_carry_cells(cells,point,2) && cells[0]==-9);
    assert(!af_v3_room_carry_parent(NULL,&native.access,native.actors+1));
    assert(!af_v3_room_carry_angle(NULL,&native.access,native.actors+1));
}

int main(void) {
    /* Every shape, empty/full/mixed top, translation, both rotations, and wrap. */
    const unsigned masks[]={0,0xF0,0xFF,0xF5,0x51};
    for(int shape=0;shape<6;++shape)for(unsigned mask=0;mask<sizeof(masks)/sizeof(masks[0]);++mask)
        for(int direction=-1;direction<=1;++direction)motion_case(shape,masks[mask],direction);
    rejection_cases();
    printf("%u donor carrying cases, %u transformed/drawn frames; transactional guards pass\n",cases,frames);
}
