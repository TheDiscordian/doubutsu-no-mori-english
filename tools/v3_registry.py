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

# Reviewed static furniture reservations. Values are runtime index, saved item
# ID, and object VROM. Native 0..946 and the index-947 conversion sentinel stay
# untouched. Holes are not supported items; future additions must be explicit.
FURNITURE_REGISTRY_VERSION = 1
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
}

# Additive clothing reservations, independent of donor furniture and native
# clothing identities. These are not enabled items or saved-profile support.
CLOTHING_REGISTRY_VERSION = 1
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


def clothing_slot(donor_item):
    if donor_item not in CLOTHING:
        raise ValueError('Unassigned imported clothing identity')
    return CLOTHING[donor_item]

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
