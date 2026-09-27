#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <vector>
extern "C" {
#include "../overlays/v3/console_save.h"
#include "../overlays/v3/console_image.h"
}
using u8=uint8_t;
using u16=uint16_t;
using u32=uint32_t;
static u32 be(const u8 *p) { return u32(p[0])<<24|u32(p[1])<<16|u32(p[2])<<8|p[3]; }
static u32 half(const u8 *p) { return u32(p[0])<<8|p[1]; }
static void put(u8 *p,u32 v) { p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v; }
static unsigned checks;
#define CHECK(x) do { assert(x);checks++; } while(0)

namespace donor {
enum { HIGHSCORE_STATE_UNSET,HIGHSCORE_STATE_SET,HIGHSCORE_STATE_2,HIGHSCORE_STATE_UNINITIALIZED };
struct Cpu { u8 wram[2048]; } cpu;
struct Common { Cpu *sp; u8 *bbramp,*nesromp; } famicomCommon={&cpu,nullptr,nullptr};
static u8 highscore_num,highscore_updated,*highscore_flags,*nesinfo_tags_start,*nesinfo_tags_end;
static u8 nesinfo_mcrd_game_name[33],*nesinfo_data_start,*nesinfo_data_end;
static u32 nesinfo_tags_size,nesinfo_data_size,nesinfo_expand_rom_size;
static bool tcs_bad,ics_bad;
static char **nesrom_filename_ptrs;
enum { TRUE=1,FALSE=0,EXPAND_SWITCH_DECOMPRESS=0 };
/* No selected donor recipe invokes these unrelated external-ROM operations. */
static u16 calc_check_sum2(void *,size_t) { assert(false);return 0; }
struct JKRFileLoader {
    static u32 readGlbResource(void *,u32,char *,int) { assert(false);return 0; }
};
#define OSReport(...) ((void)0)
#define VT_COL(a,b) ""
#define VT_RST ""
#include "donor_console_save.inc"
#undef OSReport
#undef VT_COL
#undef VT_RST
static void begin(u8 *save,u8 *tags,u32 size,u8 *battery,u8 *image,u8 *flags) {
    famicomCommon.bbramp=battery;famicomCommon.nesromp=image;
    nesinfo_tags_start=tags;nesinfo_tags_end=tags+size;nesinfo_tags_size=size;
    nesinfo_tag_process1(nullptr,0,nullptr);
    highscore_setup_flags(flags);
    /* The original runs on big-endian PPC; only this direct u32 field needs
       conversion on the little-endian host. Tag fields use explicit bytes. */
    u32 bits=be(save+4);std::memcpy(save+4,&bits,4);
    nesinfo_tag_process1(save,1,nullptr);
    std::memcpy(&bits,save+4,4);put(save+4,bits);
}
}

