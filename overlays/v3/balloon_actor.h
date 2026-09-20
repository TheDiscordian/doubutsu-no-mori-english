#ifndef AF_V3_BALLOON_ACTOR_H
#define AF_V3_BALLOON_ACTOR_H
typedef unsigned char u8;
typedef unsigned short u16;
typedef signed short s16;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
typedef struct { float x,y,z; } BalloonPosition;
typedef struct { s16 x,y,z; } BalloonAngle;
typedef struct {
    u8 actor[0x174], keyframe[0x70];
    BalloonAngle work[8], morph[8];
    u32 padding;
    u8 matrices[2][4][64];
    int mode, saved_type, pending, type;
    BalloonAngle angle;
    s16 lean;
    float frame, speed;
    BalloonPosition position;
    int ready;
    u8 align_assets[8];
    u8 model[5728], animation[1440];
} Balloon;
_Static_assert(__builtin_offsetof(Balloon,keyframe)==0x174,"Native keyframe");
_Static_assert(__builtin_offsetof(Balloon,matrices)==0x248,"Double-buffered matrices");
_Static_assert(__builtin_offsetof(Balloon,mode)==0x448,"Source mode fields");
_Static_assert(__builtin_offsetof(Balloon,model)==0x480,"Aligned independent model bank");
_Static_assert(sizeof(Balloon)==0x2080,"Complete independently owned balloon");
#define BWORD(p,o) (*(int *)((u8 *)(p)+(o)))
#define BREAL(p,o) (*(float *)((u8 *)(p)+(o)))
#define BSHORT(p,o) (*(s16 *)((u8 *)(p)+(o)))
#define BPOS(p,o) (*(BalloonPosition *)((u8 *)(p)+(o)))
#ifdef __mips__
#define BSEG (*(u32 *)0x801458B8u)
static inline void *balloon_native(u32 at) {
    if (at>=0x808B2D50u) at=*(volatile u32 *)0x80143900u-0x808DD748u+at;
    return (void *)at;
}
#else
extern u32 af_test_balloon_segment;
extern void *af_test_balloon_function(u32);
#define BSEG af_test_balloon_segment
#define balloon_native af_test_balloon_function
#endif
#define BFN(at,result,...) ((result (*)(__VA_ARGS__))balloon_native(at))
extern int af_v3_player_selected_equipment(u32);
extern void af_v3_balloon_draw(Balloon *,void *);
extern void af_v3_balloon_hide(Balloon *,void *);
extern int af_v3_balloon_fly(Balloon *,void *,int,const BalloonAngle *,s16,
                            const BalloonPosition *,float,float);
#endif
