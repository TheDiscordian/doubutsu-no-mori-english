/* Pure bounded save/profile codec. Native storage hooks are separate. */
#include "save_codec.h"
typedef af_save_u8 u8;
typedef af_save_u32 u32;

static u32 read16(const u8 *p) { return (u32)p[0] << 8 | p[1]; }
static u32 read32(const u8 *p) { return read16(p) << 16 | read16(p + 2); }
static void write32(u8 *p, u32 value) {
    p[0] = value >> 24; p[1] = value >> 16; p[2] = value >> 8; p[3] = value;
}
static void copy(u8 *to, const u8 *from, u32 count) {
    for (u32 i = 0; i < count; ++i) to[i] = from[i];
}
static int overlaps(const u8 *a, u32 an, const u8 *b, u32 bn) {
    unsigned long x = (unsigned long)a, y = (unsigned long)b;
    return x <= y ? y - x < an : x - y < bn;
}
/* CRC-32/ISO-HDLC; treat one field as zero without changing caller memory. */
static u32 crc(const u8 *p, u32 count, u32 zero, u32 width) {
    u32 value = ~0u;
    for (u32 i = 0; i < count; ++i) {
        value ^= i >= zero && i - zero < width ? 0 : p[i];
        for (u32 bit = 0; bit < 8; ++bit)
            value = (value >> 1) ^ (0xEDB88320u & (0u - (value & 1u)));
    }
    return ~value;
}
static u32 sum(const u8 *bank) {
    u32 value = 0;
    for (u32 i = 0; i < AF_SAVE_PAYLOAD; i += 2) value += read16(bank + i);
    return value & 0xFFFFu;
}
static int town_valid(const u8 *bank) {
    return bank[8] == 0x30 && read16(bank + 8) == read16(bank + 0x2F68);
}
static int catalogue_valid(const u8 *profile, const u8 *catalogue) {
    for (u32 i = 0; i < AF_SAVE_FURNITURE_CATALOGUE; ++i)
        if (catalogue[i] & ~profile[32 + (i & 127)]) return 0;
    return 1;
}
#ifdef AF_V3_CLOTHING_PROFILE
static int clothing_valid(const u8 *profile, const u8 *catalogue) {
    for (u32 i = 0; i < 128; ++i)
        if (catalogue[i] & ~profile[i & 31]) return 0;
    return 1;
}
#endif
#ifdef AF_V3_REWARD_PROFILE
#include "save_rewards.h"
#ifdef AF_V3_EXTERNAL_REWARD_VALIDATOR
#define rewards_valid af_v3_reward_data_valid
#else
#define rewards_valid af_save_rewards_valid
#endif
#endif

#ifdef AF_V3_SURFACE_PROFILE
static int surfaces_valid(const u8 *data) {
    for (u32 i=0;i<4*AF_SAVE_SURFACE_PROFILE;i++)
        if (data[AF_SAVE_SURFACE_PROFILE+i] & ~data[i%AF_SAVE_SURFACE_PROFILE]) return 0;
    return 1;
}
#endif

