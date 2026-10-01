#include "travel_native.h"
typedef af_save_u8 u8;
typedef af_save_u32 u32;
enum { PRIVATE=0xBD0,PASSPORT=0x1200,CAPSULE=0x11C0,CACHE_FULL=1,CACHE_LEGACY=2 };
_Static_assert((unsigned)AF_TP_BYTES==AF_PI_STAGING,"Full player record must fit export staging");
#ifdef __mips__
#ifndef AF_TRAVEL_STATE_RAM
#error Traveller state requires an explicitly checked reservation
#endif
#define visitor ((AFTravelVisitor *)AF_TRAVEL_STATE_RAM)
#define native_players ((u8 *)0x80126EC0u)
#define foreign ((u8 *)0x801439A0u)
#define passport ((u8 *)0x80137C40u)
#define loaded (*(u32 *)0x80138E44u)
#else
extern AFTravelVisitor af_travel_test_visitor;
extern u8 af_travel_test_players[4*PRIVATE],af_travel_test_foreign[PRIVATE];
extern u8 af_pi_passport[PASSPORT];
extern u32 af_pi_loaded;
#define visitor (&af_travel_test_visitor)
#define native_players af_travel_test_players
#define foreign af_travel_test_foreign
#define passport af_pi_passport
#define loaded af_pi_loaded
#endif
static AFTravelTown town;
static AFTravelSelection selection;
static u8 *arrival;
static int departing,received;
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void put(u8 *p,u32 v) {p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static void copy(u8 *d,const u8 *s,u32 n) {while(n--)*d++=*s++;}
static int equal(const u8 *a,const u8 *b,u32 n) {while(n--)if(*a++!=*b++)return 0;return 1;}
static unsigned resident(const u8 *p) {
    for(unsigned i=0;i<4;i++)if(p==native_players+i*PRIVATE)return i;
    return 4;
}
static unsigned matched(const u8 *identity) {
    for(unsigned i=0;i<4;i++)if(equal(native_players+i*PRIVATE,identity,16))return i;
    return 4;
}
static int guards(void) {
    if(visitor->magic!=AF_TRAVEL_MAGIC || visitor->ready>CACHE_LEGACY ||
       visitor->reserved[0] || visitor->reserved[1])return 0;
    for(unsigned i=0;i<4;i++)if(visitor->guard[i]!=AF_TRAVEL_GUARD)return 0;
    return 1;
}
int af_v3_travel_prepare(void) {
    if(!guards() || !af_travel_storage_idle() || !af_travel_town(&town,&selection) ||
       town.players!=native_players)return 0;
    return !visitor->ready || af_v3_player_records_valid(visitor->record,AF_TP_BYTES,&selection)==AF_SAVE_OK;
}
static unsigned checksum(const u8 *p,unsigned n) {
    unsigned sum=0;for(unsigned i=0;i<n;i+=2)sum+=((unsigned)p[i]<<8)|p[i+1];return sum&65535;
}
static void seal(u8 *p) {
    p[0]=p[1]=0;unsigned sum=(-checksum(p,PASSPORT))&65535;p[0]=sum>>8;p[1]=sum;
}
static u32 crc(const u8 *p,unsigned n) {
    u32 v=~0u;for(unsigned i=0;i<n;i++) {
        v^=p[i];for(unsigned b=0;b<8;b++)v=(v>>1)^(0xEDB88320u&-(v&1));
    }return ~v;
}
/* Return catches explicitly instead of treating a valid old capsule as a full
 * modern record. In particular, returning legacy notes cannot erase diaries. */
static int legacy_catches(const u8 *p,u8 profile[4],u8 caught[4]) {
    const u8 *c=p+CAPSULE;
    for(unsigned i=0;i<4;i++)profile[i]=caught[i]=0;
    if(!word(p+2) && !p[6] && !p[7] && word(c)!=0x41464354u)return 1;
    if(word(p+2)!=0x41465633u || p[6]!='C' || p[7]!='T' ||
       word(c)!=0x41464354u || word(c+4)!=0x00010030u || !equal(c+8,p+8,16) ||
       word(c+32)!=crc(c,32) || word(c+36)!=~word(c+32) || word(c+40) || word(c+44) ||
       (c[26]&254) || c[27])return 0;
    for(unsigned i=0;i<4;i++) {
        if((c[24+i]&~selection.bytes[256+i]) || (c[28+i]&~c[24+i]))return 0;
        profile[i]=c[24+i];caught[i]=c[28+i];
    }return 1;
}
static int target_valid(const u8 *identity);
int af_pi_legacy_validate(unsigned kind,const u8 *p) {
    unsigned n=kind?AF_PAK_BACKUP_NOTE:PASSPORT;
    if(!p || checksum(p,n))return 0;
    if(kind)return 1;
    if(af_pi_null_identity(p+8))return !word(p+2) && !p[6] && !p[7];
    u8 profile[4],caught[4];
    return af_pak_check_private(p+8)==1 && target_valid(p+8) && legacy_catches(p,profile,caught);
}
static int target_valid(const u8 *identity) {
    if(!arrival)return 1;
    unsigned n=resident(arrival);
    return arrival==foreign || (n<4 && equal(arrival,identity,16));
}
int af_pi_record_validate(const AFPakView *v) {
    if(!v || v->kind>1 || v->native_bytes!=(v->kind?AF_PAK_BACKUP_NOTE:PASSPORT) ||
       checksum(v->native,v->native_bytes))return 0;
    if(!v->record_bytes)return af_pi_legacy_validate(v->kind,v->native) &&
        (v->kind || target_valid(v->native+8));
    if(v->record_bytes!=AF_TP_BYTES ||
       af_v3_player_records_valid(v->records,v->record_bytes,&selection)!=AF_SAVE_OK ||
       !equal(v->identity,v->records+16,16))return 0;
    if(v->kind)return 1;
    return word(v->native+2)==0x41465633u && v->native[6]=='P' && v->native[7]=='T' &&
        af_pak_check_private(v->native+8)==1 && !af_pi_null_identity(v->native+8) &&
        equal(v->native+8,v->identity,16) && target_valid(v->identity);
}
static int visitor_matches(const u8 *p) {
    return p==foreign && guards() && visitor->ready && equal(p,visitor->record+16,16) &&
        af_v3_player_records_valid(visitor->record,AF_TP_BYTES,&selection)==AF_SAVE_OK;
}
int af_pi_record_export(unsigned kind,const u8 *p,const AFPakView *previous,
    u8 *staging,u32 capacity,AFPakInput *out) {
    if(kind>1 || !p || !staging || capacity!=AF_TP_BYTES || !out)return 0;
    out->native=p;out->native_bytes=kind?AF_PAK_BACKUP_NOTE:PASSPORT;out->kind=kind;
    static const u8 binding[32]="AFV3-PASSPORT-PLAYER-1";copy(out->binding,binding,32);
    if(!kind)copy(out->identity,p+8,16);
    /* Nonce updates preserve the validated card record. A resident's older
     * home record must not replace the returning traveller's newer record. */
    if(!kind && !departing) {
        if(af_pi_null_identity(p+8))return af_pi_legacy_validate(0,p);
        if(previous && previous->record_bytes && equal(previous->identity,p+8,16)) {
            copy(staging,previous->records,AF_TP_BYTES);
        } else return af_pi_legacy_validate(0,p);
    } else {
        const u8 *identity=kind?af_travel_active():p+8;
        if(!identity || af_pak_check_private(identity)!=1)return 0;
        unsigned n=matched(identity);
        if(n<4) {
            if(af_v3_player_export(staging,AF_TP_BYTES,&town,n,&selection)!=AF_SAVE_OK)return 0;
        } else {
            if(!visitor_matches(foreign) || !equal(identity,foreign,16))return 0;
            copy(staging,visitor->record,AF_TP_BYTES);
            if(af_v3_player_rebind(staging,AF_TP_BYTES,&selection)!=AF_SAVE_OK)return 0;
        }
        copy(out->identity,identity,16);
    }
    out->records=staging;out->record_bytes=AF_TP_BYTES;return 1;
}
void af_pi_legacy_publish(unsigned kind,const u8 *p) {
    if(kind || !arrival)return;
    if(af_pi_null_identity(p+8))return;
    u8 profile[4],caught[4];
    if(!legacy_catches(p,profile,caught))af_v3_save_halt(AF_SAVE_FORMAT);
    if(af_v3_player_blank(visitor->record,AF_TP_BYTES,p+8,&selection)!=AF_SAVE_OK)
        af_v3_save_halt(AF_SAVE_ARGUMENT);
    put(visitor->record+12,AF_TP_UNKNOWN_EDITABLE);
    copy(visitor->record+AF_TP_CREATURES,caught,4);visitor->ready=CACHE_LEGACY;received=1;
}
void af_pi_record_publish(const AFPakView *v) {
    if(v->kind || !arrival)return;
    if(!v->record_bytes) {af_pi_legacy_publish(0,v->native);return;}
    copy(visitor->record,v->records,AF_TP_BYTES);
    if(af_v3_player_rebind(visitor->record,AF_TP_BYTES,&selection)!=AF_SAVE_OK)
        af_v3_save_halt(AF_SAVE_PROFILE_MISSING);
    visitor->ready=(word(visitor->record+12)&AF_TP_UNKNOWN_EDITABLE)?CACHE_LEGACY:CACHE_FULL;received=1;
}
void af_v3_travel_passport_clear(u8 *p) {
    for(unsigned i=0;i<8;i++)p[i]=0;
    af_pak_clear_private(p+8);af_pak_clear_animal(p+0xBD8);
    p[0x1100]=p[0x1101]=255;for(unsigned i=0;i<48;i++)p[CAPSULE+i]=0;
}
int af_v3_travel_passport_save(u8 *priv,const u8 *animal,void *info) {
    if(!priv || !animal || !info || departing || arrival ||
       af_pak_check_private(priv)!=1 || !af_v3_travel_prepare())return 0;
    unsigned n=matched(priv);
    if(n==4 && (!visitor_matches(foreign) || !equal(priv,foreign,16)))return 0;
    copy(passport+8,priv,PRIVATE);copy(passport+0xBD8,animal,0x528);
    put(passport+2,0x41465633u);passport[6]='P';passport[7]='T';
    for(unsigned i=0;i<48;i++)passport[CAPSULE+i]=0;
    af_cw_passport_stage(passport+8);seal(passport);af_pak_set_kind(info,0);
    departing=1;int result=af_v3_pak_native_write(info,passport);departing=0;
    af_cw_passport_complete(priv,result);return result;
}
static void restore(unsigned n) {
    if(af_v3_player_restore(&town,n,visitor->record,AF_TP_BYTES,&selection)!=AF_SAVE_OK)
        af_v3_save_halt(AF_SAVE_BINDING);
}
int af_v3_travel_passport_load(u8 *priv,u8 *animal,void *info) {
    if(!priv || !animal || !info || arrival || departing ||
       (priv!=foreign && resident(priv)==4) || !af_v3_travel_prepare())return 0;
    arrival=priv;received=0;af_pak_set_kind(info,0);
    int result=af_v3_pak_native_read(info,passport);arrival=0;
    if(result!=1 || !received) {loaded=0;return 0;}
    unsigned n=resident(priv);if(n<4)restore(n);
    copy(priv,passport+8,PRIVATE);copy(animal,passport+0xBD8,0x528);loaded=1;return 1;
}
void af_v3_travel_private_copy(u8 *dst,const u8 *src) {
    unsigned n=resident(dst);
    if(n<4 && src==foreign) {
        if(!af_v3_travel_prepare() || !visitor_matches(src) || !equal(dst,src,16))
            af_v3_save_halt(AF_SAVE_BINDING);
        restore(n);
    }
    copy(dst,src,PRIVATE);
}
int af_v3_travel_visitor_collect(u8 *priv,unsigned item,unsigned mark) {
    if(!af_v3_travel_prepare() || !visitor_matches(priv))return AF_SAVE_BINDING;
    return af_v3_player_collect(visitor->record,AF_TP_BYTES,priv,item,mark,&selection);
}
int af_v3_travel_visitor_paper(u8 *priv,unsigned mark) {
    if(!af_v3_travel_prepare() || !visitor_matches(priv))return AF_SAVE_BINDING;
    return af_v3_player_paper(visitor->record,AF_TP_BYTES,priv,mark,&selection);
}
int af_v3_travel_creature_collect(u8 *priv,unsigned item,unsigned mark) {
    if(mark>1 || !((item>=0x2320 && item<=0x2328) ||
       (item>=0x2D20 && item<=0x2D27)))return 0;
    int result=af_v3_travel_visitor_collect(priv,item,mark);
    if(result<0) {if(mark)af_v3_save_halt(result);return 0;}
    return result;
}
