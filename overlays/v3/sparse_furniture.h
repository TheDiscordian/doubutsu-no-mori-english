/* Fixed canonical slots; absent imports remain zero, never compacted. */
#ifndef AF_V3_SPARSE_FURNITURE_H
#define AF_V3_SPARSE_FURNITURE_H
#define AF_V3_STATIC_IMPORT_RAM 0x80484000u
#define AF_V3_STATIC_IMPORT_COUNT 1024
#define AF_V3_ITEM_TABLE_RAM 0x80498000u
#define AF_V3_ITEM_TABLE_COUNT 1024
#define AF_V3_SPARSE_FIRST 1024u
#define AF_V3_SPARSE_END 2048u
_Static_assert(AF_V3_STATIC_IMPORT_RAM + 80u * AF_V3_STATIC_IMPORT_COUNT ==
               AF_V3_ITEM_TABLE_RAM, "Sparse furniture tables overlap");
_Static_assert(AF_V3_ITEM_TABLE_RAM + 32u * AF_V3_ITEM_TABLE_COUNT ==
               0x804A0000u, "Sparse furniture tables exceed package guard");
#endif
