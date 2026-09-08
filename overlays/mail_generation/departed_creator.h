#ifndef AF_DEPARTED_CREATOR_H
#define AF_DEPARTED_CREATOR_H

#include "mother_creator.h"

/* Twelve-byte synchronous animal argument: DM, native eight-byte departed
 * villager memory, reserved zero, FD. Player points to the unchanged 16-byte
 * personal identity. Condition/origin are zero and visitor reply is null.
 */
int af_departed_mail_create(AfNpcMailCreateWork *,unsigned char *,AfNpcMailSession **,unsigned int *);

#endif
