#ifndef AF_ITEM_NAME_H
#define AF_ITEM_NAME_H

#define AF_ITEM_WIDTH 16u
#define AF_ITEM_VROM 0x02A00000u
#define AF_ITEM_COUNT 4544u

int af_item_name_index(unsigned int item);
int af_item_header_valid(const unsigned int *header);
int af_load_item_name(unsigned char *destination, unsigned int capacity, unsigned int item);

#endif
