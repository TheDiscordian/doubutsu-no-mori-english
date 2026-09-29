#include "save_compressed.h"
typedef unsigned char u8;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ address;
enum { PAYLOAD=0xF980, EXT=0x680, MIRROR=0x2F68, START=0x14,
       CAPACITY=PAYLOAD-START-2, HEADER=40 };
static u32 half(const u8 *p) { return (u32)p[0]<<8|p[1]; }
static u32 word(const u8 *p) { return half(p)<<16|half(p+2); }
static void put(u8 *p,u32 n) { p[0]=n>>24;p[1]=n>>16;p[2]=n>>8;p[3]=n; }
static void copy(u8 *d,const u8 *s,u32 n) { while(n--) *d++=*s++; }
static void zero(u8 *d,u32 n) { while(n--) *d++=0; }
static u32 crc(const u8 *p,u32 n,u32 omit,u32 skip) {
    u32 v=~0u,i,b;
    for(i=0;i<n;i++) {
        v^=(i>=omit && i-omit<skip)?0:p[i];
        for(b=0;b<8;b++) v=(v>>1)^(0xEDB88320u&(0u-(v&1)));
    }
    return ~v;
}
static u32 disk_crc(const u8 *p) {
    u32 v=~0u,i,b;
    for(i=0;i<AF_CZ_BANK;i++) {
        v^=(i==0x12 || i==0x13 || (i>=PAYLOAD+24 && i<PAYLOAD+28))?0:p[i];
        for(b=0;b<8;b++) v=(v>>1)^(0xEDB88320u&(0u-(v&1)));
    }
    return ~v;
}
static u32 sum(const u8 *p) {
    u32 v=0,i;for(i=0;i<PAYLOAD;i+=2)v+=half(p+i);return v&0xFFFF;
}
static int town(const u8 *p) {
    return word(p+4)==0x4E414633 && p[8]==0x30 && half(p+8)==half(p+MIRROR);
}
static int canonical_valid(const u8 *p) {
    const u8 *e=p+PAYLOAD;
    int version=word(e+4)==0x00040680 && word(e+8)==3;
#ifdef AF_V3_CREATURE_PROFILE
    version |= word(e+4)==0x00060680 && word(e+8)==4;
#endif
#ifdef AF_V3_INSECT_SEASONS
    version |= word(e+4)==0x00080680 && word(e+8)==5;
#endif
    return town(p) && !sum(p) && word(e)==0x41465333 && version &&
        word(e+12)==crc(p,PAYLOAD,0x12,2) &&
        word(e+16)==crc(e,EXT,16,4);
}
static int disjoint(const void *a,u32 an,const void *b,u32 bn) {
    address x=(address)a,y=(address)b;
    if(an>(address)-1-x || bn>(address)-1-y) return 0;
    return x<=y ? y-x>=an : x-y>=bn;
}
struct Input {const u8 *canonical,*console,*extra;u32 extra_bytes;};
static u8 source(const struct Input *s,u32 at) {
    if(at<AF_CZ_BANK)return s->canonical[at];
    if(at<AF_CZ_RAW)return s->console[at-AF_CZ_BANK];
    return s->extra[at-AF_CZ_RAW];
}
static u32 physical(u32 logical) {
    u32 at=START+logical;return at>=MIRROR?at+2:at;
}
static void emit(u8 *bank,u32 at,u8 value) { if(bank) bank[physical(at)]=value; }
static u32 key(const struct Input *s,u32 at) {
    return ((u32)source(s,at)*0x1E35A7BDu ^
        (u32)source(s,at+1)*0x9E3779B1u ^ source(s,at+2))>>20;
}
/* Yaz0 token grammar without a file header: eight flags, then literals or a
 * 12-bit distance and 4-bit length; zero length introduces an extra byte +18.
 * One bounded hash candidate per byte keeps encoder work linear and bounded. */
