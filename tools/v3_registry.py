"""Persistent destination reservations, not a declaration of playable content."""
from v3_storage import START as STORAGE

REGISTRY_VERSION = 1
# Keep native ordinary IDs 0..215 and the original two test IDs 216/217.
# Literal reservations never change with selection order or donor availability.
VILLAGERS = {
    216: 218, 217: 219, 218: 220, 219: 221, 220: 222,
    221: 223, 222: 224, 223: 225, 224: 226, 225: 227,
    226: 228, 227: 229, 228: 230, 229: 231, 230: 232,
    231: 233, 232: 234, 233: 235, 234: 236, 235: 237,
}

# Special actors are not ordinary residents or individually selectable villagers.
# Native profiles C9/CA/CB are the no-demo sentinel, summer tent, and balloon.
# The existing camper mask uses D08F. These reservations do not enable spawning.
SPECIAL_NPC_REGISTRY_VERSION = 4
SPECIAL_NPCS = {
    'GAFE01-r0/npc/ev-soncho2': dict(donor_name=0xD074, donor_profile=0xCC,
        name=0xD090, profile=0xCC, model_bank=448, texture_bank=449),
    # Separate event ownership from native Miko; no actor/resources enabled yet.
    'GAFE01-r0/npc/ev-miko': dict(donor_name=0xD03D, donor_profile=0x84,
        name=0xD091, profile=0xCD, model_bank=450, texture_bank=451, draw_index=299),
    # The Halloween owner uses the pumpkin model/voice, not ordinary Tortimer.
    'GAFE01-r0/npc/ev-soncho2-costume': dict(donor_name=0xD079, donor_profile=0xCC,
        name=0xD092, profile=0xE2, model_bank=452, texture_bank=453, draw_index=359),
    'GAFE01-r0/npc/exercise-copper': dict(donor_name=0xD04E, donor_profile=0x93,
        name=0xD0AE, profile=0xE3, model_bank=454, texture_bank=455, draw_index=316),
    'GAFE01-r0/npc/exercise-tortimer': dict(donor_name=0xD078, donor_profile=0x93,
        name=0xD0B3, profile=0xE5, model_bank=448, texture_bank=449, draw_index=358),
}

# Shared event actors are resident villagers in temporary roles, not additional
# villagers. Keep their identities independent of the donor/native event numbers.
# New Year uses four residents; the source's fifth slot is not spawned.
PARTICIPANT_REGISTRY_VERSION = 1
PARTICIPANTS = {
    'tokyoso_control': dict(profile=0xD9, event=15, save=8, name=0, source=0, count=0),
    'tunahiki_control': dict(profile=0xDA, event=14, save=9, name=0, source=0, count=0),
    'hatumode_control': dict(profile=0xDB, event=1, save=7, name=0, source=0, count=0),
    'tokyoso_npc0': dict(profile=0xDC, event=15, save=8, name=0xD0A0, source=0xD02D, count=1),
    'tokyoso_npc1': dict(profile=0xDD, event=15, save=8, name=0xD0A1, source=0xD02E, count=4),
    'tunahiki_npc0': dict(profile=0xDE, event=14, save=9, name=0xD0A5, source=0xD05F, count=1),
    'tunahiki_npc1': dict(profile=0xDF, event=14, save=9, name=0xD0A6, source=0xD060, count=4),
    'hatumode_npc0': dict(profile=0xE0, event=1, save=7, name=0xD0AA, source=0xD058, count=4),
    'rope': dict(profile=0xE1, event=14, save=9, name=0, source=0, count=0),
}
PARTICIPANT_ROPE_PROFILE = 0xE1

# One complete controller serves all six exercise roles. The first five remain
# contiguous for source role arithmetic; Tortimer remains outside that range.
# These reservations alone do not enable the owners or claim ready artwork.
EXERCISE_PARTICIPANTS = (
    dict(profile=0xE3,name=0xD0AE,source=0xD04E,count=1,kind=3),
    dict(profile=0xE4,name=0xD0AF,source=0xD04F,count=4,kind=2),
    dict(profile=0xE5,name=0xD0B3,source=0xD078,count=1,kind=3),
)