int af_v3_save_check(const u8 *bank, u32 size, const u8 *current, u8 *state) {
    if (!bank || size != AF_SAVE_BANK || !current || (state &&
            (overlaps(state, AF_SAVE_STATE, bank, size) ||
             overlaps(state, AF_SAVE_STATE, current, AF_SAVE_PROFILE)))) return AF_SAVE_ARGUMENT;
    u32 magic = read32(bank + 4);
    if ((magic != 0x4E41464Au && magic != 0x4E414633u) || !town_valid(bank)) return AF_SAVE_HEADER;
    if (sum(bank)) return AF_SAVE_CHECKSUM;
    const u8 *ext = bank + AF_SAVE_PAYLOAD;
    int result = AF_SAVE_LEGACY;
#ifdef AF_V3_CLOTHING_PROFILE
    int clothing_format = 0;
#endif
#ifdef AF_V3_REWARD_PROFILE
    int reward_format = 0;
#endif
#ifdef AF_V3_SURFACE_PROFILE
    int surface_format = 0;
#endif
    if (magic == 0x4E414633u) {
#ifdef AF_V3_CLOTHING_PROFILE
#ifdef AF_V3_REWARD_PROFILE
        u32 version=read32(ext+4), registry=read32(ext+8);
#ifdef AF_V3_SURFACE_PROFILE
        surface_format = version == 0x00040680u && registry == 3;
        reward_format = surface_format || (version == 0x00030680u && registry == 2);
        clothing_format = reward_format || (version == 0x00020680u && registry == 2);
#else
        reward_format = version == 0x00030680u && registry == 2;
        clothing_format = (version == 0x00020680u || reward_format) && registry == 2;
#endif
        if (read32(ext) != 0x41465333u || (!clothing_format &&
                (version != 0x00010680u || registry != 1))) return AF_SAVE_FORMAT;
#else
        clothing_format = read32(ext+4) == 0x00020680u && read32(ext+8) == 2;
        if (read32(ext) != 0x41465333u || (!clothing_format &&
                (read32(ext+4) != 0x00010680u || read32(ext+8) != 1))) return AF_SAVE_FORMAT;
#endif
#else
        if (read32(ext) != 0x41465333u || read32(ext + 4) != 0x00010680u ||
                read32(ext + 8) != 1) return AF_SAVE_FORMAT;
#endif
        for (u32 i = 0x14; i < AF_SAVE_CAPSULE; ++i)
            if ((i < 0x18 || (i >= 0xB8 && i < 0xC0) ||
#ifdef AF_V3_SURFACE_PROFILE
                    i >= (surface_format ? 0x4D0u : reward_format ? 0x390u : clothing_format ? 0x360u : 0x2C0u)
#elif defined(AF_V3_REWARD_PROFILE)
                    i >= (reward_format ? 0x390u : clothing_format ? 0x360u : 0x2C0u)
#elif defined(AF_V3_CLOTHING_PROFILE)
                    i >= (clothing_format ? 0x360u : 0x2C0u)
#else
                    i >= 0x2C0
#endif
                    ) && ext[i])
                return AF_SAVE_FORMAT;
        if (crc(ext, AF_SAVE_CAPSULE, 0x10, 4) != read32(ext + 0x10)) return AF_SAVE_CRC;
        if (crc(bank, AF_SAVE_PAYLOAD, 0x12, 2) != read32(ext + 0xC)) return AF_SAVE_BINDING;
        for (u32 i = 0; i < AF_SAVE_BASE_PROFILE; ++i)
            if (ext[0x18 + i] & ~current[i]) return AF_SAVE_PROFILE_MISSING;
        if (!catalogue_valid(ext + 0x18, ext + 0xC0)) return AF_SAVE_CATALOGUE_INVALID;
#ifdef AF_V3_CLOTHING_PROFILE
        if (clothing_format) {
            for (u32 i = 0; i < 32; ++i)
                if (ext[0x2C0+i] & ~current[160+i]) return AF_SAVE_PROFILE_MISSING;
            if (!clothing_valid(ext+0x2C0, ext+0x2E0)) return AF_SAVE_CATALOGUE_INVALID;
        }
#endif
#ifdef AF_V3_REWARD_PROFILE
        if (reward_format && !rewards_valid(ext+0x360)) return AF_SAVE_REWARD_INVALID;
#endif
#ifdef AF_V3_SURFACE_PROFILE
        if (surface_format) {
            for (u32 i=0;i<AF_SAVE_SURFACE_PROFILE;i++)
                if (ext[0x390+i] & ~af_v3_surface_profile_byte(i)) return AF_SAVE_PROFILE_MISSING;
            if (!surfaces_valid(ext+0x390)) return AF_SAVE_CATALOGUE_INVALID;
        }
#endif
        result = AF_SAVE_OK;
    }
    if (state) {
        copy(state, current, AF_SAVE_PROFILE);
        for (u32 i = 0; i < AF_SAVE_FURNITURE_CATALOGUE; ++i)
            state[AF_SAVE_PROFILE + i] = result == AF_SAVE_OK ? ext[0xC0 + i] : 0;
#ifdef AF_V3_CLOTHING_PROFILE
        for (u32 i = 0; i < 128; ++i)
            state[AF_SAVE_PROFILE+512+i] = clothing_format ? ext[0x2E0+i] : 0;
#endif
#ifdef AF_V3_REWARD_PROFILE
        for (u32 i=0;i<AF_SAVE_REWARD_BYTES;++i)
            state[AF_SAVE_REWARD_OFFSET+i] = reward_format ? ext[0x360+i] : 0;
#endif
#ifdef AF_V3_SURFACE_PROFILE
        for (u32 i=0;i<AF_SAVE_SURFACE_PROFILE;i++)
            state[AF_SAVE_SURFACE_OFFSET+i]=(u8)af_v3_surface_profile_byte(i);
        for (u32 i=0;i<4*AF_SAVE_SURFACE_PROFILE;i++)
            state[AF_SAVE_SURFACE_OFFSET+AF_SAVE_SURFACE_PROFILE+i]=surface_format ? ext[0x3D0+i] : 0;
#endif
    }
    return result;
}

