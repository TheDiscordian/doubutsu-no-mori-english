#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/diary.h"
#include "../overlays/v3/save_compressed.h"
typedef unsigned char u8;
typedef unsigned int u32;
static AFDiary diary,work,before;
static AFDiaryDraft draft,old_draft;
static u8 canonical[65536],bank[65536],saved[65536],console[6528],widths[256];
static u8 decoded[AF_CZ_DIARY_RAW],bad[65536];
static u32 hash[AF_CZ_HASH_WORDS],calls;
static u32 rng=391;
static u8 random_byte(void) {rng=rng*1664525u+1013904223u;return rng>>24;}
static int capacity(void *ctx,const AFDiary *candidate) {
    assert(ctx==&calls);calls++;
    return af_v3_save_measure_diary(canonical,sizeof(canonical),console,sizeof(console),candidate,hash,sizeof(hash));
}
static int full(void *ctx,const AFDiary *candidate) {(void)ctx;assert(af_diary_valid(candidate));return -1;}
static void read_file(const char *path,u8 *p,size_t n) {
    FILE *f=fopen(path,"rb");assert(f);assert(fread(p,1,n,f)==n);assert(fgetc(f)==EOF);assert(!fclose(f));
}
static void write_file(const char *path,const u8 *p,size_t n) {
    FILE *f=fopen(path,"wb");assert(f);assert(fwrite(p,1,n,f)==n);assert(!fclose(f));
}
static void edit(void) {
    AFDiaryLayout layout;memset(widths,6,sizeof(widths));widths['i']=2;widths['I']=3;widths['W']=10;
    af_diary_reset(&diary);assert(af_diary_valid(&diary));assert(AF_DIARY_BYTES==48048);
    for(u32 p=0;p<4;p++)for(u32 m=0;m<12;m++) {
        const u8 *page=af_diary_page(&diary,p,p,m);assert(page);
        for(u32 i=0;i<992;i++)assert(page[i]==32);
        assert(af_diary_begin(&draft,&diary,p,p,m,widths)==1);
        assert(draft.length==0 && draft.cursor==0);
        assert(af_diary_command(&draft,8,'A'+p,widths)==1);
        assert(af_diary_command(&draft,8,'a'+m,widths)==1);
        assert(af_diary_command(&draft,8,0xCD,widths)==1);
        assert(af_diary_command(&draft,8,'W',widths)==1);
        before=diary;old_draft=draft;
        assert(af_diary_commit(&diary,&draft,&work,widths,full,0)==AF_DIARY_CAPACITY);
        assert(!memcmp(&diary,&before,sizeof(diary)) && !memcmp(&draft,&old_draft,sizeof(draft)));
        assert(af_diary_commit(&diary,&draft,&work,widths,capacity,&calls)==1);
        assert(page[0]=='A'+p && page[1]=='a'+m && page[2]==0xCD && page[3]=='W');
    }
    assert(calls==48);
    assert(af_diary_lock(&diary,0,1,1)==AF_DIARY_READONLY);
    assert(af_diary_lock(&diary,1,1,1)==1);
    assert(!af_diary_page(&diary,0,1,0));assert(af_diary_page(&diary,1,1,0));
    assert(af_diary_begin(&draft,&diary,0,1,0,widths)==AF_DIARY_LOCKED);
    assert(af_diary_lock(&diary,1,1,0)==1);
    assert(af_diary_begin(&draft,&diary,0,1,0,widths)==1 && draft.readonly);
    old_draft=draft;
    assert(af_diary_command(&draft,8,'x',widths)==AF_DIARY_READONLY);
    assert(af_diary_commit(&diary,&draft,&work,widths,capacity,&calls)==AF_DIARY_READONLY);
    assert(!memcmp(&draft,&old_draft,sizeof(draft)));
    assert(!af_diary_page(&diary,4,0,0) && !af_diary_page(&diary,0,0,12));
    assert(af_diary_begin(&draft,&diary,0,0,0,widths)==1);
    memset(draft.text,'x',992);draft.length=draft.cursor=992;
    assert(af_diary_layout(draft.text,992,992,widths,&layout)==1 && layout.rows==31);
    old_draft=draft;assert(af_diary_command(&draft,8,'x',widths)==AF_DIARY_FULL);
    assert(!memcmp(&draft,&old_draft,sizeof(draft)));
    assert(af_diary_command(&draft,6,0,widths)==1 && draft.length==991);
    assert(af_diary_command(&draft,4,0,widths)==1 && draft.length==992 && draft.text[991]==32);
    memset(draft.text,32,992);memset(draft.text,0xCD,30);draft.length=draft.cursor=30;draft.scroll=0;
    assert(af_diary_layout(draft.text,30,30,widths,&layout)==1 && layout.rows==31);
    old_draft=draft;assert(af_diary_command(&draft,8,0xCD,widths)==AF_DIARY_FULL);
    assert(!memcmp(&draft,&old_draft,sizeof(draft)));
    assert(af_diary_scroll(&draft,10,widths)==1 && draft.scroll==10);
    assert(af_diary_scroll(&draft,31,widths)==1 && draft.scroll==24);
    assert(af_diary_scroll(&draft,-31,widths)==1 && !draft.scroll);
    memset(draft.text,32,992);memcpy(draft.text,"Wi\315iW",5);draft.length=5;draft.cursor=1;
    assert(af_diary_command(&draft,2,0,widths)==1 && draft.cursor==5);
    assert(af_diary_command(&draft,3,0,widths)==1 && draft.cursor==2);
    assert(af_diary_command(&draft,7,0x80,widths)==AF_DIARY_ARGUMENT);
    before=diary;assert(af_diary_player_clear(&diary,2)==1);
    for(u32 p=0;p<4;p++)if(p!=2)assert(!memcmp(diary.bytes+16+p*AF_DIARY_PLAYER,
        before.bytes+16+p*AF_DIARY_PLAYER,AF_DIARY_PLAYER));
    assert(af_diary_begin(&draft,&diary,0,0,0,widths)==1);
    assert(af_diary_player_clear(&diary,0)==1);
    assert(af_diary_commit(&diary,&draft,&work,widths,capacity,&calls)==AF_DIARY_CHANGED);
    assert(af_diary_commit(&diary,&draft,&diary,widths,capacity,&calls)==AF_DIARY_ARGUMENT);
}
int main(int argc,char **argv) {
    assert(argc==4);read_file(argv[1],canonical,sizeof(canonical));
    for(u32 i=0;i<sizeof(console);i++)console[i]=random_byte();
    edit();af_diary_reset(&diary);
    /* All 48 pages are full; distinct monthly prose is generated from a fixed
     * vocabulary. This is a capacity fixture, not a guarantee for all writing. */
    const char *words[]={"river ","fish ","today ","friend ","home ","music ","green ","forest ",
        "village ","letter ","shop ","flower ","rain ","fun ","garden ","walk ","hello ","night "};
    for(u32 p=0;p<4;p++)for(u32 m=0;m<12;m++) {
        u8 *page=diary.bytes+16+p*AF_DIARY_PLAYER+104+m*992;
        for(u32 i=0;i<992;) {const char *w=words[random_byte()%18];while(*w && i<992)page[i++]=(u8)*w++;}
    }
    diary.bytes[16+98]=1;
    diary.bytes[16+100]=7;diary.bytes[16+101]=234;diary.bytes[16+102]=9;
    diary.bytes[16+3]=1;diary.bytes[16+48+2]=8;diary.bytes[16+97]=0x7F;
    int n=capacity(&calls,&diary);assert(n>0);
    assert(af_v3_save_compress_diary(bank,sizeof(bank),canonical,sizeof(canonical),console,sizeof(console),
        &diary,hash,sizeof(hash))==n);
    memcpy(saved,bank,sizeof(bank));
    assert(bank[0xF985]==11);
    assert(af_v3_save_expand(bank,sizeof(bank),decoded,AF_CZ_RAW)==AF_CZ_FORMAT);
    assert(af_v3_save_expand_diary(bank,sizeof(bank),decoded,sizeof(decoded))==0);
    assert(!memcmp(decoded,canonical,65536) && !memcmp(decoded+65536,console,6528));
    assert(!memcmp(decoded+AF_CZ_RAW,&diary,sizeof(diary)));
    write_file(argv[2],bank,sizeof(bank));write_file(argv[3],decoded,sizeof(decoded));
    printf("Full 48-page vocabulary fixture: %d / 63850 stream bytes; %u diary bytes retained.\n",n,AF_DIARY_BYTES);
    assert(af_v3_save_compress(bank,sizeof(bank),canonical,sizeof(canonical),console,sizeof(console),hash,sizeof(hash))>0);
    assert(bank[0xF985]==9);
    memset(decoded,0xA5,sizeof(decoded));assert(af_v3_save_expand_diary(bank,sizeof(bank),decoded,sizeof(decoded))==0);
    af_diary_reset(&before);assert(!memcmp(decoded+AF_CZ_RAW,&before,sizeof(before)));
    assert(!memcmp(decoded,canonical,65536) && !memcmp(decoded+65536,console,6528));
    for(u32 i=0;i<sizeof(bad);i+=211) {
        memcpy(bad,saved,sizeof(bad));bad[i]^=0x40;
        assert(af_v3_save_expand_diary(bad,sizeof(bad),decoded,sizeof(decoded))<0);
    }
    assert(af_v3_save_expand_diary(saved,sizeof(saved),saved,sizeof(decoded))==AF_CZ_ARGUMENT);
    assert(af_v3_save_expand_diary(saved,sizeof(saved),decoded,sizeof(decoded)-1)==AF_CZ_ARGUMENT);
    before=diary;before.bytes[7]=1;memcpy(bank,saved,sizeof(bank));
    assert(af_v3_save_compress_diary(bank,sizeof(bank),canonical,sizeof(canonical),console,sizeof(console),
        &before,hash,sizeof(hash))==AF_CZ_FORMAT);assert(!memcmp(bank,saved,sizeof(bank)));
    /* Valid metadata with incompressible page data must reject atomically. */
    for(u32 p=0;p<4;p++)for(u32 i=0;i<12*992;i++)diary.bytes[16+p*AF_DIARY_PLAYER+104+i]=random_byte();
    assert(af_v3_save_compress_diary(bank,sizeof(bank),canonical,sizeof(canonical),console,sizeof(console),
        &diary,hash,sizeof(hash))==AF_CZ_SPACE);assert(!memcmp(bank,saved,sizeof(bank)));
    assert(af_v3_save_measure_diary(canonical,sizeof(canonical),console,sizeof(console),&diary,
        hash,sizeof(hash))==AF_CZ_SPACE);
    puts("Diary edit/access/commit, complete save round-trip, migration, and rejection checks pass.");
    return 0;
}