static int encode(u8 *bank,const struct Input *s,u32 *hash) {
    u32 i,at=0,out=0,total=AF_CZ_RAW+s->extra_bytes;
    for(i=0;i<AF_CZ_HASH_WORDS;i++)hash[i]=~0u;
    while(at<total) {
        u32 mask=0x80,flag_at=out++,flags=0;
        if(out>CAPACITY)return AF_CZ_SPACE;
        while(mask && at<total) {
            u32 match=0,distance=0;
            if(at+2<total) {
                u32 k=key(s,at),previous=hash[k],limit=total-at;
                hash[k]=at;
                if(limit>273)limit=273;
                if(previous<at && at-previous<=4096) {
                    while(match<limit && source(s,previous+match)==source(s,at+match))match++;
                    distance=at-previous-1;
                }
            }
            if(match>=3) {
                u32 length=match>=18?3:2,end=at+match;
                if(length>CAPACITY-out)return AF_CZ_SPACE;
                emit(bank,out++,((match>=18?0:match-2)<<4)|(distance>>8));
                emit(bank,out++,distance);
                if(match>=18)emit(bank,out++,match-18);
                for(i=at+1;i<end && i+2<total;i++)hash[key(s,i)]=i;
                at=end;
            } else {
                if(out==CAPACITY)return AF_CZ_SPACE;
                flags|=mask;emit(bank,out++,source(s,at++));
            }
            mask>>=1;
        }
        emit(bank,flag_at,flags);
    }
    return (int)out;
}

static int compress(u8 *bank,u32 bank_bytes,const u8 *canonical,u32 canonical_bytes,
    const u8 *console,u32 console_bytes,const u8 *extra,u32 extra_bytes,u32 *hash,u32 hash_bytes,int measure) {
    const void *buffers[5]={bank,canonical,console,hash,extra};
    const u32 sizes[5]={AF_CZ_BANK,AF_CZ_BANK,AF_CZ_CONSOLE,AF_CZ_WORK_BYTES,extra_bytes};
    const struct Input input={canonical,console,extra,extra_bytes};
    u32 i,j,checksum;int length;
    if((!bank && !measure) || !canonical || !console || !hash || (extra_bytes && !extra) || bank_bytes!=AF_CZ_BANK ||
       canonical_bytes!=AF_CZ_BANK || console_bytes!=AF_CZ_CONSOLE ||
       hash_bytes!=AF_CZ_WORK_BYTES || ((address)hash&3))return AF_CZ_ARGUMENT;
    for(i=measure?1:0;i<(extra_bytes?5u:4u);i++)for(j=measure?1:0;j<i;j++)
        if(!disjoint(buffers[i],sizes[i],buffers[j],sizes[j]))return AF_CZ_ARGUMENT;
    if(!canonical_valid(canonical))return AF_CZ_FORMAT;
#ifdef AF_V3_DIARY_STORAGE
    int valid_extra=extra_bytes==AF_DIARY_BYTES;
#ifdef AF_V3_FISHING_STORAGE
    valid_extra |= extra_bytes==AF_CZ_FISHING_EXTRA;
    int has_fishing=extra_bytes==AF_CZ_FISHING_EXTRA;
#ifdef AF_V3_CARD_STORAGE
    valid_extra |= extra_bytes==AF_CZ_CARD_EXTRA;
    has_fishing |= extra_bytes==AF_CZ_CARD_EXTRA;
    if(extra_bytes==AF_CZ_CARD_EXTRA && !af_holiday_cards_valid(extra+AF_CZ_FISHING_EXTRA))return AF_CZ_FORMAT;
#ifdef AF_V3_CARRIED_PROFILE
    if(extra_bytes==AF_CZ_CARD_EXTRA && extra[AF_CZ_FISHING_EXTRA+4]!=AF_HC_CARRIED_WIRE)return AF_CZ_FORMAT;
#elif defined(AF_V3_EVENT_ITEM_PROFILE)
    if(extra_bytes==AF_CZ_CARD_EXTRA && extra[AF_CZ_FISHING_EXTRA+4]!=2)return AF_CZ_FORMAT;
#endif
#endif
    if(has_fishing && !af_holiday_fish_wire_valid(extra+AF_DIARY_BYTES))return AF_CZ_FORMAT;
#endif
    if(extra_bytes && (!valid_extra || !af_diary_valid((const AFDiary *)extra) ||
        word(canonical+PAYLOAD+4)!=0x00080680 || word(canonical+PAYLOAD+8)!=5))return AF_CZ_FORMAT;
#ifdef AF_V3_HOLIDAY_STORAGE
    if(extra_bytes && extra[5]!=2)return AF_CZ_FORMAT;
#endif
#else
    if(extra_bytes)return AF_CZ_ARGUMENT;
#endif
    /* Capacity is measured BEFORE modifying output; never write a partial save. */
    length=encode(0,&input,hash);
    if(length<0 || measure)return length;
    zero(bank,AF_CZ_BANK);
    copy(bank,canonical,START);copy(bank+MIRROR,canonical+MIRROR,2);
    encode(bank,&input,hash);
    put(bank+PAYLOAD,0x41465333);
#ifdef AF_V3_HOLIDAY_STORAGE
    put(bank+PAYLOAD+4,extra_bytes?0x000C0680:word(canonical+PAYLOAD+4)+0x10000u);
#else
    put(bank+PAYLOAD+4,extra_bytes?0x000B0680:word(canonical+PAYLOAD+4)+0x10000u);
#endif
#ifdef AF_V3_FISHING_STORAGE
    if(extra_bytes==AF_CZ_FISHING_EXTRA)put(bank+PAYLOAD+4,0x000D0680);
#ifdef AF_V3_CARD_STORAGE
    if(extra_bytes==AF_CZ_CARD_EXTRA)put(bank+PAYLOAD+4,
#ifdef AF_V3_CARRIED_PROFILE
#ifdef AF_V3_CARRIED_QUEST
        0x00110680
#else
        0x00100680
#endif
#elif defined(AF_V3_EVENT_ITEM_PROFILE)
        0x000F0680
#else
        0x000E0680
#endif
    );
#endif
#endif
    put(bank+PAYLOAD+8,word(canonical+PAYLOAD+8));put(bank+PAYLOAD+12,AF_CZ_RAW+extra_bytes);
    put(bank+PAYLOAD+16,(u32)length);put(bank+PAYLOAD+20,1);
    put(bank+PAYLOAD+28,crc(canonical,AF_CZ_BANK,AF_CZ_BANK,0));
    put(bank+PAYLOAD+32,crc(console,AF_CZ_CONSOLE,AF_CZ_CONSOLE,0));
    if(extra_bytes)put(bank+PAYLOAD+36,crc(extra,extra_bytes,extra_bytes,0));
    put(bank+PAYLOAD+24,disk_crc(bank));
    checksum=(half(bank+0x12)-sum(bank))&0xFFFF;
    bank[0x12]=checksum>>8;bank[0x13]=checksum;
    return length;
}

