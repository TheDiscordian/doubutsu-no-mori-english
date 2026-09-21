/* Single-buffer copies used by arranged villager rooms. */
#include "surface_transfer.h"
void af_v3_single_wall(void *target,int index) {
    copy_surface(target,index,0x0182A000u,AF_SURFACE_WALL_VROM,0x1020u);
}
void af_v3_single_floor(void *target,int index) {
    copy_surface(target,index,0x017A1000u,AF_SURFACE_FLOOR_VROM,0x2020u);
}