static void fill_pattern(std::vector<u8>& out,u32 seed) {
    for(auto &v:out) { seed=seed*1664525u+1013904223u;v=seed>>24; }
}
static void compare(const AFConsoleSave &state,const std::vector<u8>& saved,
    const std::vector<u8>& reference,const std::vector<u8>& work,
    const std::vector<u8>& battery,const std::vector<u8>& ref_battery,
    const std::vector<u8>& image,const std::vector<u8>& ref_image,const u8 *flags) {
    CHECK(saved==reference);CHECK(battery==ref_battery);CHECK(image==ref_image);
    CHECK(std::memcmp(work.data(),donor::cpu.wram,2048)==0);
    unsigned score=0;
    for(unsigned i=0;i<state.operation_count;i++)
        if(state.operations[i*16]==1) CHECK(state.score_state[i]==flags[score++]);
}
static const std::vector<u8>* image_pool;
static unsigned reads,fail_read;
static int read_image(void *context,unsigned offset,void *destination,unsigned bytes) {
    CHECK(context==image_pool && !(offset&15) && !(bytes&15) && bytes && bytes<=1024);
    CHECK(!(uintptr_t(destination)&15) && offset<=image_pool->size() && bytes<=image_pool->size()-offset);
    if(++reads==fail_read)return -1;
    std::memcpy(destination,image_pool->data()+offset,bytes);return 0;
}
static void exercise(std::vector<u8>& packet,const std::vector<u8>& complete,bool streaming) {
    std::vector<u8> saved(AF_CONSOLE_SAVE_BYTES),reference;
    fill_pattern(saved,47);
    for(unsigned player=0;player<4;player++) put(saved.data()+player*1632+4,0);
    reference=saved;
    /* First play, reload, reset, and updated scores through the SAME executor
       for every supplied game and all four independent player blocks. */
    for(unsigned pass=0;pass<2;pass++) for(unsigned player=0;player<4;player++)
    for(unsigned game=1;game<=19;game++) {
        const u8 *entry=packet.data()+32+(game-1)*64;
        u32 length=be(entry+20),ops=be(entry+40),count=be(entry+44);
        u32 tags_at=be(entry+32),tags_len=be(entry+36);
        std::vector<u8> work(2048),battery(8192),image(length);
        fill_pattern(work,game*11+pass);fill_pattern(battery,game*13+pass);
        auto ref_battery=battery;
        const u8 *full=complete.data()+32+(game-1)*64;
        std::vector<u8> ref_image(complete.begin()+be(full+16),complete.begin()+be(full+16)+length);
        if(streaming) {
            AFConsoleImageWork workspace;reads=fail_read=0;
            CHECK(af_v3_console_load_image(packet.data(),packet.size(),game,read_image,
                (void *)image_pool,image_pool->size(),image.data(),image.size(),&workspace)==0);
            CHECK(image==ref_image);
        }
        std::memcpy(donor::cpu.wram,work.data(),2048);
        u8 flags[64]={0};AFConsoleSave state;
        auto open=streaming?af_v3_console_open_loaded:af_v3_console_open;
        CHECK(open(&state,packet.data(),packet.size(),game,player,
            saved.data(),saved.size(),work.data(),work.size(),battery.data(),battery.size(),
            image.data(),image.size())==int(pass==0));
        donor::begin(reference.data()+player*1632,packet.data()+tags_at,tags_len,
                     ref_battery.data(),ref_image.data(),flags);
        auto check=[&]() { compare(state,saved,reference,work,battery,ref_battery,image,ref_image,flags); };
        auto frame=[&](int reset) {
            donor::highscore_updated=0;
            donor::nesinfo_update_highscore(reference.data()+player*1632,reset);
            CHECK(af_v3_console_frame(&state,reset)==int(donor::highscore_updated));check();
        };
        check();frame(0); // arbitrary initial CPU RAM must not overwrite saved scores
        for(unsigned cycle=0;cycle<4;cycle++) {
            for(unsigned i=0;i<count;i++) {
                const u8 *op=packet.data()+ops+i*16;
                if(op[0]!=1) continue;
                u32 from=be(op+8)&0x7FF,n=half(op+2),defaults=be(op+12);
                std::memcpy(work.data()+from,packet.data()+defaults,n);
            }
            std::memcpy(donor::cpu.wram,work.data(),2048);frame(0); // restore on default
            for(unsigned i=0;i<count;i++) {
                const u8 *op=packet.data()+ops+i*16;
                if(op[0]!=1) continue;
                for(u32 k=0;k<half(op+2);k++) work[(be(op+8)&0x7FF)+k]^=u8(31+cycle+k);
            }
            std::memcpy(donor::cpu.wram,work.data(),2048);frame(0);frame(0);frame(1);
        }
        // Donor states 2 and 3 have distinct update semantics as well.
        for(u8 mode:{u8(2),u8(3)}) {
            unsigned score=0;
            for(unsigned i=0;i<count;i++) if(state.operations[i*16]==1) {
                state.score_state[i]=mode;flags[score++]=mode;
            }
            frame(1);frame(0);
        }
        for(unsigned i=0;i<count;i++) {
            const u8 *op=packet.data()+ops+i*16;
            if(op[0]!=2 && op[0]!=3) continue;
            auto &target=op[0]==2?battery:image;
            for(u32 k=0;k<half(op+2);k++) target[be(op+8)+k]^=u8(k+game+player+1);
        }
        ref_battery=battery;ref_image=image;
        // Reallocation of vectors can move donor pointers; keep the binding explicit.
        donor::famicomCommon.bbramp=ref_battery.data();donor::famicomCommon.nesromp=ref_image.data();
        auto old=saved;
        donor::nesinfo_tag_process3(reference.data()+player*1632);
        int changed=af_v3_console_close(&state);
        CHECK(changed==int(old!=saved));CHECK(saved==reference);
        for(unsigned other=0;other<4;other++) if(other!=player)
            CHECK(std::memcmp(saved.data()+other*1632,old.data()+other*1632,1632)==0);
        CHECK(af_v3_console_frame(&state,0)==AF_CONSOLE_BAD_STATE);
        CHECK(af_v3_console_close(&state)==AF_CONSOLE_BAD_STATE);
    }
}

