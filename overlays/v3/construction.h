/* Fixed tables inside the already-loaded, CRC-checked resident package. */
#ifndef AF_V3_CONSTRUCTION_H
#define AF_V3_CONSTRUCTION_H
#ifdef AF_V3_SPARSE_FURNITURE
#include "sparse_furniture.h"
#elif defined(AF_V3_WESTERN_LARGE)
#define AF_V3_STATIC_IMPORT_RAM 0x80482000u
#define AF_V3_STATIC_IMPORT_COUNT 25
#define AF_V3_ITEM_TABLE_COUNT 26
#define AF_V3_ITEM_TABLE_RAM 0x80482800u
#else
#define AF_V3_STATIC_IMPORT_RAM 0x80481500u
#if defined(AF_V3_WESTERN_ITEMS)
#define AF_V3_STATIC_IMPORT_COUNT 22
#define AF_V3_ITEM_TABLE_COUNT 23
#define AF_V3_ITEM_TABLE_RAM 0x80481C00u
#elif defined(AF_V3_GARDEN_ITEMS)
#define AF_V3_STATIC_IMPORT_COUNT 15
#define AF_V3_ITEM_TABLE_COUNT 16
#define AF_V3_ITEM_TABLE_RAM 0x80481A00u
#else
#define AF_V3_STATIC_IMPORT_COUNT 9
#define AF_V3_ITEM_TABLE_COUNT 10
#define AF_V3_ITEM_TABLE_RAM 0x80481800u
#endif
#endif
#endif
