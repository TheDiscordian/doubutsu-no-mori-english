/* Add the donor's summer greetings; retain native winter/ordinary selection. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef int (*TimeKind)(int);
struct Private {
    u8 prefix[0x14];
    u16 items[15], padding;
    u32 conditions, wallet;
};
_Static_assert(__builtin_offsetof(struct Private, conditions) == 0x34, "Native conditions");
_Static_assert(__builtin_offsetof(struct Private, wallet) == 0x38, "Native wallet");
extern const struct Private *native_private;
extern const u8 native_hour;
extern const u16 camper_last_gift;
extern int native_looks(const void *);
extern int native_first(TimeKind, int, int, int);
extern int native_winter(const void *, TimeKind, int);
extern int native_ordinary(const void *, TimeKind, int);
extern float native_random(void);
extern u32 native_item_kind(u32, u32);

/* These fixed native IDs are the complete donor personality blocks. */
static const int repeat_messages[6] = {11826,11856,11887,11917,11947,11977};

int af_v3_camper_greeting(const void *client, TimeKind get_time, int meeting) {
    u16 actor = *(const u16 *)((const u8 *)client + 6);
    if (actor == 0xD05E) return native_winter(client, get_time, meeting);
    if (actor != 0xD08F) return native_ordinary(client, get_time, meeting);
    int looks = native_looks(client);
    if ((unsigned)looks >= 6u) return -1;
    if (!meeting) return native_first(get_time, 11754, looks, native_hour);

    const struct Private *priv = native_private;
    unsigned kind = 0;
    if (priv) {
        u16 ignore = camper_last_gift;
        for (unsigned i = 0; i < 15; ++i) {
            u16 item = priv->items[i];
            if (!item && priv->wallet >= 3000u) kind |= 1u;
            if (item != ignore && ((priv->conditions >> (i * 2)) & 3u) == 0u &&
                    (native_item_kind(item, 2) == 1u ||
                     (item & 0xFF00u) == 0x2600u || (item & 0xFF00u) == 0x2700u))
                kind |= 2u;
        }
    }
    if (kind == 3u) kind = 1u + (unsigned)(native_random() * 2.0f);
    return repeat_messages[looks] + (int)kind;
}
