#ifndef AF_SNOWMAN_CREATOR_H
#define AF_SNOWMAN_CREATOR_H

#define AF_SNOWMAN_CHOICES 12u
#define AF_SNOWMAN_ROW_BYTES 36u
#define AF_SNOWMAN_TABLE_BYTES (AF_SNOWMAN_CHOICES*2u*AF_SNOWMAN_ROW_BYTES)
extern const unsigned char af_snowman_templates[AF_SNOWMAN_TABLE_BYTES];

/* All snapshots and final capitalization states are validated at build time
 * against immutable catalogue four and the twelve exact English item names.
 * This fixed-gift creator performs no allocation, DMA, or random selection.
 */
int af_snowman_create(unsigned char *mail,const unsigned char *player,
                       unsigned int choice,unsigned int *capital);

#endif