int af_v3_save_pack(u8 *bank, u32 size, const u8 *state) {
    if (!bank || size != AF_SAVE_BANK || !state || overlaps(bank, size, state, AF_SAVE_STATE))
        return AF_SAVE_ARGUMENT;
    if (!town_valid(bank)) return AF_SAVE_HEADER;
    if (!catalogue_valid(state, state + AF_SAVE_PROFILE)) return AF_SAVE_CATALOGUE_INVALID;
#ifdef AF_V3_CLOTHING_PROFILE
    if (!clothing_valid(state+160, state+AF_SAVE_PROFILE+512)) return AF_SAVE_CATALOGUE_INVALID;
#endif
#ifdef AF_V3_REWARD_PROFILE
    if (!rewards_valid(state+AF_SAVE_REWARD_OFFSET)) return AF_SAVE_REWARD_INVALID;
#endif
#ifdef AF_V3_SURFACE_PROFILE
    if (!surfaces_valid(state+AF_SAVE_SURFACE_OFFSET)) return AF_SAVE_CATALOGUE_INVALID;
#endif
    u8 *ext = bank + AF_SAVE_PAYLOAD;
    write32(bank + 4, 0x4E414633u);
    for (u32 i = 0; i < AF_SAVE_CAPSULE; ++i) ext[i] = 0;
    write32(ext, 0x41465333u);
#ifdef AF_V3_CLOTHING_PROFILE
#ifdef AF_V3_REWARD_PROFILE
    write32(ext + 4, 0x00030680u);
    copy(ext+0x360, state+AF_SAVE_REWARD_OFFSET, AF_SAVE_REWARD_BYTES);
#else
    write32(ext + 4, 0x00020680u);
#endif
    write32(ext + 8, 2);
    copy(ext+0x2C0, state+160, 32);
    copy(ext+0x2E0, state+AF_SAVE_PROFILE+512, 128);
#else
    write32(ext + 4, 0x00010680u);
    write32(ext + 8, 1);
#endif
    copy(ext + 0x18, state, AF_SAVE_BASE_PROFILE);
    copy(ext + 0xC0, state + AF_SAVE_PROFILE, AF_SAVE_FURNITURE_CATALOGUE);
#ifdef AF_V3_SURFACE_PROFILE
    write32(ext+4,0x00040680u);write32(ext+8,3);
    copy(ext+0x390,state+AF_SAVE_SURFACE_OFFSET,AF_SAVE_SURFACE_BYTES);
#endif
    write32(ext + 0xC, crc(bank, AF_SAVE_PAYLOAD, 0x12, 2));
    write32(ext + 0x10, crc(ext, AF_SAVE_CAPSULE, 0x10, 4));
    u32 checksum = (read16(bank + 0x12) - sum(bank)) & 0xFFFFu;
    bank[0x12] = checksum >> 8; bank[0x13] = checksum;
    return AF_SAVE_OK;
}

int af_v3_save_collect(u8 *state, u32 player, u32 item, u32 mark) {
    if (!state || player >= 4 || mark > 1) return AF_SAVE_ARGUMENT;
#ifdef AF_V3_SURFACE_PROFILE
    if ((item>>8)-0x26u<2u && (item&255u)>=64u) {
        u32 byte=((item>>8)-0x26u)*32u+((item&255u)>>3),bit=1u<<(item&7u);
        if (!(state[AF_SAVE_SURFACE_OFFSET+byte]&bit)) return AF_SAVE_PROFILE_MISSING;
        u8 *collected=state+AF_SAVE_SURFACE_OFFSET+AF_SAVE_SURFACE_PROFILE*(player+1)+byte;
        if (mark) *collected|=(u8)bit;
        return (*collected&bit)!=0;
    }
#endif
    if (item < 0x3000 || item > 0x3FFF) return AF_SAVE_ARGUMENT;
#ifdef AF_V3_CLOTHING_PROFILE
    if ((item & 0xFF00) == 0x3400) {
        u32 index = item & 255, byte = index >> 3, bit = 1u << (index & 7);
        if (!(state[160+byte] & bit)) return AF_SAVE_PROFILE_MISSING;
        u8 *collected = state+AF_SAVE_PROFILE+512+player*32+byte;
        if (mark) *collected |= bit;
        return (*collected & bit) != 0;
    }
#endif
    u32 index = (item & 0xFFF) >> 2, byte = index >> 3, bit = 1u << (index & 7);
    if (!(state[32 + byte] & bit)) return AF_SAVE_PROFILE_MISSING;
    u8 *collected = state + AF_SAVE_PROFILE + player * 128 + byte;
    if (mark) *collected |= bit;
    return (*collected & bit) != 0;
}