# Each complete five-role group remains contiguous for donor role arithmetic.
# Moon viewing and meteor showers intentionally share the same five owners.
FESTIVAL_PARTICIPANTS = {
    'hanami_npc0': dict(profile=0xE6,name=0xD0B4,source=0xD032,count=4,event=20,save=20),
    'hanami_npc1': dict(profile=0xE7,name=0xD0B8,source=0xD036,count=1,event=20,save=20),
    'tukimi_npc0': dict(profile=0xE8,name=0xD0B9,source=0xD03F,count=1,event=43,save=37),
    'tukimi_npc1': dict(profile=0xE9,name=0xD0BA,source=0xD040,count=4,event=43,save=37),
    'countdown_npc0': dict(profile=0xEA,name=0xD0BE,source=0xD044,count=1,event=64,save=64),
    'countdown_npc1': dict(profile=0xEB,name=0xD0BF,source=0xD045,count=4,event=64,save=64),
    'tamaire_npc0': dict(profile=0xEC,name=0xD0C3,source=0xD053,count=1,event=12,save=12),
    'tamaire_npc1': dict(profile=0xED,name=0xD0C4,source=0xD054,count=4,event=12,save=12),
    'harvest_npc0': dict(profile=0xEE,name=0xD0C8,source=0xD082,count=4,event=56,save=56),
    'harvest_npc1': dict(profile=0xEF,name=0xD0CC,source=0xD086,count=1,event=56,save=56),
}

# Additive event structures retain the native structure allocation category.
# Their source variants are separate identities, never positions in a selection.
DECORATION_REGISTRY_VERSION = 1
DECORATION_PROFILES = {
    'Goza_Profile': 0xCE, 'Radio_Profile': 0xCF, 'Yatai_Profile': 0xD0,
    'Mikuji_Profile': 0xD1, 'Count_Profile': 0xD2, 'Count02_Profile': 0xD3,
    'Tama_Profile': 0xD4, 'Kago_Profile': 0xD5, 'Turi_Profile': 0xD6,
    'Ghog_Profile': 0xD7, 'Htable_Profile': 0xD8,
}
DECORATION_NAMES = {
    0x582A: 0x5F00, 0x582B: 0x5F01, 0x582C: 0x5F02,
    0x582D: 0x5F03, 0x582E: 0x5F04, 0x5831: 0x5F05,
    0x5832: 0x5F06, 0x5833: 0x5F07, 0x5834: 0x5F08,
    0x5835: 0x5F09, 0x5836: 0x5F0A, 0x5837: 0x5F0B,
    0x5838: 0x5F0C, 0x5839: 0x5F0D, 0x5845: 0x5F0E,
    0x5846: 0x5F0F, 0x5847: 0x5F10, 0x5848: 0x5F11,
}
# Existing foreground markers, verified against the matching native actor
# initializers. Kago and Turi deliberately share a marker in both engines;
# native ball-toss effects also consume that identity. F300/F301 are separate
# transient Groundhog/Harvest markers, outside native and F200..F213 house
# identities. They use the checked full-width field store and marker draw
# exclusion; they are never ordinary item-table indices or selectable items.
DECORATION_DUMMIES = {
    0xF108: 0xF0F4, 0xF109: 0xF0F5, 0xF10A: 0xF0F6,
    0xF10D: 0xF0F9, 0xF10E: 0xF0FA, 0xF10F: 0xF0FB,
    0xF110: 0xF0FC, 0xF111: 0xF0FD,
    0xF125: 0xF300, 0xF126: 0xF301,
}

# Reviewed furniture reservations. Values are runtime index, saved item
# ID, and object VROM. Native 0..946 and the index-947 conversion sentinel stay
# untouched. Holes are not supported items; future additions must be explicit.
FURNITURE_REGISTRY_VERSION = 1
# Version 2 records use the canonical donor identity rule below. Object VROMs
# belong to the checked build manifest, not saved identity or checkbox order.
CANONICAL_FURNITURE_VERSION = 2

