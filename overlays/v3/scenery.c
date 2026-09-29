#include "scenery.h"
#ifdef AF_V3_SCENERY_FAMILIES
#include "resource_dma.h"
#endif

static int span(u32 at,u32 count,u32 stride,u32 size) {
    return at>=128u && !(at&3u) && at<=size && count<=(size-at)/stride;
}

static void palette(u8 *bank) {
    u32 *h=(u32 *)bank;
    int term=af_scenery_term();
    if ((u32)term>=18u) term=0;
    if (h[TERM]==(u32)term) return;
    u32 count=h[VERSION]==2u ? h[PALETTE_N] : 1u;
    for (u32 index=0;index<count;index++) {
        const u32 *r=(const u32 *)(bank+h[PALETTES]+index*16u);
        u32 data=h[VERSION]==2u ? r[0] : h[PALETTES];
        u32 active=h[VERSION]==2u ? r[1] : h[ACTIVE];
        u32 terms=h[VERSION]==2u ? r[2] : h[TERMS];
        u8 *dest=bank+active;
        const u8 *src=bank+data+32u*bank[terms+(u32)term];
        for (u32 i=0;i<32u;i++) dest[i]=src[i];
        af_scenery_writeback(dest,32);
    }
    h[TERM]=(u32)term;
}

static void body(void *graph,void *gfx,void *list,void *positions,void *table,u32 variant) {
    const Scenery *c=af_v3_scenery_config+variant;
    u8 *owner=scene_owner(c);
    if (!owner) return;
    u8 *bank=owner+c->bank_offset;
    if (((u32 *)bank)[READY]!=0x53434E31u) return;
    palette(bank);
#ifdef __mips__
    ((void (*)(void *,void *,void *,void *,void *))(owner+c->body_loop))(graph,gfx,list,positions,table);
#else
    af_test_scenery_body(graph,gfx,list,positions,table,variant);
#endif
}
#define BODY(n) \
void af_v3_scenery_body##n(void *a,void *b,void *c,void *d,void *e) { body(a,b,c,d,e,n); }
BODY(0) BODY(1) BODY(2) BODY(3)
static void (*const bodies[4])(void *,void *,void *,void *,void *)={
    af_v3_scenery_body0,af_v3_scenery_body1,af_v3_scenery_body2,af_v3_scenery_body3};

