#ifndef AF_V3_BALLOON_RELEASE_H
#define AF_V3_BALLOON_RELEASE_H
#include "balloon_actor.h"
#ifdef __mips__
#define BPTR(p,o) (*(void **)((u8 *)(p)+(o)))
#define BSETPTR(p,o,v) (BPTR(p,o)=(v))
#define BPRIVATE (*(u8 **)0x80136FD8u)
#else
extern void *af_test_balloon_pointer(void *,u32);
extern void af_test_balloon_set_pointer(void *,u32,void *);
extern u8 *af_test_balloon_private;
#define BPTR af_test_balloon_pointer
#define BSETPTR af_test_balloon_set_pointer
#define BPRIVATE af_test_balloon_private
#endif
extern int af_v3_balloon_request(void *,int,int,const void *,void *,int);
extern int af_v3_balloon_queue(void *,u32,int);
extern void af_v3_tool_getup(void *,void *,int,float);
extern void af_v3_reward_release_setup(void *,void *);
extern void af_v3_reward_release_transition(void *,void *);
extern int af_v3_reward_request(void *,int,int,int);
#endif
