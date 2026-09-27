/* Added catch records follow the native passport's exact player identity.
 * Native private/animal/letter sizes and the Pak file size remain unchanged. */
#include "save_runtime.h"
typedef af_save_u8 u8;
typedef af_save_u32 u32;
enum { PRIVATE=0xBD0, PASSPORT=0x1200, CAPSULE=0x11C0, CAPSULE_BYTES=48 };
struct Visitor { u8 identity[16],profile[4],collected[4]; u32 valid; };
_Static_assert(sizeof(struct Visitor)==28,"Creature visitor-state reservation");
#ifdef __mips__
#define players ((u8 *)0x80126EC0u)
#define foreign ((u8 *)0x801439A0u)
#define passport ((u8 *)0x80137C40u)
#define loaded (*(volatile u32 *)0x80138E44u)
#define state ((struct AfSaveRuntime *)0x8046C000u)
#define visitor (*(struct Visitor *)0x80655FC0u)
#else
extern u8 af_creature_players[4*PRIVATE],af_travel_foreign[PRIVATE],af_travel_passport[PASSPORT];
extern u32 af_travel_loaded;
extern struct AfSaveRuntime af_creature_collection_state;
extern struct Visitor af_travel_visitor;
#define players af_creature_players
#define foreign af_travel_foreign
#define passport af_travel_passport
#define loaded af_travel_loaded
#define state (&af_creature_collection_state)
#define visitor af_travel_visitor
#endif
extern void af_v3_require_save_state(void);
extern void af_v3_save_halt(int) __attribute__((noreturn));
extern void af_pak_set_kind(void *,unsigned);
extern int af_pak_read(void *,void *),af_pak_write(void *,const void *);
extern int af_pak_check_private(const u8 *);
extern void af_pak_clear_private(u8 *),af_pak_clear_animal(u8 *);

static void copy(u8 *d,const u8 *s,unsigned n) {for (unsigned i=0;i<n;i++) d[i]=s[i];}
static int equal(const u8 *a,const u8 *b,unsigned n) {
    for (unsigned i=0;i<n;i++) if (a[i]!=b[i]) return 0;
    return 1;
}
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void put(u8 *p,u32 n) {p[0]=n>>24;p[1]=n>>16;p[2]=n>>8;p[3]=n;}
static u32 crc(const u8 *p,unsigned n) {
    u32 v=~0u;
    for (unsigned i=0;i<n;i++) {
        v^=p[i];
        for (unsigned b=0;b<8;b++) v=(v>>1)^(0xEDB88320u&-(v&1));
    }
    return ~v;
}
static unsigned player(const u8 *p) {
    for (unsigned i=0;i<4;i++) if (p==players+i*PRIVATE) return i;
    return 4;
}
static int valid_bits(const u8 *profile,const u8 *bits) {
    if ((profile[2]&0xFE) || profile[3]) return 0;
    for (unsigned i=0;i<4;i++) if (bits[i]&~profile[i]) return 0;
    return 1;
}
static int supported(const u8 *profile) {
    for (unsigned i=0;i<4;i++) if (profile[i]&~af_v3_creature_profile_byte(i)) return 0;
    return 1;
}
static int visitor_matches(const u8 *p) {
    return p==foreign && visitor.valid==0x41464354 && equal(p,visitor.identity,16) &&
        valid_bits(visitor.profile,visitor.collected) && supported(visitor.profile);
}
static unsigned checksum(const u8 *p) {
    unsigned sum=0;
    for (unsigned i=0;i<PASSPORT;i+=2) sum+=((unsigned)p[i]<<8)|p[i+1];
    return sum&65535;
}
static void seal(u8 *p) {
    p[0]=p[1]=0;unsigned sum=(-checksum(p))&65535;p[0]=sum>>8;p[1]=sum;
}

/* The marker is in unused native header bytes, independently of the trailing
 * capsule. A damaged new header must not be accepted as a legacy passport. */
