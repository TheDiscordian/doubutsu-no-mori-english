#include "password_runtime.h"
extern int af_pw_dma(void *, af_pw_u32, af_pw_u32);
extern af_pw_u32 af_pw_crc(void *, af_pw_u32);
extern void af_pw_writeback(void *, af_pw_u32), af_pw_invalidate(void *, af_pw_u32);
extern void af_pw_fault(const char *, const char *);
#ifdef __mips__
#define cache (*(volatile af_pw_u32 *)0x804B4EF0u)
#define packet ((void *)0x804C0000u)
#define execute ((int (*)(const af_pw_u8 *, const af_pw_u8 *, const af_pw_u8 *, struct AfPasswordOffer *))0x804C0000u)
#else
extern volatile af_pw_u32 af_pw_cache;
extern af_pw_u8 af_pw_packet[0x8000];
extern int af_pw_execute(const af_pw_u8 *, const af_pw_u8 *, const af_pw_u8 *, struct AfPasswordOffer *);
#define cache af_pw_cache
#define packet af_pw_packet
#define execute af_pw_execute
#endif
int af_v3_password_boot_check(const af_pw_u8 *code, const af_pw_u8 *player,
                              const af_pw_u8 *town, struct AfPasswordOffer *offer) {
    /* Startup loads a zero cache word for every new cartridge session. */
    if (cache != AF_PW_PACKET_CRC) {
        if (af_pw_dma(packet, AF_PW_PACKET_VROM, 0x8000) ||
                af_pw_crc(packet, 0x8000) != AF_PW_PACKET_CRC) {
            af_pw_fault("V3 item codes", "Invalid password module");
            return AF_PW_INVALID;
        }
        af_pw_writeback(packet, 0x8000);
        af_pw_invalidate(packet, 0x8000);
        cache = AF_PW_PACKET_CRC;
    }
    return execute(code, player, town, offer);
}
