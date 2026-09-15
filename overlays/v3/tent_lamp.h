#ifndef AF_V3_TENT_LAMP_H
#define AF_V3_TENT_LAMP_H
typedef unsigned char u8;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
typedef struct { u32 a,b; } LampCommand;
typedef struct {
    u8 prefix[0x298];
    LampCommand *opa;
    u8 *opa_tail;
    u8 pad[0x2A8-0x298-sizeof(LampCommand*)-sizeof(u8*)];
    LampCommand *xlu;
    u8 *xlu_tail;
} LampGraphics;
typedef struct {
    u32 magic;
    void *owner,*game;
    u8 *allocation;
    float visual,light;
    int target;
    u32 retry,failures;
} LampState;
extern LampState af_v3_lamp_state;
void af_v3_lamp_ct(void*,void*);
void af_v3_lamp_dt(void*,void*);
void af_v3_lamp_mv(void*,void*);
void af_v3_lamp_dw(void*,void*);
void af_v3_lamp_environment(void*,void*,void*);
void af_v3_lamp_room_prim(void*);
#endif
