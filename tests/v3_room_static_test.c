#include <assert.h>
#include <string.h>
#include "room_static.h"

const RoomStaticTable af_v3_room_static_table={0x41464931,2,8,0,
    {{1139,2,15,0,0},{1808,1,1,0x71,0}}};
RoomSoundTable af_v3_test_room_sounds={ROOM_SOUND_MAGIC,1,8,0,{{1808,0x71,{0}}}};
RoomNativeTrigger af_v3_test_room_triggers[6];
RoomPrivateWallet *af_v3_test_static_private;
RoomStaticClip *af_v3_test_static_clip;
static RoomSoundActor *expected;
static void *expected_room;
static unsigned sounds,melodies;
void af_v3_room_sound_mv(RoomSoundActor *,void *,RoomRigGame *,u8 *);
void sAdo_OngenTrgStart(u32 word,float *position) {
    assert(word==0x71 && position==expected->position);++sounds;
}
static void melody(RoomSoundActor *actor,void *room,u32 index) {
    assert(actor==expected && room==expected_room && index==15);++melodies;
}
int main(void) {
    RoomSoundActor actor={0};RoomPrivateWallet player;
    RoomStaticClip clip={0};clip.melody=melody;
    expected=&actor;expected_room=&clip;
    af_v3_test_static_private=&player;af_v3_test_static_clip=&clip;
    const unsigned money[]={0,1,99999};const unsigned pulse[]={0,1,2,255};
    for (unsigned alias=0;alias<2;++alias) for (unsigned state=0;state<16;++state)
    for (unsigned m=0;m<3;++m) for (unsigned p=0;p<4;++p) {
        memset(&player,0xA5,sizeof(player));player.wallet=money[m];
        RoomPrivateWallet before=player;
        actor.index=1808+alias*1024;actor.state=state;actor.changed=pulse[p];
        sounds=0;af_v3_room_sound_mv(&actor,expected_room,0,0);
        unsigned used=money[m] && pulse[p];
        assert(sounds==used && player.wallet==money[m]-used);
        assert(!memcmp(&player,&before,0x38));assert(actor.changed==pulse[p]);
    }
    actor.changed=1;sounds=0;af_v3_test_static_private=0;
    af_v3_room_sound_mv(&actor,expected_room,0,0);assert(!sounds);
    af_v3_test_static_private=&player;
    for (unsigned alias=0;alias<2;++alias) for (unsigned state=0;state<16;++state)
    for (unsigned p=0;p<4;++p) {
        actor.index=1139+alias*1024;actor.state=state;actor.changed=pulse[p];
        melodies=sounds=0;af_v3_room_sound_mv(&actor,expected_room,0,0);
        assert(melodies==1 && sounds==0 && actor.changed==pulse[p]);
    }
    melodies=0;af_v3_test_static_clip=0;
    af_v3_room_sound_mv(&actor,expected_room,0,0);assert(!melodies);
    af_v3_test_static_clip=&clip;clip.melody=0;
    af_v3_room_sound_mv(&actor,expected_room,0,0);assert(!melodies);
    assert(!af_v3_room_static_mv(0,0));actor.index=100;
    assert(!af_v3_room_static_mv(&actor,0));
    return 0;
}
