#include <assert.h>
#include <stdio.h>
#include "../overlays/v3/display_conversion.c"

static int selected = 1, calls;
static u32 last;
int af_v3_furniture_import_profile(u32 index) { assert(index == 1727); return selected; }
u32 af_v3_display_pocket_item(u32 item) {
    return selected && (item & 0xFFFCu) == 0x3AFCu ? 0x34BFu : item;
}
u16 af_v3_prior_display_item(u32 item) { ++calls; last = item; return (u16)item; }
u16 af_v3_prior_pocket_item(u32 item) { ++calls; last = item; return (u16)item; }

int main(void) {
    for (u32 enabled = 0; enabled < 2; ++enabled) {
        selected = (int)enabled;
        for (u32 item = 0; item <= 65535; ++item) {
            u32 argument = 0xABCD0000u | item;
            calls = 0;
            assert(af_v3_room_display_item(argument) ==
                   (enabled && item == 0x34BF ? 0x3AFC : item));
            assert(calls == !(enabled && item == 0x34BF));
            if (calls) assert(last == argument);
            calls = 0;
            assert(af_v3_room_pocket_item(argument) ==
                   (enabled && (item & 0xFFFC) == 0x3AFC ? 0x34BF : item));
            assert(calls == !(enabled && (item & 0xFFFC) == 0x3AFC));
            if (calls) assert(last == argument);
        }
    }
    puts("selected conversion, four orientations, and all native argument fallbacks pass");
    return 0;
}
