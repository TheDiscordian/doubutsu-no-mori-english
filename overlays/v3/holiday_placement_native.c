/* Actual N64 field/NPC primitives. Check the current owner before resolving
 * private helpers; link-time overlay addresses are never callable addresses. */
#include "holiday_placement.h"
#include "holiday_native.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef struct {float x,y,z;} Position;
extern const u32 af_holiday_manager_descriptor[8];
extern const u8 af_holiday_native_rtc[8];
extern const u32 *af_holiday_native_clip;
extern void *af_holiday_native_game;
extern u16 af_holiday_native_field_id(void);
extern int af_holiday_native_bg_busy(int,int);
extern int af_holiday_native_other(int,AFHolidayBlock);
extern int af_holiday_native_unit(int *,int *,int,int);
extern const u32 *af_holiday_native_collision(int,int);
extern const u16 *af_holiday_native_foreground(int,int);
extern int af_holiday_native_fg_allowed(u16,u32);
extern void af_holiday_native_position(Position *,int,int,int,int);
extern int af_holiday_native_height_gap(Position);
extern AFHolidayPlace *af_holiday_native_get_place(int,u8);
extern AFHolidayPlace *af_holiday_native_reserve_place(int,u8);
extern void af_holiday_native_set_status(int,int);
extern int af_holiday_native_check_status(int,int);
#define FN(at,ret,...) ((ret (*)(__VA_ARGS__))(at))

typedef struct {void *manager;u32 owner;} Native;
static int outdoors(void *c) {(void)c;return !(af_holiday_native_field_id()&0xF000);}
static int busy(void *c,int x,int z) {(void)c;return af_holiday_native_bg_busy(x,z);}
static int other(void *c,u32 t,AFHolidayBlock b) {(void)c;return af_holiday_native_other(t,b);}
static int unit(void *c,int *x,int *z,int bx,int bz) {(void)c;return af_holiday_native_unit(x,z,bx,bz);}
static int height(void *c,int bx,int bz,int x,int z) {
    (void)c;
    const u32 *col=af_holiday_native_collision(bx,bz);
    const u16 *fg=af_holiday_native_foreground(bx,bz);
    if(!col || !fg || !af_holiday_native_fg_allowed(fg[z*16+x],col[z*16+x]&63))return 0;
    Position p;af_holiday_native_position(&p,bx,bz,x,z);
    return !af_holiday_native_height_gap(p);
}
static AFHolidayPlace *get(void *c,u32 t,u32 id) {(void)c;return af_holiday_native_get_place(t,id);}
static AFHolidayPlace *reserve(void *c,u32 t,u32 id) {(void)c;return af_holiday_native_reserve_place(t,id);}
static int forward(void *c,int *x,int *z) {
    Native *n=c;return FN(n->owner,int,int *,int *)(x,z); /* get_forward_block */
}
static void flatten(void *c,AFHolidayPlace *p) {
    Native *n=c;FN(n->owner+0x13D8,void,AFHolidayPlace *)(p); /* be_flat_unit */
}
static int spawn(void *c,AFHolidayPlace *p) {
    (void)c;
    if(!af_holiday_native_clip || !af_holiday_native_clip[0] || !af_holiday_native_game)return 0;
    return FN(af_holiday_native_clip[0],int,void *,u16,int,int,int,int,int,int,int)(
        af_holiday_native_game,p->name,-1,-1,-1,p->block.x,p->block.z,p->unit.x,p->unit.z);
}
static void error(void *c,u32 type) {(void)c;af_holiday_native_set_status(type,AF_HE_ERROR);}
static int bind(Native *n,void *manager,AFHolidayField *f,AFHolidayPlacementOps *o) {
    const u32 *d=af_holiday_manager_descriptor;
    if(!manager || d[0]!=0x03800000 || d[2]!=0x8095B8B0 || d[3]-d[2]!=d[1]-d[0] ||
       d[1]-d[0]<40048 || d[1]-d[0]>0x10000 || d[4]<0x80000000 || d[4]>=0x80800000 ||
       d[1]-d[0]>0x80800000-d[4])return 0;
    n->manager=manager;n->owner=d[4];
    /* Same four physical landmarks as native search_free_unit. The N64 town
     * has no donor island dock; no fake dock coordinates are supplied. */
    if(!af_holiday_placement_field(manager,af_holiday_native_rtc,f))return 0;
    *o=(AFHolidayPlacementOps){n,outdoors,busy,other,unit,height,get,reserve,forward,flatten,spawn,error};
    return 1;
}
int af_holiday_placement_native_make(void *manager,u32 donor,u32 name,u32 donor_name,AFHolidayPlace **out) {
    Native n;AFHolidayField f;AFHolidayPlacementOps o;AFHolidayOwner owner;
    int type=af_holiday_native_type(donor);
    if(type<0 || af_holiday_event_owner(af_holiday_event_data,812,donor,&owner)!=1 ||
       !bind(&n,manager,&f,&o) ||
       (donor_name!=(owner.kind==AF_HE_HALLOWEEN?0xD079u:0xD074u)))return -1;
    return af_holiday_placement_make(&f,&o,(u32)type,name,0x51,owner.kind,
        (int)(donor+donor_name+0x51),out);
}
int af_holiday_placement_native_show_id(void *manager,u32 donor,u32 id,AFHolidayBlock *forward_block) {
    Native n;AFHolidayField f;AFHolidayPlacementOps o;
    int type=af_holiday_native_type(donor);
    if(type<0 || !bind(&n,manager,&f,&o))return 0;
    return af_holiday_placement_show(&f,&o,(u32)type,id,forward_block);
}
int af_holiday_placement_native_show(void *manager,u32 donor,AFHolidayBlock *forward_block) {
    return af_holiday_placement_native_show_id(manager,donor,0x51,forward_block);
}
int af_holiday_placement_native_cull(u32 donor) {
    int type=af_holiday_native_type(donor);
    return type>=0 && af_holiday_native_check_status(type,AF_HE_STOP);
}
