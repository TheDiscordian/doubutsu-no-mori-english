/* Shared creator/state test. Native setup is observed here, not emulated;
 * current-cartridge composition verifies its real allocation and loop patches. */
#include "creature_insect_manager.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static struct {u32 before;AfInsectController owner;u32 after;} guarded;
static AfInsectController foreign;
static u8 original[3][0x1C00] __attribute__((aligned(16)));
static void *buffers[AF_INSECT_SLOTS];
static u32 profile=0x1FFFF,created;
static int last_slot;
static u8 game;
u32 af_v3_insect_spawn_mode;
static AfNativeInsectClip clip;
AfNativeInsectClip *af_insect_native_clip=&clip;
u32 af_v3_creature_profile_byte(u32 n) {assert(n<3);return profile>>(n*8)&255;}
void af_v3_insect_position(ACTOR *actor) {(void)actor;}
static void reload(GAME *g) {(void)g;}
static void destroy(ACTOR *a,GAME *g) {(void)a;(void)g;}
static ACTOR *release(GAME *g,int type,xyz_t *p) {(void)g;(void)type;(void)p;return NULL;}

static void setup(AfInsectInit *init,int slot) {
    assert(init && init->game==(GAME *)&game && slot>=0 && slot<AF_INSECT_SLOTS);
    aINS_INSECT_ACTOR *insect=guarded.owner.insects+slot;
    assert(!insect->exist_flag && insect->native_program==buffers[slot]);
    insect->exist_flag=1;insect->type=init->type;
    insect->tools_actor.actor_class.world.position=init->position;
    insect->tools_actor.actor_class.block_x=(s8)(slot+1);
    insect->tools_actor.actor_class.block_z=3;
    created++;last_slot=slot;
}

static void bind(unsigned mode) {
    memset(&guarded,0,sizeof guarded);guarded.before=0x10234567;guarded.after=0x76543210;
    guarded.owner.native_bank=1;
    for (unsigned i=0;i<3;i++) guarded.owner.insects[i].native_program=original[i];
    clip=(AfNativeInsectClip){NULL,reload,destroy,release};
    af_v3_insect_spawn_mode=mode;af_insect_pool_bind(&guarded.owner,setup);
    assert(clip.make && clip.reload==reload && clip.destroy==destroy && clip.release==release);
    assert(!af_insect_extra(&foreign.insects[0]));
    for (unsigned i=0;i<AF_INSECT_SLOTS;i++) {
        aINS_INSECT_ACTOR *insect=guarded.owner.insects+i;
        buffers[i]=insect->native_program;
        assert(buffers[i] && !((uintptr_t)buffers[i]&15u));
        if (i<3) assert(buffers[i]==original[i]);
        for (unsigned j=0;j<i;j++) {
            uintptr_t a=(uintptr_t)buffers[i],b=(uintptr_t)buffers[j];
            assert(a+0x1C00<=b || b+0x1C00<=a);
        }
        AfInsectExtra *extra=af_insect_extra(insect);
        assert(extra && extra->ut_x==-1 && extra->ut_z==-1 && extra->bg_range==12.0f);
        memset(buffers[i],(int)i+1,0x1C00);
    }
    created=0;last_slot=-1;
}

static void guards(void) {
    assert(guarded.before==0x10234567 && guarded.after==0x76543210);
    for (unsigned i=0;i<AF_INSECT_SLOTS;i++) {
        assert(guarded.owner.insects[i].native_program==buffers[i]);
        const u8 *p=buffers[i];
        for (unsigned j=0;j<0x1C00;j++) assert(p[j]==i+1);
    }
}

int main(void) {
    AfInsectInit init={0,{100,2,100},0,(GAME *)&game};
    bind(0);
    assert(clip.make(&init,0)==(ACTOR *)guarded.owner.insects && last_slot==0);
    init.position=(xyz_t){140,300,140};
    assert(!clip.make(&init,0)); /* Inclusive square boundary; Y is irrelevant. */
    init.position.z=140.01f;
    assert(clip.make(&init,0)==(ACTOR *)(guarded.owner.insects+1) && last_slot==1);
    assert(!clip.make(&init,0) && created==2);
    init.type=39;
    assert(clip.make(&init,1)==(ACTOR *)(guarded.owner.insects+AF_INSECT_RELEASE_SLOT));
    assert(!clip.make(&init,1) && created==3);
    assert(!af_insect_occupied_acre(9,3)); /* Released object never blocks wild spawning. */
    assert(af_insect_occupied_acre(1,3) && af_insect_occupied_acre(2,3));
    for (unsigned i=2;i<AF_INSECT_WILD_SLOTS;i++) assert(!guarded.owner.insects[i].exist_flag);
    guards();

    bind(1);init.position=(xyz_t){100,2,100};
    for (unsigned i=0;i<AF_INSECT_WILD_SLOTS;i++) {
        init.type=32+(int)i;
        assert(clip.make(&init,0)==(ACTOR *)(guarded.owner.insects+i));
        assert(last_slot==(int)i && af_insect_occupied_acre((int)i+1,3));
    }
    assert(!clip.make(&init,0) && created==8);
    assert(clip.make(&init,1)==(ACTOR *)(guarded.owner.insects+8) && created==9);
    assert(!clip.make(&init,1));
    guarded.owner.insects[5].exist_flag=0;init.type=0;
    assert(clip.make(&init,0)==(ACTOR *)(guarded.owner.insects+5));
    assert(created==10);guards();

    /* Original and added species share the same capacity machinery. Selected
     * additions are gated at creation, including the release/colony route. */
    bind(1);profile=1u<<9;
    for (int type=0;type<32;type++) {
        init.type=type;
        assert(clip.make(&init,0)==(ACTOR *)guarded.owner.insects);
        guarded.owner.insects[0].exist_flag=0;
    }
    init.type=32;assert(clip.make(&init,0));guarded.owner.insects[0].exist_flag=0;
    for (int type=33;type<40;type++) {
        init.type=type;assert(!clip.make(&init,0) && !clip.make(&init,1));
    }
    init.type=-1;assert(!clip.make(&init,0));init.type=40;assert(!clip.make(&init,0));
    init.type=0;assert(!clip.make(&init,-1) && !clip.make(&init,2));
    assert(!clip.make(NULL,0));init.game=NULL;assert(!clip.make(&init,0));init.game=(GAME *)&game;
    guarded.owner.native_bank=-1;assert(!clip.make(&init,0));guarded.owner.native_bank=1;
    af_v3_insect_spawn_mode=2;assert(!clip.make(&init,0));af_v3_insect_spawn_mode=1;
    assert(created==33);guards();
    af_insect_pool_unbind(&foreign);assert(af_insect_extra(guarded.owner.insects));
    af_insect_pool_unbind(&guarded.owner);
    assert(!clip.make(&init,0) && !af_insect_extra(guarded.owner.insects));
    puts("Complete population creator: both modes, nine independent buffers, release, profile, and teardown");
    return 0;
}
