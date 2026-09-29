/* Per-material textures for complete NPC models that exceed the native atlas.
 * Both native NPC owners call this with the same six-argument skeleton ABI.
 * Ordinary characters retain the installed accessory wrapper unchanged. */
#include "npc_stream_draw.h"
typedef AFNpcU8 u8;
typedef AFNpcU16 u16;
typedef AFNpcU32 u32;
typedef __UINTPTR_TYPE__ uptr;
typedef struct {u32 a,b;} Command;
typedef struct {
    u8 prefix[0x298];Command *p,*d;u8 gap[8];Command *xp,*xd;
} Graphics;
#ifdef __mips__
#define skeleton_draw ((void (*)(void *,void *,void *,AFNpcDrawCallback,AFNpcDrawCallback,void *))0x80473100u)
#define segments ((const u32 *)0x801458A0u)
_Static_assert(__builtin_offsetof(Graphics,xp)==0x2A8,"Native translucent head");
#else
extern void af_npc_stream_skeleton(void *,void *,void *,AFNpcDrawCallback,AFNpcDrawCallback,void *);
extern u32 af_npc_stream_segments[16];
#define skeleton_draw af_npc_stream_skeleton
#define segments af_npc_stream_segments
#endif

static int space(Command *p,Command *d,unsigned int count) {
    return p && (uptr)d>=(uptr)p && (uptr)d-(uptr)p>=count*sizeof(Command);
}
static void bind(Command **head,const u32 *addresses,unsigned int n) {
    Command *p=*head;
    for(unsigned int i=0;i<n;++i)
        *p++=(Command){0xDB060000u+(7u+i)*4u,addresses[i]&0x1FFFFFFFu};
    *head=p;
}
void af_v3_npc_stream_draw(void *game,void *skeleton,void *matrices,
        AFNpcDrawCallback before,AFNpcDrawCallback after,void *actor) {
    const u8 *npc=actor;
    const AFNpcStreamRecord *row=npc?af_v3_npc_stream_record(*(const u16 *)(npc+6)):0;
    if(!row) {
        skeleton_draw(game,skeleton,matrices,before,after,actor);
        return;
    }
    if(!game || !matrices || row->name!=*(const u16 *)(npc+6) ||
            row->texture_bytes>0x1620u || row->texture_bytes<4096u ||
            row->body_offset>row->texture_bytes-4096u || (row->body_offset&7u) ||
            (row->mouth_count && row->mouth_count!=6u))return;
    /* Draw-record pointers are segment-six offsets, not CPU pointers. The
     * native renderer temporarily binds the texture slot, then restores the
     * model slot before this call. Resolve the actor's actual texture slot. */
    u32 slot=*(const u32 *)(npc+0x708),count=*(const u32 *)((const u8 *)game+0x1904);
    if(count>73u || slot>=count || *(const u32 *)(npc+0x750)!=0x06000000u)return;
    const u8 *bank=(const u8 *)game+0x110+slot*0x54;
    if(*(const short *)bank<=0 || *(const u32 *)(bank+0x10)<row->texture_bytes)return;
    u32 palette=*(const u32 *)(bank+4),eye=npc[0x710],mouth=npc[0x71C];
    int eyes=!!row->eyes[0];
    for(unsigned int i=0;i<8;i++)if(!!row->eyes[i]!=eyes)return;
    if(!eyes && row->mouth_count)return;
    if((palette&7u) || palette<0x80000000u || palette>0x80800000u-row->texture_bytes ||
            (eyes && eye>=8u) || (row->mouth_count && mouth>=row->mouth_count))return;
    u32 offsets[3]={row->body_offset,eyes?row->eyes[eye]:0,0};
    unsigned int n=row->mouth_count?3:eyes?2:1;
    if(!eyes)for(unsigned int i=0;i<8;i++)if(*(const u32 *)(npc+0x754+4*i))return;
    if(n==3)offsets[2]=row->mouths[mouth];
    u32 addresses[3],saved[3];
    for(unsigned int i=0;i<n;++i) {
        if(i && ((offsets[i]&7u) || offsets[i]>row->texture_bytes-256u))return;
        addresses[i]=palette+offsets[i];saved[i]=segments[7+i];
        u32 native=*(const u32 *)(npc+(i==0?0x74C:i==1?0x754+eye*4:0x774+mouth*4));
        if(native!=0x06000000u+offsets[i])return;
    }
    Graphics *g=*(Graphics **)game;
    if(!g || !space(g->p,g->d,n*2) || !space(g->xp,g->xd,n*2))return;
    Command *old=g->p,*xold=g->xp;
    bind(&g->p,addresses,n);bind(&g->xp,addresses,n);
    skeleton_draw(game,skeleton,matrices,before,after,actor);
    if(!space(g->p,g->d,n) || !space(g->xp,g->xd,n)) {
        /* Discard this actor's commands if its draw leaves no restoration room.
         * Retain any matrix allocations; never rewind the arena tail. */
        g->p=old;g->xp=xold;
        return;
    }
    bind(&g->p,saved,n);bind(&g->xp,saved,n);
}
