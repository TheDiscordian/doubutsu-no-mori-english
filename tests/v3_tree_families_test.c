#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_SCENERY_FAMILIES
#include "../overlays/v3/scenery.c"
#define CONFIG(s) {s,16,32768,4096,0x2200000,1234,128,108,65,32,48,64}
const Scenery af_v3_scenery_config[4]={CONFIG(0),CONFIG(1),CONFIG(2),CONFIG(3)};
static u32 owners[4][9232],source[1024],calls,faults,fallbacks,drawers;
static u32 selected;
static u32 recipe[36],page_reads;
static int term;
u8 *af_test_scenery_owners[4];
u8 *af_v3_ground_prepare(u32 v) { return af_test_scenery_owners[v]; }
int af_v3_player_selected_equipment(u32 item) { assert(item==0x223B);return selected&1u?1:-1; }
int af_carried_category(u32 item) {
    assert(item==0x2807u || item==0x290Au);
    return selected&(item==0x2807u?2u:4u) ? 50 : 0;
}
int af_scenery_dma(void *dest,u32 vrom,u32 n) {
    if(vrom==0x80300000u) { assert(n==sizeof(recipe));memcpy(dest,recipe,n);return 0; }
    if(vrom==0x80100000u) { assert(n<=sizeof(source));memcpy(dest,source,n);page_reads++;return 0; }
    assert(vrom==0x2200000 && n==4096);memcpy(dest,source,n);return 0;
}
u32 af_scenery_crc(const void *p,u32 n) { assert(p && n==4096);return 1234; }
void af_scenery_writeback(void *p,u32 n) { assert(p && n); }
void af_scenery_invalidate(void *p,u32 n) { assert(p && n==16); }
int af_scenery_term(void) { return term; }
void af_scenery_fault(const char *a,const char *b) { assert(a && b);faults++; }
void af_test_scenery_constructor(void *a,void *b,u32 v) { assert(a && b && v<4);calls++; }
void af_test_scenery_body(void *a,void *b,void *c,void *d,void *e,u32 v) {
    assert(a && b && c && d && e && v<4);drawers++;
}
void af_test_scenery_classify(u32 item,void *a,void *b,void *c,u32 v) {
    assert(!item && a && b && c && v<4);fallbacks++;
}
static void fixture(u32 variant) {
    memset(source,0,sizeof(source));
    u32 h[]={0x41465343,2,4096,0,2800,1,2804,1,2808,2,128,31+(variant==2),
        384,41,1088,0,0,2720,0,3,1120+3*16,variant==2?0x7D58:0};
    memcpy(source,h,sizeof(h));
    source[2800/4]=128;source[128/4]=2740;
    source[2804/4]=2740;source[2740/4]=2752;
    source[2808/4]=2760;source[2812/4]=1;
    source[2816/4]=2764;source[2820/4]=variant==2?2:0;
    for(u32 i=0;i<h[ROW_N];i++)source[128/4+i*2+1]=(i&1)?0x10000:0;
    for(u32 i=0;i<41;i++) {
        source[384/4+i*4]=0x800+i;
        source[384/4+i*4+1]=i%h[ROW_N];
        source[h[SELECTIONS]/4+i]=(u32[]){0x223B,0x2807,0x290A}[i%3];
    }
    for(u32 i=0;i<3;i++) {
        u32 data=1344+i*448,active=3060+i*32,terms=3000+i*20;
        u32 row[]={data,active,terms,6+i};memcpy(source+1088/4+i*4,row,sizeof(row));
        for(u32 j=0;j<448;j++)((u8 *)source)[data+j]=(u8)(j+i*29);
        for(u32 j=0;j<18;j++)((u8 *)source)[terms+j]=(j+i)%14;
    }
}
int main(void) {
    for(u32 v=0;v<4;v++) {
        fixture(v);memset(owners[v],0xA5,sizeof(owners[v]));
        af_test_scenery_owners[v]=(u8 *)owners[v];
        af_v3_scenery_construct((void *)1,(void *)2,v);assert(!faults && calls==v+1);
        u8 *bank=(u8 *)owners[v]+32768;u32 *h=(u32 *)bank;
        assert(h[READY]==0x53434E31 && !af_v3_scenery_relocate((u8 *)owners[v],v));
        assert(*(u32 *)(bank+2764)==(u32)(uptr)(v==2?(void *)((u8 *)owners[v]+0x7D58):(void *)bodies[v]));
        for(u32 i=0;i<h[ROW_N];i++)assert(owners[v][(128+65*8)/4+i*2+1]==((i&1)?0x10000u:0));
        for(term=0;term<18;term++) {
            body((void *)1,(void *)2,(void *)3,(void *)4,(void *)5,v);
            for(u32 i=0;i<3;i++) {
                const u32 *r=(const u32 *)(bank+h[PALETTES]+i*16);
                assert(!memcmp(bank+r[1],bank+r[0]+32*bank[r[2]+term],32));
            }
        }
        term=0;
        for(selected=0;selected<8;selected++)for(u32 i=0;i<41;i++) {
            u32 out[]={0xABABABAB,0,0,0,0xCDCDCDCD};u32 before=fallbacks;
            classify(0x800+i,out+1,(void *)3,(void *)4,v);
            if(selected&(1u<<(i%3)))assert(out[1]==65+i%h[ROW_N] && fallbacks==before);
            else assert(fallbacks==before+1 && !out[1]);
            assert(out[0]==0xABABABAB && out[4]==0xCDCDCDCD);
        }
        assert(owners[v][0]==0xA5A5A5A5 && owners[v][9216]==0xA5A5A5A5);
    }
    fixture(2);
    const u32 mutations[][2]={{ROW_N,33},{TYPE_N,42},{PALETTE_N,4},{PALETTES,4092},
        {SELECTIONS,4092},{LIGHT_LOOP,0},{LIGHT_LOOP,0x7D54},{1088/4,4000},
        {1088/4+3,9},{1088/4+7,6},{3000/4,~0u},{1168/4,0x2901},{2820/4,3}};
    for(u32 i=0;i<sizeof(mutations)/sizeof(*mutations);i++) {
        u8 *bank=(u8 *)owners[2]+32768;memcpy(bank,source,sizeof(source));
        ((u32 *)bank)[mutations[i][0]]=mutations[i][1];u8 before[4096];memcpy(before,bank,sizeof(before));
        assert(!af_v3_scenery_relocate((u8 *)owners[2],2));assert(!memcmp(before,bank,sizeof(before)));
    }
    assert(drawers==72);
    /* The installed page reader reconstructs shared pages and a partial tail.
       Invalid source ranges reject before the first destination DMA. */
    Scenery paged=af_v3_scenery_config[0];paged.vrom=0xC0300000u;paged.bytes=4112;
    u8 rebuilt[4112+16];memset(rebuilt,0xA5,sizeof(rebuilt));
    recipe[0]=0x41465047;recipe[1]=4112;recipe[2]=4096;recipe[3]=2;
    recipe[4]=recipe[5]=0x100000;
    assert(load_bank(rebuilt,&paged));assert(page_reads==2);
    assert(!memcmp(rebuilt,source,4096) && !memcmp(rebuilt+4096,source,16));
    for(u32 i=4112;i<sizeof(rebuilt);i++)assert(rebuilt[i]==0xA5);
    const u32 bad_pages[][2]={{0,0},{1,4096},{2,2048},{3,0},{3,33},{4,0x100004},
        {5,0xFFFF0},{4,0x3FFFFF0},{5,0x4000000}};
    for(u32 i=0;i<sizeof(bad_pages)/sizeof(*bad_pages);i++) {
        u32 pos=bad_pages[i][0],saved=recipe[pos];recipe[pos]=bad_pages[i][1];
        memset(rebuilt,0xA5,sizeof(rebuilt));page_reads=0;
        assert(!load_bank(rebuilt,&paged) && !page_reads);
        for(u32 j=0;j<sizeof(rebuilt);j++)assert(rebuilt[j]==0xA5);
        recipe[pos]=saved;
    }
    puts("Shared tree palettes, descriptors, native lights, independent selections, and rejection bounds pass");
}
