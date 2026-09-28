#ifndef AF_V3_CLOTHING_BATCH_H
#define AF_V3_CLOTHING_BATCH_H
#include "clothing.h"
#define AF_CLOTHING_COUNT 8u
struct ClothingIdentity { unsigned short item, index; unsigned int vrom; };
struct ClothingStock { unsigned int pointer; unsigned char counts[5], padding[3]; };
extern const struct Clothing af_v3_batch_clothing[AF_CLOTHING_COUNT];
extern const struct ClothingIdentity af_v3_batch_identities[AF_CLOTHING_COUNT];
extern const struct ClothingStock af_v3_batch_stock[3];
const struct Clothing *af_v3_roster_clothing_record(unsigned int item);
#endif
