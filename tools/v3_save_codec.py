"""Install the bounded V3 save codec without enabling native save hooks."""
from aflib import sha256
from v3_furniture_room import BLOB_SIZE

ABI, CODE = 13, 0xB400
PAYLOAD, BANK, CAPSULE = 0xF980, 0x10000, 0x680
PROFILE, STATE = 160, 672
SOURCES = ('tools/v3_save_codec.py', 'overlays/v3/save_codec.c',
           'overlays/v3/save_codec.h', 'overlays/v3/save_codec.ld')


def install(blob, helper, symbols, pockets_report):
    if (len(blob) != BLOB_SIZE or any(blob[CODE:-16])
            or 0xB200 + pockets_report['bytes'] > CODE or not helper
            or len(helper) > BLOB_SIZE - CODE - 16):
        raise ValueError('Save codec overlaps resident code/data')
    for name in ('af_v3_save_check', 'af_v3_save_pack', 'af_v3_save_collect'):
        if not 0x80460000 + CODE <= symbols[name] < 0x80460000 + CODE + len(helper) or symbols[name] & 3:
            raise ValueError('Invalid public save-codec entry')
    blob[CODE:CODE + len(helper)] = helper
    return {'native_save_hooks_enabled': False, 'native_catalogue_hooks_enabled': False,
            'device_io_performed': False, 'bank_bytes': BANK, 'legacy_payload_bytes': PAYLOAD,
            'capsule_bytes': CAPSULE, 'work_state_bytes': STATE,
            'save_magic': 'NAF3', 'capsule_magic': 'AFS3', 'format_version': 1, 'registry_version': 1,
            'helper_sha256': sha256(helper)}