int af_v3_save_compress(u8 *bank,u32 bank_bytes,const u8 *canonical,u32 canonical_bytes,
    const u8 *console,u32 console_bytes,u32 *hash,u32 hash_bytes) {
    return compress(bank,bank_bytes,canonical,canonical_bytes,console,console_bytes,0,0,hash,hash_bytes,0);
}

static int expand(const u8 *bank,u32 bank_bytes,u8 *scratch,u32 scratch_bytes,u32 extra_bytes) {
    const u8 *e;u32 length,i,at=0,out=0,total,extended=0,stored_extra=0;
    if(!bank || !scratch || bank_bytes!=AF_CZ_BANK || scratch_bytes!=AF_CZ_RAW+extra_bytes ||
       !disjoint(bank,AF_CZ_BANK,scratch,scratch_bytes))return AF_CZ_ARGUMENT;
    e=bank+PAYLOAD;length=word(e+16);
    int version=word(e+4)==0x00050680 && word(e+8)==3;
#ifdef AF_V3_CREATURE_PROFILE
    version |= word(e+4)==0x00070680 && word(e+8)==4;
#endif
#ifdef AF_V3_INSECT_SEASONS
    version |= word(e+4)==0x00090680 && word(e+8)==5;
#endif
#ifdef AF_V3_DIARY_STORAGE
    int diary_capacity=extra_bytes==AF_DIARY_BYTES;
#ifdef AF_V3_FISHING_STORAGE
    int fishing_capacity=extra_bytes==AF_CZ_FISHING_EXTRA;
#ifdef AF_V3_CARD_STORAGE
    fishing_capacity |= extra_bytes==AF_CZ_CARD_EXTRA;
#endif
    diary_capacity |= fishing_capacity;
#endif
    extended=diary_capacity && word(e+4)==0x000B0680 && word(e+8)==5;
#ifdef AF_V3_HOLIDAY_STORAGE
    extended |= diary_capacity && word(e+4)==0x000C0680 && word(e+8)==5;
#endif
    if(extended)stored_extra=AF_DIARY_BYTES;
#ifdef AF_V3_FISHING_STORAGE
    if(fishing_capacity && word(e+4)==0x000D0680 && word(e+8)==5) {
        extended=1;stored_extra=AF_CZ_FISHING_EXTRA;
    }
#ifdef AF_V3_CARD_STORAGE
    if(extra_bytes==AF_CZ_CARD_EXTRA && (word(e+4)==0x000E0680
#ifdef AF_V3_EVENT_ITEM_PROFILE
            || word(e+4)==0x000F0680
#endif
#ifdef AF_V3_CARRIED_PROFILE
            || word(e+4)==0x00100680
#ifdef AF_V3_CARRIED_QUEST
            || word(e+4)==0x00110680
#endif
#endif
            ) && word(e+8)==5) {
        extended=1;stored_extra=AF_CZ_CARD_EXTRA;
    }
#endif
#endif
    version |= extended;
#endif
    total=AF_CZ_RAW+stored_extra;
    if(!town(bank) || word(e)!=0x41465333 || !version ||
       word(e+12)!=total || !length || length>CAPACITY ||
       word(e+20)!=1 || (!extended && word(e+36)))return AF_CZ_FORMAT;
    if(sum(bank) || word(e+24)!=disk_crc(bank))return AF_CZ_CHECKSUM;
    for(i=HEADER;i<EXT;i++)if(e[i])return AF_CZ_FORMAT;
    for(i=length;i<CAPACITY;i++)if(bank[physical(i)])return AF_CZ_FORMAT;
    while(out<total) {
        u32 flags,mask=0x80;
        if(at==length)return AF_CZ_STREAM;
        flags=bank[physical(at++)];
        while(mask && out<total) {
            if(flags&mask) {
                if(at==length)return AF_CZ_STREAM;
                scratch[out++]=bank[physical(at++)];
            } else {
                u32 first,second,n,distance;
                if(length-at<2)return AF_CZ_STREAM;
                first=bank[physical(at++)];second=bank[physical(at++)];
                n=first>>4;distance=((first&15)<<8)+second+1;
                if(n)n+=2;
                else {
                    if(at==length)return AF_CZ_STREAM;
                    n=bank[physical(at++)]+18;
                }
                if(distance>out || n>total-out)return AF_CZ_STREAM;
                while(n--) { scratch[out]=scratch[out-distance];out++; }
            }
            mask>>=1;
        }
        if(out==total && mask && (flags&(mask*2-1)))return AF_CZ_STREAM;
    }
    if(at!=length)return AF_CZ_STREAM;
    if(crc(scratch,AF_CZ_BANK,AF_CZ_BANK,0)!=word(e+28) ||
       crc(scratch+AF_CZ_BANK,AF_CZ_CONSOLE,AF_CZ_CONSOLE,0)!=word(e+32))return AF_CZ_CHECKSUM;
    if(!canonical_valid(scratch))return AF_CZ_FORMAT;
    if(word(scratch+PAYLOAD+8)!=word(e+8) ||
       (extended?word(scratch+PAYLOAD+4)!=0x00080680:
        word(scratch+PAYLOAD+4)+0x10000u!=word(e+4)))return AF_CZ_FORMAT;
    for(i=0;i<START;i++)if(i!=0x12 && i!=0x13 && scratch[i]!=bank[i])return AF_CZ_FORMAT;
#ifdef AF_V3_DIARY_STORAGE
    if(extended) {
        if(crc(scratch+AF_CZ_RAW,stored_extra,stored_extra,0)!=word(e+36))return AF_CZ_CHECKSUM;
        if(!af_diary_valid((const AFDiary *)(scratch+AF_CZ_RAW)))return AF_CZ_FORMAT;
#ifdef AF_V3_HOLIDAY_STORAGE
        if(scratch[AF_CZ_RAW+5]!=(word(e+4)==0x000B0680?1:2))return AF_CZ_FORMAT;
        if(af_diary_upgrade((AFDiary *)(scratch+AF_CZ_RAW))!=AF_DIARY_OK)return AF_CZ_FORMAT;
#endif
    } else if(extra_bytes)af_diary_reset((AFDiary *)(scratch+AF_CZ_RAW));
#ifdef AF_V3_FISHING_STORAGE
    if(fishing_capacity) {
        u8 *fish=scratch+AF_CZ_RAW+AF_DIARY_BYTES;
        if(stored_extra>=AF_CZ_FISHING_EXTRA) {
            if(!af_holiday_fish_wire_valid(fish))return AF_CZ_FORMAT;
        } else af_holiday_fish_wire_reset(fish);
    }
#ifdef AF_V3_CARD_STORAGE
    if(extra_bytes==AF_CZ_CARD_EXTRA) {
        u8 *cards=scratch+AF_CZ_RAW+AF_CZ_FISHING_EXTRA;
        if(stored_extra==AF_CZ_CARD_EXTRA) {
            if(!af_holiday_cards_valid(cards))return AF_CZ_FORMAT;
            if(cards[4]!=(word(e+4)==0x00110680?4:word(e+4)==0x00100680?3:
                         word(e+4)==0x000F0680?2:1))return AF_CZ_FORMAT;
        } else af_holiday_cards_reset(cards);
    }
#endif
#endif
#endif
    return 0;
}

