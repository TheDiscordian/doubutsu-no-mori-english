#ifndef AF_FORTUNE_ACTOR_H
#define AF_FORTUNE_ACTOR_H

#include "fortune_slip.h"

#define AF_MIKO_PENDING_OFFSET 0x948u
#define AF_MIKO_INSTANCE_BYTES 0x960u
#define AF_MIKO_MAIL_OFFSET 0x40Au

enum { AF_MIKO_EMPTY, AF_MIKO_ARMED, AF_MIKO_SELECTED, AF_MIKO_DELIVERED };

/* Native pointers are four bytes. Packing also keeps the host mock's larger
 * pointer aligned with the same native actor-prefix offset.
 */
typedef struct __attribute__((packed,aligned(4))) {
    AfFortuneSlipChoice choice;
    unsigned int state;
    unsigned int capital;
    unsigned char *owner;
    unsigned int reserved;
} AfMikoPending;

typedef struct {
    AfFortuneSlipWork generation;
    unsigned char mail[164];
} AfMikoWork;

/* The two replacements occupy native init-table slot two and process-table
 * slot three. All other actor actions, including the charge, remain native.
 * Pending choices belong to this actor and survive failed give attempts.
 * Work is allocated and freed within one synchronous call, never retained.
 */
void af_miko_fortune_init(unsigned char *actor, void *play);
void af_miko_fortune_give(unsigned char *actor, void *play);

#endif
