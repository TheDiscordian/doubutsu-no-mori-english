#ifndef AF_MOTHER_CREATOR_H
#define AF_MOTHER_CREATOR_H

#include "npc_creator.h"

/* Optional system dispatch uses the existing synchronous loader unchanged.
 * Its twelve-byte animal input becomes an explicit, collision-free descriptor:
 * 'AFMO', big-endian template/gift halfwords, paper, two zero bytes, and FE.
 * A real native animal identity starts with E000..E0FF and has looks 0..5.
 * Player, condition zero, foreign zero, and null visitor inputs remain required.
 * The descriptor is copied/consumed during this call, never retained in a save.
 */
int af_system_mail_create(AfNpcMailCreateWork *,unsigned char *,AfNpcMailSession **,unsigned int *);

#endif
