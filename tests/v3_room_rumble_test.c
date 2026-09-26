#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/room_rumble.c"
#include "../overlays/v3/room_reactions.c"
#define AF_V3_ROOM_REACTIONS
#include "../overlays/v3/room_materials.c"
RoomMaterialTable af_v3_test_room_materials;
void *_Matrix_to_Mtx_new(void *gfx) { (void)gfx;assert(0);return 0; }
RoomReactionState af_v3_test_reaction_state;
const RoomRumbleBank *af_v3_test_rumble_waves;
static union { int align;u8 bytes[0xD00]; } player;
static u32 interrupt_mask=0x3FFF01;
static unsigned shock_requests;
u32 af_rumble_mask(u32 value) { u32 old=interrupt_mask;interrupt_mask=value;return old; }
u8 *af_reaction_player(void *game) { assert(game);return player.bytes; }
int af_reaction_shock(void *game,float frames,s16 angle,int swing) {
    assert(game && frames==10 && angle==-1234 && !swing && interrupt_mask==0x3FFF01);
    ++shock_requests;return 0;
}

/* The four actual donor functions are extracted unchanged for this test.
   Waveforms come from the checked disc binary, not the C initializer text. */
typedef float f32;
typedef struct { int type,frames; f32 step; } mVibInfo_elem_entry_c;
typedef struct {
    mVibInfo_elem_entry_c entries[3];
    f32 step0,step1;
    int now_entry,state_idx;
    f32 frame_intensity;
    int entry_frame;
    f32 now_intensity;
    int command;
} mVibElem_c;
typedef struct {
    mVibElem_c *target_elem,elements[4];
    int num_elements,force_stop,last_force_stop;
} mVibInfo_c;
typedef struct { const u8 *data;int count; } mVibWorkData_c;
static mVibWorkData_c mVW_data[16];
enum { mVibctl_ELEM_ENTRY_ATTACK,mVibctl_ELEM_ENTRY_SUSTAIN,mVibctl_ELEM_ENTRY_RELEASE,
       mVibctl_ELEM_ENTRY_END,mVibctl_ELEM_NUM=4 };
enum { PAD_MOTOR_STOP,PAD_MOTOR_RUMBLE,PAD_MOTOR_STOP_HARD };
#define bzero(p,n) memset(p,0,n)
#define bcopy(s,d,n) memmove(d,s,n)
#include "donor_vibration.inc"

static int initialised,accesses,init_result,access_result,last_command;
static void *expected_queue;
static int af_test_motor_init(void *q,void *p,int channel) {
    assert(q==expected_queue && p && !channel && interrupt_mask==0x3FFF01);++initialised;return init_result;
}
int af_rumble_motor_init(void *q,void *p,int c) {return af_test_motor_init(q,p,c);}
int af_rumble_motor_access(void *p,int on) {
    assert(p && (on==0 || on==1) && interrupt_mask==0x3FFF01);++accesses;last_command=on;return access_result;
}

