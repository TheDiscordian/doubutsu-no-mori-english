"""Persistent destination reservations, not a declaration of playable content."""

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
    0x3224: (1161, 0x3224, 0x03F08000),
    0x32B8: (1198, 0x32B8, 0x03F0A000),
}


def furniture_slot(donor_item):
    if donor_item not in FURNITURE:
        raise ValueError('Unassigned imported furniture identity')
    return FURNITURE[donor_item]


def villager_actor(donor_index):
    if donor_index not in VILLAGERS:
        raise ValueError('Unassigned imported villager identity')
    return 0xE000 + VILLAGERS[donor_index]
