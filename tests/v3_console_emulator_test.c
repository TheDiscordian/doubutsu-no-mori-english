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
static int valid_storage=1,fail_read;
static u8 *state_pointer;
const u8 *af_test_console_metadata=meta;
u32 af_console_test_caller=RELOCATED+0x8082E0E0u-BASE;
static unsigned checks;
#define CHECK(test) do {checks++;if(!(test)){fprintf(stderr,"line %d: %s\n",__LINE__,#test);abort();}} while(0)

void *af_console_test_memory(u32 at) {
    if(at>=RELOCATED && at<RELOCATED+sizeof(native))return native+at-RELOCATED;
    if(at==0x804FE820u)return session_memory;
    if(at==0x804FC820u)return meta;
    if(at==0x80137898u)return &game_number;
    if(at==0x80136EA3u)return &player_number;
    if(at==0x80137899u)return &failure;
    fprintf(stderr,"unexpected native data address %08x\n",at);abort();
}
static void *native_alloc(u32 bytes) {
    CHECK(calls<12);alloc_sizes[calls++]=bytes;
    if(calls==fail_allocation)return 0;
    bytes=(bytes+15)&~15u;CHECK(used+bytes+16<=sizeof(arena));
    void *p=arena+used;memset(p,0,bytes);memset(arena+used+bytes,0xA6,16);used+=bytes+16;return p;
}
static void native_init(u8 *state,void *header,void *graphics,u8 *image) {
    CHECK(state==state_pointer && header && graphics && image);init_calls++;
    memset(state,0,0x16F90);memset(state+0x20A0,0xC3,8192);
}
static void native_frame(void *controls) {CHECK(controls==native);frame_calls++;}
static void native_reset(void) {reset_calls++;memset(state_pointer+0x20A0,0xD8,8192);}
static void native_close(void) {
    /* RSP completion happens before progress capture; simulate a final write. */
    close_calls++;state_pointer[0x20A0+2]^=0x5A;
}
static void *native_setup(void) {setup_calls++;return native;}
static void native_return(void *game) {CHECK(game==native);return_calls++;}
void *af_console_test_function(u32 at) {
    if(at==0x800C6E14)return native_return;
    switch(at-RELOCATED+BASE) {
    case 0x8082A814:return native_alloc;
    case 0x8082A6EC:return native_init;
    case 0x8082A46C:return native_frame;
    case 0x8082A648:return native_reset;
    case 0x8082A10C:return native_close;
    case 0x8082D29C:return native_setup;
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
    used=calls=0;game_number=game;player_number=player;
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
int main(int argc,char **argv) {
    CHECK(argc==4);load_file(argv[1],meta,sizeof(meta));load_file(argv[2],pool,sizeof(pool));load_file(argv[3],full,sizeof(full));
    CHECK(af_v3_console_validate(meta,sizeof(meta))==0);
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
        for(u32 player=0;player<4;player++)for(u32 repeat=0;repeat<2;repeat++) {
            memcpy(saved_snapshot,players,sizeof(players));
            void *graphics=start(game,player);CHECK(graphics);
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
                    if(!repeat)for(u32 j=0;j<length;j++)CHECK(battery[j]==0);
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
    for(u32 failure_case=0;failure_case<10;failure_case++) {
        memcpy(saved_snapshot,players,sizeof(players));
        fail_allocation=(failure_case>=5&&failure_case<=8)?failure_case-3:0;
        fail_read=failure_case==4;valid_storage=failure_case!=3;
        start(failure_case==0?20:failure_case==1?10:8,failure_case==2?4:0);
        if(failure_case==9)meta[0]^=1;
        CHECK(!af_v3_console_setup());CHECK(!*global(0x80854B78));
        CHECK(!memcmp(players,saved_snapshot,sizeof(players)));
        if(failure_case==9)meta[0]^=1;
        check_guards();
    }
    valid_storage=1;fail_read=0;fail_allocation=0;
    void *graphics=start(8,0);u8 *image=af_v3_console_setup();CHECK(image);image[16]^=1;
    memcpy(saved_snapshot,players,sizeof(players));
    af_v3_console_initialize(state_pointer,native,graphics,image);
    CHECK(session->error==4 && failure==1 && return_calls==1 && !session->save.active);
    CHECK(!memcmp(players,saved_snapshot,sizeof(players)));af_v3_console_close_native();check_guards();
    printf("%u native-adapter checks: original paths, eleven full iNES images, four players, reset, close, and rejection; CPU/PPU/audio stubbed\n",checks);
    return 0;
}
