"""Four full-name dialogue preparations using the guarded startup display bridge."""
import copy
import struct

from aflib import by_vrom, sha256, verified_rom
from shop_item_names import jump
from text_names import BRIDGE, verify_installed_bridge

RAMS = {'conversation': 0x80918450, 'resident': 0x8091D7B0}
VROMS = {'conversation': 0x008108C0, 'resident': 0x03910000}
CALLS = {'conversation': ((0x80919BDC, 0x80919BFC), (0x80919C18, 0x80919C40), (0x80919D08, 0x80919D30)),
         'resident': ((0x8091EB04, 0x8091EB28),)}


def patch(name, data, *, reverse=False):
    result = bytearray(data); ram = RAMS[name]
    for call, length in CALLS[name]:
        for address, before, after in ((call, jump(0x800ACD18, link=True), jump(BRIDGE, link=True)),
                                       (length, 0x24070006, 0x24070008)):
            if reverse: before, after = after, before
            if struct.unpack_from('>I', result, address-ram)[0] != before:
                raise ValueError('Changed conversation identity-name preparation')
            struct.pack_into('>I', result, address-ram, after)
    return bytes(result)


def validate_relocations(name, reloc):
    text, data, _, _, count = struct.unpack_from('>5I', reloc)
    touched = {address-RAMS[name] for pair in CALLS[name] for address in pair}
    for (word,) in struct.iter_unpack('>I', reloc[20:20+4*count]):
        section, at = word >> 30, word & 0xFFFFFF
        if section not in (1, 2, 3): raise ValueError('Unknown conversation relocation section')
        at += (0, text, text+data)[section-1]
        if at in touched: raise ValueError('Conversation name patch has an unexpected relocation')


def install(native, replacements, report):
    import secret_actor as s
    import text_extension as t
    # This integration extends the installed display route, not a saved-name API.
    verified_rom(native)
    if not report.get('text_extension', {}).get('identities'):
        raise ValueError('Conversation names require the installed identity bridge')
    original, reloc = t.source(native, 'letter'); spec = t.ACTORS['letter']
    expected = bytearray(original); at = spec.entry-spec.ram
    expected[at:at+t.CALLS['letter'][0]] = t.call_body('letter')
    if replacements.get(spec.vrom) != expected:
        raise ValueError('Conversation names require the complete preceding item adapter')
    secret = copy.deepcopy(report['secret_actor'])
    before = replacements[s.VROM]; old_secret = secret['overlay']
    if old_secret.get('dialogue_identity_names') or sha256(before) != old_secret['overlay_sha256']:
        raise ValueError('Overlapping resident identity preparation')
    validate_relocations('conversation', reloc)
    validate_relocations('resident', replacements[s.RELOCATION])
    changed = {'conversation': patch('conversation', expected), 'resident': patch('resident', before)}
    old_secret['dialogue_identity_names'] = True
    old_secret['overlay_sha256'] = sha256(changed['resident'])
    # Existing secret-letter validation verifies all unmodified prefix/BSS/table
    # content when the layered profile is installed and in the final cartridge.
    replacements.update({spec.vrom: changed['conversation'], s.VROM: changed['resident']})
    report['secret_actor'] = secret
    return {'actors': {name: {'vrom': f'{VROMS[name]:08X}', 'sha256': sha256(data),
                             'calls': [f'{call:08X}' for call, _ in CALLS[name]]} for name, data in changed.items()},
            'bridge': f'{BRIDGE:08X}', 'name_bytes': 8, 'actor_size_changes': False,
            'saved_layout_changes': False}


def verify_installation(built, native, report):
    import secret_actor as s
    import text_extension as t
    verify_installed_bridge(built)
    if not report.get('text_extension', {}).get('identities'):
        raise ValueError('Missing verified conversation identity capability')
    files = by_vrom(built); entry = report['conversation_names']
    original, reloc = t.source(native, 'letter'); spec = t.ACTORS['letter']
    expected = bytearray(original); at = spec.entry-spec.ram
    expected[at:at+t.CALLS['letter'][0]] = t.call_body('letter')
    expected = patch('conversation', expected)
    if files[spec.vrom].extract(built) != expected or files[spec.relocation].extract(built) != reloc:
        raise ValueError('Incomplete conversation identity-name actor')
    s.verify_installation(built, native, report['runtime_module'], report['secret_actor'])
    if report['secret_actor']['overlay'].get('dialogue_identity_names') is not True:
        raise ValueError('Resident dialogue identity-name reader is absent')
    data = files[s.NEW_VROM].extract(built); patch('resident', data, reverse=True)
    wanted = {'actors': {name: {'vrom': f'{VROMS[name]:08X}', 'sha256': sha256(value),
                              'calls': [f'{call:08X}' for call, _ in CALLS[name]]}
                        for name, value in (('conversation', expected), ('resident', data))},
              'bridge': f'{BRIDGE:08X}', 'name_bytes': 8, 'actor_size_changes': False, 'saved_layout_changes': False}
    if entry != wanted: raise ValueError('Changed conversation identity-name evidence')
    return entry
