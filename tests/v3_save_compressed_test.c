#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/save_compressed.h"
typedef unsigned char u8;
typedef unsigned int u32;
enum { P=0xF980,CAP=P-22 };
static unsigned checks;
#define CHECK(x) do { assert(x);checks++; } while(0)
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void put(u8 *p,u32 x) {p[0]=x>>24;p[1]=x>>16;p[2]=x>>8;p[3]=x;}
static u32 sum(const u8 *p) {u32 s=0;for(u32 i=0;i<P;i+=2)s+=((u32)p[i]<<8)|p[i+1];return s&65535;}
static void balance(u8 *p) {
    u32 v=(((u32)p[18]<<8)|p[19])-sum(p);p[18]=v>>8;p[19]=v;
}
static void seal(u8 *bank) {
    u32 crc=~0u;
    for(u32 i=0;i<65536;i++) {
        crc^=(i==18 || i==19 || (i>=P+24 && i<P+28))?0:bank[i];
        for(unsigned b=0;b<8;b++)crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1)));
    }
    put(bank+P+24,~crc);balance(bank);
}
static void file_read(const char *folder,const char *name,u8 *data,size_t length) {
    char path[4096];CHECK(snprintf(path,sizeof(path),"%s/%s",folder,name)<(int)sizeof(path));
    FILE *f=fopen(path,"rb");CHECK(f!=NULL);CHECK(fread(data,1,length,f)==length);
    CHECK(fgetc(f)==EOF);CHECK(fclose(f)==0);
}
static void file_write(const char *folder,const char *name,const u8 *data) {
    char path[4096];CHECK(snprintf(path,sizeof(path),"%s/%s",folder,name)<(int)sizeof(path));
    FILE *f=fopen(path,"wb");CHECK(f!=NULL);CHECK(fwrite(data,1,65536,f)==65536);CHECK(fclose(f)==0);
}
static u8 *buffer(size_t length) {
    u8 *p=malloc(length+32);CHECK(p!=NULL);memset(p,0xA9,length+32);return p+16;
}
static void free_guarded(u8 *p,size_t length) {
    for(unsigned i=0;i<16;i++){CHECK((p-16)[i]==0xA9);CHECK(p[length+i]==0xA9);}
    free(p-16);
}
static u32 physical(u32 at) {return at+20+(at+20>=0x2F68?2:0);}
int main(int argc,char **argv) {
    CHECK(argc==2);
    u8 *raw=buffer(65536),*console=buffer(6528),*packed=buffer(65536),*out=buffer(AF_CZ_RAW);
    u8 *saved=buffer(65536),*bad=buffer(65536),*raw_before=buffer(65536),*console_before=buffer(6528);
    u32 *hash=(u32 *)buffer(AF_CZ_WORK_BYTES);
    file_read(argv[1],"console.bin",console,6528);memcpy(console_before,console,6528);
    const char *names[]={"zero.bin","town.bin","dense.bin","incompressible.bin"};
    const char *results[]={"zero.packed","town.packed","dense.packed"};
    for(unsigned which=0;which<4;which++) {
        file_read(argv[1],names[which],raw,65536);memcpy(raw_before,raw,65536);
        memset(packed,0x7B,65536);memcpy(saved,packed,65536);
        int n=af_v3_save_compress(packed,65536,raw,65536,console,6528,hash,AF_CZ_WORK_BYTES);
        CHECK(memcmp(raw,raw_before,65536)==0 && memcmp(console,console_before,6528)==0);
        if(which==3) {
            CHECK(n==AF_CZ_SPACE);CHECK(memcmp(packed,saved,65536)==0);
            puts("incompressible: rejected before output modification");continue;
        }
        CHECK(n>0 && n<=CAP);CHECK(sum(packed)==0);
        CHECK(af_v3_save_expand(packed,65536,out,AF_CZ_RAW)==0);
        CHECK(memcmp(out,raw,65536)==0 && memcmp(out+65536,console,6528)==0);
        memcpy(saved,packed,65536);
        CHECK(af_v3_save_compress(packed,65536,raw,65536,console,6528,hash,AF_CZ_WORK_BYTES)==n);
        CHECK(memcmp(packed,saved,65536)==0);file_write(argv[1],results[which],packed);
        printf("%s: %d compressed bytes, %d spare stream bytes\n",names[which],n,CAP-n);
        CHECK(af_v3_save_expand(packed,65535,out,AF_CZ_RAW)==AF_CZ_ARGUMENT);
        CHECK(af_v3_save_expand(packed,65536,out,AF_CZ_RAW-1)==AF_CZ_ARGUMENT);
        CHECK(af_v3_save_expand(packed,65536,packed,AF_CZ_RAW)==AF_CZ_ARGUMENT);
        CHECK(af_v3_save_compress(raw,65536,raw,65536,console,6528,hash,AF_CZ_WORK_BYTES)==AF_CZ_ARGUMENT);
        CHECK(af_v3_save_compress(packed,65536,raw,65536,console,6528,(u32 *)console,AF_CZ_WORK_BYTES)==AF_CZ_ARGUMENT);
        CHECK(memcmp(packed,saved,65536)==0 && memcmp(raw,raw_before,65536)==0);
        // Complete envelope damage, including compensated native checksum damage.
        const u32 offsets[]={4,8,18,20,0x2F68,P,P+4,P+8,P+12,P+16,P+20,P+24,P+28,P+32,P+36,P+40,65535};
        for(unsigned i=0;i<sizeof(offsets)/sizeof(*offsets);i++) {
            memcpy(bad,packed,65536);bad[offsets[i]]^=1;
            if(offsets[i]!=18)balance(bad);
            CHECK(af_v3_save_expand(bad,65536,out,AF_CZ_RAW)<0);
        }
        // Authenticated but malformed token streams must still reject safely.
        memcpy(bad,packed,65536);put(bad+P+16,1);bad[20]=0;seal(bad);
        CHECK(af_v3_save_expand(bad,65536,out,AF_CZ_RAW)<0);
        memcpy(bad,packed,65536);bad[20]=0;bad[21]=0x10;bad[22]=0;seal(bad);
        CHECK(af_v3_save_expand(bad,65536,out,AF_CZ_RAW)==AF_CZ_STREAM);
        memcpy(bad,packed,65536);put(bad+P+16,word(bad+P+16)+1);seal(bad);
        CHECK(af_v3_save_expand(bad,65536,out,AF_CZ_RAW)==AF_CZ_STREAM);
        memcpy(bad,packed,65536);bad[physical(n)]=1;seal(bad);
        CHECK(af_v3_save_expand(bad,65536,out,AF_CZ_RAW)==AF_CZ_FORMAT);
        // Whole output remains unchanged on malformed canonical input too.
        raw[0x500]^=1;
        CHECK(af_v3_save_compress(packed,65536,raw,65536,console,6528,hash,AF_CZ_WORK_BYTES)==AF_CZ_FORMAT);
        CHECK(memcmp(packed,saved,65536)==0);
    }
    free_guarded(raw,65536);free_guarded(console,6528);free_guarded(packed,65536);
    free_guarded(out,AF_CZ_RAW);free_guarded(saved,65536);free_guarded(bad,65536);
    free_guarded(raw_before,65536);free_guarded(console_before,6528);free_guarded((u8 *)hash,AF_CZ_WORK_BYTES);
    printf("%u compressed-bank assertions; no flash I/O\n",checks);
    return 0;
}