static int unpack(const u8 *p,struct Visitor *v) {
    const u8 *c=p+CAPSULE;u32 marker=word(p+2);
    if (checksum(p) || !af_pak_check_private(p+8)) return 0;
    for (unsigned i=0;i<sizeof(*v);i++) ((u8 *)v)[i]=0;
    copy(v->identity,p+8,16);
    if (marker==0 && p[6]==0 && p[7]==0 && word(c)!=0x41464354) {
        /* Native passports have no extended record. Never erase a resident's
         * existing catches when a legacy player comes home. */
        v->valid=0x41464354;return 1;
    }
    if (marker!=0x41465633 || p[6]!='C' || p[7]!='T' || word(c)!=0x41464354 ||
        word(c+4)!=0x00010030 || !equal(c+8,p+8,16) ||
        word(c+32)!=crc(c,32) || word(c+36)!=~word(c+32) || word(c+40) || word(c+44) ||
        !valid_bits(c+24,c+28) || !supported(c+24)) return 0;
    copy(v->profile,c+24,4);copy(v->collected,c+28,4);v->valid=0x41464354;return 1;
}
static void pack(u8 *p,const struct Visitor *v) {
    u8 *c=p+CAPSULE;
    put(p+2,0x41465633);p[6]='C';p[7]='T';
    for (unsigned i=0;i<CAPSULE_BYTES;i++) c[i]=0;
    put(c,0x41464354);put(c+4,0x00010030);copy(c+8,v->identity,16);
    copy(c+24,v->profile,4);copy(c+28,v->collected,4);
    put(c+32,crc(c,32));put(c+36,~word(c+32));
}
static void merge_resident(unsigned n,const struct Visitor *v) {
    af_v3_require_save_state();
    u8 *p=state->working+AF_SAVE_CREATURE_OFFSET+4+n*4;
    for (unsigned i=0;i<4;i++) p[i]|=v->collected[i];
}

void af_v3_creature_passport_clear(u8 *p) {
    for (unsigned i=0;i<8;i++) p[i]=0;
    af_pak_clear_private(p+8);af_pak_clear_animal(p+0xBD8);
    p[0x1100]=p[0x1101]=255;
    for (unsigned i=0;i<CAPSULE_BYTES;i++) p[CAPSULE+i]=0;
}

int af_v3_creature_passport_save(u8 *priv,const u8 *animal,void *info) {
    if (!priv || !animal || !af_pak_check_private(priv)) return 0;
    unsigned n=player(priv);struct Visitor v;
    copy(v.identity,priv,16);
    if (n<4) {
        af_v3_require_save_state();
        copy(v.profile,state->working+AF_SAVE_CREATURE_OFFSET,4);
        copy(v.collected,state->working+AF_SAVE_CREATURE_OFFSET+4+n*4,4);
    } else {
        if (!visitor_matches(priv)) return 0;
        copy(v.profile,visitor.profile,4);copy(v.collected,visitor.collected,4);
    }
    /* The passport can carry fish in pockets or letters without a catch event.
     * Preserve the full selected profile, as the town save does, not just the
     * collection bits. Returning to a smaller profile must reject safely. */
    for (unsigned i=0;i<4;i++) v.profile[i]|=af_v3_creature_profile_byte(i);
    if (!valid_bits(v.profile,v.collected) || !supported(v.profile)) return 0;
    /* Validate before modifying a staged passport or starting any Pak I/O. */
    copy(passport+8,priv,PRIVATE);copy(passport+0xBD8,animal,0x528);
    pack(passport,&v);seal(passport);af_pak_set_kind(info,0);
    return af_pak_write(info,passport);
}

int af_v3_creature_passport_load(u8 *priv,u8 *animal,void *info) {
    if (!priv || !animal || (priv!=foreign && player(priv)==4)) return 0;
    af_pak_set_kind(info,0);
    if (af_pak_read(info,passport)!=1) {loaded=0;return 0;}
    struct Visitor v;
    if (!unpack(passport,&v)) {loaded=0;return 0;}
    unsigned n=player(priv);
    /* Complete validation precedes both the native copies and extended state. */
    if (n<4) {
        if (!equal(priv,v.identity,16)) return 0;
        merge_resident(n,&v);
    } else copy((u8 *)&visitor,(const u8 *)&v,sizeof(v));
    copy(priv,passport+8,PRIVATE);copy(animal,passport+0xBD8,0x528);loaded=1;
    return 1;
}

void af_v3_creature_private_copy(u8 *dst,const u8 *src) {
    unsigned n=player(dst);
    if (n<4 && src==foreign) {
        if (!visitor_matches(src) || !equal(dst,src,16)) af_v3_save_halt(AF_SAVE_BINDING);
        merge_resident(n,&visitor);
    }
    copy(dst,src,PRIVATE);
}

int af_v3_creature_visitor_collect(u8 *priv,unsigned item,unsigned mark) {
    unsigned i=item>=0x2320 && item<=0x2328 ? item-0x2320 :
        item>=0x2D20 && item<=0x2D27 ? item-0x2D20+9 : 17;
    if (i>=17 || mark>1) return 0;
    if (!visitor_matches(priv)) {
        if (mark) af_v3_save_halt(AF_SAVE_ARGUMENT);
        return 0;
    }
    unsigned byte=i/8,bit=1u<<(i&7);
    if (!(af_v3_creature_profile_byte(byte)&bit)) return 0;
    if (mark) {visitor.profile[byte]|=bit;visitor.collected[byte]|=bit;}
    return !!(visitor.collected[byte]&bit);
}
