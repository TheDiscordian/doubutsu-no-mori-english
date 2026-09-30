/* Bind complete hiding/arrival to real native fields and a loaded manager. */
#include "holiday_hiding.h"
#include "holiday_events.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef struct {float x,y,z;} Position;
extern const u32 af_holiday_manager_descriptor[8];
extern const u8 af_holiday_native_rtc[8];
extern const u32 *af_holiday_native_clip;
extern void *af_holiday_native_game;
extern u16 af_holiday_native_field_id(void);
extern int af_holiday_native_bg_busy(int,int),af_holiday_native_other(int,AFHolidayBlock);
extern int af_holiday_native_unit(int *,int *,int,int);
extern const u32 *af_holiday_native_collision(int,int);
extern const u16 *af_holiday_native_foreground(int,int);
extern AFHolidayPlace *af_holiday_native_get_place(int,u8),*af_holiday_native_reserve_place(int,u8);
extern void af_holiday_native_set_status(int,int);
extern int af_holiday_hide_native_hard(u16,u32),af_holiday_hide_native_check(int,int,int,int);
extern void af_holiday_hide_native_police(int *,int *,int *,int *);
extern int af_holiday_hide_native_block(int *,int *,Position);
extern int af_holiday_hide_native_kind(int *,int *,u32);
extern const Position af_holiday_hide_native_ball;
#define FN(at,ret,...) ((ret (*)(__VA_ARGS__))(at))
typedef struct {void *manager;u32 owner;AFHolidayField *field;AFHolidayHiding *hiding;} Native;
static int outdoors(void *c) {(void)c;return !(af_holiday_native_field_id()&0xF000);}
static int busy(void *c,int x,int z) {(void)c;return af_holiday_native_bg_busy(x,z);}
static int other(void *c,u32 type,AFHolidayBlock b) {(void)c;return af_holiday_native_other(type,b);}
static int unit(void *c,int *x,int *z,int bx,int bz) {(void)c;return af_holiday_native_unit(x,z,bx,bz);}
static const u32 *collision(void *c,int x,int z) {(void)c;return af_holiday_native_collision(x,z);}
static const u16 *foreground(void *c,int x,int z) {(void)c;return af_holiday_native_foreground(x,z);}
static int height(void *c,int bx,int bz,int x,int z) {
    (void)c;
    const u32 *col=af_holiday_native_collision(bx,bz);
    const u16 *fg=af_holiday_native_foreground(bx,bz);
    return col && fg && x>=0 && x<16 && z>=0 && z<16 &&
        af_holiday_hide_native_hard(fg[z*16+x],col[z*16+x]&63);
}
static int ball(void *c,AFHolidayBlock *b) {
    (void)c;return af_holiday_hide_native_block(&b->x,&b->z,af_holiday_hide_native_ball);
}
static int marine(void *c,AFHolidayBlock *b) {
    (void)c;return af_holiday_hide_native_kind(&b->x,&b->z,0x880);
}
static AFHolidayPlace *get(void *c,u32 t,u32 id) {(void)c;return af_holiday_native_get_place(t,id);}
static AFHolidayPlace *reserve(void *c,u32 t,u32 id) {(void)c;return af_holiday_native_reserve_place(t,id);}
static int forward(void *c,int *x,int *z) {Native *n=c;return FN(n->owner,int,int *,int *)(x,z);}
static void flatten(void *c,AFHolidayPlace *p) {Native *n=c;FN(n->owner+0x13D8,void,AFHolidayPlace *)(p);}
static int spawn(void *c,AFHolidayPlace *p) {
    (void)c;
    return af_holiday_native_clip && af_holiday_native_clip[0] && af_holiday_native_game &&
        FN(af_holiday_native_clip[0],int,void *,u16,int,int,int,int,int,int,int)(
            af_holiday_native_game,p->name,-1,-1,-1,p->block.x,p->block.z,p->unit.x,p->unit.z);
}
static void error(void *c,u32 type) {(void)c;af_holiday_native_set_status(type,AF_HE_ERROR);}
static int occupied(void *c,const AFHolidayPlace *p) {
    (void)c;
    if(!af_holiday_hide_native_check(p->block.x,p->block.z,p->unit.x,p->unit.z))return 1;
    int bx,bz,x,z;af_holiday_hide_native_police(&bx,&bz,&x,&z);
    return p->block.x==bx && p->block.z==bz && p->unit.x==x && p->unit.z==z;
}
static int free_unit(void *c,u32 type,AFHolidayPlace *p,int seed) {
    Native *n=c;
    return af_holiday_placement_search(n->field,&n->hiding->placement,type,p,1,seed);
}
static int bind(Native *n,void *manager,AFHolidayField *f,AFHolidayHiding *h) {
    const u32 *d=af_holiday_manager_descriptor;
    if(!manager || d[0]!=0x03800000 || d[2]!=0x8095B8B0 || d[3]-d[2]!=d[1]-d[0] ||
       d[1]-d[0]<40048 || d[1]-d[0]>0x10000 || d[4]<0x80000000 || d[4]>=0x80800000 ||
       d[1]-d[0]>0x80800000-d[4] || !af_holiday_placement_field(manager,af_holiday_native_rtc,f))return 0;
    *n=(Native){manager,d[4],f,h};
    *h=(AFHolidayHiding){
        {n,outdoors,busy,other,unit,height,get,reserve,forward,flatten,spawn,error},
        foreground,collision,af_holiday_hide_native_hard,ball,marine,occupied,free_unit};
    return 1;
}
int af_holiday_hide_native_make(void *m,u32 type,u32 name,u32 id,int seed,AFHolidayPlace **out) {
    Native n;AFHolidayField f;AFHolidayHiding h;
    if(!out)return -1;
    *out=0;
    return bind(&n,m,&f,&h)?af_holiday_hide_make(&f,&h,type,name,id,seed,out):-1;
}
int af_holiday_hide_native_walk(void *m,u32 type,u32 source_name,u32 id,int seed,AFHolidayPlace **out) {
    Native n;AFHolidayField f;AFHolidayHiding h;
    if(!out)return -1;
    *out=0;
    return bind(&n,m,&f,&h)?af_holiday_hide_walk(&f,&h,type,source_name,id,seed,out):-1;
}
int af_holiday_hide_native_show(void *m,u32 type,u32 id,int seed,AFHolidayBlock *forward_block) {
    Native n;AFHolidayField f;AFHolidayHiding h;
    return bind(&n,m,&f,&h)?af_holiday_hide_show(&f,&h,type,id,seed,forward_block):0;
}
int af_holiday_hide_native_fluctuation(void *m,int *seed) {
    Native n;AFHolidayField f;AFHolidayHiding h;
    if(!seed || !bind(&n,m,&f,&h))return 0;
    *seed=*(const int *)(n.owner+0x6B24);return 1;
}
