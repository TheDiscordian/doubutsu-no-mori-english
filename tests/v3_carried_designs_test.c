#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/carried_designs.h"
static AFDesign templates[8];
static AFDesigns live,before,scratch;
static AFDesignDraft draft;
static AFDesignFillWork fill;
static int calls,allow;
static int capacity(void *context,const AFDesigns *candidate) {
    assert(context==&calls && af_design_valid(candidate));calls++;
    assert(!memcmp(&live,&before,sizeof(live)));return allow;
}
int main(int argc,char **argv) {
    assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);
    assert(fread(templates,1,sizeof(templates),f)==sizeof(templates));assert(fgetc(f)==EOF);fclose(f);
    assert(af_design_reset(&live,templates)==1 && af_design_valid(&live));
    for(unsigned p=0;p<4;p++)for(unsigned i=0;i<8;i++) {
        assert(live.order[p][i]==i);
        assert(!memcmp(&live.patterns[p][i],templates+i,sizeof(AFDesign)));
        assert((__UINTPTR_TYPE__)live.patterns[p][i].texture%32==0);
    }
    before=live;
    assert(af_design_reorder(&live,2,0,7)==1);
    assert(af_design_physical(&live,2,0)==&live.patterns[2][0]);
    assert(af_design_selected(&live,2,0)==&live.patterns[2][7]);
    assert(!memcmp(before.patterns,live.patterns,sizeof(live.patterns)));
    assert(af_design_begin(&draft,&live,2,0)==1 && draft.index==7);
    assert(af_design_begin(&draft,&live,4,0)==AF_DESIGN_ARGUMENT);
    assert(af_design_begin(&draft,&live,2,8)==AF_DESIGN_ARGUMENT);
    assert(!af_design_physical(&live,4,0));assert(!af_design_selected(&live,0,8));
    for(int y=0;y<32;y++)for(int x=0;x<32;x++) {
        unsigned colour=(x*3+y*5)&15;
        assert(af_design_paint(&draft.edited,x,y,colour)>=0);
        assert(af_design_pixel(&draft.edited,x,y)==(int)colour);
    }
    for(int y=0;y<32;y++)for(int x=0;x<32;x++)assert(af_design_pixel(&draft.edited,x,y)==((x*3+y*5)&15));
    AFDesign pattern=draft.edited;
    assert(af_design_paint(&draft.edited,-1,0,3)==AF_DESIGN_ARGUMENT);
    assert(af_design_paint(&draft.edited,0,32,3)==AF_DESIGN_ARGUMENT);
    assert(af_design_paint(&draft.edited,31,31,16)==AF_DESIGN_ARGUMENT);
    assert(!memcmp(&pattern,&draft.edited,sizeof(pattern)));
    for(unsigned pal=0;pal<16;pal++)assert(af_design_palette(&draft.edited,pal)>=0);
    assert(af_design_palette(&draft.edited,16)==AF_DESIGN_ARGUMENT);
    assert(af_design_name(&draft.edited,(const unsigned char *)"custom design",13)==1);
    assert(!memcmp(draft.edited.name,"custom design   ",16));
    const unsigned char bad[2]={0x7F,0};
    assert(af_design_name(&draft.edited,bad,2)==AF_DESIGN_ARGUMENT);
    memset(draft.edited.texture,0,sizeof(draft.edited.texture));
    assert(af_design_fill(&draft.edited,0,0,15,&fill)==1);
    for(unsigned i=0;i<512;i++)assert(draft.edited.texture[i]==255);
    assert(af_design_fill(&draft.edited,31,31,15,&fill)==0);
    for(int y=0;y<32;y++)af_design_paint(&draft.edited,16,y,3);
    assert(af_design_fill(&draft.edited,0,31,4,&fill)==1);
    for(int y=0;y<32;y++)for(int x=0;x<32;x++)assert(af_design_pixel(&draft.edited,x,y)==(x<16?4:x==16?3:15));
    pattern=draft.edited;
    assert(af_design_fill(&draft.edited,-1,0,0,&fill)==AF_DESIGN_ARGUMENT);
    assert(af_design_fill(&draft.edited,0,0,16,&fill)==AF_DESIGN_ARGUMENT);
    assert(!memcmp(&pattern,&draft.edited,sizeof(pattern)));
    before=live;allow=0;
    assert(af_design_commit(&live,&draft,&scratch,capacity,&calls)==AF_DESIGN_CAPACITY && calls==1);
    assert(!memcmp(&live,&before,sizeof(live)));
    assert(af_design_commit(&live,&draft,&live,capacity,&calls)==AF_DESIGN_ARGUMENT);
    assert(af_design_commit(&live,&draft,&scratch,0,&calls)==AF_DESIGN_ARGUMENT);
    allow=1;assert(af_design_commit(&live,&draft,&scratch,capacity,&calls)==1 && calls==2);
    assert(!memcmp(&live.patterns[2][7],&draft.edited,sizeof(AFDesign)));
    before.patterns[2][7]=draft.edited;assert(!memcmp(&live,&before,sizeof(live)));
    assert(af_design_commit(&live,&draft,&scratch,capacity,&calls)==AF_DESIGN_CHANGED && calls==2);
    assert(af_design_begin(&draft,&live,2,0)==1);
    assert(af_design_commit(&live,&draft,&scratch,capacity,&calls)==0 && calls==2);
    before=live;assert(af_design_reset_player(&live,2,templates)==1);
    memcpy(before.patterns[2],templates,sizeof(templates));
    for(unsigned i=0;i<8;i++)before.order[2][i]=i;
    assert(!memcmp(&live,&before,sizeof(live)));
    live.order[0][1]=0;assert(!af_design_valid(&live));live=before;
    live.patterns[3][7].palette=16;assert(!af_design_valid(&live));live=before;
    live.patterns[3][7].reserved[13]=1;assert(!af_design_valid(&live));live=before;
    templates[7].palette=16;assert(af_design_reset(&live,templates)==AF_DESIGN_ARGUMENT);
    assert(!memcmp(&live,&before,sizeof(live)));
    puts("All 32 physical designs retain stable ordering, full pixels/palettes, bounded fill, and atomic capacity-checked edits");
    return 0;
}