int af_v3_save_expand(const u8 *bank,u32 bank_bytes,u8 *scratch,u32 scratch_bytes) {
    return expand(bank,bank_bytes,scratch,scratch_bytes,0);
}
#ifdef AF_V3_DIARY_STORAGE
int af_v3_save_compress_diary(u8 *bank,u32 bank_bytes,const u8 *canonical,u32 canonical_bytes,
    const u8 *console,u32 console_bytes,const AFDiary *diary,u32 *hash,u32 hash_bytes) {
    return compress(bank,bank_bytes,canonical,canonical_bytes,console,console_bytes,
        (const u8 *)diary,AF_DIARY_BYTES,hash,hash_bytes,0);
}
int af_v3_save_measure_diary(const u8 *canonical,u32 canonical_bytes,const u8 *console,u32 console_bytes,
    const AFDiary *diary,u32 *hash,u32 hash_bytes) {
    return compress(0,AF_CZ_BANK,canonical,canonical_bytes,console,console_bytes,
        (const u8 *)diary,AF_DIARY_BYTES,hash,hash_bytes,1);
}
int af_v3_save_expand_diary(const u8 *bank,u32 bank_bytes,u8 *scratch,u32 scratch_bytes) {
    return expand(bank,bank_bytes,scratch,scratch_bytes,AF_DIARY_BYTES);
}
#ifdef AF_V3_FISHING_STORAGE
int af_v3_save_compress_fishing(u8 *bank,u32 bank_bytes,const u8 *canonical,u32 canonical_bytes,
    const u8 *console,u32 console_bytes,const u8 *extended,u32 *hash,u32 hash_bytes) {
    return compress(bank,bank_bytes,canonical,canonical_bytes,console,console_bytes,
        extended,AF_CZ_FISHING_EXTRA,hash,hash_bytes,0);
}
int af_v3_save_measure_fishing(const u8 *canonical,u32 canonical_bytes,const u8 *console,u32 console_bytes,
    const u8 *extended,u32 *hash,u32 hash_bytes) {
    return compress(0,AF_CZ_BANK,canonical,canonical_bytes,console,console_bytes,
        extended,AF_CZ_FISHING_EXTRA,hash,hash_bytes,1);
}
int af_v3_save_expand_fishing(const u8 *bank,u32 bank_bytes,u8 *scratch,u32 scratch_bytes) {
    return expand(bank,bank_bytes,scratch,scratch_bytes,AF_CZ_FISHING_EXTRA);
}
#ifdef AF_V3_CARD_STORAGE
int af_v3_save_compress_cards(u8 *bank,u32 bank_bytes,const u8 *canonical,u32 canonical_bytes,
    const u8 *console,u32 console_bytes,const u8 *extended,u32 *hash,u32 hash_bytes) {
    return compress(bank,bank_bytes,canonical,canonical_bytes,console,console_bytes,
        extended,AF_CZ_CARD_EXTRA,hash,hash_bytes,0);
}
int af_v3_save_measure_cards(const u8 *canonical,u32 canonical_bytes,const u8 *console,u32 console_bytes,
    const u8 *extended,u32 *hash,u32 hash_bytes) {
    return compress(0,AF_CZ_BANK,canonical,canonical_bytes,console,console_bytes,
        extended,AF_CZ_CARD_EXTRA,hash,hash_bytes,1);
}
int af_v3_save_expand_cards(const u8 *bank,u32 bank_bytes,u8 *scratch,u32 scratch_bytes) {
    return expand(bank,bank_bytes,scratch,scratch_bytes,AF_CZ_CARD_EXTRA);
}
#endif
#endif
#endif
