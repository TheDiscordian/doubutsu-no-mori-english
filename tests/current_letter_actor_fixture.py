"""In-memory early actor-install stages with current source-bound dependencies.

The real combined cartridge stays separate: its later reader and accent changes
are verified, never replaced on disk or presented as a new playable build.
"""

from copy import deepcopy
import json
from types import SimpleNamespace

from aflib import CODE_RAM,CODE_VROM,by_vrom,replace_dma,sha256,verified_rom
from leaflet_dates import patched
from mail_view_patch import install as install_reader,verify_reader_files
from runtime_layout import MODULE_VROM
from runtime_module import verify_test_module
import event_actor
import fortune_actor
import renewal_actor


def current_actor_fixture(root,kind):
    owner = {'event':event_actor,'renewal':renewal_actor,'fortune':fortune_actor}[kind]
    directory = root/('build/shop-notice-'+kind)
    base = root/'build/v0-hardware-fixes-02'
    native = verified_rom((root/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    current = (base/'animal-forest-halfwidth.z64').read_bytes()
    current_build = json.loads((base/'build.json').read_text())
    if sha256(current)!=current_build['output_sha256']:
        raise ValueError('Changed combined letter-actor fixture cartridge')
    module = current_build['runtime_module'];files = by_vrom(current)
    verify_test_module(current,module)
    if kind=='fortune':
        data,reloc = ((directory/name).read_bytes() for name in ('overlay.bin','relocation.bin'))
        report = json.loads((directory/'overlay.json').read_text());creator = None
        owner.verify_installation(current,native,current_build['fortune_actor']['overlay'],module)
        owner.validate(native,data,reloc,report,module)
    else:
        data,reloc,report,creator = owner.load(directory)
        owner.verify_installation(current,native,current_build[kind+'_actor']['overlay'],module,creator)
        owner.validate(native,data,reloc,report,module,creator,report['creator'])
    installed = current_build[kind+'_actor']['overlay']
    if kind=='event':
        # The actual current actor has the later, fully verified accent adapter.
        from accent_mail_overlay_profile import validate as validate_accent
        previous,previous_reloc,previous_report,_ = validate_accent(
            'event',files[owner.NEW_VROM].extract(current),files[owner.NEW_RELOCATION].extract(current),installed)
        if (previous!=data or previous_reloc!=reloc
                or previous_report!={**report,'creator_offset':owner.PREFIX_BYTES}):
            raise ValueError('Current event actor does not retain the source-built predecessor')
    elif (installed!=report or files[owner.NEW_VROM].extract(current)!=data
            or files[owner.NEW_RELOCATION].extract(current)!=reloc):
        raise ValueError('Current letter actor differs from its source-built fixture')

    moved = {int(k,16):int(v,16) for k,v in current_build['vrom_relocations'].items()}
    replacements = {int(k,16):files[moved.get(int(k,16),int(k,16))].extract(current)
                    for k in current_build['replacement_files']}
    additions = {int(k,16):files[int(k,16)].extract(current) for k in current_build['added_files']}
    original_maps = dict(replacements)

    # These early installers require their exact original snapshot-reader pair.
    # Construct it through the guarded reader installer, not a relaxed check.
    raw = bytearray(additions[MODULE_VROM]);raw[56:0x88] = bytes(0x88-56)
    if sha256(raw)!=module['module_sha256']:
        raise ValueError('Current actor fixture does not contain the approved resident code')
    reader = {};install_reader(native,reader,{MODULE_VROM:bytes(raw)},module,snapshots=True)
    if set(reader)!={0x7908A0,0x792610}:
        raise ValueError('Unexpected early snapshot-reader ownership')
    verify_reader_files(current,native,module,reader)
    replacements.update(reader)
    replacements.update({owner.VROM:data,owner.RELOCATION:reloc})
    code = replacements[CODE_VROM];at = owner.METADATA-CODE_RAM
    if code[at:at+32]!=owner.metadata(len(data)):
        raise ValueError('Early actor fixture requires different ownership bounds')
    changed = {v for v in replacements if replacements[v]!=original_maps.get(v)}
    expected = set(reader) | ({owner.VROM,owner.RELOCATION} if kind=='event' else set())
    if changed!=expected:
        raise ValueError('Early actor fixture changes unexpected combined resources')
    # Expected installed ROM is assembled independently of owner.install.
    rom = replace_dma(native,replacements,moved,additions)
    build = deepcopy(current_build);build[kind+'_actor']['overlay'] = report
    build['output_sha256'] = sha256(rom)

    # Back out only this owner's installation. Renewal/event require a date
    # patch; fortune requires the unmodified original actor and no replacement.
    if kind=='fortune':
        for v in (owner.VROM,owner.RELOCATION): replacements.pop(v)
    else:
        replacements[owner.VROM],replacements[owner.RELOCATION] = patched(native,kind,module)
    code = bytearray(code);code[at:at+32] = by_vrom(native)[CODE_VROM].extract(native)[at:at+32]
    replacements[CODE_VROM] = bytes(code)
    for v in (owner.VROM,owner.RELOCATION): moved.pop(v)
    return SimpleNamespace(native=native,current=current,current_build=current_build,module=module,
        directory=directory,data=data,reloc=reloc,report=report,creator=creator,rom=rom,build=build,
        replacements=replacements,additions=additions,moved=moved)
