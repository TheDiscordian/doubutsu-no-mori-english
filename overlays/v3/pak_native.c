#include "pak_native.h"
typedef af_pak_u8 u8;
typedef af_pak_u32 u32;
typedef __UINTPTR_TYPE__ address;
enum { STATE=0x74, ERROR=0x70, EXT=10, MISSING=5, FULL=7, DIRFULL=8 };
#ifdef __mips__
#define passport ((u8 *)0x80137C40u)
#define loaded (*(u32 *)0x80138E44u)
#define serial_queue (*(void **)0x80138E40u)
#else
extern u8 af_pi_passport[AF_PAK_PRIVATE_NOTE];
extern u32 af_pi_loaded;
extern void *af_pi_serial_queue;
#define passport af_pi_passport
#define loaded af_pi_loaded
#define serial_queue af_pi_serial_queue
#endif
struct Slot {u32 bytes,generation;int present,uncommitted;};
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void put(u8 *p,u32 v) {p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static void copy(u8 *d,const u8 *s,u32 n) {while(n--)*d++=*s++;}
static void zero(u8 *p,u32 n) {while(n--)*p++=0;}
static int equal(const u8 *a,const u8 *b,u32 n) {while(n--)if(*a++!=*b++)return 0;return 1;}
static int separate(const void *a,u32 an,const void *b,u32 bn) {
    address x=(address)a,y=(address)b;
    if(an>(address)-1-x || bn>(address)-1-y)return 0;
    return x<=y?y-x>=an:x-y>=bn;
}
static int external(const AFPIWorkspace *w,const void *p,u32 n) {
    return p && separate(p,n,w->notes[0],AF_PI_NOTE) &&
        separate(p,n,w->notes[1],AF_PI_NOTE) && separate(p,n,w->raw,AF_PI_RAW) &&
        separate(p,n,w->hash,AF_PAK_HASH_BYTES) && separate(p,n,w->binding,32);
}
static int workspace_valid(const AFPIWorkspace *w) {
    return w->notes[0] && w->notes[1] && w->raw && w->hash && w->binding &&
        !((address)w->hash&3) &&
        separate(w->notes[0],AF_PI_NOTE,w->notes[1],AF_PI_NOTE) &&
        separate(w->notes[0],AF_PI_NOTE,w->raw,AF_PI_RAW) &&
        separate(w->notes[1],AF_PI_NOTE,w->raw,AF_PI_RAW) &&
        separate(w->hash,AF_PAK_HASH_BYTES,w->notes[0],AF_PI_NOTE) &&
        separate(w->hash,AF_PAK_HASH_BYTES,w->notes[1],AF_PI_NOTE) &&
        separate(w->hash,AF_PAK_HASH_BYTES,w->raw,AF_PI_RAW) &&
        separate(w->binding,32,w->notes[0],AF_PI_NOTE) &&
        separate(w->binding,32,w->notes[1],AF_PI_NOTE) &&
        separate(w->binding,32,w->raw,AF_PI_RAW) &&
        separate(w->binding,32,w->hash,AF_PAK_HASH_BYTES) &&
        external(w,w,sizeof(*w));
}
static u32 header_crc(const u8 *p) {
    u32 v=~0u;
    for(u32 i=0;i<AF_PI_PAGE;i++) {
        v^=i>=24 && i<28?0:p[i];
        for(u32 b=0;b<8;b++)v=(v>>1)^(0xEDB88320u&-(v&1));
    }
    return ~v;
}
static u32 native_bytes(unsigned kind) {return kind?AF_PAK_BACKUP_NOTE:AF_PAK_PRIVATE_NOTE;}
static int kind_of(const u8 *info) {
    u32 n=word(info+STATE);
    int kind=n==AF_PAK_PRIVATE_NOTE?0:n==AF_PAK_BACKUP_NOTE?1:-1;
    return kind>=0 && info[STATE+EXT]==0x1A+kind?kind:-1;
}
static void select_slot(u8 *info,const u8 original[32],unsigned kind,unsigned slot) {
    copy(info+STATE,original,32);
    u8 *e=info+STATE+EXT;e[0]=0x1A+kind;e[1]=0x1F;e[2]=3;e[3]=slot+1;
}
static int slot_read(u8 *info,const u8 original[32],unsigned kind,unsigned index,
    u8 *out,struct Slot *slot) {
    slot->bytes=slot->generation=0;slot->present=slot->uncommitted=0;
    select_slot(info,original,kind,index);
    if(af_pi_open(info)!=1)return word(info+ERROR)==MISSING?0:-1;
    slot->present=1;
    u32 bytes=af_pi_file_state(info+4,info+STATE);
    /* FileState returns the actual allocation; never load the logical length
     * into a physical buffer or trust a name search as a size check. */
    if(!bytes)return -1;
    u8 expected[32];copy(expected,original,32);
    expected[EXT]=0x1A+kind;expected[EXT+1]=0x1F;expected[EXT+2]=3;expected[EXT+3]=index+1;
    if(!equal(info+STATE+4,expected+4,26))return -1;
    slot->bytes=bytes;
    if(bytes<2*AF_PI_PAGE || bytes>AF_PI_NOTE || bytes%AF_PI_PAGE)return 0;
    if(af_pi_load(info+4,0,(int)bytes,out)!=1)return -1;
    slot->uncommitted=1;
    for(u32 i=0;i<AF_PI_PAGE;i++)if(out[i]) {slot->uncommitted=0;break;}
    if(word(out)!=0x41464A31 || word(out+4)!=1 || !word(out+8) ||
       word(out+12)!=~word(out+8) || word(out+16)!=kind ||
       word(out+20)!=bytes-AF_PI_PAGE || word(out+24)!=header_crc(out))return 0;
    for(u32 i=28;i<AF_PI_PAGE;i++)if(out[i])return 0;
    slot->generation=word(out+8);return 1;
}
static int scan(u8 *info,const u8 original[32],unsigned kind,const AFPIWorkspace *w,
    struct Slot slots[2]) {
    if(slot_read(info,original,kind,0,w->notes[0],slots)<0 ||
       slot_read(info,original,kind,1,w->notes[1],slots+1)<0)return -2;
    if(slots[0].generation && slots[1].generation &&
       slots[0].generation==slots[1].generation)return -2;
    if(!slots[0].generation && !slots[1].generation)
        return (slots[0].present && !slots[0].uncommitted) ||
            (slots[1].present && !slots[1].uncommitted)?-2:-1;
    return slots[1].generation>slots[0].generation?1:0;
}
static int decode(unsigned kind,unsigned slot,const AFPIWorkspace *w,
    const struct Slot *s,AFPakView *v) {
    if(af_v3_pak_decode(w->notes[slot]+AF_PI_PAGE,s->bytes-AF_PI_PAGE,
        w->binding,0,w->raw,AF_PI_RAW,v)<0 || v->kind!=kind ||
       v->native_bytes!=native_bytes(kind))return 0;
    return af_pi_record_validate(v)==1;
}
/* 1 valid new note, 2 valid legacy note, 0 missing, -1 rejected/device error.
 * Missing or incompatible frames never reach the original auto-delete path. */
static int read_locked(u8 *info,const u8 original[32],unsigned kind,
    const AFPIWorkspace *w,AFPakView *v) {
    struct Slot slots[2];int selected=scan(info,original,kind,w,slots);
    if(selected>=0)return decode(kind,(unsigned)selected,w,slots+selected,v)?1:-1;
    if(selected!=-1)return -1;
    copy(info+STATE,original,32);
    if(af_pi_open(info)!=1)return word(info+ERROR)==MISSING?0:-1;
    u32 bytes=af_pi_file_state(info+4,info+STATE);
    if(bytes!=native_bytes(kind) || !equal(info+STATE+4,original+4,26) ||
       af_pi_load(info+4,0,(int)bytes,w->raw)!=1 ||
       af_pi_legacy_validate(kind,w->raw)!=1)return -1;
    return 2;
}
static int read_common(u8 *info,u8 *out,unsigned kind,const AFPIWorkspace *w,int *missing) {
    u8 original[32];copy(original,info+STATE,32);AFPakView view;
    int result=read_locked(info,original,kind,w,&view);
    if(missing)*missing=result==0;
    if(result==1) {
        af_pi_record_publish(&view);copy(out,view.native,native_bytes(kind));
    } else if(result==2) {
        af_pi_legacy_publish(kind,w->raw);copy(out,w->raw,native_bytes(kind));
    }
    copy(info+STATE,original,32);
    return result>0;
}
int af_v3_pak_native_read(void *opaque,void *output) {
    u8 *info=opaque,*out=output;AFPIWorkspace w;
    if(!info || !out || kind_of(info)<0 || !af_pi_workspace_acquire(&w))return 0;
    int result=0;
    if(workspace_valid(&w) && external(&w,info,0x2E0) &&
       external(&w,out,native_bytes((unsigned)kind_of(info))) &&
       separate(info,0x2E0,out,native_bytes((unsigned)kind_of(info)))) {
        serial_queue=af_pi_lock();
        result=read_common(info,out,(unsigned)kind_of(info),&w,0);
        af_pi_unlock(serial_queue);
    }
    return af_pi_workspace_release()==1?result:0;
}
static int write_locked(u8 *info,const u8 *native,unsigned kind,const AFPIWorkspace *w) {
    u8 original[32];copy(original,info+STATE,32);
    struct Slot slots[2];AFPakView previous;AFPakInput input;
    int result=0,made=0,committed=0;unsigned target=0;
    int selected=scan(info,original,kind,w,slots);
    if(selected==-2 || (selected>=0 && !decode(kind,(unsigned)selected,w,slots+selected,&previous)))goto done;
    zero((u8 *)&input,sizeof(input));
    if(af_pi_record_export(kind,native,&input)!=1 || input.kind!=kind ||
       input.native!=native || input.native_bytes!=native_bytes(kind) ||
       !equal(input.binding,w->binding,32) ||
       (input.record_bytes && !external(w,input.records,input.record_bytes)))goto done;
    int framed=af_v3_pak_measure(&input,AF_PI_NOTE-AF_PI_PAGE,w->hash,AF_PAK_HASH_BYTES);
    if(framed<0)goto done;
    target=selected<0?0:1-(unsigned)selected;
    u32 bytes=(u32)framed+AF_PI_PAGE,generation=selected<0?1:slots[selected].generation+1;
    if(!generation)goto done;
    u8 *note=w->notes[target];
    if(af_v3_pak_encode(note+AF_PI_PAGE,AF_PI_NOTE-AF_PI_PAGE,&input,w->hash,AF_PAK_HASH_BYTES)!=framed)goto done;
    /* Semantic validation precedes any deletion/allocation/write. */
    AFPakView check;
    if(af_v3_pak_decode(note+AF_PI_PAGE,(u32)framed,w->binding,0,w->raw,AF_PI_RAW,&check)<0 ||
       af_pi_record_validate(&check)!=1)goto done;
    if(af_pi_num(info)!=1 || af_pi_free(info)!=1)goto done;
    if(word(info+0x2D4)+slots[target].bytes<bytes) {put(info+ERROR,FULL);goto done;}
    if(!slots[target].present && word(info+0x2DC)>=word(info+0x2D8)) {put(info+ERROR,DIRFULL);goto done;}
    select_slot(info,original,kind,target);
    /* Only the older slot is reclaimed; the selected successful note and all
     * legacy/unrelated notes remain intact throughout a failed new write. */
    if(slots[target].present && af_pi_delete(info+4,info+STATE)!=1)goto done;
    put(info+STATE,bytes);
    if(af_pi_make(info)!=1)goto done;
    made=1;
    zero(note,AF_PI_PAGE);
    if(af_pi_save(info+4,0,AF_PI_PAGE,note)!=1 ||
       af_pi_save(info+4,AF_PI_PAGE,framed,note+AF_PI_PAGE)!=1 ||
       af_pi_load(info+4,AF_PI_PAGE,framed,w->notes[1-target])!=1 ||
       !equal(note+AF_PI_PAGE,w->notes[1-target],(u32)framed))goto done;
    put(note,0x41464A31);put(note+4,1);put(note+8,generation);put(note+12,~generation);
    put(note+16,kind);put(note+20,(u32)framed);put(note+24,header_crc(note));
    /* Commit last. A torn payload has no committed header and cannot replace
     * the preceding note. Read back the complete physical note before success. */
    if(af_pi_save(info+4,0,AF_PI_PAGE,note)!=1)goto done;
    committed=1;
    if(af_pi_load(info+4,0,(int)bytes,w->notes[1-target])!=1 ||
       !equal(note,w->notes[1-target],bytes))goto done;
    result=1;
done:
    if(made && !committed) {
        /* Reclaim only this attempt's uncommitted allocation. In particular,
         * a failed first header write need not leave an unreadable note which
         * prevents retrying. Device removal may prevent cleanup; the preceding
         * successful note remains untouched in that case as well. */
        u32 error=word(info+ERROR);select_slot(info,original,kind,target);
        (void)af_pi_delete(info+4,info+STATE);put(info+ERROR,error);
    }
    copy(info+STATE,original,32);return result;
}
int af_v3_pak_native_write(void *opaque,const void *source) {
    u8 *info=opaque;const u8 *native=source;AFPIWorkspace w;
    if(!info || !native || kind_of(info)<0 || !af_pi_workspace_acquire(&w))return 0;
    int result=0;
    if(workspace_valid(&w) && external(&w,info,0x2E0) &&
       external(&w,native,native_bytes((unsigned)kind_of(info)))) {
        serial_queue=af_pi_lock();
        result=write_locked(info,native,(unsigned)kind_of(info),&w);
        af_pi_unlock(serial_queue);
    }
    return af_pi_workspace_release()==1?result:0;
}
int af_v3_pak_native_status(int *status,int kind,void *opaque,void *backup) {
    u8 *info=opaque;AFPIWorkspace w;
    u8 *out=kind?(u8 *)backup:passport;
    if(!status || !info || kind<0 || kind>1 || kind_of(info)!=kind || !out ||
       !separate(status,sizeof(*status),info,0x2E0) ||
       !separate(status,sizeof(*status),out,native_bytes((unsigned)kind)) ||
       !separate(info,0x2E0,out,native_bytes((unsigned)kind)) ||
       !af_pi_workspace_acquire(&w))return 0;
    int result=0,missing=0;
    if(workspace_valid(&w) && external(&w,info,0x2E0) && external(&w,status,sizeof(*status)) &&
       external(&w,out,native_bytes((unsigned)kind))) {
        *status=5;
        serial_queue=af_pi_lock();
        if(read_common(info,out,(unsigned)kind,&w,&missing)) {
            if(!kind && !af_pi_null_identity(out+8)) {loaded=1;*status=0;}
            else *status=2;
            result=1;
        } else if(missing && af_pi_num(info)==1) {
            if(word(info+0x2DC)>=word(info+0x2D8)) {*status=4;result=1;}
            else if(af_pi_free(info)==1) {
                /* Exact compressed size depends on the staged departing
                 * record. The write entry measures it before touching a note. */
                *status=word(info+0x2D4)>=2*AF_PI_PAGE?1:3;result=1;
            }
        }
        af_pi_unlock(serial_queue);
    }
    return af_pi_workspace_release()==1?result:0;
}
