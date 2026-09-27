/* Shared native iNES lifecycle. QD engine support remains a separate dependency.
 * Original IDs 0..7 retain their original data, score logic, and allocation. */
#include "console_image.h"
typedef unsigned char u8;
typedef unsigned int u32;
#define BASE 0x8082A070u
#define MAGIC 0x41464E45u
#define GUARD 0x4E455321u
typedef struct {
    u32 magic,base,game,player,image_bytes,error;
    u8 *image,*emulator,*battery_copy;
    AFConsoleSave save;
    AFConsoleImageWork input;
    u32 guard[4];
} Session;
_Static_assert(sizeof(Session)<=0x800,"Console session exceeds reservation");
#ifdef __mips__
#define MEMORY(at) ((void *)(at))
#define FN(at,type,...) ((type (*)(__VA_ARGS__))(at))
#define CALLER ((u32)__builtin_return_address(0))
#define af_console_saved_players() FN(AF_CONSOLE_SAVED_PLAYERS,u8 *,void)()
#define af_console_storage_valid() FN(AF_CONSOLE_STORAGE_VALID,int,void)()
#else
extern void *af_console_test_memory(u32);
extern void *af_console_test_function(u32);
extern u32 af_console_test_caller;
#define MEMORY(at) af_console_test_memory(at)
#define FN(at,type,...) ((type (*)(__VA_ARGS__))af_console_test_function(at))
#define CALLER af_console_test_caller
extern u8 *af_console_saved_players(void);
extern int af_console_storage_valid(void);
#endif
#define session ((Session *)MEMORY(0x804FE820u))
#define metadata ((const u8 *)MEMORY(0x804FC820u))
extern int af_v3_console_image_native_load(u32,void *,u32,AFConsoleImageWork *);
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void clear(void *p,u32 n) {u8 *b=p;while(n--)*b++=0;}
static void copy(u8 *d,const u8 *s,u32 n) {while(n--)*d++=*s++;}
static u32 native_address(u32 linked) {return session->base+linked-BASE;}
static u32 *global(u32 linked) {return MEMORY(native_address(linked));}
static int valid(void) {
    if(session->magic!=MAGIC || (session->base&15) || session->base<0x80000400u ||
       session->base>0x80400000u-0x2E990u)return 0;
    for(u32 i=0;i<4;i++)if(session->guard[i]!=GUARD)return 0;
    return 1;
}
static void *allocate(u32 n) {return FN(native_address(0x8082A814u),void *,u32)(n);}
static int imported(void) {return valid() && session->game>7;}

void *af_v3_console_graphics(u32 requested) {
    u32 base=CALLER-(0x8082E0E0u-BASE),size=requested;
    clear(session,sizeof(*session));session->magic=MAGIC;session->base=base;
    for(u32 i=0;i<4;i++)session->guard[i]=GUARD;
    session->game=*(u8 *)MEMORY(0x80137898u);
    session->player=*(u8 *)MEMORY(0x80136EA3u);
    if(!valid() || requested!=0x25008u) {
        session->magic=0;
        return 0;
    }
    if(session->game>7) {
        if(session->game>19 || session->player>=4 ||
            af_v3_console_validate(metadata,AF_CONSOLE_METADATA_BYTES)<0)session->error=1;
        else {
            const u8 *entry=metadata+32+(session->game-1)*64;
            const u8 *header=metadata+word(entry+16);
            session->image_bytes=word(entry+20);
            if(word(entry+4)!=1)session->error=2; /* Full QD image, no disk engine yet. */
            else {
                u32 required=0x2008u+((u32)header[5]<<13);
                if(required>size)size=required;
            }
        }
    }
    return allocate(size);
}

void *af_v3_console_setup(void) {
    if(!valid())return 0;
    if(!imported())return FN(native_address(0x8082D29Cu),void *,void)();
    if(session->error || !af_console_storage_valid() ||
        !*global(0x80854A08u) || !*global(0x80854A10u) || !*global(0x80854A14u))return 0;
    session->image=allocate(session->image_bytes);
    session->battery_copy=allocate(AF_CONSOLE_BATTERY_BYTES);
    if(!session->image || !session->battery_copy ||
        af_v3_console_image_native_load(session->game,session->image,session->image_bytes,&session->input)) {
        session->error=3;return 0;
    }
    /* Native B834 already clears all optional tag/container pointers. Leave them
     * null: donor recipes are interpreted by the common executor, not N64 tags. */
    *global(0x80854B78u)=(u32)(__UINTPTR_TYPE__)session->image;
    *global(0x80854B74u)=session->image_bytes;
    *global(0x80854B7Cu)=(u32)(__UINTPTR_TYPE__)(session->image+session->image_bytes);
    return session->image;
}

void af_v3_console_initialize(u8 *state,void *header,void *graphics,u8 *image) {
    if(!valid())return;
    FN(native_address(0x8082A6ECu),void,u8 *,void *,void *,u8 *)(state,header,graphics,image);
    if(!imported())return;
    session->emulator=state;
    int result=af_v3_console_open_loaded(&session->save,metadata,AF_CONSOLE_METADATA_BYTES,
        session->game,session->player,af_console_saved_players(),AF_CONSOLE_SAVE_BYTES,
        state,AF_CONSOLE_WORK_BYTES,state+0x20A0,AF_CONSOLE_BATTERY_BYTES,
        image,session->image_bytes);
    if(result<0) {
        session->error=4;
        /* The emulator/audio are initialized and can use ordinary cleanup. */
        FN(0x800C6E14u,void,void *)(MEMORY(*global(0x80854A28u)));
        *(u8 *)MEMORY(0x80137899u)=1;
    }
}

void af_v3_console_frame_native(void *controls) {
    if(!valid())return;
    FN(native_address(0x8082A46Cu),void,void *)(controls);
    if(imported() && session->save.active)af_v3_console_frame(&session->save,0);
}
void af_v3_console_reset_native(void) {
    if(!valid())return;
    int active=imported() && session->save.active;
    if(active) {
        copy(session->battery_copy,session->emulator+0x20A0,AF_CONSOLE_BATTERY_BYTES);
        af_v3_console_frame(&session->save,1);
    }
    FN(native_address(0x8082A648u),void,void)();
    if(active)copy(session->emulator+0x20A0,session->battery_copy,AF_CONSOLE_BATTERY_BYTES);
}
void af_v3_console_close_native(void) {
    if(!valid())return;
    FN(native_address(0x8082A10Cu),void,void)();
    if(imported() && session->save.active)af_v3_console_close(&session->save);
    session->magic=0;
}
