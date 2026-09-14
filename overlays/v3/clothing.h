#ifndef AF_V3_CLOTHING_H
#define AF_V3_CLOTHING_H
struct Clothing {
    unsigned short item, index;
    unsigned int vrom;
    unsigned short price;
    unsigned char enabled, reserved, name[16];
    unsigned int padding;
};
_Static_assert(sizeof(struct Clothing) == 32, "Clothing metadata layout");
unsigned int af_v3_clothing_source(int index, unsigned int palette);
#endif
