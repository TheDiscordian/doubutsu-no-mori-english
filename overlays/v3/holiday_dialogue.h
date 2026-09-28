#ifndef AF_V3_HOLIDAY_DIALOGUE_H
#define AF_V3_HOLIDAY_DIALOGUE_H
#include "holiday_talk.h"

typedef struct {
    unsigned int magic,version,count;
    struct {unsigned int first,end,target;} ranges[3];
    unsigned char days[31][4],events[29][16];
} AFHolidayDialogue;
typedef struct {
    void *actor,*window;
    int (*item_name)(unsigned char *,unsigned int,unsigned int);
    const unsigned char *(*town_name)(void);
    void (*item)(void *,int,const unsigned char *,int);
    void (*free_string)(void *,int,const unsigned char *,int);
    void (*turn)(unsigned char);
    void (*camera)(int);
    void (*message)(int);
    void (*continuation)(void *,int);
    void (*listen)(void);
    void (*start)(void *);
    void (*order)(int,int,unsigned short);
} AFHolidayTransport;

/* Official IDs are stable independently of the selected imports. Reject an
 * unknown ID rather than accidentally displaying an unrelated native message. */
int af_holiday_message(const AFHolidayDialogue *,unsigned int donor);
int af_holiday_transport(const AFHolidayDialogue *,const AFHolidayTransport *,const AFHolidayAction *);
#endif
