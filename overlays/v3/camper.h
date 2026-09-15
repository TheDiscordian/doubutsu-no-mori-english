#ifndef AF_V3_CAMPER_H
#define AF_V3_CAMPER_H
typedef unsigned char camp_u8;
typedef unsigned short camp_u16;
typedef unsigned int camp_u32;
typedef struct {
    camp_u32 magic, version, bytes, mask;
    camp_u8 greeted, reserved[15];
    camp_u8 animal[0x528];
    camp_u8 padding[8];
    camp_u32 guard[4];
} AfCamper;
_Static_assert(sizeof(AfCamper) == 0x560, "Complete independent native Animal owner");
typedef struct {
    camp_u16 event, texture, npc, cloth;
    camp_u8 exists, use;
    camp_u16 reserved;
} AfCamperAlias;
extern AfCamper camper;
extern volatile camp_u32 native_installed;
extern AfCamperAlias *native_event(camp_u32);
extern int native_free_event(void);
extern int native_register(camp_u32, camp_u32, camp_u32, camp_u32);
extern int selected_villager(int);
extern int selected_outfit(camp_u32);
extern void native_clear_animal(camp_u8 *);
extern void native_set_index(camp_u8 *, int);
extern void native_set_memory(const camp_u8 *, camp_u8 *);
extern const camp_u8 *native_private;
extern void original_npc_info(camp_u8 *, int);
static inline camp_u32 camper_id(void) {
    return ((camp_u32)camper.animal[0] << 8) | camper.animal[1];
}
int af_v3_camper_register(camp_u32, camp_u32, camp_u32);
void af_v3_camper_npc_info(camp_u8 *, int);
#endif
