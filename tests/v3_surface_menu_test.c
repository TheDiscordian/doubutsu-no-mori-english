#include <assert.h>
#include <string.h>
#include "../overlays/v3/surface_menu.c"
static union {u32 align;u8 data[4*0xBD0];} players;
u8 *af_surface_menu_active;
static int native_calls,owned_calls;
static u32 last_item;
static const u32 *last_bits;
static int last_index;
static int native(const u32 *bits,int index) {
    native_calls++;last_bits=bits;last_index=index;return 17;
}
int af_v3_catalogue_owned(const u8 *p,u32 item) {
    assert(p==af_surface_menu_active);owned_calls++;last_item=item;return 23;
}
int main(void) {
    for (int player=0;player<4;player++) {
        af_surface_menu_active=players.data+player*0xBD0;
        for (int kind=0;kind<2;kind++) {
            const u32 *bits=(const u32 *)(af_surface_menu_active+0xB68+kind*8);
            for (int i=0;i<256;i++) {
                native_calls=owned_calls=0;
                int r=af_v3_surface_catalogue_bit(bits,i,native);
                if(i<64) {
                    assert(r==17 && native_calls==1 && !owned_calls);
                    assert(last_bits==bits && last_index==i);
                } else {
                    assert(r==23 && owned_calls==1 && !native_calls);
                    assert(last_item==(kind?0x2600u:0x2700u)+(u32)i);
                }
            }
            native_calls=owned_calls=0;
            assert(!af_v3_surface_catalogue_bit(bits,-1,native));
            assert(!af_v3_surface_catalogue_bit(bits,256,native));
            assert(!native_calls && !owned_calls);
        }
        const u32 *furniture=(const u32 *)(af_surface_menu_active+0xAF0);
        assert(af_v3_surface_catalogue_bit(furniture,2047,native)==17);
        assert(af_v3_surface_catalogue_bit(furniture,2048,native)==23 && last_item==0x3000);
        assert(af_v3_surface_catalogue_bit(furniture,3071,native)==23 && last_item==0x3FFC);
        assert(!af_v3_surface_catalogue_bit(furniture,3072,native));
        assert(!af_v3_surface_catalogue_bit(furniture+1,2048,native));
        assert(af_v3_surface_catalogue_bit(furniture+1,31,native)==17);
    }
    af_surface_menu_active=0;
    assert(!af_v3_surface_catalogue_bit((u32 *)players.data,2048,native));
    assert(af_v3_surface_catalogue_bit((u32 *)players.data,0,native)==17);
    return 0;
}
