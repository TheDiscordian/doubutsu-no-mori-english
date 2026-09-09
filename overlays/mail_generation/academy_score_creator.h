#ifndef AF_ACADEMY_SCORE_CREATOR_H
#define AF_ACADEMY_SCORE_CREATOR_H

#include "academy_creator.h"

#define AF_ACADEMY_SERIES_BYTES 1440u
/* FA reply descriptor: points BE32, item BE16, reserved BE16, year BE16,
 * month/day bytes, template BE16, zero gift BE16, FA, paper 51. The animal
 * slot borrows the original ten-byte series string only for templates 3A/3B.
 */
int af_academy_score_mail_create(AfNpcMailCreateWork *,unsigned char *,AfNpcMailSession **,unsigned int *);

#endif