/* Validate the entire fixup graph before writing any pointer or native row. */
int af_v3_scenery_relocate(u8 *owner,u32 variant) {
    if (!owner || variant>=4u) return 0;
    const Scenery *c=af_v3_scenery_config+variant;
    u8 *bank=owner+c->bank_offset;u32 *h=(u32 *)bank;
    int multi=h[VERSION]==2u;
#ifndef AF_V3_SCENERY_FAMILIES
    if (multi) return 0;
#endif
    if (h[MAGIC]!=0x41465343u || (h[VERSION]!=1u && !multi) || h[BYTES]!=c->bytes || h[READY]
            || (!multi && (h[ROW_N]!=10u || h[TYPE_N]!=14u))
            || (multi && !((h[ROW_N]==31u+(variant==2u) && h[TYPE_N]==41u) ||
                          (h[ROW_N]==21u+(variant==2u) && h[TYPE_N]==27u)))
            || c->first_index>=c->table_count
            || h[ROW_N]>c->table_count-c->first_index
            || !span(h[ROWS],h[ROW_N],8,c->bytes) || !span(h[TYPES],h[TYPE_N],16,c->bytes)
            || !span(h[TRAMPOLINE],1,16,c->bytes)) return 0;
    if (multi) {
        if (h[PALETTE_N]!=(h[TYPE_N]==41u?3u:2u) ||
            !span(h[PALETTES],h[PALETTE_N],16,c->bytes) ||
            !span(h[SELECTIONS],h[TYPE_N],4,c->bytes) ||
            (variant==2u ? h[LIGHT_LOOP]!=0x7D58u || h[LIGHT_LOOP]+556u>c->bank_offset : h[LIGHT_LOOP]!=0u)) return 0;
    }
    u32 seen_slots=0;
    for (u32 i=0;i<(multi?h[PALETTE_N]:1u);i++) {
        const u32 *r=(const u32 *)(bank+h[PALETTES]+i*16u);
        u32 data=multi?r[0]:h[PALETTES],active=multi?r[1]:h[ACTIVE],terms=multi?r[2]:h[TERMS];
        if (!span(data,14,32,c->bytes) || !span(active,1,32,c->bytes) ||
            !span(terms,18,1,c->bytes) || (multi &&
                (r[3]<6u || r[3]>8u || (seen_slots&(1u<<r[3]))))) return 0;
        if (multi) seen_slots|=1u<<r[3];
        for (u32 j=0;j<18u;j++) if (bank[terms+j]>=14u) return 0;
    }
    if (multi && seen_slots!=(h[TYPE_N]==41u?0x1C0u:0xC0u)) return 0;
    for (u32 k=CPU;k<=CALLBACK;k+=2u) {
        u32 stride=k==CALLBACK?8u:4u;
        if (!span(h[k],h[k+1],stride,c->bytes)) return 0;
        const u32 *fix=(const u32 *)(bank+h[k]);u32 last=0;
        for (u32 i=0;i<h[k+1];i++) {
            u32 at=fix[i*(stride/4u)];
            if (!span(at,1,4,c->bytes) || at<=last) return 0;
            last=at;
            if (k==CALLBACK) {
                u32 kind=fix[i*2u+1u];
                if (kind>(multi?2u:1u) || (kind==2u && !h[LIGHT_LOOP]) || *(u32 *)(bank+at)) return 0;
            }
            else if (!span(*(u32 *)(bank+at),1,1,c->bytes)) return 0;
        }
    }
    for (u32 i=0;i<h[TYPE_N];i++) {
        const u32 *row=(const u32 *)(bank+h[TYPES]+16u*i);
        if (row[0]>65535u || row[1]>=h[ROW_N]
                || (i && row[0]<=row[-4])) return 0;
        if (multi) {
            u32 selected=((const u32 *)(bank+h[SELECTIONS]))[i];
            if (selected!=0x223Bu && selected!=0x2807u && selected!=0x290Au) return 0;
        }
    }
    for (u32 k=CPU;k<=GPU;k+=2u) {
        const u32 *fix=(const u32 *)(bank+h[k]);
        u32 base=(u32)(uptr)bank;
        if (k==GPU) base&=0x1FFFFFFFu;
        for (u32 i=0;i<h[k+1];i++) *(u32 *)(bank+fix[i])+=base;
    }
    const u32 *callbacks=(const u32 *)(bank+h[CALLBACK]);
    for (u32 i=0;i<h[CALLBACK_N];i++)
        *(u32 *)(bank+callbacks[2u*i])=callbacks[2u*i+1u]==2u ?
            (u32)(uptr)(owner+h[LIGHT_LOOP]) : callbacks[2u*i+1u] ?
            (u32)(uptr)(owner+c->shadow_loop) : (u32)(uptr)bodies[variant];
    u32 *table=(u32 *)(owner+c->table_offset+c->first_index*8u);
    const u32 *rows=(const u32 *)(bank+h[ROWS]);
    for (u32 i=0;i<h[ROW_N]*2u;i++) table[i]=rows[i];
    for (u32 i=0;i<h[TYPE_N];i++) ((u32 *)(bank+h[TYPES]+16u*i))[1]+=c->first_index;
    u32 *trampoline=(u32 *)(bank+h[TRAMPOLINE]);
    trampoline[0]=0x27BDFFE0u;trampoline[1]=0xAFB00018u;
    trampoline[2]=0x08000000u|(((u32)(uptr)owner+c->classify+8u)>>2&0x03FFFFFFu);
    trampoline[3]=0;
    h[TERM]=~0u;palette(bank);h[READY]=0x53434E31u;
    af_scenery_writeback(bank,c->bytes);af_scenery_invalidate(trampoline,16);
    return 1;
}

