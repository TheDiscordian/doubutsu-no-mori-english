/* External complete object banks use the ordinary worker and notifications.
 * Install the worker dispatch only after the checked resident packet is loaded.
 * Audio keeps its separate, unchanged physical-ROM path. */
#include "npc_dma.h"
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
extern void af_npc_dma_previous(AFNpcDmaRequest *);
extern int af_npc_dma_pi(u32,void *,u32);
extern void af_npc_dma_error(AFNpcDmaRequest *,const char *,const char *,const char *);
extern void af_npc_dma_writeback(void *,u32),af_npc_dma_invalidate(void *,u32);
#ifdef __mips__
#define worker ((volatile u32 *)0x80026A24u)
_Static_assert(sizeof(AFNpcDmaRequest)==32,"Complete native request");
#else
extern volatile u32 af_npc_dma_worker[2];
#define worker af_npc_dma_worker
#endif
static int valid(void) {
    const AFNpcDma *t=&af_v3_npc_dma;
    if(t->magic!=0x41464E44 || t->version!=1 || !t->count || t->count>8 || t->stride!=12)return 0;
    for(u32 i=0;i<t->count;++i) {
        const AFNpcDmaRow *r=t->rows+i;
        if((r->start|r->end|r->physical)&15u || r->start<0x03FE0000u ||
                r->start>=r->end || r->end>0x04000000u || r->physical<0x100000u ||
                r->physical>0x04000000u-(r->end-r->start))return 0;
        for(u32 j=0;j<i;++j)if(t->rows[j].start<r->end && r->start<t->rows[j].end)return 0;
    }
    return 1;
}
void af_v3_npc_dma_request(AFNpcDmaRequest *q) {
    if(q && valid())for(u32 i=0;i<af_v3_npc_dma.count;++i) {
        const AFNpcDmaRow *r=af_v3_npc_dma.rows+i;
        if(q->vrom>=r->start && q->vrom<r->end) {
            uptr destination=(uptr)q->vram;
            if(!q->bytes || (q->vrom|q->bytes)&1u || destination&7u ||
                    destination<0x80000000u || destination>=0x80800000u ||
                    q->bytes>0x80800000u-destination || q->bytes>r->end-q->vrom) {
                af_npc_dma_error(q,0,"Invalid additional NPC transfer",0);return;
            }
            if(af_npc_dma_pi(r->physical+q->vrom-r->start,q->vram,q->bytes))
                af_npc_dma_error(q,0,"Additional NPC transfer failed",0);
            return;
        }
    }
    /* Includes unknown VROM and damaged metadata: preserve native fatal errors,
     * never report completion of an unperformed transfer. */
    af_npc_dma_previous(q);
}
int af_v3_npc_dma_init(void) {
    if(!valid() || worker[1]!=0x00808025u)return 0;
    u32 call=0x0C000000u|(((uptr)af_v3_npc_dma_request>>2)&0x03FFFFFFu);
    if(worker[0]==call)return 1;
    if(worker[0]!=0x0C009A0Au)return 0;
    worker[0]=call;
    af_npc_dma_writeback((void *)worker,8);af_npc_dma_invalidate((void *)worker,8);
    return 1;
}
