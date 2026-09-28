#ifndef AF_V3_NPC_STREAM_DRAW_H
#define AF_V3_NPC_STREAM_DRAW_H
typedef unsigned char AFNpcU8;
typedef unsigned short AFNpcU16;
typedef unsigned int AFNpcU32;
typedef int (*AFNpcDrawCallback)(void *,void *,int,void *,void *,void *,void *,void *);
/* Offsets address the complete converted texture bank, whose palette is first.
 * This is model-format metadata, not an independently selectable import. */
typedef struct {
    AFNpcU16 name,texture_bytes,body_offset,mouth_count;
    AFNpcU16 eyes[8],mouths[6];
} AFNpcStreamRecord;
_Static_assert(sizeof(AFNpcStreamRecord)==36,"Streamed NPC texture record");
/* The native actor registry supplies this lookup when the actor is installed.
 * It must return NULL for every ordinary/non-streamed character. */
const AFNpcStreamRecord *af_v3_npc_stream_record(unsigned int name);
void af_v3_npc_stream_draw(void *,void *,void *,AFNpcDrawCallback,AFNpcDrawCallback,void *);
#endif
