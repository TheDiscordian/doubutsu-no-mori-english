/* A saved summer visitor cannot simultaneously become a town resident.
 * These wrappers are bound only to two boolean candidate checks, never to a
 * general reader that would use the returned resident index. */
typedef unsigned char u8;
typedef unsigned int u32;
extern const volatile u32 native_installed;
extern const u8 *native_event_save(int, int);
extern int native_animal_search(u8 *, u32, int);
extern int native_animal_free(const u8 *);

static int is_camper(u32 identity) {
    const u8 *saved;
    u32 visitor;
    if (native_installed != 1 || (identity & 0xF000u) != 0xE000u) return 0;
    saved = native_event_save(70, 0);
    if (!saved) return 0;
    visitor = ((u32)saved[0] << 8) | saved[1];
    return visitor == identity;
}

int af_v3_camper_movein_candidate(u8 *animals, u32 identity, int count) {
    int resident = native_animal_search(animals, identity, count);
    if (resident == -1 && is_camper(identity)) return 0;
    return resident;
}

int af_v3_camper_transfer_blocked(const u8 *animal) {
    int empty = native_animal_free(animal);
    if (empty) return empty;
    return is_camper(((u32)animal[0] << 8) | animal[1]);
}
