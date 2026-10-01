#include "../overlays/v3/pak_native.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef af_pak_u8 u8;
typedef af_pak_u32 u32;
enum { STATE=0x74, ERROR=0x70, FILE_NO=0x6C, EXT=10, FILES=16 };
struct File {u8 name[26],bytes[AF_PI_NOTE];u32 size;int used;};
static struct File files[FILES];
static u8 scratch[AF_PI_SCRATCH],info[0x2E0],native[AF_PAK_BACKUP_NOTE];
static u8 output[AF_PAK_BACKUP_NOTE],before[AF_PAK_BACKUP_NOTE];
static u8 records[14204],published[14204],bound[32];
static u32 hash[AF_PAK_HASH_WORDS];
static int busy,locked,publish_count,fail_save,save_calls,fail_load,load_calls;
static int fail_open,fail_make,fail_delete,fail_state,invalid_record,invalid_legacy;
static int acquire_fail,release_fail,fail_free,fail_num;
static u32 free_limit;
u8 af_pi_passport[AF_PAK_PRIVATE_NOTE];
u32 af_pi_loaded;
void *af_pi_serial_queue;
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void put(u8 *p,u32 n) {p[0]=n>>24;p[1]=n>>16;p[2]=n>>8;p[3]=n;}
static u32 used(void) {u32 n=0;for(int i=0;i<FILES;i++)if(files[i].used)n+=files[i].size;return n;}
static void reset(unsigned kind) {
    assert(!busy && !locked);memset(files,0,sizeof(files));memset(info,0,sizeof(info));
    memset(scratch,0,sizeof(scratch));memset(records,0,sizeof(records));
    for(u32 i=0;i<sizeof(records);i++)records[i]=(u8)(i%19);
    for(u32 i=0;i<sizeof(native);i++)native[i]=(u8)(i%31);
    for(u32 i=0;i<32;i++)bound[i]=(u8)(i+4);
    put(info+STATE,kind?AF_PAK_BACKUP_NOTE:AF_PAK_PRIVATE_NOTE);
    put(info+STATE+4,0x4E41464A);info[STATE+8]=info[STATE+9]=0x30;
    info[STATE+EXT]=0x1A+kind;memcpy(info+STATE+14,"ANIMAL FOREST   ",16);
    free_limit=AF_PI_NOTE;publish_count=save_calls=load_calls=0;af_pi_loaded=0;
    fail_save=fail_load=fail_open=fail_make=fail_delete=fail_state=0;
    invalid_record=invalid_legacy=acquire_fail=release_fail=fail_free=fail_num=0;
}
int af_pi_workspace_acquire(AFPIWorkspace *w) {
    if(acquire_fail || busy)return 0;
#ifdef AF_TEST_REAL_TRAVEL
    if(!af_v3_travel_prepare())return 0;
#endif
    busy=1;w->notes[0]=scratch;w->notes[1]=scratch+AF_PI_NOTE;
    w->raw=scratch+2*AF_PI_NOTE;w->staging=w->raw+AF_PI_RAW;
    w->hash=hash;w->binding=bound;return 1;
}
int af_pi_workspace_release(void) {assert(busy && !locked);busy=0;return !release_fail;}
#ifndef AF_TEST_REAL_TRAVEL
int af_pi_record_export(unsigned kind,const u8 *source,const AFPakView *prior,
    u8 *staging,u32 capacity,AFPakInput *p) {
    (void)prior;assert(capacity>=sizeof(records));memcpy(staging,records,sizeof(records));
    p->kind=kind;p->native=source;p->native_bytes=kind?AF_PAK_BACKUP_NOTE:AF_PAK_PRIVATE_NOTE;
    p->records=staging;p->record_bytes=sizeof(records);
    memcpy(p->binding,bound,32);memcpy(p->identity,kind?records:source+8,16);return 1;
}
int af_pi_record_validate(const AFPakView *p) {
    if(invalid_record || p->record_bytes!=sizeof(records))return 0;
    /* The native adapter must call this before publishing any caller bytes. */
    return 1;
}
int af_pi_legacy_validate(unsigned kind,const u8 *source) {(void)kind;(void)source;return !invalid_legacy;}
void af_pi_record_publish(const AFPakView *p) {memcpy(published,p->records,sizeof(published));publish_count++;}
void af_pi_legacy_publish(unsigned kind,const u8 *p) {(void)kind;(void)p;memset(published,0,sizeof(published));publish_count++;}
#endif
void *af_pi_lock(void) {assert(!locked && busy);locked=1;return info;}
void af_pi_unlock(void *q) {assert(locked && q==info);locked=0;}
int af_pi_open(void *opaque) {
    assert(locked && opaque==info);
    if(fail_open) {put(info+ERROR,1);return 0;}
    for(int i=0;i<FILES;i++)if(files[i].used && !memcmp(files[i].name,info+STATE+4,26)) {
        put(info+FILE_NO,(u32)i);put(info+ERROR,0);return 1;
    }
    put(info+ERROR,5);return 0;
}
int af_pi_make(void *opaque) {
    assert(locked && opaque==info);
    u32 n=word(info+STATE);
    if(fail_make || used()+n>free_limit) {put(info+ERROR,7);return 0;}
    for(int i=0;i<FILES;i++)if(!files[i].used) {
        files[i].used=1;files[i].size=n;memcpy(files[i].name,info+STATE+4,26);
        /* The actual allocator does not promise fresh zero bytes. */
        memset(files[i].bytes,0xD5,sizeof(files[i].bytes));
        put(info+FILE_NO,(u32)i);put(info+ERROR,0);return 1;
    }
    put(info+ERROR,8);return 0;
}
unsigned af_pi_file_state(void *pfs,void *state) {
    assert(locked && pfs==info+4 && state==info+STATE);
    if(fail_state) {put(info+ERROR,1);return 0;}
    struct File *f=files+word(info+FILE_NO);assert(f->used);
    put(state,f->size);memcpy((u8 *)state+4,f->name,26);put(info+ERROR,0);return f->size;
}
int af_pi_load(void *pfs,int offset,int bytes,u8 *out) {
    assert(locked && pfs==info+4);struct File *f=files+word(info+FILE_NO);
    assert(f->used && offset>=0 && bytes>0 && (u32)(offset+bytes)<=f->size);
    load_calls++;if(fail_load==load_calls) {put(info+ERROR,1);return 0;}
    memcpy(out,f->bytes+offset,(unsigned)bytes);put(info+ERROR,0);return 1;
}
int af_pi_save(void *pfs,int offset,int bytes,const u8 *source) {
    assert(locked && pfs==info+4);struct File *f=files+word(info+FILE_NO);
    assert(f->used && offset>=0 && bytes>0 && (u32)(offset+bytes)<=f->size);
    save_calls++;
    if(fail_save==save_calls) {put(info+ERROR,1);return 0;}
    memcpy(f->bytes+offset,source,(unsigned)bytes);put(info+ERROR,0);return 1;
}
int af_pi_delete(void *pfs,void *state) {
    assert(locked && pfs==info+4 && state==info+STATE);
    if(fail_delete) {put(info+ERROR,1);return 0;}
    for(int i=0;i<FILES;i++)if(files[i].used && !memcmp(files[i].name,info+STATE+4,26)) {
        files[i].used=0;return 1;
    }
    return 0;
}
int af_pi_num(void *opaque) {
    assert(locked && opaque==info);if(fail_num)return 0;
    u32 n=0;for(int i=0;i<FILES;i++)n+=!!files[i].used;
    put(info+0x2D8,FILES);put(info+0x2DC,n);return 1;
}
int af_pi_free(void *opaque) {
    assert(locked && opaque==info);if(fail_free)return 0;
    put(info+0x2D4,free_limit-used());put(info+ERROR,0);return 1;
}
int af_pi_null_identity(const u8 *p) {for(u32 i=0;i<16;i++)if(p[i])return 0;return 1;}
static void state_retained(const u8 *state) {assert(!memcmp(state,info+STATE,32));assert(!busy && !locked);}
static void roundtrip(unsigned kind) {
    reset(kind);u8 state[32];memcpy(state,info+STATE,32);
    u32 n=word(info+STATE);int status=-1;
    assert(af_v3_pak_native_status(&status,(int)kind,info,output)==1 && status==1);
    assert(af_v3_pak_native_write(info,native)==1);state_retained(state);
    memset(output,0xAA,sizeof(output));
    assert(af_v3_pak_native_read(info,output)==1);state_retained(state);
    assert(!memcmp(native,output,n) && !memcmp(published,records,sizeof(records)));
    native[33]++;records[111]++;
    assert(af_v3_pak_native_write(info,native)==1);
    native[34]++;records[112]++;
    assert(af_v3_pak_native_write(info,native)==1);
    assert(af_v3_pak_native_read(info,output)==1);
    assert(!memcmp(native,output,n) && !memcmp(published,records,sizeof(records)));
    assert(af_v3_pak_native_status(&status,(int)kind,info,output)==1 && status==(kind?2:0));
    if(!kind)assert(af_pi_loaded && !memcmp(af_pi_passport,native,n));
    state_retained(state);
}
static void failures(unsigned kind) {
    reset(kind);u8 state[32];memcpy(state,info+STATE,32);u32 n=word(info+STATE);
    assert(af_v3_pak_native_write(info,native)==1);memcpy(before,native,n);
    native[33]++;records[111]++;
    for(int failure=1;failure<=3;failure++) {
        save_calls=0;fail_save=failure;
        assert(af_v3_pak_native_write(info,native)==0);state_retained(state);fail_save=0;
        assert(af_v3_pak_native_read(info,output)==1 && !memcmp(before,output,n));
    }
    fail_make=1;assert(!af_v3_pak_native_write(info,native));fail_make=0;
    assert(af_v3_pak_native_read(info,output)==1 && !memcmp(before,output,n));
    free_limit=used();u32 random=51;
    for(u32 i=0;i<sizeof(records);i++) {random=random*1664525+1013904223;records[i]=(u8)(random>>24);}
    assert(!af_v3_pak_native_write(info,native));free_limit=AF_PI_NOTE;
    for(u32 i=0;i<sizeof(records);i++)records[i]=(u8)(i%19);
    records[111]++;
    assert(af_v3_pak_native_read(info,output)==1 && !memcmp(before,output,n));
    fail_open=1;memset(output,0xAA,n);int count=publish_count;
    assert(!af_v3_pak_native_read(info,output));fail_open=0;
    for(u32 i=0;i<n;i++)assert(output[i]==0xAA);
    assert(publish_count==count);state_retained(state);
    for(int mode=0;mode<4;mode++) {
        if(mode==0)invalid_record=1;
        if(mode==1)bound[0]^=1;
        if(mode==2)fail_state=1;
        if(mode==3) {load_calls=0;fail_load=1;}
        assert(!af_v3_pak_native_read(info,output));
        assert(publish_count==count);for(u32 i=0;i<n;i++)assert(output[i]==0xAA);
        invalid_record=fail_state=fail_load=0;if(mode==1)bound[0]^=1;
        state_retained(state);
    }
    assert(af_v3_pak_native_write(info,native)==1);memcpy(before,native,n);
    native[33]++;records[111]++;
    fail_delete=1;assert(!af_v3_pak_native_write(info,native));fail_delete=0;
    assert(af_v3_pak_native_read(info,output)==1 && !memcmp(before,output,n));
    assert(af_v3_pak_native_write(info,native)==1);
    assert(af_v3_pak_native_read(info,output)==1 && !memcmp(native,output,n));
    state_retained(state);
}
static void legacy(unsigned kind) {
    reset(kind);u8 state[32];memcpy(state,info+STATE,32);u32 n=word(info+STATE);
    files[0].used=1;files[0].size=n;memcpy(files[0].name,info+STATE+4,26);
    memcpy(files[0].bytes,native,n);
    assert(af_v3_pak_native_read(info,output)==1 && !memcmp(output,native,n));
    native[33]++;
    /* A fresh-format write never deletes or rewrites the native legacy note. */
    assert(af_v3_pak_native_write(info,native)==1);
    assert(files[0].used && !memcmp(files[0].name,state+4,26) && files[0].bytes[33]!=native[33]);
    assert(af_v3_pak_native_read(info,output)==1 && !memcmp(output,native,n));
    files[1].bytes[AF_PI_PAGE+40]^=1;
    memset(output,0xAA,n);int count=publish_count;
    assert(!af_v3_pak_native_read(info,output));
    assert(publish_count==count);for(u32 i=0;i<n;i++)assert(output[i]==0xAA);
    state_retained(state);
}
static void first_write_recovery(void) {
    for(int step=1;step<=3;step++) {
        reset(0);fail_save=step;
        assert(!af_v3_pak_native_write(info,native));fail_save=0;
        assert(!used());
        assert(af_v3_pak_native_write(info,native)==1);
        assert(af_v3_pak_native_read(info,output)==1);
    }
}
static void both_notes(void) {
    reset(0);assert(af_v3_pak_native_write(info,native)==1);
    put(info+STATE,AF_PAK_BACKUP_NOTE);info[STATE+EXT]=0x1B;
    assert(af_v3_pak_native_write(info,native)==1);
    assert(af_v3_pak_native_read(info,output)==1 && !memcmp(output,native,AF_PAK_BACKUP_NOTE));
    put(info+STATE,AF_PAK_PRIVATE_NOTE);info[STATE+EXT]=0x1A;
    assert(af_v3_pak_native_read(info,output)==1 && !memcmp(output,native,AF_PAK_PRIVATE_NOTE));
}
static void admission_errors(void) {
    reset(0);int status=-1;free_limit=0;
    assert(af_v3_pak_native_status(&status,0,info,0)==1 && status==3);
    assert(!af_v3_pak_native_write(info,native) && !used());
    free_limit=AF_PI_NOTE;
    fail_num=1;assert(!af_v3_pak_native_write(info,native) && !used());fail_num=0;
    fail_free=1;assert(!af_v3_pak_native_write(info,native) && !used());fail_free=0;
    acquire_fail=1;assert(!af_v3_pak_native_read(info,output));acquire_fail=0;
    busy=1;assert(!af_v3_pak_native_write(info,native));busy=0;
    for(int i=0;i<FILES;i++) {files[i].used=1;files[i].size=256;memset(files[i].name,0xC1,26);}
    assert(af_v3_pak_native_status(&status,0,info,0)==1 && status==4);
    assert(!af_v3_pak_native_write(info,native));
    for(int i=0;i<FILES;i++)assert(files[i].used && files[i].name[0]==0xC1);
    reset(0);assert(af_v3_pak_native_write(info,native));
    files[0].size=AF_PI_NOTE+AF_PI_PAGE;int count=publish_count;
    memset(output,0xAA,sizeof(output));
    assert(!af_v3_pak_native_read(info,output));assert(publish_count==count);
    for(u32 i=0;i<sizeof(output);i++)assert(output[i]==0xAA);
}
int main(void) {
    for(unsigned kind=0;kind<2;kind++) {roundtrip(kind);failures(kind);legacy(kind);}
    first_write_recovery();both_notes();admission_errors();
    puts("Native read/write/status callers, both note kinds, commit-last device failures, bounded physical reads, and original-note preservation passed");
    return 0;
}
