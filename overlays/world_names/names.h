#ifndef AF_WORLD_NAMES_H
#define AF_WORLD_NAMES_H

void af_world_reset(void *, int);
void af_world_load(unsigned char *, unsigned short);
void af_world_measure(void);
float af_world_draw(void *, const unsigned char *, int, float, float,
                    int, int, int, int, int, int, float, float, int);

#endif
