#ifndef AF_DISPLAY_NAME_H
#define AF_DISPLAY_NAME_H

#define AF_DISPLAY_NAME_WIDTH 8u
#define AF_DISPLAY_NAME_VROM 0x02C00000u
#define AF_DISPLAY_NAME_COUNT 280u
#define AF_VILLAGER_COUNT 216u
#define AF_SPECIAL_COUNT 64u

int af_display_name_index(unsigned int npc);
int af_display_name_header_valid(const unsigned int *header);
int af_load_display_name(unsigned char *destination, unsigned int capacity, unsigned int npc);

#endif
