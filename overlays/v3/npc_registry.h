#ifndef AF_V3_NPC_REGISTRY_H
#define AF_V3_NPC_REGISTRY_H
#include "npc_stream_draw.h"
enum {
    AF_NPC_EXTRA_MAGIC=0x41464E58, AF_NPC_SLOT_MAGIC=0x41464E53,
    AF_NPC_SLOT_GUARD=0x4E504347,
    AF_NPC_EXTRA_IMPLEMENTED=1, AF_NPC_EXTRA_SELECTED=2,
    AF_NPC_EXTRA_MAX=8
};
typedef struct {
    unsigned short name,profile;
    unsigned int flags,actor_bytes,slots,stride;
    unsigned char *area,*descriptor;
    const unsigned char *draw;
    const AFNpcStreamRecord *stream;
    unsigned int voice;
    unsigned short model_bank,texture_bank;
} AFNpcExtra;
typedef struct {
    unsigned int magic,version,count,stride;
    AFNpcExtra rows[AF_NPC_EXTRA_MAX];
} AFNpcExtras;
#ifdef __mips__
_Static_assert(sizeof(AFNpcExtra)==44,"Native additional NPC record");
#endif
extern const AFNpcExtras af_v3_npc_extras;
void *af_v3_npc_extra_descriptor(int);
int af_v3_npc_extra_allocate(void **,const void *,void *,const unsigned char *,unsigned short);
void af_v3_npc_extra_free(void *);
int af_v3_npc_extra_draw(void *,unsigned int);
unsigned int af_v3_npc_extra_voice(const unsigned char *);
const AFNpcExtra *af_v3_npc_extra_owned(const void *);
/* Both the new model renderer and native constructor use this one registry. */
const AFNpcStreamRecord *af_v3_npc_stream_record(unsigned int);

/* Checked prior implementations, bound by the installer; no caller bypasses
 * existing normal villagers, campsite, balloons, or voice conversion. */
void *af_npc_previous_descriptor(int);
int af_npc_previous_allocate(void **,const void *,void *,const unsigned char *,unsigned short);
void af_npc_previous_free(void *);
void af_npc_allocation_failed(void *,unsigned short);
int af_npc_previous_draw(void *,unsigned int);
unsigned int af_npc_previous_voice(const unsigned char *);
#endif
