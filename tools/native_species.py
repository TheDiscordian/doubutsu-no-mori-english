"""Source-bound correction for the N64 fish replaced in the English GC game."""

from aflib import sha256

NATIVE_ID = 0x021A
NATIVE_SHA256 = 'c3d4514ebda8d17a615ccb08273d27833684a25cee0d71bcaa5de6b8095f980d'
DONOR = b'brook trout'
ENGLISH = b'herabuna'
SOURCE = 'project-authored native herabuna identity correction'


def correct_word(native_id, source, donor):
    if native_id != NATIVE_ID:
        return donor
    if sha256(source) != NATIVE_SHA256 or donor != DONOR:
        raise ValueError('Changed native herabuna source or replaced GameCube species')
    return ENGLISH
