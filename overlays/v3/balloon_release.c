/* Extend the native creature action; preserve original fish/insect consumers. */
#include "balloon_release.h"

int af_v3_balloon_request(void *game,int type,int flag,const void *data,void *existing,int priority) {
    if (!game || !data) return 0;
    void *player=BFN(0x800B1C84u,void *,void *)(game);
    if (!player) return 0;
    if (type==2) {
        unsigned shape=*(const u32 *)data;
        void *owned=BPTR(player,0x13A0);
        if (shape>=8u || !owned || (existing && existing!=owned) ||
                af_v3_player_selected_equipment(0x2244u+shape)!=(int)(91u+shape)) return 0;
    }
    if (!BFN(0x808D71F8u,int,void *,int,const void *,void *,int)(game,type,data,existing,priority)) return 0;
    BWORD(player,0xD70)=flag!=0;
    return 1;
}

void af_v3_balloon_submenu(void *player,void *game) {
    if (!player || !game) return;
    u8 *change=BFN(0x800B1F74u,u8 *,void)();
    (void)af_v3_balloon_request(game,BWORD(change,8),BWORD(change,0x20),change+12,0,31);
}

void af_v3_balloon_release_setup(void *player,void *game) {
    if (!player || !game) return;
    if (BWORD(player,0xD58)!=2) { af_v3_reward_release_setup(player,game);return; }
    void *flying=BPTR(player,0xD6C);
    int birth=flying==0,flag=BWORD(player,0xD70),animation,part;
    if (birth) {
        BalloonAngle angle={0,BSHORT(player,0xDE),0};
        BalloonPosition position=BPOS(player,0x28);
        float sine=BFN(0x80099A94u,float,s16)(angle.y);
        float cosine=BFN(0x80099A54u,float,s16)(angle.y);
        position.x+=12.5f*sine+10.0f*cosine;
        position.y+=17.5f;
        position.z+=10.0f*cosine-12.5f*sine;
        flying=BPTR(player,0x13A0);
        if (!af_v3_balloon_fly(flying,game,BWORD(player,0xD5C),&angle,0,&position,-1.0f,7.0f)) flying=0;
    }
    BWORD(player,0xD10)=2;BSETPTR(player,0xD14,flying);
    BREAL(player,0xD18)=0;BWORD(player,0xD1C)=birth;BWORD(player,0xD20)=flag!=0;
    BWORD(player,0x13A4)=flying==0;
    BFN(0x808B846Cu,void,void *,int,float,int *,int *)(player,0,-5.0f,&animation,&part);
    BFN(0x808B4924u,void,void *,void *,int,int,float,float,float,float,int)
        (player,game,0,animation,1.0f,1.0f,1.0f,-5.0f,part);
    BFN(0x808B3BD0u,void,void *,void *)(player,game);
}

void af_v3_balloon_release_transition(void *player,void *game) {
    if (!player || !game) return;
    if (BWORD(player,0xD10)!=2) { af_v3_reward_release_transition(player,game);return; }
    BREAL(player,0xD18)+=1.0f;
    if (BREAL(player,0xD18)>=42.0f && BWORD(player,0x13A4)) {
        BFN(0x808B3648u,void,void *)(player);
        if (BWORD(player,0xD20)) (void)af_v3_reward_request(game,118,3,34);
        else (void)BFN(0x808C1064u,int,void *,float,int,int)(game,-5.0f,0,1);
        BREAL(player,0xD18)=42.0f;
    }
}

__attribute__((section(".af_balloon_queue")))
int af_v3_balloon_queue(void *game,u32 item,int flag) {
    unsigned shape=item-0x2244u;
    if (!game || shape>=8u || af_v3_player_selected_equipment(item)!=(int)(91u+shape)) return 0;
    void *player=BFN(0x800B1C84u,void *,void *)(game);
    if (!player || !BPTR(player,0x13A0)) return 0;
    u8 *change=BFN(0x800B1F74u,u8 *,void)();
    BWORD(change,0)=81;BWORD(change,8)=2;BWORD(change,12)=(int)shape;
    for (unsigned at=16;at<32;at+=4) BWORD(change,at)=0;
    BWORD(change,0x20)=flag!=0;BWORD(change,4)=1;
    return 1;
}
