/* Fixed tables inside the already-loaded, CRC-checked resident package. */
#ifndef AF_V3_CONSTRUCTION_H
#define AF_V3_CONSTRUCTION_H
#define AF_V3_STATIC_IMPORT_RAM 0x80481500u
#ifdef AF_V3_GARDEN_ITEMS
#define AF_V3_STATIC_IMPORT_COUNT 15
#define AF_V3_ITEM_TABLE_COUNT 16
#define AF_V3_ITEM_TABLE_RAM 0x80481A00u
#else
#define AF_V3_STATIC_IMPORT_COUNT 9
#define AF_V3_ITEM_TABLE_COUNT 10
#define AF_V3_ITEM_TABLE_RAM 0x80481800u
#endif
#endif
