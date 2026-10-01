/* Native-address adapter exercise, with actual prepared images and save core.
 * Native CPU/PPU/audio calls are stubs: this is not emulator gameplay proof. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/console_emulator.c"

#define RELOCATED 0x80200000u
static _Alignas(16) u8 native[0x2E990],session_memory[0x800],meta[6336];
static _Alignas(16) u8 arena[0x160000],players[AF_CONSOLE_SAVE_BYTES];
static u8 pool[770144],full[1472384],game_number,player_number,failure;
static u8 saved_snapshot[AF_CONSOLE_SAVE_BYTES],battery_snapshot[8192];
static u32 used,calls,fail_allocation,alloc_sizes[12],init_calls,frame_calls,reset_calls,close_calls,setup_calls,return_calls;
static u32 arena_calls;
static int valid_storage=1,fail_read;
static u8 *state_pointer;
#ifdef AF_CONSOLE_DISK
AFQNative af_qdn_test_context;
static _Alignas(16) u8 disk_memory[0x16010],native_reference[0x2E990];
static u32 disk_cpu_calls,disk_waits,disk_events;
#endif
const u8 *af_test_console_metadata=meta;
u32 af_console_test_caller=RELOCATED+0x8082E0E0u-BASE;
static unsigned checks;
#define CHECK(test) do {checks++;if(!(test)){fprintf(stderr,"line %d: %s\n",__LINE__,#test);abort();}} while(0)

void *af_console_test_memory(u32 at) {
#ifdef AF_CONSOLE_DISK
    if(at==0x80638000)return &af_qdn_test_context;
    if(at>=0x80630000 && at<0x80646010)return disk_memory+at-0x80630000;
#endif
    if(at>=RELOCATED && at<RELOCATED+sizeof(native))return native+at-RELOCATED;
    if(at==0x804FE820u)return session_memory;
    if(at==0x804FC820u)return meta;
    if(at==0x80137898u)return &game_number;
    if(at==0x80136EA3u)return &player_number;
    if(at==0x80137899u)return &failure;
    fprintf(stderr,"unexpected native data address %08x\n",at);abort();
}
static u32 *native_word(u32 linked) {return (u32 *)(native+linked-BASE);}
static void *native_arena(void *heap,u32 bytes) {
    u32 *h=heap;arena_calls++;h[3]=((h[3]&~15u)-bytes)&~15u;
    return (void *)(uintptr_t)h[3];
}
static void *native_alloc(u32 bytes) {
    CHECK(calls<12);alloc_sizes[calls++]=bytes;
    if(calls==fail_allocation)return 0;
    u32 aligned=(bytes+15)&~15u,*primary=native_word(0x80854A34),*fallback=native_word(0x80854A2C);
    int available=0;
    if(primary[0] && primary[1]>=aligned) {primary[0]+=aligned;primary[1]-=aligned;available=1;}
    else if(*native_word(0x80854A28))
        available=af_v3_console_arena_allocate(*native_word(0x80854A28)+0x78,bytes)!=0;
    if(!available && fallback[0] && fallback[1]>=aligned) {fallback[0]+=aligned;fallback[1]-=aligned;available=1;}
    if(!available)return 0;
    bytes=aligned;CHECK(used+bytes+16<=sizeof(arena));
    void *p=arena+used;memset(p,0,bytes);memset(arena+used+bytes,0xA6,16);used+=bytes+16;return p;
}
static void native_init(u8 *state,void *header,void *graphics,u8 *image) {
    CHECK(state==state_pointer && header && graphics && image);init_calls++;
    memset(state,0,0x16F90);memset(state+0x20A0,0xC3,8192);
}
static void native_frame(void *controls) {
    CHECK(controls==native);frame_calls++;
#ifdef AF_CONSOLE_DISK
    af_v3_console_cpu_frame(state_pointer);
#endif
}
static void native_reset(void) {reset_calls++;memset(state_pointer+0x20A0,0xD8,8192);}
static void native_close(void) {
    /* RSP completion happens before progress capture; simulate a final write. */
    close_calls++;state_pointer[0x20A0+2]^=0x5A;
#ifdef AF_CONSOLE_DISK
    if(disk_game())CHECK(qd()->magic && qd()->initialized);
