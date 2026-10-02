/* GameCube freshwater patrol, on the retained N64 actor layout.
 * Port the complete SWIM/WAIT/ESCAPE callbacks and initializers together.
 * One N64 update spans two donor updates: phase increments and raw heading
 * additions are evaluated twice; elapsed timers are stored in 30-Hz units.
 * Native collision, current, player, bobber, and action services retain their
 * platform layouts and the installed creature/golden-rod adaptations.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef short s16;
typedef unsigned int u32;
#define H(p,n) (*(s16 *)((u8 *)(p)+(n)))
#define U(p,n) (*(u16 *)((u8 *)(p)+(n)))
#define W(p,n) (*(int *)((u8 *)(p)+(n)))
#define F(p,n) (*(float *)((u8 *)(p)+(n)))
extern float af_patrol_random(void),af_patrol_random2(void),af_patrol_sin(s16);
extern int af_patrol_chase_angle(s16 *,s16,s16),af_patrol_chase_float(float *,float,float);
extern int af_fresh_player_near(void *,void *),af_fresh_search(void *,void *),af_fresh_wall(void *);
extern s16 af_fresh_flow_reverse(void *);
extern void af_fresh_flow(void *);
extern void af_fresh_setup(void *,int);
static int timer(void *a) {if (W(a,0x214)) --W(a,0x214);return W(a,0x214);}
static void uki(void *a,void *g) {
    if (!af_fresh_player_near(a,g) && af_fresh_search(a,g)) af_fresh_setup(a,3);
}
static int speed(void *a,float target,float amplitude,int curved) {
    int done=0;
    for (int tick=0;tick<2;tick++) {
        done=af_patrol_chase_float((float *)((u8 *)a+0x224),target,2.5f);
        if (curved) {
            if (F(a,0x224)>5.0f) H(a,0xDE)=(s16)(H(a,0xDE)+H(a,0x22C));
            else if (F(a,0x224)==5.0f) H(a,0x22C)=(s16)(H(a,0x22C)-H(a,0x36))/36;
        }
        if (done) break;
    }
    s16 angle=(s16)(int)(F(a,0x224)*(65536.0f/360.0f));
    F(a,0x74)=amplitude*af_patrol_sin(angle);
    if (curved && done) H(a,0x36)=H(a,0xDE);
    return done;
}
void af_v3_freshwater_swim_init(void *a) {
    switch (((u8 *)a)[0x23E]) {
    case 0:F(a,0x224)=50.0f;H(a,0x22C)=H(a,0x22E)=0;break;
    case 1:
        F(a,0x224)=0.0f;H(a,0x22C)=0;
        H(a,0x22E)=(s16)(int)(af_patrol_random2()*32768.0f);
        H(a,0x36)=(s16)(H(a,0x36)+H(a,0x22E));break;
    case 2:
        U(a,0x23C)|=0x80;F(a,0x224)=0.0f;H(a,0x22C)=af_fresh_flow_reverse(a);
        H(a,0x22E)=(s16)(H(a,0x36)+(int)(af_patrol_random2()*16384.0f));
        H(a,0xDE)=H(a,0x36);break;
    }
    F(a,0x74)=F(a,0x7C)=0.0f;
}
void af_v3_freshwater_wait_init(void *a) {
    U(a,0x23C)&=(u16)~2u;
    /* For this nonnegative count, trunc(x*2)/2 equals trunc(x). */
    W(a,0x214)=(int)(100.0f+af_patrol_random()*30.0f);
    F(a,0x74)=-0.15f+af_patrol_random2()*0.2f;F(a,0x7C)=0.0f;
}
void af_v3_freshwater_escape_init(void *a) {
    H(a,0x228)=0;W(a,0x214)=50;F(a,0x74)=2.0f;
}
void af_v3_freshwater_swim(void *a,void *g) {
    if (af_fresh_wall(a)) {af_fresh_setup(a,2);return;}
    int done=0;
    switch (((u8 *)a)[0x23E]) {
    case 0:done=speed(a,360.0f,0.5f,0);break;
    case 1:
        done=speed(a,180.0f,0.5f,0);
        if (done) H(a,0x36)=H(a,0xDE);
        break;
    case 2:
        if (U(a,0x23C)&0x80) {
            s16 target=H(a,0x22E);
            af_patrol_chase_angle((s16 *)((u8 *)a+0x36),target,0x400);
            H(a,0xDE)=H(a,0x36);
            s16 angle=(s16)(H(a,0x36)-target);
            s16 distance=(s16)(angle<0?-(int)angle:angle);
            if (distance<0x400) U(a,0x23C)&=(u16)~0x80u;
        } else done=speed(a,180.0f,1.0f,1);
        break;
    }
    if (done) af_fresh_setup(a,1);else uki(a,g);
}
void af_v3_freshwater_wait(void *a,void *g) {
    af_fresh_flow(a);
    if (!timer(a)) {
        float roll=af_patrol_random()*3.0f;
        ((u8 *)a)[0x23E]=roll<1.0f?0:roll<2.0f?1:2;
        af_fresh_setup(a,0);
    } else uki(a,g);
}
void af_v3_freshwater_escape(void *a,void *g) {
    if (af_fresh_player_near(a,g)) return;
    if (af_fresh_search(a,g)) {af_fresh_setup(a,3);return;}
    if ((U(a,0x23C)&0x40) || !af_fresh_wall(a)) {
        if (!timer(a)) {U(a,0x23C)&=(u16)~0x40u;af_fresh_setup(a,1);}
        else {
            af_patrol_chase_float((float *)((u8 *)a+0x74),0.0f,0.02f);
            af_patrol_chase_float((float *)((u8 *)a+0x74),0.0f,0.02f);
        }
    }
}