static void malformed(const std::vector<u8>& original) {
    std::vector<u8> save(AF_CONSOLE_SAVE_BYTES,0xCA),work(2048,0x5B),battery(8192,0x9D);
    std::vector<u8> image(be(original.data()+32+20),0x17);
    AFConsoleSave context;std::memset(&context,0xB5,sizeof(context));
    auto saved=save,worked=work,battery_before=battery,image_before=image;
    u8 before[sizeof(context)];std::memcpy(before,&context,sizeof(context));
    auto reject=[&](std::vector<u8>& packet,u32 game=1,u32 player=0,u32 image_size=0) {
        CHECK(af_v3_console_open(&context,packet.data(),packet.size(),game,player,
            save.data(),save.size(),work.data(),work.size(),battery.data(),battery.size(),
            image.data(),image_size?image_size:image.size())<0);
        CHECK(save==saved && work==worked && battery==battery_before && image==image_before);
        CHECK(std::memcmp(before,&context,sizeof(context))==0);
    };
    auto packet=original;
    reject(packet,0);reject(packet,20);reject(packet,1,4);reject(packet,1,0,image.size()-1);
    CHECK(af_v3_console_open(&context,packet.data(),packet.size(),1,0,
        save.data(),save.size(),save.data(),2048,battery.data(),8192,image.data(),image.size())<0);
    CHECK(save==saved && std::memcmp(before,&context,sizeof(context))==0);
    // Header, entry, image, operation, and cross-game save-overlap corruption.
    for(u32 at:{0u,4u,8u,12u,16u,20u,24u,28u,32u,44u,88u,92u}) {
        packet=original;put(packet.data()+at,0xFFFFFFFF);reject(packet);
    }
    for(u32 field:{16u,20u,24u,28u,32u,36u,40u,44u,48u,52u}) {
        packet=original;put(packet.data()+32+field,0xFFFFFFF0);reject(packet);
    }
    u32 op=be(original.data()+32+40);
    for(u32 at:{op,op+4,op+8,op+12}) {
        packet=original;put(packet.data()+at,0xFFFFFFFF);reject(packet);
    }
    packet=original;u32 second=be(packet.data()+96+40);put(packet.data()+second+4,0);reject(packet);
    packet=original;packet[be(packet.data()+48)+8]=1;reject(packet);
    for(size_t size:{size_t(0),size_t(31),size_t(1247),original.size()-1}) {
        packet.assign(original.begin(),original.begin()+size);reject(packet);
    }
}

