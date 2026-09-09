"""Pinned owner-message editor sources; installation is verified separately."""

from pathlib import Path
import struct

from aflib import by_vrom, sha256, verified_rom
from gc_names import symbol_data
from gyroid_default import native_sources as default_sources, reference_payloads, DEFAULT
from runtime_module import module_command_info

ROOT = Path(__file__).resolve().parents[1]
HBOARD, HBOARD_RELOC, HBOARD_RAM = 0x78A560, 0x78ADC0, 0x808828D0
EDITOR, EDITOR_RELOC, EDITOR_RAM = 0x78CB80, 0x790530, 0x80885140
OWNER, OWNER_RELOC = 0x7749C0, 0x7778B0
NATIVE = {
    HBOARD: (2144, '5c1b25289e3db5811211db27ffb97bd3a4482251365b8c1603fd6051384149e8'),
    HBOARD_RELOC: (112, '335935f98d42bdf26b13497e7db0c5b3edc74b898a85de96f9cc36cf8fa31ea2'),
    EDITOR: (14768, '3def63100dd8c7910784eab8f14277bb99813be632fefd2e0afebcfddc9c3011'),
    EDITOR_RELOC: (880, 'cfd0b256e3c63d13ca5612bcb3647d72dbf7f5bf0aa68ae469a428eb6afdc572'),
    OWNER: (12016, 'ff0c90d15d6e17baa1eee5acdf86cf1fe8af9ce5479acc8f6e55d731fc837a20'),
    OWNER_RELOC: (560, '6bf5b91ed57e9ede41bbff8bbe6dea18844e99fcfe668b88a0e115cc5669a5fa'),
}
METADATA = {
    HBOARD: (0x2A50, bytes.fromhex('0078a5600078adc0808828d0808831308088306c808830e880882fac00000000')),
    EDITOR: (0x2B50, bytes.fromhex('0078cb80007905308088514080888b20808883f8808884e48088835400000000')),
}
GC_SYMBOLS = {
    'mHB_strLineCheck': (188, 'd4f0ef94c51dc21e00c8d1e1f689db9f7938352e1b3d0484161411063294e58d'),
    'mHB_set_character': (584, '8fb19bba276a78e58c76c720f9740c66bf882090b6e8ab8b03bbdf361b254bb9'),
    'mHB_set_dl_sub': (384, 'ac3799530a6964be38acc439e634219419308285e22430105e38df1f8ad56e30'),
    'mHB_hboard_ovl_init': (108, '486abea1fff4085d850ca214974ef92d97a0eefd4c01ff382f0f2e62c12bfc6a'),
    'mED_get_col_line_width': (360, '8313f80d1bcb0a0819f7745e935f68c2e51be28e6fccdaaeae1f2af803ad9d72'),
    'mED_check_line_over': (144, 'ef55fc0e4344e00841b8784217e0405823efa59df554c4f00c1426edffe5b4da'),
    'mED_edit_func_multi_line': (164, 'd6f514a95333bed6fbf88fbfa569fcdf7b0d917df2625ba9d3147690ee1ee657'),
    'mED_end_edit_func': (80, 'cdce56519d468ce12791d13fd5e3c1f948145fa887121b94f9f22458501320e6'),
}
GC_SOURCE = {
    'm_hboard_ovl.c': '463452d58d786124277c0aafc62c482edbe758287dbb0313d3ea0c3f0ea17a50',
    'm_editor_ovl.c': 'e3d15e50af75a51fc7d7aec816c955204456c1a2436164774d7f74fbae2e1ae4',
}


def native_sources(native):
    native = verified_rom(native); files = by_vrom(native)
    data = {v: files[v].extract(native) for v in NATIVE}
    if any((len(data[v]), sha256(data[v])) != expected for v, expected in NATIVE.items()):
        raise ValueError('Changed native owner-message editor, window, or submenu owner')
    for v, reloc, sections in ((HBOARD, HBOARD_RELOC, (2096, 32, 16, 0, 19)),
                              (EDITOR, EDITOR_RELOC, (13248, 1440, 80, 48, 212))):
        at, expected = METADATA[v]
        if (files[reloc].index != files[v].index + 1 or
                struct.unpack_from('>5I', data[reloc]) != sections or
                data[OWNER][at:at+32] != expected):
            raise ValueError('Changed owner-message editor allocation or relocation')
    # Native open passes HBOARD mode 1, 16 columns, and a pointer directly into
    # the 64-byte save field. Mode 2 uses the SAME edit function; never replace
    # the function globally when only the owner-message editor is in scope.
    if (struct.unpack_from('>2I', data[HBOARD], 0x80883054-HBOARD_RAM) != (0x0C03136C, 0x24070010)
            or struct.unpack_from('>5I', data[EDITOR], 0x80888824-EDITOR_RAM) !=
            (0x80886674, 0x808862EC, 0x808862EC, 0x808863B8, 0x808863B8)
            or struct.unpack_from('>I', data[EDITOR], 0x808869A4-EDITOR_RAM)[0] != 0x0C2216BB):
        raise ValueError('Changed owner-message opening, mode dispatch, or cursor update')
    return data


def reference_sources():
    rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(rel) != '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed supplied owner-editor executable')
    for name, expected in GC_SYMBOLS.items():
        value = symbol_data(rel, symbols, name)
        if (len(value), sha256(value)) != expected: raise ValueError('Changed English owner-editor function: '+name)
    sources = {name: (ROOT/'local/ac-decomp/src/game'/name).read_bytes() for name in GC_SOURCE}
    if any(sha256(sources[n]) != digest for n, digest in GC_SOURCE.items()):
        raise ValueError('Changed owner-editor reference source')
    return {n: value.decode() for n, value in sources.items()}


def audit(native):
    native_sources(native); reference_sources()
    saved = default_sources(native)['string'][DEFAULT]
    english, _, _ = reference_payloads(native, module_command_info(native))
    return {'native_resources': {f'{v:08X}': {'bytes': n, 'sha256': h} for v, (n, h) in NATIVE.items()},
            'reference_functions': {n: {'bytes': size, 'sha256': h} for n, (size, h) in GC_SYMBOLS.items()},
            'reference_source_sha256': GC_SOURCE, 'native_default_sha256': sha256(saved),
            'english_default_sha256': sha256(english), 'saved_bytes': 64, 'draft_bytes': 128,
            'line_pixels': 192, 'lines': 4, 'mode': 1, 'shared_native_mode_preserved': 2,
            'saved_field_follows': 'held Bells', 'native_editing': 'direct saved writes, Done closes editor',
            'status': 'Native/reference source audit; cartridge installation is not inferred'}