# Additive ordinary legacy furniture. These reviewed source identities have no
# native correspondence in the pinned worksheet or approved translation map.
# Keep reservations literal and append-only; membership is not an acquisition
# or behaviour rule. 3C00..3C0C belong to balloon representations below this range.
LEGACY_FURNITURE_VERSION = 11
LEGACY_FURNITURE = {
    0x1FA0: (1796, 0x3C10),
    0x1FB4: (1797, 0x3C14),
    0x1FD0: (1798, 0x3C18),
    0x1FD4: (1799, 0x3C1C),
    0x1FDC: (1800, 0x3C20),
    0x1FE0: (1801, 0x3C24),
    0x1FEC: (1802, 0x3C28),
    0x1FC8: (1803, 0x3C2C),
    0x1FD8: (1804, 0x3C30),
    0x1FE4: (1805, 0x3C34),
    0x1FE8: (1806, 0x3C38),
    0x1FC4: (1807, 0x3C3C),
    0x1FAC: (1808, 0x3C40),
    0x1FB8: (1809, 0x3C44),
    0x1FCC: (1810, 0x3C48),
    0x1DC4: (1811, 0x3C4C),
    0x1DC8: (1812, 0x3C50),
    0x1DCC: (1813, 0x3C54),
    0x1DD0: (1814, 0x3C58),
    0x1DD4: (1815, 0x3C5C),
    0x1DD8: (1816, 0x3C60),
    0x1DDC: (1817, 0x3C64),
    0x1DE0: (1818, 0x3C68),
    0x1DE4: (1819, 0x3C6C),
    0x1DE8: (1820, 0x3C70),
    0x1DEC: (1821, 0x3C74),
    0x1DF0: (1822, 0x3C78),
    0x12B0: (1823, 0x3C7C),
    0x12B4: (1824, 0x3C80),
    0x12C4: (1825, 0x3C84),
    0x12D8: (1826, 0x3C88),
    0x1FA4: (1827, 0x3C8C),
    0x1FB0: (1828, 0x3C90),
    0x1FC0: (1829, 0x3C94),
}


def furniture_identity(donor_item):
    if type(donor_item) is int and donor_item in LEGACY_FURNITURE:
        return LEGACY_FURNITURE[donor_item]
    if type(donor_item) is not int or not 0x3000 <= donor_item < 0x33C8 or donor_item & 3:
        raise ValueError('Not a canonical English-donor furniture identity')
    return 1024+(donor_item-0x3000)//4, donor_item


def furniture_source_index(item):
    """Decode the donor table, never an N64 destination table."""
    if type(item) is not int or item & 3:
        raise ValueError('Not a canonical donor furniture identity')
    if 0x1000 <= item < 0x2000: return (item-0x1000)//4
    if 0x3000 <= item < 0x33C8: return 1024+(item-0x3000)//4
    raise ValueError('Not a canonical donor furniture identity')


def furniture_source(row):
    """Validate a record's stable source/destination pair before source reads."""
    item = int(row['item_id'],16)
    donor = int(row.get('donor_item_id',row['item_id']),16)
    index = furniture_source_index(donor)
    native_index,native_item = furniture_identity(donor)
    if (item != native_item or row.get('runtime_index',native_index) != native_index
            or row.get('donor_runtime_index',index) != index
            or row.get('id',f'GAFE01-r0/item/{donor:04X}') != f'GAFE01-r0/item/{donor:04X}'
            or donor != item and ('donor_runtime_index' not in row or 'donor_item_id' not in row)):
        raise ValueError('Changed furniture source/destination identity')
    return donor,index


# Older donor room aliases cannot use their source indices in the shorter N64
# furniture table. Reserve additive slots beyond the full 3800..3BFC garment
# display range. These reservations are stable, not allocated by checkbox order.
ROOM_ALIAS_REGISTRY_VERSION = 1
LEGACY_ROOM_ALIASES = {
    0x1FF0: (1792, 0x3C00),
    0x1FF4: (1793, 0x3C04),
    0x1FF8: (1794, 0x3C08),
    0x1FFC: (1795, 0x3C0C),
}

# Creature room representations occupy distinct, append-only display slots.
# This reserves neither carried IDs nor playable species. In particular, the
# donor brook-trout display cannot reuse the native herabuna identity.
CREATURE_DISPLAY_REGISTRY_VERSION = 1
CREATURE_DISPLAYS = {
    0x1C48: (1830, 0x3C98), 0x1C4C: (1831, 0x3C9C),
    0x1C50: (1832, 0x3CA0), 0x1C54: (1833, 0x3CA4),
    0x1C58: (1834, 0x3CA8), 0x1C5C: (1835, 0x3CAC),
    0x1C60: (1836, 0x3CB0), 0x1C64: (1837, 0x3CB4),
    0x1C6C: (1838, 0x3CB8), 0x1CE8: (1839, 0x3CBC),
    0x1CEC: (1840, 0x3CC0), 0x1CF0: (1841, 0x3CC4),
    0x1CF4: (1842, 0x3CC8), 0x1CF8: (1843, 0x3CCC),
    0x1CFC: (1844, 0x3CD0), 0x1D00: (1845, 0x3CD4),
    0x1D04: (1846, 0x3CD8),
}

