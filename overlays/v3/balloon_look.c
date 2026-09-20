/* Donor head tracking: two source smoothing steps per native update. */
#include "balloon_release.h"
static int clamp_angle(int angle,int limit) {
    if (angle>32768) angle-=65536;
    else if (angle< -32768) angle+=65536;
    if (angle>limit) return limit;
    if (angle< -limit) return -limit;
    return angle;
}

void af_v3_balloon_look(void *player) {
    if (!player) return;
    if (BWORD(player,0xD10)!=2) { BFN(0x808D7570u,void,void *)(player);return; }
    Balloon *flying=BPTR(player,0xD14);
    s16 yaw=0,pitch=0;
    int end=1;
    if (flying) {
        if (flying->mode==1 || flying->pending>=0) {
            end=0;
            if (BREAL(player,0xD18)<30.0f) {
                float x=BREAL(flying,0x28)-BREAL(player,0x48);
                float y=BREAL(flying,0x2C)-BREAL(player,0x4C)+50.0f;
                float z=BREAL(flying,0x30)-BREAL(player,0x50);
                float distance=BFN(0x800DADC4u,float,float,float)(x,z);
                if (distance>=10.0f) {
                    yaw=(s16)clamp_angle(BFN(0x800E0008u,s16,float,float)(z,x)-BSHORT(player,0xDE),0x2AAA);
                    pitch=(s16)clamp_angle(BFN(0x800E0008u,s16,float,float)(distance,y)-BSHORT(player,0xDC),0x1555);
                }
            }
        } else BSETPTR(player,0xD14,0);
    }
    for (int step=0;step<2;step++) {
        BFN(0x8009A974u,void,s16 *,s16,float,s16,s16)
            (&BSHORT(player,0x1136),yaw,yaw?.1339745962f:.2928932309f,500,0);
        BFN(0x8009A974u,void,s16 *,s16,float,s16,s16)
            (&BSHORT(player,0x1138),pitch,pitch?.1339745962f:.2928932309f,pitch?500:200,0);
    }
    BWORD(player,0x13A4)=end;
}
