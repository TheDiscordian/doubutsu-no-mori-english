#include "pak_codec.h"
typedef af_pak_u8 u8;
typedef af_pak_u32 u32;
typedef __UINTPTR_TYPE__ address;
_Static_assert(sizeof(u32)==4,"Pak wire words are 32 bits");

static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void put(u8 *p,u32 v) {p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static void copy(u8 *d,const u8 *s,u32 n) {while(n--)*d++=*s++;}
static int equal(const u8 *a,const u8 *b,u32 n) {
    while(n--)if(*a++!=*b++)return 0;
    return 1;
}
static int separate(const void *a,u32 an,const void *b,u32 bn) {
    address x=(address)a,y=(address)b;
    if(an>(address)-1-x || bn>(address)-1-y)return 0;
    return x<=y?y-x>=an:x-y>=bn;
}
static u32 crc(const u8 *p,u32 n,u32 omit,u32 skip) {
    u32 v=~0u;
    for(u32 i=0;i<n;i++) {
        v^=(i>=omit && i-omit<skip)?0:p[i];
        for(u32 b=0;b<8;b++)v=(v>>1)^(0xEDB88320u&-(v&1));
    }
    return ~v;
}
static u32 native_size(u32 kind) {
    return kind==AF_PAK_PASSPORT?AF_PAK_PRIVATE_NOTE:kind==AF_PAK_BACKUP?AF_PAK_BACKUP_NOTE:0;
}
static u8 source(const AFPakInput *s,u32 at) {
    return at<s->native_bytes?s->native[at]:s->records[at-s->native_bytes];
}
static u32 key(const AFPakInput *s,u32 at) {
    return ((u32)source(s,at)*0x1E35A7BDu ^
        (u32)source(s,at+1)*0x9E3779B1u ^ source(s,at+2))>>20;
}
static void emit(u8 *note,u32 at,u8 v) {if(note)note[AF_PAK_HEADER+at]=v;}
/* The same bounded Yaz0 token grammar used by the FlashRAM envelope, over the
 * complete native note and added records. Compression is lossless: full diary
 * pages and game progress are never shortened to make a note fit. */
static int encode(u8 *note,const AFPakInput *s,u32 capacity,u32 *hash) {
    u32 at=0,out=0,total=s->native_bytes+s->record_bytes,limit=capacity-AF_PAK_HEADER;
    for(u32 i=0;i<AF_PAK_HASH_WORDS;i++)hash[i]=~0u;
    while(at<total) {
        u32 mask=128,flag_at=out++,flags=0;
        if(out>limit)return AF_PAK_CAPACITY;
        while(mask && at<total) {
            u32 match=0,distance=0;
            if(at+2<total) {
                u32 k=key(s,at),previous=hash[k],end=total-at;
                hash[k]=at;if(end>273)end=273;
                if(previous<at && at-previous<=4096) {
                    while(match<end && source(s,previous+match)==source(s,at+match))match++;
                    distance=at-previous-1;
                }
            }
            if(match>=3) {
                u32 bytes=match>=18?3:2,end=at+match;
                if(bytes>limit-out)return AF_PAK_CAPACITY;
                emit(note,out++,((match>=18?0:match-2)<<4)|(distance>>8));
                emit(note,out++,distance);
                if(match>=18)emit(note,out++,match-18);
                for(u32 i=at+1;i<end && i+2<total;i++)hash[key(s,i)]=i;
                at=end;
            } else {
                if(out==limit)return AF_PAK_CAPACITY;
                flags|=mask;emit(note,out++,source(s,at++));
            }
            mask>>=1;
        }
        emit(note,flag_at,flags);
    }
    return (int)out;
}
static int arguments(const AFPakInput *s,u32 capacity,u32 *hash,u32 hash_bytes) {
    if(!s || !s->native || (s->record_bytes && !s->records) ||
       !native_size(s->kind) || s->native_bytes!=native_size(s->kind) ||
       s->record_bytes>AF_PAK_MAX_RECORDS || capacity<AF_PAK_PAGE ||
       capacity>AF_PAK_MAX_NOTE || capacity%AF_PAK_PAGE || !hash ||
       hash_bytes!=AF_PAK_HASH_BYTES || ((address)hash&3))return AF_PAK_ARGUMENT;
    const void *p[4]={s,s->native,s->records,hash};
    const u32 n[4]={sizeof(*s),s->native_bytes,s->record_bytes,hash_bytes};
    for(u32 i=0;i<4;i++)for(u32 j=0;j<i;j++)
        if(n[i] && n[j] && !separate(p[i],n[i],p[j],n[j]))return AF_PAK_ARGUMENT;
    if(s->kind==AF_PAK_PASSPORT && !equal(s->native+8,s->identity,16))return AF_PAK_BINDING;
    return 1;
}
static int measure(const AFPakInput *s,u32 capacity,u32 *hash) {
    int stream=encode(0,s,capacity,hash);
    if(stream<0)return stream;
    u32 pages=((u32)stream+AF_PAK_HEADER+AF_PAK_PAGE-1)&~(AF_PAK_PAGE-1u);
    return pages>capacity?AF_PAK_CAPACITY:(int)pages;
}
int af_v3_pak_measure(const AFPakInput *s,u32 capacity,u32 *hash,u32 hash_bytes) {
    int r=arguments(s,capacity,hash,hash_bytes);
    return r<0?r:measure(s,capacity,hash);
}
int af_v3_pak_encode(u8 *note,u32 capacity,const AFPakInput *s,u32 *hash,u32 hash_bytes) {
    int r=arguments(s,capacity,hash,hash_bytes);
    if(r<0)return r;
    if(!note || !separate(note,capacity,s,sizeof(*s)) ||
       !separate(note,capacity,s->native,s->native_bytes) ||
       (s->record_bytes && !separate(note,capacity,s->records,s->record_bytes)) ||
       !separate(note,capacity,hash,hash_bytes))return AF_PAK_ARGUMENT;
    r=measure(s,capacity,hash);if(r<0)return r;
    u32 bytes=(u32)r;
    for(u32 i=0;i<bytes;i++)note[i]=0;
    int stream=encode(note,s,capacity,hash);
    put(note,0x4146504Bu);put(note+4,1);put(note+8,s->kind);put(note+12,bytes);
    put(note+16,s->native_bytes);put(note+20,s->record_bytes);put(note+24,(u32)stream);
    put(note+28,crc(s->native,s->native_bytes,0,0));
    put(note+32,crc(s->records,s->record_bytes,0,0));
    copy(note+40,s->binding,32);copy(note+72,s->identity,16);
    put(note+36,crc(note,bytes,36,4));
    return r;
}
int af_v3_pak_decode(const u8 *note,u32 bytes,const u8 binding[32],const u8 identity[16],
    u8 *raw,u32 raw_bytes,AFPakView *view) {
    if(!note || !binding || !raw || !view || bytes<AF_PAK_PAGE ||
       bytes>AF_PAK_MAX_NOTE || bytes%AF_PAK_PAGE ||
       !separate(raw,raw_bytes,note,bytes) || !separate(raw,raw_bytes,binding,32) ||
       (identity && !separate(raw,raw_bytes,identity,16)) ||
       !separate(raw,raw_bytes,view,sizeof(*view)) ||
       !separate(view,sizeof(*view),note,bytes) || !separate(view,sizeof(*view),binding,32) ||
       (identity && !separate(view,sizeof(*view),identity,16)))return AF_PAK_ARGUMENT;
    u32 kind=word(note+8),nb=word(note+16),rb=word(note+20),length=word(note+24);
    if(word(note)!=0x4146504Bu || word(note+4)!=1 || word(note+12)!=bytes ||
       !native_size(kind) || nb!=native_size(kind) || rb>AF_PAK_MAX_RECORDS ||
       !length || length>bytes-AF_PAK_HEADER ||
       ((length+AF_PAK_HEADER+AF_PAK_PAGE-1)&~(AF_PAK_PAGE-1u))!=bytes)return AF_PAK_FORMAT;
    if(nb+rb>raw_bytes)return AF_PAK_CAPACITY;
    for(u32 i=88;i<AF_PAK_HEADER;i++)if(note[i])return AF_PAK_FORMAT;
    for(u32 i=AF_PAK_HEADER+length;i<bytes;i++)if(note[i])return AF_PAK_FORMAT;
    if(word(note+36)!=crc(note,bytes,36,4))return AF_PAK_CRC;
    if(!equal(note+40,binding,32) || (identity && !equal(note+72,identity,16)))return AF_PAK_BINDING;
    u32 in=0,out=0,total=nb+rb;const u8 *stream=note+AF_PAK_HEADER;
    while(out<total) {
        if(in==length)return AF_PAK_STREAM;
        u32 flags=stream[in++],mask=128;
        while(mask && out<total) {
            if(flags&mask) {
                if(in==length)return AF_PAK_STREAM;
                raw[out++]=stream[in++];
            } else {
                if(length-in<2)return AF_PAK_STREAM;
                u32 a=stream[in++],b=stream[in++],count=a>>4,distance=((a&15)<<8|b)+1;
                if(!count) {
                    if(in==length)return AF_PAK_STREAM;
                    count=(u32)stream[in++]+18;
                } else count+=2;
                if(distance>out || count>total-out)return AF_PAK_STREAM;
                for(u32 i=0;i<count;i++) {raw[out]=raw[out-distance];out++;}
            }
            mask>>=1;
        }
        if(out==total && mask && (flags&(mask*2-1)))return AF_PAK_STREAM;
    }
    if(in!=length)return AF_PAK_STREAM;
    if(word(note+28)!=crc(raw,nb,0,0) || word(note+32)!=crc(raw+nb,rb,0,0))return AF_PAK_CRC;
    if(kind==AF_PAK_PASSPORT && !equal(raw+8,note+72,16))return AF_PAK_BINDING;
    AFPakView v={raw,raw+nb,kind,nb,rb,{0}};
    copy(v.identity,note+72,16);copy((u8 *)view,(const u8 *)&v,sizeof(v));
    return 1;
}