# Carried identities are fixed independently of selection. Native 2301 is
# herabuna; the donor's brook trout gets a new slot after its eight additions.
CREATURE_PARENT_REGISTRY_VERSION = 1
CREATURE_PARENTS = {
    **{0x2D20+i: 0x2D20+i for i in range(8)},
    **{0x2320+i: 0x2320+i for i in range(8)},
    0x2301: 0x2328,
}

# Native category B already owns 2B00. Keep its identity; diary covers retain
# their canonical furniture slots, while carried styles use an additive range.
DIARY_PARENT_REGISTRY_VERSION = 1
DIARY_PARENTS = {0x2B00+i: 0x2B10+i for i in range(16)}

# Additive miscellaneous items follow the original thirty native entries and
# the separately reserved wrapped presents. Exercise-card stamps are states of
# one carried item, not thirteen independent selector choices.
HOLIDAY_ITEM_REGISTRY_VERSION = 1
HOLIDAY_ITEMS = {item: item for item in range(0x2523, 0x2531)}
# Renderer slots only; no existing item or drawing category is replaced. Source
# categories 18/20 already use native insect/fossil types, leaving these unused
# slots available within the installed 71-entry renderer capacity.
HOLIDAY_ITEM_CATEGORIES = {47: 45, 52: 47}


def diary_parent_identity(donor_item):
    if type(donor_item) is not int or donor_item not in DIARY_PARENTS:
        raise ValueError('Not a donor diary parent')
    return DIARY_PARENTS[donor_item]


def creature_parent_identity(donor_item):
    if type(donor_item) is not int or donor_item not in CREATURE_PARENTS:
        raise ValueError('Not an additive creature parent')
    return CREATURE_PARENTS[donor_item]


def furniture_representation_identity(donor_item):
    if type(donor_item) is int and donor_item in CREATURE_DISPLAYS:
        return CREATURE_DISPLAYS[donor_item]
    if type(donor_item) is int and donor_item in LEGACY_ROOM_ALIASES:
        return LEGACY_ROOM_ALIASES[donor_item]
    return furniture_identity(donor_item)


FURNITURE = {
    0x3224: (1161, 0x3224, STORAGE+0x8000),
    0x32B8: (1198, 0x32B8, STORAGE+0xA000),
    0x3350: (1236, 0x3350, STORAGE+0x10000),
    0x31F4: (1149, 0x31F4, STORAGE+0x134000),
    0x31F8: (1150, 0x31F8, STORAGE+0x135000),
    0x31FC: (1151, 0x31FC, STORAGE+0x136000),
    0x320C: (1155, 0x320C, STORAGE+0x137000),
    0x3214: (1157, 0x3214, STORAGE+0x138000),
    0x3218: (1158, 0x3218, STORAGE+0x139000),
    0x322C: (1163, 0x322C, STORAGE+0x13A000),
    0x3268: (1178, 0x3268, STORAGE+0x15D000),
    0x3284: (1185, 0x3284, STORAGE+0x15E000),
    0x3290: (1188, 0x3290, STORAGE+0x15F000),
    0x3294: (1189, 0x3294, STORAGE+0x160000),
    0x32A0: (1192, 0x32A0, STORAGE+0x161000),
    0x32A4: (1193, 0x32A4, STORAGE+0x162000),
    0x32B0: (1196, 0x32B0, STORAGE+0x18C000),
    0x32B4: (1197, 0x32B4, STORAGE+0x18E000),
    0x32BC: (1199, 0x32BC, STORAGE+0x190000),
    0x32C0: (1200, 0x32C0, STORAGE+0x192000),
    0x3328: (1226, 0x3328, STORAGE+0x194000),
    0x3330: (1228, 0x3330, STORAGE+0x196000),
    0x3334: (1229, 0x3334, STORAGE+0x198000),
    0x32C4: (1201, 0x32C4, STORAGE+0x1C4000),
    0x32D4: (1205, 0x32D4, STORAGE+0x1C6000),
    0x32D8: (1206, 0x32D8, STORAGE+0x1C8000),
    0x3364: (1241, 0x3364, STORAGE+0x230000),
    0x3370: (1244, 0x3370, STORAGE+0x232000),
    0x339C: (1255, 0x339C, STORAGE+0x234000),
    0x33A4: (1257, 0x33A4, STORAGE+0x236000),
    0x33A8: (1258, 0x33A8, STORAGE+0x238000),
    0x33AC: (1259, 0x33AC, STORAGE+0x23A000),
    0x33B0: (1260, 0x33B0, STORAGE+0x23C000),
    0x336C: (1243, 0x336C, STORAGE+0x24E000),
    0x335C: (1239, 0x335C, STORAGE+0x268000),
    0x3360: (1240, 0x3360, STORAGE+0x26A000),
    0x3200: (1152, 0x3200, STORAGE+0x2A8000),
    0x3204: (1153, 0x3204, STORAGE+0x2A9000),
    0x3220: (1160, 0x3220, STORAGE+0x2AA000),
}