#endif
}
static void *native_setup(void) {setup_calls++;return native;}
static void native_return(void *game) {CHECK(game==native);return_calls++;}
#ifdef AF_CONSOLE_DISK
static void native_cpu(u8 *state) {
    CHECK(state==state_pointer);
    if(disk_game()) {
        CHECK(qd()->initialized && qd()->audio_initialized);
        if(++disk_cpu_calls%2==0)qd()->disk.control|=2;
    }
}
static void disk_wait(void) {disk_waits++;}
static void disk_flush(void *p,u32 bytes) {
    CHECK(bytes==8192 && (p==state_pointer+0x62C8 || p==qd()->graphics+0x2008));
}
static void disk_event(u32 at,u32 value) {
    static const u32 expected[][2]={{0x15,0},{8,0},{0x80,0x80},{0x80,0x15},{0xD5,0},{0x10,15},{15,0x11}};
    CHECK(at==expected[disk_events%7][0] && value==expected[disk_events%7][1]);disk_events++;
}
static void disk_sound_reset(void) {CHECK(disk_events && disk_events%7==0);}
static void disk_sound_bind(void *p) {CHECK(p==disk_memory+0x10000);}
void af_v3_qd_wdm_bridge(void) {}
void af_v3_qd_ram_bridge(void) {}
void af_v3_qd_read_bridge(void) {}
void af_v3_qd_write_bridge(void) {}
void af_v3_qd_irq_bridge(void) {}
void af_v3_qd_dpcm_bridge(void) {}
u8 *af_qdn_test_memory(u32 at) {return af_console_test_memory(at);}
void *af_qdn_test_function(u32 at) {return af_console_test_function(at);}
#endif
void *af_console_test_function(u32 at) {
#ifdef AF_CONSOLE_DISK
    if(at==0x8002FE00)return disk_flush;
#endif
    if(at==0x800C6E14)return native_return;
    if(at==0x800D17D4)return native_arena;
    switch(at-RELOCATED+BASE) {
    case 0x8082A814:return native_alloc;
    case 0x8082A6EC:return native_init;
    case 0x8082A46C:return native_frame;
    case 0x8082A648:return native_reset;
    case 0x8082A10C:return native_close;
    case 0x8082D29C:return native_setup;
#ifdef AF_CONSOLE_DISK
    case 0x8082F09C:return native_cpu;
    case 0x8082A070:return disk_wait;
    case 0x808345B8:return disk_event;
    case 0x808352D8:return disk_sound_reset;
    case 0x80835778:return disk_sound_bind;
#endif
    default:fprintf(stderr,"unexpected native function %08x\n",at);abort();
    }
}
u8 *af_console_saved_players(void) {return players;}
int af_console_storage_valid(void) {return valid_storage;}
int af_console_pi_read(u32 source,void *destination,u32 bytes) {
    if(fail_read)return -1;
    CHECK(source>=AF_CONSOLE_POOL_ROM && source-AF_CONSOLE_POOL_ROM+bytes<=sizeof(pool));
    memcpy(destination,pool+source-AF_CONSOLE_POOL_ROM,bytes);return 0;
}
static u32 addr(void *p) {CHECK((uintptr_t)p<=UINT32_MAX);return (u32)(uintptr_t)p;}
static void check_guards(void) {
    u32 position=0;
    for(u32 i=0;i<calls;i++) {
        if(i+1==fail_allocation)continue;
        position+=(alloc_sizes[i]+15)&~15u;
        for(u32 j=0;j<16;j++)CHECK(arena[position+j]==0xA6);
        position+=16;
    }
    CHECK(position==used);
    for(u32 i=sizeof(Session);i<sizeof(session_memory);i++)CHECK(session_memory[i]==0xA7);
}
static void *start(u32 game,u32 player) {
    memset(native,0,sizeof(native));memset(session_memory,0xA7,sizeof(session_memory));
#ifdef AF_CONSOLE_DISK
    memcpy(native,native_reference,sizeof(native));
    u32 branch=0x08000000|((u32)(uintptr_t)af_v3_qd_dpcm_bridge>>2&0x03FFFFFF);
    u8 *p=native+0x80833DBC-BASE;
    p[0]=branch>>24;p[1]=branch>>16;p[2]=branch>>8;p[3]=branch;
    memset(p+4,0,4);disk_cpu_calls=0;
#endif
    used=calls=0;game_number=game;player_number=player;
    *native_word(0x80854A34)=0x80240000;*native_word(0x80854A38)=sizeof(arena);
    state_pointer=native_alloc(0x16F90);
    void *graphics=af_v3_console_graphics(0x25008);
    void *header=native_alloc(0x210);
    *global(0x80854A08)=addr(state_pointer);*global(0x80854A10)=addr(graphics);
    *global(0x80854A14)=addr(header);*global(0x80854A28)=RELOCATED;
    return graphics;
}
static void load_file(const char *path,u8 *out,size_t bytes) {
    FILE *f=fopen(path,"rb");CHECK(f);CHECK(fread(out,1,bytes,f)==bytes);CHECK(fgetc(f)==EOF);CHECK(!fclose(f));
}
static void allocation_boundaries(void) {
    const u32 heap=RELOCATED+0x78,start=0x80240000;
    u32 *h=af_console_test_memory(heap),before[4];
    /* The native allocator reaches this hook before graphics initializes the
     * session; bounds must not depend on a current session or game identity. */
    memset(session_memory,0,sizeof(session_memory));
    for(u32 n=1;n<=33;n++) {
        u32 aligned=(n+15)&~15u;
        h[0]=0x100;h[1]=start;h[2]=start+0x100-aligned;h[3]=start+0x100;
        u32 prior=arena_calls;
        CHECK((uintptr_t)af_v3_console_arena_allocate(heap,n)==h[2]);
        CHECK(arena_calls==prior+1 && h[3]==h[2]);
        h[3]=start+0x100;h[2]++;memcpy(before,h,sizeof(before));prior=arena_calls;
        CHECK(!af_v3_console_arena_allocate(heap,n));
        CHECK(arena_calls==prior && !memcmp(before,h,sizeof(before)));
    }
    for(u32 bad=0;bad<12;bad++) {
        h[0]=0x100;h[1]=start;h[2]=start;h[3]=start+0x100;
        u32 request=16,at=heap;
        switch(bad) {
        case 0:request=0;break;
        case 1:request=0xFFFFFFF1u;break;
        case 2:h[0]=0xFFFFFFFFu;break;
        case 3:h[1]=0x7FFFFFF0;break;
        case 4:h[1]=0x80400010;break;
        case 5:h[2]=start-1;break;
        case 6:h[3]=h[2]-1;break;
        case 7:h[3]=start+0x101;break;
        case 8:h[2]=start+0xF1;h[3]=start+0xFF;request=1;break;
        case 9:at++;break;
        case 10:at=0x803FFFF4;break;
        case 11:at=0x800003FC;break;
        }
        memcpy(before,h,sizeof(before));u32 prior=arena_calls;
        CHECK(!af_v3_console_arena_allocate(at,request));
        CHECK(arena_calls==prior && !memcmp(before,h,sizeof(before)));
    }
    h[0]=0x100;h[1]=start;h[2]=start;h[3]=start+0xFF;
    CHECK((uintptr_t)af_v3_console_arena_allocate(heap,0xF0)==start);
    /* Exact high-end arena, with no address wrap. */
    h[0]=16;h[1]=h[2]=0x803FFFF0;h[3]=0x80400000;
    CHECK((uintptr_t)af_v3_console_arena_allocate(heap,16)==0x803FFFF0);
    /* Preserve native selection order: primary pool, checked arena, fallback.
     * A full arena rejects without moving its tail, allowing a real fallback. */
    memset(native,0,sizeof(native));used=calls=0;
    *native_word(0x80854A28)=RELOCATED;
    h[0]=16;h[1]=h[2]=start;h[3]=start+16;
    *native_word(0x80854A34)=start+0x100;*native_word(0x80854A38)=16;
    *native_word(0x80854A2C)=start+0x200;*native_word(0x80854A30)=16;
    u32 prior=arena_calls;
    CHECK(native_alloc(16));CHECK(arena_calls==prior && h[3]==start+16);
    CHECK(native_alloc(16));CHECK(arena_calls==prior+1 && h[3]==start);
    CHECK(native_alloc(16));CHECK(arena_calls==prior+1 && h[3]==start);
    CHECK(!native_alloc(16));CHECK(arena_calls==prior+1 && h[3]==start);
    CHECK(*native_word(0x80854A38)==0 && *native_word(0x80854A30)==0);
}
int main(int argc,char **argv) {
#ifdef AF_CONSOLE_DISK
    CHECK(argc==6);load_file(argv[4],native_reference,sizeof(native_reference));
    load_file(argv[5],disk_memory,sizeof(disk_memory));
#else
    CHECK(argc==4);
#endif
    load_file(argv[1],meta,sizeof(meta));load_file(argv[2],pool,sizeof(pool));load_file(argv[3],full,sizeof(full));
    CHECK(af_v3_console_validate(meta,sizeof(meta))==0);
    allocation_boundaries();
    for(u32 game=0;game<8;game++) {
        memset(players,0x57,sizeof(players));memcpy(saved_snapshot,players,sizeof(players));
        void *graphics=start(game,0);CHECK(alloc_sizes[1]==0x25008);
        CHECK(af_v3_console_setup()==native);
        af_v3_console_initialize(state_pointer,native,graphics,native);
        af_v3_console_frame_native(native);af_v3_console_reset_native();af_v3_console_close_native();
        CHECK(!memcmp(players,saved_snapshot,sizeof(players)));CHECK(!session->magic);check_guards();
    }
    CHECK(setup_calls==8 && init_calls==8 && frame_calls==8 && reset_calls==8 && close_calls==8);
    memset(players,0,sizeof(players));u32 imported_games=0;
    for(u32 game=8;game<=19;game++) {
        const u8 *entry=meta+32+(game-1)*64;
        if(word(entry+4)!=1)continue;
        imported_games++;
        for(u32 actor=0;actor<5;actor++)for(u32 repeat=0;repeat<2;repeat++) {
            u32 player=actor<4?actor:0; /* Original visitor fallback, not a fifth saved row. */
            memcpy(saved_snapshot,players,sizeof(players));
            void *graphics=start(game,actor);CHECK(graphics);
            CHECK(session->player==player);
            u32 need=0x2008+((u32)meta[word(entry+16)+5]<<13);
            CHECK(alloc_sizes[1]==(need>0x25008?need:0x25008));
            u8 *image=af_v3_console_setup();CHECK(image && !session->error);
            CHECK(*global(0x80854B78)==addr(image));CHECK(*global(0x80854B7C)==addr(image+session->image_bytes));
            const u8 *original=full+32+(game-1)*64;
            CHECK(!memcmp(image,full+word(original+16),session->image_bytes));
            af_v3_console_initialize(state_pointer,native,graphics,image);
            CHECK(session->save.active && !session->error);
            CHECK(session->save.save==players+player*AF_CONSOLE_PLAYER_BYTES);
            for(u32 i=0;i<session->save.operation_count;i++) {
                const u8 *op=session->save.operations+i*16;u32 length=(u32)op[2]<<8|op[3];
                if(op[0]==2) {
                    u8 *battery=state_pointer+0x20A0+word(op+8);
                    /* Zelda's special repair intentionally changes its save
                     * markers/checksums on re-open; the core has donor tests. */
                    if(!repeat && actor<4)for(u32 j=0;j<length;j++)CHECK(battery[j]==0);
                    else if(game!=19)CHECK(!memcmp(battery,players+player*AF_CONSOLE_PLAYER_BYTES+8+word(op+4),length));
                }
            }
            af_v3_console_frame_native(native);
            for(u32 i=0;i<8192;i++)state_pointer[0x20A0+i]=(u8)(i+player+game);
            memcpy(battery_snapshot,state_pointer+0x20A0,8192);
            af_v3_console_reset_native();CHECK(!memcmp(battery_snapshot,state_pointer+0x20A0,8192));
            af_v3_console_close_native();CHECK(!session->magic && !session->save.active);
            for(u32 i=0;i<session->save.operation_count;i++) {
                const u8 *op=session->save.operations+i*16;u32 length=(u32)op[2]<<8|op[3];
                if(op[0]==2)CHECK(!memcmp(players+player*AF_CONSOLE_PLAYER_BYTES+8+word(op+4),state_pointer+0x20A0+word(op+8),length));
            }
            for(u32 other=0;other<4;other++)if(other!=player)
                CHECK(!memcmp(players+other*AF_CONSOLE_PLAYER_BYTES,saved_snapshot+other*AF_CONSOLE_PLAYER_BYTES,AF_CONSOLE_PLAYER_BYTES));
            check_guards();
        }
    }
    CHECK(imported_games==11 && setup_calls==8 && !return_calls);
#ifdef AF_CONSOLE_DISK
    u32 prior_inits=init_calls,prior_resets=reset_calls;
    for(u32 actor=0;actor<5;actor++)for(u32 repeat=0;repeat<2;repeat++) {
        u32 player=actor<4?actor:0;
        memcpy(saved_snapshot,players,sizeof(players));
        void *graphics=start(10,actor);u8 *image=af_v3_console_setup();CHECK(image && disk_game());
        CHECK(session->player==player);
        CHECK(session->image_bytes==65536);
        af_v3_console_extent(image);CHECK(*global(0x80854B74)==65536);
        CHECK(*global(0x80854B7C)==addr(image+65536));
        af_v3_console_initialize(state_pointer,native,graphics,image);
        CHECK(!session->error && session->save.active && qd()->initialized && qd()->audio_initialized);
        CHECK(init_calls==prior_inits && qd()->disk.disk==image && !qd()->disk.frame_flags);
        CHECK(session->save.operation_count==1 && session->save.operations[0]==3);
        const u8 *op=session->save.operations;u32 from=word(op+8),to=8+word(op+4),length=(u32)op[2]<<8|op[3];
        if(repeat || actor>=4)CHECK(!memcmp(image+from,players+player*AF_CONSOLE_PLAYER_BYTES+to,length));
        CHECK(!af_v3_qd_boot(&qd()->disk));
        qd()->disk.ready=119;qd()->disk.control=0;disk_cpu_calls=0;
        af_v3_console_frame_native(native);
        CHECK(disk_cpu_calls==2 && qd()->disk.ready==120 && qd()->disk.motor==88);
        state_pointer[19]=0xA6;qd()->disk.program[44]=0x8B;qd()->disk.bios[0xEBD]=0xA9;
        u32 waits=disk_waits;
        af_v3_console_reset_native();
        CHECK(reset_calls==prior_resets && disk_waits==waits+1);
        CHECK(state_pointer[19]==0xA6 && qd()->disk.program[44]==0x8B && qd()->disk.bios[0xEBD]==0xA9);
        for(u32 i=0;i<length;i++)image[from+i]=(u8)(i+player+repeat*17);
        af_v3_console_close_native();CHECK(!qd()->magic && !session->magic && !session->save.active);
        CHECK(!memcmp(players+player*AF_CONSOLE_PLAYER_BYTES+to,image+from,length));
        for(u32 other=0;other<4;other++)if(other!=player)
            CHECK(!memcmp(players+other*AF_CONSOLE_PLAYER_BYTES,saved_snapshot+other*AF_CONSOLE_PLAYER_BYTES,AF_CONSOLE_PLAYER_BYTES));
        check_guards();
    }
#endif
    for(u32 failure_case=0;failure_case<10;failure_case++) {
        memcpy(saved_snapshot,players,sizeof(players));
        fail_allocation=(failure_case>=5&&failure_case<=8)?failure_case-3:0;
        fail_read=failure_case==4;valid_storage=failure_case!=3;
#ifdef AF_CONSOLE_DISK
        if(failure_case==1)disk_memory[0x16000]^=1;
#endif
        start(failure_case==0?20:failure_case==1?10:8,0);
        if(failure_case==2)session->guard[0]^=1;
        if(failure_case==9)meta[0]^=1;
        CHECK(!af_v3_console_setup());CHECK(!*global(0x80854B78));
        CHECK(!memcmp(players,saved_snapshot,sizeof(players)));
        if(failure_case==9)meta[0]^=1;
        check_guards();
#ifdef AF_CONSOLE_DISK
        if(failure_case==1)disk_memory[0x16000]^=1;
#endif
    }
    valid_storage=1;fail_read=0;fail_allocation=0;
    void *graphics=start(8,0);u8 *image=af_v3_console_setup();CHECK(image);image[16]^=1;
    memcpy(saved_snapshot,players,sizeof(players));
    af_v3_console_initialize(state_pointer,native,graphics,image);
    CHECK(session->error==4 && failure==1 && return_calls==1 && !session->save.active);
    CHECK(!memcmp(players,saved_snapshot,sizeof(players)));af_v3_console_close_native();check_guards();
#ifdef AF_CONSOLE_DISK
    printf("%u disk-session checks: original/iNES routes, full QD boot, four residents and original visitor row-zero fallback, repeat play, image extent, per-frame motor timing, soft reset, close capture and rejection; CPU/PPU/audio stubbed\n",checks);
#else
    printf("%u native-adapter checks: original paths, eleven full iNES images, four residents and original visitor row-zero fallback, reset, close, and rejection; CPU/PPU/audio stubbed\n",checks);
#endif
    return 0;
}
