#ifndef AF_EVENT_ACTOR_H
#define AF_EVENT_ACTOR_H

#include "event_leaflet.h"

typedef struct {
    unsigned int active, template_id, count, capital;
    unsigned char source[156];
} AfEventLeafletPending;

extern AfEventLeafletPending af_event_pending;
extern AfEventLeafletWork af_event_work;
extern unsigned int af_event_count, af_event_busy;
extern unsigned char af_event_saved[];
extern unsigned char af_event_init_flag;
extern unsigned int af_mail_generation_capital;

void af_event_native_sale_fields(const unsigned char *, unsigned int);
int af_event_native_special_init(void);
void af_event_native_save(void *, void *);
void af_event_native_destroy(void *, void *);

void af_event_sale_fields(const unsigned char *, unsigned int);
int af_event_register(unsigned int, unsigned int, unsigned int);
int af_event_retry(void);
int af_event_special_init(void);
void af_event_save(void *, void *);
void af_event_destroy(void *, void *);

#endif
