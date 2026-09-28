#ifndef AF_V3_HOLIDAY_FISHING_ANGLER_H
#define AF_V3_HOLIDAY_FISHING_ANGLER_H
#include "holiday_fishing_live.h"
typedef struct {
    int (*message)(AFHFH);
    void (*random_top)(void),(*topname)(void);
    int (*size)(int);
} AFHFClip;
typedef struct {const AFHFClip *previous,*source;void *owner;} AFHFClipState;
typedef struct {unsigned int words[4];} AFHFNativePerson;
extern AFHFClipState af_hf_clip_state;
extern const AFHFClip *af_hf_native_clip;
extern const AFHFClip af_hf_source_clip;
extern const AFHFClip af_hf_bridge_clip;
extern void af_hf_native_continue(void *,int),af_hf_native_start_message(int);
extern int af_hf_native_message_number(void *),af_hf_native_number(AFHFB *,int,int);
extern void af_hf_native_halt(void);
int af_hf_clip_lifecycle(void *,int);
void af_hf_angler_continue(void *,int),af_hf_angler_start_message(int);
int af_hf_angler_message_number(void *),af_hf_angler_number(AFHFB *,int,int);
void af_hf_angler_winner(AFHFNativePerson);
#endif
