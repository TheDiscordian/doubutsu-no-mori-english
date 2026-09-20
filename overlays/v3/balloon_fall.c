/* Transfer the current hand pose before destroying the held representation. */
#include "balloon_release.h"

void af_v3_balloon_getup(void *player,void *game,int kind,float morph) {
    if (!player || !game) return;
    BWORD(player,0x13A8)=-1;
    if ((unsigned)(kind-91)<8u && BPTR(player,0x13A0)) {
        BalloonAngle angle={(s16)(BSHORT(player,0x1370)+BSHORT(player,0x1372)+BSHORT(player,0x1388)),
                            BSHORT(player,0xDE),0};
        BalloonPosition position=BPOS(player,0x103C);
        if (af_v3_balloon_fly(BPTR(player,0x13A0),game,kind-91,&angle,BSHORT(player,0x1376),
                              &position,BREAL(player,0xA28),7.0f)) {
            BWORD(player,0x13A8)=kind-91;kind=-1;
            if (BFN(0x8007D90Cu,int,void)()<=0 && BPRIVATE) BSHORT(BPRIVATE,0x3EC)=0;
        }
    }
    af_v3_tool_getup(player,game,kind,morph);
}

void af_v3_balloon_getup_transition(void *player,void *game,int ended) {
    if (!player || !game || !ended) return;
    int shape=BWORD(player,0x13A8);
    if (shape<0) {
        BFN(0x808B3648u,void,void *)(player);
        (void)BFN(0x808C1064u,int,void *,float,int,int)(game,-5.0f,0,1);
    } else {
        int data[4]={shape,0,0,0};
        (void)af_v3_balloon_request(game,2,0,data,BPTR(player,0x13A0),30);
    }
}
