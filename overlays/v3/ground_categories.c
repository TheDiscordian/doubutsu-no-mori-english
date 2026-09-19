/* Seasonal tables belong to the loaded overlay, never a cached heap address. */
typedef unsigned char u8;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
typedef struct {
    u32 slot, constructor, original_table, original_count, count;
    u32 table, parts, loop, type_base;
} Ground;
_Static_assert(sizeof(Ground)==36, "Ground configuration stride");
#ifdef __mips__
#define config ((const Ground *)0x804ADC00u)
#define mapping ((const u8 *)0x804AA210u)
#define materials ((const u32 *)0x804AA300u)
#define geometry ((const u32 *)(0x804AA300u+4u*AF_V3_CATEGORY_COUNT))
#define owner_base(row) (*(u8 **)(uptr)(row)->slot)
#else
extern Ground af_test_ground_config[4];
extern u8 af_test_ground_mapping[53], *af_test_ground_owners[4];
extern u32 af_test_ground_materials[AF_V3_CATEGORY_COUNT], af_test_ground_geometry[AF_V3_CATEGORY_COUNT];
extern void af_test_ground_constructor(void *, void *, u32);
#define config af_test_ground_config
#define mapping af_test_ground_mapping
#define materials af_test_ground_materials
#define geometry af_test_ground_geometry
#define owner_base(row) af_test_ground_owners[(row)-config]
#endif

/* Build once per constructor. Original relocated scenery rows remain intact. */
u8 *af_v3_ground_prepare(u32 variant) {
    if (variant>=4u) return 0;
    const Ground *row=config+variant;
    u8 *owner=owner_base(row);
    if (!owner) return 0;
    /* The old NONE sentinel lies inside the expanded range. Its start index
       can be nonzero, so it needs a real descriptor with no drawing lists. */
    u32 *empty=(u32 *)(owner+row->parts-32u);
    for (u32 i=0;i<8u;i++) empty[i]=0;
    u32 *table=(u32 *)(owner+row->table);
    const u32 *old=(const u32 *)(owner+row->original_table);
    for (u32 i=0;i<row->count*2u;i++)
        table[i]=i<row->original_count*2u ? old[i] : (i&1u) ? 0 : (u32)(uptr)empty;
    u32 *part=(u32 *)(owner+row->parts);
    for (u32 source=0;source<53u;source++) {
        u32 category=mapping[source];
        if (!category) continue;
        /* Immutable configuration is validated before it enters the cartridge. */
        for (u32 i=0;i<13u;i++) part[i]=0;
        part[0]=(u32)(uptr)(part+8);
        part[1]=1;
        part[2]=(u32)(uptr)(part+12);
        part[8]=materials[category];
        part[9]=geometry[category];
        part[10]=(u32)(uptr)(owner+row->loop);
        part[11]=0x00010000u; /* material index 0, geometry index 1 */
        part[12]=(u32)(uptr)(part+10);
        u32 index=row->type_base+category;
        table[index*2u]=(u32)(uptr)part;
        table[index*2u+1u]=0x00010000u;
        part+=13;
    }
    return owner;
}

static void construct(void *actor, void *game, u32 variant) {
    u8 *owner=af_v3_ground_prepare(variant);
    if (!owner) return;
#ifdef __mips__
    ((void (*)(void *, void *))(owner+config[variant].constructor))(actor,game);
#else
    af_test_ground_constructor(actor,game,variant);
#endif
}
void af_v3_ground_cherry(void *actor, void *game) { construct(actor,game,0); }
void af_v3_ground_winter(void *actor, void *game) { construct(actor,game,1); }
void af_v3_ground_xmas(void *actor, void *game) { construct(actor,game,2); }
void af_v3_ground_ordinary(void *actor, void *game) { construct(actor,game,3); }
