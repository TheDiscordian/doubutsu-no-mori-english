"""Exact English sender-only parts already selected by complete letter creators."""
from aflib import sha256

# English signatures use the captured sender alone. The native source adds a
# Japanese sign-off, so a static-text-only classifier misses this replacement.
# No empty template, arbitrary command, or unselected catalogue row is approved.
PARTS = {
    'ps:0097': ('7f2ac260c00b0721', '7f2a', 'quest_replies'),
    'ps:0098': ('7f2af40b0f', '7f2a', 'quest_replies'),
    'ps:009F': ('7f2af40b0f81', '7f2a', 'quest_replies'),
    'ps:00D2': ('00f660207f25607c', '7f25', 'npc_letters'),
    'ps:00E5': ('00f660207f25607c', '7f25', 'npc_letters'),
    **{f'psz:{n:04X}': ('7f25607c', '7f25', 'npc_letters')
       for n in (0x3B, 0x3F, 0x78, 0x82, 0x91, 0xB7)},
}


def verify(identity, source_hash, value, route):
    if identity not in PARTS:
        raise ValueError('Unapproved English sender-only letter part')
    source, encoded, expected_route = PARTS[identity]
    if source_hash != sha256(bytes.fromhex(source)) or value != bytes.fromhex(encoded) or route != expected_route:
        raise ValueError('English letter omission requires its exact source, sender command, and installed route')
