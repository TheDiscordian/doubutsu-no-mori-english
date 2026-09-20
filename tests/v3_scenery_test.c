#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/scenery.c"
#define ROW(s) {s,16,8192,2048,0x2200000,1234,128,108,65,32,48,64}
const Scenery af_v3_scenery_config[4]={ROW(0),ROW(1),ROW(2),ROW(3)};
static u32 owners[4][2600], source[512], calls, fallbacks, drawers, faults, dma_fail, bad_crc;
static int selected, term;
u8 *af_test_scenery_owners[4];
u8 *af_v3_ground_prepare(u32 variant) { return af_test_scenery_owners[variant]; }
int af_v3_player_selected_equipment(u32 item) { assert(item==0x223B);return selected?90:-1; }
int af_scenery_dma(void *dest,u32 vrom,u32 size) {
    assert(vrom==0x2200000 && size==sizeof(source));
    if (dma_fail) return -1;
    memcpy(dest,source,size);return 0;
}
u32 af_scenery_crc(const void *p,u32 n) { assert(p && n==2048);return bad_crc?0:1234; }
void af_scenery_writeback(void *p,u32 n) { assert(p && n); }
void af_scenery_invalidate(void *p,u32 n) { assert(p && n==16); }
int af_scenery_term(void) { return term; }
void af_scenery_fault(const char *a,const char *b) { assert(a && b);faults++; }
void af_test_scenery_constructor(void *a,void *b,u32 v) { assert(a==(void *)1 && b==(void *)2 && v<4);calls++; }
void af_test_scenery_body(void *a,void *b,void *c,void *d,void *e,u32 v) {
    assert(a==(void *)1 && b==(void *)2 && c==(void *)3 && d==(void *)4 && e==(void *)5 && v<4);drawers++;
}
static u32 expected_fallback;
void af_test_scenery_classify(u32 item,void *a,void *b,void *c,u32 v) {
    assert(item==expected_fallback && a && b==(void *)3 && c==(void *)4 && v<4);fallbacks++;
}
static void fixture(void) {
    memset(source,0,sizeof(source));
    u32 h[]={0x41465343,1,sizeof(source),0,1200,1,1204,1,1208,1,128,10,208,14,432,880,912,944};
    memcpy(source,h,sizeof(h));
    source[1200/4]=128;source[128/4]=1024; /* CPU descriptor pointer */
    source[1204/4]=1024;source[1024/4]=1040; /* physical graphics pointer */
    source[1208/4]=1048;source[1212/4]=1; /* native shadow callback */
    for (u32 i=0;i<14;i++) { source[208/4+4*i]=0x863+i;source[208/4+4*i+1]=i%10; }
    for (u32 i=0;i<448;i++) ((u8 *)source)[432+i]=(u8)i;
    for (u32 i=0;i<18;i++) ((u8 *)source)[912+i]=i%14;
}
int main(void) {
    fixture();
    assert(!af_v3_scenery_relocate(0,0));assert(!af_v3_scenery_relocate((u8 *)owners[0],4));
    for (u32 v=0;v<4;v++) {
        memset(owners[v],0xA5,sizeof(owners[v]));
        af_test_scenery_owners[v]=(u8 *)owners[v];
        af_v3_scenery_construct((void *)1,(void *)2,v);assert(calls==v+1 && !faults);
        u8 *bank=(u8 *)owners[v]+8192;u32 *h=(u32 *)bank;
        assert(h[READY]==0x53434E31 && !af_v3_scenery_relocate((u8 *)owners[v],v));
        assert(*(u32 *)(bank+128)==(u32)(uptr)bank+1024);
        assert(*(u32 *)(bank+1024)==((u32)(uptr)bank&0x1FFFFFFF)+1040);
        assert(*(u32 *)(bank+1048)==(u32)(uptr)owners[v]+48);
        assert(owners[v][(128+65*8)/4]==(u32)(uptr)bank+1024);
        assert(owners[v][(128+65*8)/4-1]==0xA5A5A5A5);
        assert(owners[v][(128+75*8)/4]==0xA5A5A5A5);
        assert(owners[v][0]==0xA5A5A5A5 && owners[v][2560]==0xA5A5A5A5);
        assert(!memcmp(bank+880,bank+432,32));
        for (term=0;term<18;term++) {
            body((void *)1,(void *)2,(void *)3,(void *)4,(void *)5,v);
            assert(!memcmp(bank+880,bank+432+32*(term%14),32));
        }
        term=-1;body((void *)1,(void *)2,(void *)3,(void *)4,(void *)5,v);
        assert(!memcmp(bank+880,bank+432,32));term=0;
        u32 result[5]={0xABABABAB,0,0,0,0xCDCDCDCD};selected=1;
        for (u32 i=0;i<14;i++) {
            classify(0x863+i,result+1,(void *)3,(void *)4,v);
            assert(result[1]==65+i%10 && result[0]==0xABABABAB && result[4]==0xCDCDCDCD);
        }
        selected=0;expected_fallback=0;classify(0x863,result+1,(void *)3,(void *)4,v);
        expected_fallback=0x2200;classify(0x2200,result+1,(void *)3,(void *)4,v);
    }
    assert(drawers==76 && fallbacks==8);
    /* Every malformed dependency fails before relocating any pointer. */
    const u32 mutations[][2]={{MAGIC,0},{READY,1},{CPU,2048},{CPU_N,~0u},{ROWS,2040},
        {PALETTES,1900},{TYPE_N,15},{TRAMPOLINE,2040},{1200/4,3},{1204/4,2048},
        {1212/4,2},{128/4,2048},{208/4+1,10},{912/4,0xFFFFFFFF}};
    for (u32 i=0;i<sizeof(mutations)/sizeof(*mutations);i++) {
        u8 *bank=(u8 *)owners[0]+8192;
        memcpy(bank,source,sizeof(source));((u32 *)bank)[mutations[i][0]]=mutations[i][1];
        u8 before[2048];memcpy(before,bank,sizeof(before));
        assert(!af_v3_scenery_relocate((u8 *)owners[0],0));assert(!memcmp(before,bank,sizeof(before)));
    }
    dma_fail=1;af_v3_scenery_construct((void *)1,(void *)2,0);assert(faults==1 && calls==4);
    dma_fail=0;bad_crc=1;af_v3_scenery_construct((void *)1,(void *)2,0);assert(faults==2 && calls==4);
    bad_crc=0;af_v3_scenery_construct((void *)1,(void *)2,0);assert(faults==2 && calls==5);
    puts("Scenery relocation, palettes, four owners, selection, fallbacks, and failure bounds pass");
}
