"""Carry checked translation corrections into the shared V3 refresh pipeline."""
import copy
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from catalogue_names import Image
from letter_ui_fix import compile_part
import letter_names as names
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, MODULE_VROM
import v2_museum_header_fix as museum

ROOT = museum.ROOT
BASELINE = dict(path='build/v2-museum-header-12-final/Animal Forest English V2.z64',
    sha256='a09373b051cbcd93991e5dd6cb17a238a2afb1e2e2d7694d75408d24a55d4eee', build='V2-12')
BOARD_SHA = '947308fd0d1df3aba78b75b57b78436b32a6ca9eaae9c789ab6a5c6b9a2a9fbe'
READER_BOUND = 0x80198548-MODULE_RAM
SOURCES = ('tools/v3_translation_updates.py', 'tools/letter_ui_fix.py',
           'translations/provenance.json') + museum.SOURCES


def stable_reference(report):
    """Resolve a supported explicit baseline, without changing any served build."""
    row = report.get('translation_baseline')
    if row != BASELINE:
        raise ValueError('Unknown corrected translation baseline')
    path = ROOT/row['path']
    if sha256(path.read_bytes()) != row['sha256']:
        raise ValueError('Changed corrected translation baseline')
    return path, row['sha256'], row['build']


def patch_reader(module, gate, stable_before, stable_after):
    """Retain every V3 change; add the museum case and extended-name bound only."""
    start = museum.NAME_ENTRY-MODULE_RAM
    end = 0x80198584-MODULE_RAM
    if (sha256(stable_before) != museum.MODULE_SHA or
            stable_after != museum.patch_module(stable_before, gate) or
            module[start:end] != stable_before[start:end] or any(module[0x88:0x100]) or
            struct.unpack_from('>I',module,READER_BOUND)[0] != 0x2CC200D8):
        raise ValueError('Changed complete letter name reader or occupied adapter reservation')
    result = bytearray(module)
    result[0x90:0x90+len(gate)] = gate
    struct.pack_into('>2I',result,start,museum.jump(museum.GATE),0)
    struct.pack_into('>I',result,READER_BOUND,0x2CC200EE)
    return result


def install(base, prior, module, output):
    if 'translation_updates' in prior:
        raise ValueError('Translation corrections already installed')
    stable_path, stable_sha, stable_build = stable_reference({'translation_baseline':BASELINE})
    fixed = stable_path.read_bytes()
    before = (ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
    if sha256(before) != museum.BASE_SHA:
        raise ValueError('Changed preceding translation baseline')
    old_files, fixed_files, files = by_vrom(before), by_vrom(fixed), by_vrom(base)
    old_board = files[names.NEW_VROM].extract(base)
    old_rel = files[names.NEW_RELOC].extract(base)
    # The sole prior V3 board edit expands the native villager-name lookup.
    expected = bytearray(old_files[names.NEW_VROM].extract(before))
    if sha256(expected) != museum.BOARD_SHA or struct.unpack_from('>I',expected,0x1FF8)[0] != 0x2CC200D8:
        raise ValueError('Changed prior translation letter board')
    struct.pack_into('>I',expected,0x1FF8,0x2CC200EE)
    if old_board != expected or sha256(old_board) != BOARD_SHA or sha256(old_rel) != museum.REL_SHA:
        raise ValueError('Changed V3 editor or name-bound extension')
    spec = dict(vrom=names.NEW_VROM,reloc=names.NEW_RELOC,ram=names.RAM,
                sha=BOARD_SHA,reloc_sha=museum.REL_SHA,imports=names.IMPORTS,calls={})
    data, relocation, receipt = compile_part('translation_headers',base,output/'translation-headers',
        spec=spec,source='/source/overlays/letter_names/names.c',
        flags=('-DAF_MUSEUM_HEADER','-DAF_LETTER_NPC_COUNT=238u'))
    data = bytearray(data); at = names.HEADER-names.RAM
    if struct.unpack_from('>2I',old_board,at) != (museum.jump(names.RAM+7828),0):
        raise ValueError('Changed header entry')
    struct.pack_into('>I',data,at,museum.jump(names.RAM+receipt['symbols']['af_letter_header']))
    rows = struct.unpack_from('>'+str(struct.unpack_from('>I',relocation,16)[0])+'I',relocation,20)
    if rows.count(0x44000000|at) != 1:
        raise ValueError('Missing header entry relocation')
    for location in (0x80200010,0x80378010):
        old = relocate_verified_data(Image(names.RAM,len(old_board),struct.unpack_from('>5I',old_rel)),old_board,old_rel,location)
        new = relocate_verified_data(Image(names.RAM,len(data),struct.unpack_from('>5I',relocation)),data,relocation,location)
        if old[:at] != new[:at] or old[at+4:] != new[at+4:len(old)]:
            raise ValueError('Translation update changes retained V3 editor code')
    growth = ((len(data)+63)&~63)-((len(old_board)+63)&~63)
    if (len(old_board) != 10992 or not 0 < growth <= 2560 or
            struct.unpack_from('>I',files[CODE_VROM].extract(base),0x800C4B10-CODE_RAM)[0] != 0x25CE8E20):
        raise ValueError('Changed V3 submenu pool or exhausted letter reservation')
    owner = bytearray(files[names.OWNER].extract(base))
    if struct.unpack_from('>4I',owner,names.OWNER_AT) != (names.NEW_VROM,names.NEW_VROM+len(old_board),names.RAM,names.RAM+len(old_board)):
        raise ValueError('Changed V3 letter owner allocation')
    struct.pack_into('>4I',owner,names.OWNER_AT,names.NEW_VROM,names.NEW_VROM+len(data),names.RAM,names.RAM+len(data))
    gate = museum.compile_gate(output/'translation-reader')
    updated = patch_reader(module,gate,old_files[MODULE_VROM].extract(before),fixed_files[MODULE_VROM].extract(fixed))
    module[:] = updated
    receipt.update(overlay_sha256=sha256(data),touched_offsets=list(range(at,at+4)))
    changes = {names.NEW_VROM:bytes(data),names.NEW_RELOC:relocation,names.OWNER:bytes(owner)}
    readers = copy.deepcopy(prior['villager_readers'])
    rows = [r for r in readers['owners'] if r['vrom'] == f'{names.NEW_VROM:08X}']
    if len(rows) != 1 or rows[0]['output_sha256'] != sha256(old_board):
        raise ValueError('Changed installed letter-reader receipt')
    rows[0].update(bytes=len(data),output_sha256=sha256(data),relocation_sha256=sha256(relocation),
        translation_headers_updated=True)
    readers['resident_header_bound'] = dict(address=f'{READER_BOUND+MODULE_RAM:08X}',
        before='2CC200D8',after='2CC200EE',limit=238)
    report = dict(format='AFV3-TRANSLATION-UPDATES-1',museum_headers=True,
        official_text_id='ui/mail/museum-name',board=receipt,board_growth_bytes=growth,
        additional_pool_bytes=0,reader_gate=f'{museum.GATE:08X}',reader_gate_bytes=len(gate),
        reader_gate_sha256=sha256(gate),reader_bound=f'{READER_BOUND+MODULE_RAM:08X}',
        villager_limit=238,saved_format_changed=False,delivery_code_changed=False,
        web_patcher_enabled=False,native_test='pending changed translation headers',
        changed_resources={f'{v:08X}':sha256(d) for v,d in changes.items()},
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return changes,dict(translation_updates=report,villager_readers=readers,
        translation_baseline=dict(path=str(stable_path.relative_to(ROOT)),sha256=stable_sha,build=stable_build))
