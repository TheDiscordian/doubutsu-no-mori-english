/* Source-sized field fish readers. Actor padding is transient, never saved. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef short s16;
extern float af_fish_sin(s16),af_fish_cos(s16);
#ifdef __mips__
#define values ((const u32 *)0x80649400u)
#else
extern const u32 af_test_fish_values[96];
#define values af_test_fish_values
#endif
#define U16(p,n) (*(u16 *)((u8 *)(p)+(n)))
#define U32(p,n) (*(u32 *)((u8 *)(p)+(n)))
#define F32(p,n) (*(float *)((u8 *)(p)+(n)))
static float value(void *actor,unsigned row,float fallback) {
    union {u32 u;float f;} v;
    unsigned size=U16(actor,0x1D8);
    if (!((u8 *)actor)[0x1DA] || size>6) return fallback;
    v.u=values[row*8+size];return v.f;
}
void af_v3_fish_position(void *actor) {
    float distance=value(actor,6,-20.0f);
    s16 angle=(s16)U16(actor,0x36);
    F32(actor,0x28)+=distance*af_fish_sin(angle);
    F32(actor,0x30)+=distance*af_fish_cos(angle);
}
void af_v3_fish_near_init(void *actor) {
    F32(actor,0x74)=value(actor,0,U32(actor,0x1D4)==31?2.0f:1.25f);
    U16(actor,0x23C)|=2;
    F32(actor,0x7C)=12.0f;
}
