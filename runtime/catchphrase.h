#ifndef AF_CATCHPHRASE_H
#define AF_CATCHPHRASE_H

#define AF_CATCHPHRASE_VROM 0x02E00000u
#define AF_CATCHPHRASE_WIDTH 10u
#define AF_CATCHPHRASE_COUNT 216u

int af_catchphrase_header_valid(const unsigned int *header);
int af_load_catchphrase(unsigned char *destination, unsigned int capacity,
                       unsigned int npc, const unsigned char *saved);
void af_get_catchphrase(unsigned char *destination, const unsigned char *actor);
int af_copy_catchphrase(const unsigned char *actor, unsigned char *data, int index, int length);

#endif
