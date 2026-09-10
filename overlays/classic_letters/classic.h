#ifndef AF_CLASSIC_LETTERS_H
#define AF_CLASSIC_LETTERS_H

#include "../mail_generation/npc_creator.h"

/* Retained diagnostic/old-version templates only. Live scheduling and the
 * complete wider-field owner routes keep their existing creators. */
static unsigned int af_classic_mask(unsigned int number) {
    if (number == 0u || number == 0x182u || number == 0x183u
            || (number >= 0x186u && number <= 0x189u)) return 0;
    if (number == 1u) return 0xFFC00u;
    if (number == 0x4Du || number == 0xBFu) return 1u;
    if (number >= 0x53u && number <= 0x56u) return 0x3Eu;
    if (number >= 0x58u && number <= 0x5Bu) return 0x30u;
    return ~0u;
}

int af_classic_mail_create(AfNpcMailCreateWork *, unsigned char *, AfNpcMailSession **, unsigned int *);
int af_notice_seasonal_create(AfNpcMailCreateWork *, unsigned char *, AfNpcMailSession **, unsigned int *);
void af_classic_load(unsigned char *, unsigned int *, unsigned char *, unsigned char *, unsigned int);
int af_classic_install(void);

#endif
