#ifndef AF_V3_CREATURE_WATER_H
#define AF_V3_CREATURE_WATER_H
typedef struct {float x,y,z;} FishVector;
typedef struct {int bx,bz;const unsigned *collision;} FishWaterBlock;
int af_v3_water_site(void *,unsigned,unsigned,unsigned);
int af_v3_water_wall(void *);
int af_v3_water_nearshore(void *);
/* The linker binds these to the corresponding native collision/field readers. */
extern unsigned af_water_attribute(FishVector,void *);
extern unsigned *af_water_unit(FishVector);
extern int af_water_is_water(unsigned);
extern unsigned af_water_block(int,int);
extern void af_water_centre(FishVector *,int,int,int,int);
extern float af_water_ground(void *,FishVector,float);
extern float af_water_height(FishVector,const char *,int);
#endif