static void streamed_errors(const std::vector<u8>& original,const std::vector<u8>& full,
    const std::vector<u8>& pool) {
    struct GuardedWork { u8 pre[16];AFConsoleImageWork work;u8 post[16]; } workspace;
    std::memset(&workspace,0xB9,sizeof(workspace));
    auto guards=[&]() {for(u8 v:workspace.pre)CHECK(v==0xB9);for(u8 v:workspace.post)CHECK(v==0xB9);};
    for(unsigned game=1;game<=19;game++) {
        const u8 *entry=original.data()+32+(game-1)*64;
        u32 size=be(entry+20);std::vector<u8> guarded(size+32,0xED);
        auto check_guards=[&]() {guards();for(unsigned i=0;i<16;i++)CHECK(guarded[i]==0xED && guarded[size+16+i]==0xED);};
        auto metadata=original;image_pool=&pool;reads=fail_read=0;
        auto load_game=[&]() {return af_v3_console_load_image(metadata.data(),metadata.size(),game,
            read_image,(void *)image_pool,image_pool->size(),guarded.data()+16,size,&workspace.work);};
        CHECK(load_game()==0);unsigned total_reads=reads;check_guards();
        for(unsigned fail:{1u,total_reads/2+1,total_reads}) {
            reads=0;fail_read=fail;CHECK(load_game()==AF_CONSOLE_READ_FAILED);CHECK(reads==fail);check_guards();
        }
        fail_read=0;
        // Corrupt output headers, compressed flags, and both integrity bindings.
        for(unsigned mode=0;mode<6;mode++) {
            metadata=original;auto damaged=pool;image_pool=&damaged;reads=0;
            u32 descriptor=be(entry+16),at=be(original.data()+descriptor+20);
            if(mode==0)damaged[at+4]^=1;
            if(mode==1)damaged[at+8]=1;
            if(mode==2){damaged[at+16]=0;damaged[at+17]=0x10;damaged[at+18]=0;} // impossible first reference
            if(mode==3)metadata[descriptor+16]^=1;
            if(mode==4)metadata[32+(game-1)*64+12]^=1;
            if(mode==5)put(metadata.data()+descriptor+24,be(metadata.data()+descriptor+24)-1);
            CHECK(load_game()==AF_CONSOLE_BAD_PACKET);check_guards();
        }
        metadata=original;image_pool=&pool;
        // Invalid complete descriptors reject without reading the game pool.
        for(unsigned mode=0;mode<5;mode++) {
            metadata=original;reads=0;u32 descriptor=be(entry+16);
            if(mode==0)put(metadata.data()+descriptor+20,0xFFFFFFF0);
            if(mode==1)put(metadata.data()+descriptor+24,0xFFFFFFFF);
            if(mode==2)put(metadata.data()+descriptor+28,1);
            if(mode==3)put(metadata.data()+32+(game-1)*64+16,metadata.size()-16);
            if(mode==4)put(metadata.data()+descriptor+20,be(metadata.data()+descriptor+20)+1);
            auto before=guarded;CHECK(load_game()<0);CHECK(reads==0 && guarded==before);check_guards();
        }
        // A fully loaded but corrupted image cannot change a persistence session.
        metadata=original;CHECK(load_game()==0);
        AFConsoleSave state;std::memset(&state,0xAF,sizeof(state));u8 state_before[sizeof(state)];
        std::memcpy(state_before,&state,sizeof(state));
        std::vector<u8> saved(AF_CONSOLE_SAVE_BYTES,0x63),work(2048,0x36),battery(8192,0x58);
        auto saved_before=saved,work_before=work,battery_before=battery;
        guarded[16+size-1]^=1;auto image_before=guarded;
        CHECK(af_v3_console_open_loaded(&state,metadata.data(),metadata.size(),game,0,
            saved.data(),saved.size(),work.data(),work.size(),battery.data(),battery.size(),
            guarded.data()+16,size)==AF_CONSOLE_BAD_PACKET);
        CHECK(saved==saved_before && work==work_before && battery==battery_before && guarded==image_before);
        CHECK(std::memcmp(&state,state_before,sizeof(state))==0);
        CHECK(af_v3_console_open(&state,metadata.data(),metadata.size(),game,0,
            saved.data(),saved.size(),work.data(),work.size(),battery.data(),battery.size(),
            guarded.data()+16,size)==AF_CONSOLE_BAD_PACKET);
        CHECK(af_v3_console_open_loaded(&state,full.data(),full.size(),game,0,
            saved.data(),saved.size(),work.data(),work.size(),battery.data(),battery.size(),
            guarded.data()+16,size)==AF_CONSOLE_BAD_PACKET);
    }
    image_pool=&pool;
}

static std::vector<u8> load(const char *path) {
    std::ifstream file(path,std::ios::binary);assert(file);
    return std::vector<u8>((std::istreambuf_iterator<char>(file)),std::istreambuf_iterator<char>());
}

int main(int argc,char **argv) {
    assert(argc==4);auto packet=load(argv[1]),metadata=load(argv[2]),pool=load(argv[3]);image_pool=&pool;
    CHECK(af_v3_console_validate(packet.data(),packet.size())==0);
    CHECK(af_v3_console_validate(metadata.data(),metadata.size())==0);
    exercise(packet,packet,false);malformed(packet);exercise(metadata,packet,true);
    streamed_errors(metadata,packet,pool);
    std::printf("%u checks: full and streamed 19 donor games, four players, first/repeat launch, score/reset states, battery/disk/Zelda, and bounded rejection\n",checks);
}
