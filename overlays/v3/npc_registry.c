/* Additional NPC profiles share one bounded allocation, drawing, and voice
 * registry. Original NPC pools and all prior dispatchers stay unchanged. */
#include "npc_registry.h"
typedef unsigned char u8;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
static unsigned int read16(const u8 *p) {return (u32)p[0]*256u+p[1];}
static unsigned int read32(const u8 *p) {
    return (u32)p[0]<<24 | (u32)p[1]<<16 | (u32)p[2]<<8 | p[3];
}
static int table_valid(void) {
    const AFNpcExtras *t=&af_v3_npc_extras;
    if(t->magic!=AF_NPC_EXTRA_MAGIC || t->version!=1 || t->count>AF_NPC_EXTRA_MAX || t->stride!=44)return 0;
    for(u32 i=0;i<t->count;++i) {
        const AFNpcExtra *r=t->rows+i;
        if(r->name<0xD090 || r->name>=0xE000 || r->profile<0xCC || r->profile>=0x8000 ||
                (r->flags&~3u) || r->actor_bytes<0x93C || r->actor_bytes>0x10000 ||
                !r->slots || r->slots>16 || !r->area || ((uptr)r->area&15u) ||
                r->stride!=((r->actor_bytes+15u)&~15u)+32u ||
                !r->descriptor || !r->draw || !r->stream || r->stream->name!=r->name ||
                r->model_bank<448 || r->texture_bank<448 || r->model_bank==r->texture_bank ||
                read16(r->draw)!=r->model_bank || read16(r->draw+2)!=r->texture_bank ||
                r->draw[0x5F]!=255 || r->voice>=299)return 0;
        uptr start=(uptr)r->area,end=start+(uptr)r->slots*r->stride;
        if(end<start)return 0;
        for(u32 j=0;j<i;++j) {
            const AFNpcExtra *p=t->rows+j;uptr a=(uptr)p->area,b=a+(uptr)p->slots*p->stride;
            if(r->name==p->name || r->profile==p->profile || (start<b && a<end))return 0;
        }
    }
    return 1;
}
static const AFNpcExtra *name_row(unsigned int name) {
    if(!table_valid())return 0;
    for(u32 i=0;i<af_v3_npc_extras.count;++i)
        if(af_v3_npc_extras.rows[i].name==name)return af_v3_npc_extras.rows+i;
    return 0;
}
static int slot_valid(const AFNpcExtra *r,const u8 *slot) {
    const u32 *h=(const u32 *)slot,*g=(const u32 *)(slot+r->stride-16);
    return h[0]==AF_NPC_SLOT_MAGIC && h[1]<=1 && h[2]==r->name && h[3]==r->profile &&
        g[0]==AF_NPC_SLOT_GUARD && g[1]==AF_NPC_SLOT_GUARD &&
        g[2]==AF_NPC_SLOT_GUARD && g[3]==AF_NPC_SLOT_GUARD;
}
void *af_v3_npc_extra_descriptor(int profile) {
    if(table_valid())for(u32 i=0;i<af_v3_npc_extras.count;++i) {
        const AFNpcExtra *r=af_v3_npc_extras.rows+i;
        if(r->profile==profile)return r->descriptor;
    }
    return af_npc_previous_descriptor(profile);
}
int af_v3_npc_extra_allocate(void **out,const void *profile,void *descriptor,
        const u8 *file,unsigned short name) {
    const AFNpcExtra *r=name_row(name);
    if(!r)return af_npc_previous_allocate(out,profile,descriptor,file,name);
    if(!out)return 0;
    *out=0;
    const u8 *p=profile;
    if(p && r->flags==3 && descriptor==r->descriptor &&
            read16(p)==r->profile && p[2]==3 && read16(p+8)==r->name &&
            read32(p+12)==r->actor_bytes) {
        for(u32 i=0;i<r->slots;++i) {
            u8 *slot=r->area+i*r->stride;
            if(!slot_valid(r,slot))break;
            u32 *h=(u32 *)slot;
            if(!h[1]) {h[1]=1;*out=slot+16;return 1;}
        }
    }
    /* This is the original allocation-failure cleanup after object registration. */
    af_npc_allocation_failed(descriptor,name);return 0;
}
const AFNpcExtra *af_v3_npc_extra_owned(const void *actor) {
    if(!actor || !table_valid())return 0;
    for(u32 i=0;i<af_v3_npc_extras.count;++i) {
        const AFNpcExtra *r=af_v3_npc_extras.rows+i;
        for(u32 j=0;j<r->slots;++j) {
            const u8 *slot=r->area+j*r->stride;
            if(actor==slot+16)
                return slot_valid(r,slot) && ((const u32 *)slot)[1]==1 &&
                    read16(actor)==r->profile && read16((const u8 *)actor+6)==r->name?r:0;
        }
    }
    return 0;
}
void af_v3_npc_extra_free(void *actor) {
    if(table_valid())for(u32 i=0;i<af_v3_npc_extras.count;++i) {
        const AFNpcExtra *r=af_v3_npc_extras.rows+i;
        for(u32 j=0;j<r->slots;++j) {
            u8 *slot=r->area+j*r->stride;
            if(actor==slot+16) {
                /* Keep actor contents: the native delete caller still reads the
                 * actor's name after releasing the slot. A damaged slot is
                 * quarantined, never handed to the original pool or reused. */
                if(slot_valid(r,slot) && ((u32 *)slot)[1]) {
                    ((u32 *)slot)[1]=0;
                    /* Resident descriptors have no overlay vramStart, so the
                     * native caller skips its usual loaded-count decrement. */
                    if(!read32(r->descriptor+8) && r->descriptor[0x1E])--r->descriptor[0x1E];
                }
                return;
            }
        }
    }
    af_npc_previous_free(actor);
}
int af_v3_npc_extra_draw(void *out,unsigned int name) {
    const AFNpcExtra *r=name_row((unsigned short)name);
    if(!r)return af_npc_previous_draw(out,name);
    if(!out)return 0;
    for(u32 i=0;i<100;++i)((u8 *)out)[i]=r->draw[i];
    return 1;
}
unsigned int af_v3_npc_extra_voice(const u8 *draw) {
    if(draw && table_valid())for(u32 i=0;i<af_v3_npc_extras.count;++i) {
        const AFNpcExtra *r=af_v3_npc_extras.rows+i;
        if(read16(draw)==r->model_bank && read16(draw+2)==r->texture_bank) {
            u32 j;for(j=0;j<100;++j)if(draw[j]!=r->draw[j])break;
            if(j==100)return r->voice;
        }
    }
    return af_npc_previous_voice(draw);
}
const AFNpcStreamRecord *af_v3_npc_stream_record(unsigned int name) {
    const AFNpcExtra *r=name_row(name);return r?r->stream:0;
}
#ifdef __mips__
void af_npc_previous_free(void *actor) {
    const unsigned int *clip=*(const unsigned int *const *)0x80136EECu;
    ((void (*)(void *))clip[0x10/4])(actor);
}
#endif
