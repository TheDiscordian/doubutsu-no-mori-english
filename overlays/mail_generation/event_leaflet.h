#ifndef AF_EVENT_LEAFLET_H
#define AF_EVENT_LEAFLET_H

#include "leaflet.h"

typedef struct {
    AfLeafletWork generation;
    AfLeafletChoice choice;
    AfLeafletItem items[3];
    unsigned char mail[164] __attribute__((aligned(16)));
} AfEventLeafletWork;

/* Original native event save is 156 bytes. The caller supplies the original
 * selected template/count, not fresh random selections. Work is caller-owned
 * and sixteen-byte aligned. No allocation or retained pointer belongs here.
 * The owner must retain failed selections and arrange retries across its life.
 */
int af_event_leaflet_publish(const unsigned char *event, unsigned int event_bytes,
    unsigned int template_id, unsigned int item_count, unsigned int *capital,
    AfEventLeafletWork *work);

void af_event_leaflet_clear_mail(unsigned char *);
int af_event_leaflet_receipt(unsigned char *, unsigned int);

#endif
