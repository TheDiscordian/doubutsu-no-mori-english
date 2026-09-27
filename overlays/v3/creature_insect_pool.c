/* Shared native controller capacity. Original insects keep their native
 * programs, now with independent storage for every live slot in either mode. */
#include "creature_insect_manager.h"
static AfInsectController *pool;
static void (*native_setup)(AfInsectInit *,int);
static u8 programs[AF_INSECT_SLOTS-3][0x1C00] __attribute__((aligned(16)));

static ACTOR *make(AfInsectInit *init,int release) {
    unsigned mode=*(const volatile u32 *)&af_v3_insect_spawn_mode;
    if (!pool || !native_setup || pool->native_bank<0 || !init || !init->game ||
            mode>1 || (release!=0 && release!=1) || (unsigned)init->type>=40) return NULL;
    if (init->type>=32) {
        unsigned bit=(unsigned)init->type-32+9;
        if (!(af_v3_creature_profile_byte(bit/8)&(1u<<(bit&7)))) return NULL;
    }
    unsigned limit=mode?AF_INSECT_WILD_SLOTS:2;
    unsigned slot=release?AF_INSECT_RELEASE_SLOT:0;
    if (!release) {
        for (;slot<limit;slot++) if (!pool->insects[slot].exist_flag) break;
        if (slot==limit) return NULL;
        /* Preserve N64's square forty-unit exclusion in native mode. The
         * donor has no such check, allowing its deliberate multi-insect groups. */
        if (!mode) {
            const aINS_INSECT_ACTOR *other=pool->insects+(slot^1u);
            xyz_t pos=other->tools_actor.actor_class.world.position;
            f32 dx=pos.x-init->position.x,dz=pos.z-init->position.z;
            if (other->exist_flag==1 && dx>=-40.0f && dx<=40.0f && dz>=-40.0f && dz<=40.0f)
                return NULL;
        }
    } else if (pool->insects[slot].exist_flag) return NULL;
    /* Native setup retains each slot's program pointer, loads its complete
     * graphics, establishes collision/shadow state, and calls the category hook. */
    native_setup(init,(int)slot);
    return (ACTOR *)(pool->insects+slot);
}

void af_insect_pool_bind(AfInsectController *owner,void (*setup)(AfInsectInit *,int)) {
    pool=owner;native_setup=setup;
    if (owner) {
        /* The original constructor provides the first three program buffers.
         * Additional buffers belong to this startup-loaded resident packet. */
        for (unsigned i=0;i<AF_INSECT_SLOTS;i++) {
            owner->insects[i].exist_flag=0;
            if (i>=3) owner->insects[i].native_program=programs[i-3];
        }
        if (af_insect_native_clip) af_insect_native_clip->make=make;
    }
    af_v3_insect_bind_controller(owner);
}

void af_insect_pool_unbind(AfInsectController *owner) {
    if (pool==owner) {pool=NULL;native_setup=NULL;}
    af_v3_insect_unbind_controller(owner);
}