static int load_bank(u8 *dest,const Scenery *c) {
#ifdef AF_V3_SCENERY_FAMILIES
    if(c->vrom&0x40000000u) {
        /* Bit 30 is the scenery-only page-table tag. Native physical DMA uses
           bit 31; never pass the page-table tag into that reader. */
        u32 pages[36];
        if((c->vrom&0xBC00000Fu)!=0x80000000u ||
           (c->vrom&0x3FFFFFFFu)>0x4000000u-sizeof(pages) ||
           af_v3_resource_read(pages,c->vrom&~0x40000000u,sizeof(pages),af_scenery_dma) ||
           pages[0]!=0x41465047u || pages[1]!=c->bytes || pages[2]!=4096u ||
           !pages[3] || pages[3]>32u || pages[3]!=(c->bytes+4095u)/4096u)return 0;
        /* Validate every source extent before changing the destination. */
        for(u32 i=0;i<pages[3];i++) {
            u32 n=c->bytes-i*4096u;if(n>4096u)n=4096u;
            if((pages[i+4]&15u) || pages[i+4]<0x100000u || pages[i+4]>0x4000000u-n)return 0;
        }
        for(u32 i=0;i<pages[3];i++) {
            u32 n=c->bytes-i*4096u;if(n>4096u)n=4096u;
            if(af_v3_resource_read(dest+i*4096u,pages[i+4]|0x80000000u,n,af_scenery_dma))return 0;
        }
        return 1;
    }
#endif
    return !af_scenery_dma(dest,c->vrom,c->bytes);
}

void af_v3_scenery_construct(void *actor,void *game,u32 variant) {
    if (variant>=4u) return;
    const Scenery *c=af_v3_scenery_config+variant;
    u8 *owner=af_v3_ground_prepare(variant);
    if (!owner || !load_bank(owner+c->bank_offset,c)
            || af_scenery_crc(owner+c->bank_offset,c->bytes)!=c->crc
            || !af_v3_scenery_relocate(owner,variant)) {
        af_scenery_fault("V3 scenery", "Invalid scene resource");return;
    }
#ifdef __mips__
    ((void (*)(void *,void *))(owner+c->constructor))(actor,game);
#else
    af_test_scenery_constructor(actor,game,variant);
#endif
}

static void classify(u32 item,void *result,void *collision,void *types,u32 variant) {
    const Scenery *c=af_v3_scenery_config+variant;
    u8 *owner=scene_owner(c);
    if (!owner) { af_scenery_fault("V3 scenery","Missing scene owner");return; }
    u8 *bank=owner+c->bank_offset;const u32 *h=(const u32 *)bank;
    if (h[READY]!=0x53434E31u) { af_scenery_fault("V3 scenery","Uninitialized scene");return; }
    item&=65535u;
    for (u32 i=0;i<h[TYPE_N];i++) {
        const u8 *row=bank+h[TYPES]+16u*i;
        if (*(const u32 *)row!=item) continue;
        int selected;
#ifdef AF_V3_SCENERY_FAMILIES
        u32 selector=h[VERSION]==2u ? ((const u32 *)(bank+h[SELECTIONS]))[i] : 0x223Bu;
        selected=selector==0x223Bu ? af_v3_player_selected_equipment(selector)>=0 : af_carried_category(selector)>0;
#else
        selected=af_v3_player_selected_equipment(0x223Bu)>=0;
#endif
        if (selected) {
            for (u32 j=0;j<12u;j++) ((u8 *)result)[j]=row[4u+j];
            return;
        }
        /* Imported scenery cannot index a shorter native foreground table. */
        item=0;break;
    }
#ifdef __mips__
    ((void (*)(u32,void *,void *,void *))(bank+h[TRAMPOLINE]))(item,result,collision,types);
#else
    af_test_scenery_classify(item,result,collision,types,variant);
#endif
}
#define TYPE(n) \
void af_v3_scenery_type##n(u32 a,void *b,void *c,void *d) { classify(a,b,c,d,n); }
TYPE(0) TYPE(1) TYPE(2) TYPE(3)
