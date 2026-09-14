#include <string.h>
struct Clothing { unsigned short item, index; unsigned int vrom;
    unsigned short price; unsigned char enabled, reserved, name[16]; unsigned int padding; };
struct Clothing af_v3_clothing;
unsigned char private_bytes[0xA80], buffers[2][576];
unsigned char *af_v3_player_private = private_bytes;
int af_v3_player_bank_ids[4], active_bank, missing_bank, calls, toggles, dmas, invalid_calls;
unsigned int banks[4], sources[4], sizes[4];
int af_v3_player_register_bank(void *game, int bank, unsigned int vrom, unsigned int size) {
    if (!game || calls >= 4) { ++invalid_calls; return -1; }
    banks[calls] = bank; sources[calls] = vrom; sizes[calls++] = size;
    return bank-14;
}
int af_v3_player_toggle_bank(void) { ++toggles; return active_bank ^= 1; }
unsigned char *af_v3_player_texture_buffer(void *game) {
    if (!game) ++invalid_calls;
    return missing_bank ? 0 : buffers[active_bank]+16;
}
int af_v3_clothing_dma(void *out, unsigned int vrom, unsigned int size) {
    if (!out || (size != 32 && size != 512)) { ++invalid_calls; return -1; }
    ++dmas;
    memset(out, (vrom >> 5) & 255, size);
    return 0;
}