# Additive clothing reservations, independent of donor furniture and native
# clothing identities. These are not enabled items or saved-profile support.
CLOTHING_REGISTRY_VERSION = 2
CLOTHING = {
    0x24BF: (0x34BF, 0x10BF, STORAGE+0xF000),
    0x241A: (0x341A, 0x101A, STORAGE+0xE2000),
    0x241B: (0x341B, 0x101B, STORAGE+0xE2400),
}

# A placed garment uses a mannequin identity, not its pocket clothing identity.
# These dependencies are never independently selectable or assigned by order.
CLOTHING_DISPLAY_REGISTRY_VERSION = 1
CLOTHING_DISPLAYS = {
    0x24BF: (1727, 0x3AFC),
    0x241A: (1562, 0x3868),
    0x241B: (1563, 0x386C),
}

# Append-only identities for the complete remaining donor-appearance category.
# Resource addresses are allocated by the checked common item-data writer and
# bound in each build report; they are not save identities or checkbox indices.
for _garment in (0x244B, 0x2469, 0x24B6, 0x24CB, 0x24E3):
    _index = _garment-0x2400
    CLOTHING[_garment] = (0x3400+_index, 0x1000+_index, None)
    CLOTHING_DISPLAYS[_garment] = (1536+_index, 0x3800+_index*4)


def clothing_slot(donor_item):
    if donor_item not in CLOTHING:
        raise ValueError('Unassigned imported clothing identity')
    return CLOTHING[donor_item]


# Additive room surfaces retain native player/shop textures and floor-sound
# identities 0..72, including special rooms. Paired surfaces share an index for
# room-series scoring. These are reservations, not installed items/save support.
SURFACE_REGISTRY_VERSION = 1
SURFACES = {
    0x2612: (73, 0x2649), 0x261A: (74, 0x264A),
    0x2640: (75, 0x264B), 0x2641: (76, 0x264C), 0x2642: (77, 0x264D),
    0x2712: (73, 0x2749), 0x271A: (74, 0x274A),
    0x2740: (75, 0x274B), 0x2741: (76, 0x274C), 0x2742: (77, 0x274D),
}


def surface_identity(donor_item):
    if type(donor_item) is not int or donor_item not in SURFACES:
        raise ValueError('Unassigned additive room-surface identity')
    return SURFACES[donor_item]

# Preserve the native sorted house-layer range 398..855. Each imported villager
# owns two fixed layer slots, including unavailable villagers and subsets.
HOUSE_LAYER_BASE, HOUSE_LAYER_CAPACITY = 856, 40
HOUSE_MARKER_BASE, HOUSE_MARKER_CAPACITY = 0xF200, 20


def villager_house_marker(donor_index):
    return HOUSE_MARKER_BASE + villager_actor(donor_index) - 0xE0DA


def villager_house_layers(donor_index):
    slot = villager_actor(donor_index) - 0xE0DA
    return HOUSE_LAYER_BASE + slot * 2, HOUSE_LAYER_BASE + slot * 2 + 1


def furniture_slot(donor_item):
    if donor_item not in FURNITURE:
        raise ValueError('Unassigned imported furniture identity')
    return FURNITURE[donor_item]


def villager_actor(donor_index):
    if donor_index not in VILLAGERS:
        raise ValueError('Unassigned imported villager identity')
    return 0xE000 + VILLAGERS[donor_index]