static u32 donor_step(mVibInfo_c *state) {
    for(int i=0;i<state->num_elements;++i) mVibElem_move(state->elements+i);
    for(int i=state->num_elements-1;i>=0;--i)
        if(state->elements[i].now_entry>=mVibctl_ELEM_ENTRY_END) mVibInfo_elem_delete(state,i);
    mVibInfo_set_target_elem(state);
    return state->target_elem ? (u32)state->target_elem->command : 0;
}
static u32 read32(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static u16 read16(const u8 *p) {return (u16)((u16)p[0]<<8|p[1]);}
static unsigned checks;
static void compare(RoomRumbleEnvelope *ours,mVibInfo_c *donor,const RoomRumbleBank *bank) {
    u32 a=af_v3_rumble_step(ours,bank),b=donor_step(donor);
    assert(a==b && ours->count==(u32)donor->num_elements);
    assert(!memcmp(ours->elements,donor->elements,sizeof(ours->elements)));
    ++checks;
}
static void add(RoomRumbleEnvelope *ours,mVibInfo_c *donor,const RoomRumbleBank *bank,
        int percent,int a,int s,int r,int af,int sf,int rf,float distance) {
    int before=donor->num_elements;
    mVibInfo_elem_entry(donor,percent,a,s,r,af,sf,rf,distance);
    assert(af_v3_rumble_entry(ours,bank,percent,a,s,r,af,sf,rf,distance)==
        (donor->num_elements>before));
    assert(ours->count==(u32)donor->num_elements);
    assert(!memcmp(ours->elements,donor->elements,sizeof(ours->elements)));
}
int main(int argc,char **argv) {
    assert(argc==2);
    union { u32 align;u8 data[1024]; } storage={0};
    FILE *f=fopen(argv[1],"rb");assert(f);
    size_t n=fread(storage.data,1,sizeof(storage.data),f);assert(!ferror(f));fclose(f);
    assert(n>=80 && n<=1024);
    RoomRumbleBank *bank=(RoomRumbleBank *)storage.data;
    u32 header[4];for(int i=0;i<4;++i) header[i]=read32(storage.data+i*4);
    for(int i=0;i<16;++i) {
        u16 off=read16(storage.data+16+i*4),count=read16(storage.data+18+i*4);
        bank->waves[i]=(RoomRumbleWave){off,count};
        assert(off>=80 && off+count<=n);mVW_data[i]=(mVibWorkData_c){storage.data+off,count};
    }
    memcpy(storage.data,header,sizeof(header));assert(bank->bytes==n);
    for(int wave=0;wave<16;++wave) for(int mask=1;mask<8;++mask) {
        RoomRumbleEnvelope ours={0};mVibInfo_c donor={0};
        add(&ours,&donor,bank,100,wave,wave,wave,mask&1?7:0,mask&2?7:0,mask&4?7:0,0);
        for(int frame=0;frame<25;++frame) compare(&ours,&donor,bank);
        assert(!ours.count);
    }
    RoomRumbleEnvelope ours={0};mVibInfo_c donor={0};
    add(&ours,&donor,bank,100,1,1,13,0,7,7,0);
    for(int i=0;i<20;++i) compare(&ours,&donor,bank);
    for(int i=0;i<6;++i) add(&ours,&donor,bank,100,1,i,13,2,7,5,(float)(i*30));
    for(int i=0;i<30;++i) {
        compare(&ours,&donor,bank);
        if(i==4 || i==9) add(&ours,&donor,bank,60,3,1,15,0,4,9,40.5f);
    }
    add(&ours,&donor,bank,100,1,1,13,0,0,0,0);
    add(&ours,&donor,bank,100,1,1,13,0,7,7,640);
    assert(!af_v3_rumble_entry(&ours,bank,100,16,1,13,0,7,7,0));
    assert(!af_v3_rumble_entry(&ours,bank,100,1,1,13,-1,7,7,0));
    add(&ours,&donor,bank,100,1,1,13,0,7,7,0);
    af_v3_rumble_clear(&ours);assert(!ours.count);
    ours.count=5;assert(!af_v3_rumble_step(&ours,bank) && !ours.count);
    u16 save=bank->waves[0].offset;bank->waves[0].offset=1024;
    assert(!af_v3_rumble_step(&ours,bank));bank->waves[0].offset=save;

    struct { u32 before;RoomRumbleMotor motor;u32 after; } guarded={.before=0x13572468,.after=0x24681357};
    RoomRumbleMotor *motor=&guarded.motor;int queue=0;expected_queue=&queue;
    af_v3_rumble_motor(motor,&queue,1,0,0);assert(!initialised && !accesses);
    init_result=5;af_v3_rumble_motor(motor,&queue,1,1,0);
    assert(initialised==1 && !accesses && motor->retry==30);
    for(int i=0;i<30;++i) af_v3_rumble_motor(motor,&queue,1,1,0);
    assert(initialised==1);init_result=0;
    af_v3_rumble_motor(motor,&queue,1,1,0);assert(initialised==2 && accesses==1 && last_command==1);
    af_v3_rumble_motor(motor,&queue,1,1,0);assert(accesses==1);
    af_v3_rumble_motor(motor,&queue,2,1,0);assert(accesses==2 && !last_command);
    af_v3_rumble_motor(motor,&queue,0,1,0);assert(accesses==2);
    af_v3_rumble_motor(motor,&queue,1,1,0);assert(accesses==3 && last_command==1);
    access_result=4;af_v3_rumble_motor(motor,&queue,0,1,0);
    assert(!motor->ready && motor->on==2);
    access_result=0;for(int i=0;i<31;++i) af_v3_rumble_motor(motor,&queue,0,1,0);
    assert(motor->ready && !motor->on && accesses==5 && !last_command);
    af_v3_rumble_motor(motor,&queue,1,1,1);assert(initialised==4 && accesses==6);
    af_v3_rumble_motor(motor,&queue,0,0,0);assert(!motor->ready && !motor->on && accesses==6);
    af_v3_rumble_motor(motor,&queue,0,1,0);assert(initialised==4 && accesses==6);
    assert(guarded.before==0x13572468 && guarded.after==0x24681357);
    motor->on=2;init_result=11;
    af_v3_rumble_motor(motor,&queue,0,1,0);assert(!motor->ready && !motor->on);
    for(int i=0;i<40;++i) af_v3_rumble_motor(motor,&queue,0,1,0);
    assert(initialised==5 && accesses==6);init_result=0;

    /* Full material reaction, shared envelope, controller transport, and
       30/60-Hz timing in one fixture, including suppressed shock requests. */
    af_v3_test_rumble_waves=bank;
    RoomRig actor,untouched;memset(&actor,0xA5,sizeof(actor));untouched=actor;
    af_v3_test_room_materials=(RoomMaterialTable){.magic=ROOM_MATERIAL_MAGIC,.count=1,
        .stride=40,.rows={{.index=1804,.bytes=128,.mode=2,.segment=8,.frames=2,.models=1,
                          .frame_bytes=32,.frame_offsets={8,40},.state_offset=0x1A4,.kind=1,.lifecycle=2}}};
    actor.index=1804;untouched.index=1804;u8 model[128]={0};
    af_v3_room_material_ct(&actor,model);
    untouched.joint[0][0]=0;untouched.joint[0][1]=0;
    assert(!memcmp(&actor,&untouched,sizeof(actor)));
    u8 pad[0x480]={0};pad[0x2C9]=1;pad[0x16]=1;
    RoomRigGame game={0};int room=0;
    *(s16 *)(player.bytes+0xDE)=-1234;
    assert(af_v3_room_material_mv(&actor,0,&game,model));
    assert(!af_v3_test_reaction_state.magic && !shock_requests);
    for(int frame=0;frame<26;++frame) {
        actor.changed=frame==0;
        if(frame==3) *(int *)(player.bytes+0xCF0)=0x61;
        assert(af_v3_room_material_mv(&actor,&room,&game,model));
        if(frame<15) assert(!af_v3_test_reaction_state.envelope.count);
        if(frame==15) assert(af_v3_test_reaction_state.envelope.count==1);
        if(frame<25) assert(actor.joint[0][0]==1 && actor.joint[0][1]==49-frame*2);
        else assert(!actor.joint[0][0] && !actor.joint[0][1]);
        af_v3_room_rumble_retrace(&queue,pad);
        af_v3_room_rumble_retrace(&queue,pad);
    }
    assert(shock_requests==3 && !af_v3_test_reaction_state.pending);
    assert(!af_v3_test_reaction_state.envelope.count && !af_v3_test_reaction_state.motor.on);
    /* Stop during a suspended owner and pre-NMI, without blocking under the
       game's interrupt mask or sharing a Controller Pak state object. */
    for(int stop=0;stop<2;++stop) {
        af_v3_test_reaction_state.heartbeat=af_v3_test_reaction_state.tick;
        assert(af_v3_rumble_entry(&af_v3_test_reaction_state.envelope,bank,100,1,1,1,0,60,60,0));
        af_v3_room_rumble_retrace(&queue,pad);assert(af_v3_test_reaction_state.motor.on==1);
        if(stop) pad[0x47E]=1;
        for(int i=0;i<(stop?1:6);++i) af_v3_room_rumble_retrace(&queue,pad);
        assert(!af_v3_test_reaction_state.envelope.count && !af_v3_test_reaction_state.motor.on);
    }
    assert(interrupt_mask==0x3FFF01);
    printf("%u donor frame comparisons; motor detection, start, stop, failed-stop retry, replacement, and bounds pass\n",checks);
    return 0;
}
