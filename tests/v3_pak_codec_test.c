#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/pak_codec.h"
typedef unsigned char u8;
typedef unsigned int u32;
static u8 native[AF_PAK_BACKUP_NOTE],records[AF_PAK_MAX_RECORDS];
static u8 note[AF_PAK_MAX_NOTE],second[AF_PAK_MAX_NOTE],saved[AF_PAK_MAX_NOTE];
static u8 raw[AF_PAK_BACKUP_NOTE+AF_PAK_MAX_RECORDS+16];
static u32 hash[AF_PAK_HASH_WORDS];
static AFPakInput input;
static AFPakView view;
static u32 random_state=0x19840205;
static u32 random_word(void) {
    random_state^=random_state<<13;random_state^=random_state>>17;random_state^=random_state<<5;
    return random_state;
}
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void put(u8 *p,u32 v) {p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static u32 crc(const u8 *p,u32 n) {
    u32 v=~0u;
    for(u32 i=0;i<n;i++) {
        v^=(i>=36 && i<40)?0:p[i];
        for(u32 b=0;b<8;b++)v=(v>>1)^(0xEDB88320u&-(v&1));
    }
    return ~v;
}
static void reseal(u32 bytes) {put(note+36,crc(note,bytes));}
static void rejects(u32 bytes,int expected) {
    AFPakView before=view;
    assert(af_v3_pak_decode(note,bytes,input.binding,input.identity,raw,sizeof(raw)-16,&view)==expected);
    assert(!memcmp(&before,&view,sizeof(view)));
    for(u32 i=sizeof(raw)-16;i<sizeof(raw);i++)assert(raw[i]==0xA5);
}
static void setup(u32 kind,u32 count,u32 mode) {
    input=(AFPakInput){native,records,kind,kind?AF_PAK_BACKUP_NOTE:AF_PAK_PRIVATE_NOTE,count,{0},{0}};
    for(u32 i=0;i<32;i++)input.binding[i]=(u8)(i*17+3);
    for(u32 i=0;i<input.native_bytes;i++)native[i]=mode?(u8)random_word():0;
    for(u32 i=0;i<count;i++)records[i]=mode?(u8)random_word():(u8)(i%19==0?i&7:0);
    for(u32 i=0;i<16;i++)input.identity[i]=(u8)(41+i);
    if(!kind)memcpy(native+8,input.identity,16);
    memset(raw,0xA5,sizeof(raw));memset(note,0xA5,sizeof(note));memset(&view,0xA5,sizeof(view));
}
static void roundtrip(u32 kind,u32 count,u32 mode) {
    setup(kind,count,mode);
    int bytes=af_v3_pak_measure(&input,sizeof(note),hash,sizeof(hash));
    memcpy(saved,note,sizeof(saved));
    if(bytes==AF_PAK_CAPACITY) {
        assert(kind && mode);
        assert(af_v3_pak_encode(note,sizeof(note),&input,hash,sizeof(hash))==bytes);
        assert(!memcmp(saved,note,sizeof(saved)));return;
    }
    assert(bytes>=256 && bytes%256==0);
    assert(af_v3_pak_encode(note,sizeof(note),&input,hash,sizeof(hash))==bytes);
    memset(second,0xA5,sizeof(second));
    assert(af_v3_pak_encode(second,sizeof(second),&input,hash,sizeof(hash))==bytes);
    assert(!memcmp(note,second,sizeof(note)));
    for(u32 i=(u32)bytes;i<sizeof(note);i++)assert(note[i]==0xA5);
    assert(af_v3_pak_decode(note,(u32)bytes,input.binding,input.identity,raw,sizeof(raw)-16,&view)==1);
    assert(view.kind==kind && view.native==raw && view.records==raw+input.native_bytes);
    assert(view.native_bytes==input.native_bytes && view.record_bytes==count);
    assert(!memcmp(view.native,native,input.native_bytes) && !memcmp(view.records,records,count));
    assert(!memcmp(view.identity,input.identity,16));
    for(u32 i=input.native_bytes+count;i<sizeof(raw);i++)assert(raw[i]==0xA5);
    assert(af_v3_pak_decode(note,(u32)bytes,input.binding,0,raw,sizeof(raw)-16,&view)==1);
    memcpy(saved,note,sizeof(saved));
    note[AF_PAK_HEADER+word(note+24)/2]^=1;rejects((u32)bytes,AF_PAK_CRC);
    memcpy(note,saved,sizeof(note));note[40]^=1;reseal((u32)bytes);rejects((u32)bytes,AF_PAK_BINDING);
    memcpy(note,saved,sizeof(note));note[72]^=1;reseal((u32)bytes);rejects((u32)bytes,AF_PAK_BINDING);
    memcpy(note,saved,sizeof(note));note[28]^=1;reseal((u32)bytes);rejects((u32)bytes,AF_PAK_CRC);
    memcpy(note,saved,sizeof(note));note[32]^=1;reseal((u32)bytes);rejects((u32)bytes,AF_PAK_CRC);
    memcpy(note,saved,sizeof(note));note[88]=1;reseal((u32)bytes);rejects((u32)bytes,AF_PAK_FORMAT);
    memcpy(note,saved,sizeof(note));put(note+20,AF_PAK_MAX_RECORDS+1);reseal((u32)bytes);rejects((u32)bytes,AF_PAK_FORMAT);
    memcpy(note,saved,sizeof(note));put(note+4,2);reseal((u32)bytes);rejects((u32)bytes,AF_PAK_FORMAT);
    memcpy(note,saved,sizeof(note));put(note+12,(u32)bytes+256);reseal((u32)bytes);rejects((u32)bytes,AF_PAK_FORMAT);
    memcpy(note,saved,sizeof(note));put(note+16,0x1201);reseal((u32)bytes);rejects((u32)bytes,AF_PAK_FORMAT);
    memcpy(note,saved,sizeof(note));put(note+8,2);reseal((u32)bytes);rejects((u32)bytes,AF_PAK_FORMAT);
    memcpy(note,saved,sizeof(note));
    if(AF_PAK_HEADER+word(note+24)<(u32)bytes) {
        note[AF_PAK_HEADER+word(note+24)]=1;reseal((u32)bytes);rejects((u32)bytes,AF_PAK_FORMAT);
    }
    memcpy(note,saved,sizeof(note));
    assert(af_v3_pak_decode(note,(u32)bytes,input.binding,input.identity,raw,input.native_bytes+count-1,&view)==AF_PAK_CAPACITY);
    assert(af_v3_pak_encode(note,256,&input,hash,sizeof(hash))==AF_PAK_CAPACITY ||
           af_v3_pak_measure(&input,256,hash,sizeof(hash))==256);
}
int main(void) {
    const u32 sizes[]={0,1,2,3,7,8,9,272,12008+1632+512,AF_PAK_MAX_RECORDS};
    for(u32 kind=0;kind<2;kind++)for(u32 mode=0;mode<2;mode++)
        for(u32 i=0;i<sizeof(sizes)/sizeof(sizes[0]);i++)roundtrip(kind,sizes[i],mode);
    setup(0,AF_PAK_MAX_RECORDS,1);
    memcpy(saved,note,sizeof(note));
    assert(af_v3_pak_encode(note,AF_PAK_PRIVATE_NOTE,&input,hash,sizeof(hash))==AF_PAK_CAPACITY);
    assert(!memcmp(saved,note,sizeof(note)));
    input.identity[0]^=1;
    assert(af_v3_pak_encode(note,sizeof(note),&input,hash,sizeof(hash))==AF_PAK_BINDING);
    assert(!memcmp(saved,note,sizeof(note)));input.identity[0]^=1;
    assert(af_v3_pak_measure(&input,sizeof(note)-1,hash,sizeof(hash))==AF_PAK_ARGUMENT);
    assert(af_v3_pak_measure(&input,sizeof(note),hash,sizeof(hash)-4)==AF_PAK_ARGUMENT);
    assert(af_v3_pak_measure(&input,sizeof(note),(u32 *)(void *)(native+1),sizeof(hash))==AF_PAK_ARGUMENT);
    assert(af_v3_pak_measure(&input,sizeof(note),(u32 *)(void *)native,sizeof(hash))==AF_PAK_ARGUMENT);
    assert(af_v3_pak_encode(native,sizeof(note),&input,hash,sizeof(hash))==AF_PAK_ARGUMENT);
    assert(af_v3_pak_encode((u8 *)&input,sizeof(note),&input,hash,sizeof(hash))==AF_PAK_ARGUMENT);
    assert(af_v3_pak_encode((u8 *)hash,sizeof(note),&input,hash,sizeof(hash))==AF_PAK_ARGUMENT);
    setup(0,0,0);
    int bytes=af_v3_pak_encode(note,sizeof(note),&input,hash,sizeof(hash));assert(bytes>0);
    memcpy(saved,note,sizeof(note));
    /* A checksum-correct malformed stream must not publish a view. */
    note[AF_PAK_HEADER]=0;note[AF_PAK_HEADER+1]=0x10;note[AF_PAK_HEADER+2]=0;
    reseal((u32)bytes);rejects((u32)bytes,AF_PAK_STREAM);
    memcpy(note,saved,sizeof(note));
    assert(af_v3_pak_decode(note,(u32)bytes,input.binding,input.identity,note,sizeof(note),&view)==AF_PAK_ARGUMENT);
    assert(af_v3_pak_decode(note,(u32)bytes,input.binding,input.identity,raw,sizeof(raw),(AFPakView *)(void *)raw)==AF_PAK_ARGUMENT);
    /* Deterministic damaged-file fuzzing includes recomputed framing CRCs. */
    for(u32 i=0;i<600;i++) {
        memcpy(note,saved,sizeof(note));
        u32 at=random_word()%(u32)bytes;note[at]^=(u8)(1u<<(random_word()&7));
        if(i&1)reseal((u32)bytes);
        AFPakView before=view;
        int r=af_v3_pak_decode(note,(u32)bytes,input.binding,input.identity,raw,sizeof(raw)-16,&view);
        if(r<0)assert(!memcmp(&before,&view,sizeof(view)));
        else {
            /* Resealing can undo a mutation of the CRC field. A changed
             * back-reference can also decode to identical repeated bytes. */
            assert(r==1 && view.kind==input.kind && view.record_bytes==0);
            assert(!memcmp(view.native,native,input.native_bytes));
            assert(!memcmp(view.identity,input.identity,16));
        }
    }
    puts("pass: full native notes and imported records, lossless page-sized round trips, deterministic output, capacity rejection before output, binding/identity/CRC checks, bounded malformed streams, and overlap guards");
}
