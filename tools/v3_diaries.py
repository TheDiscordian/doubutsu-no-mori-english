"""One source/category contract for all sixteen carried diaries.

The prepared editing/save core does not enable imports. Inventory, calendar/UI,
native saving, and selector installation must be connected before availability.
"""
import struct
import argparse
import json
from pathlib import Path

from aflib import sha256
from v3_room_aliases import discover as room_aliases

ROOT = Path(__file__).resolve().parents[1]
LAYOUT = dict(code=dict(ram=0x80670000, bytes=0x6000),
    state=dict(ram=0x80676000, bytes=48048, guard=0x80681BB0),
    scratch=dict(ram=0x80682000, bytes=120112, guard=0x8069F530))
SOURCES = ('tools/v3_diaries.py','overlays/v3/diary.c','overlays/v3/diary.h',
    'overlays/v3/diary_storage.ld','overlays/v3/save_runtime.c','overlays/v3/save_runtime.h',
    'overlays/v3/console_storage.c','overlays/v3/console_storage.h','overlays/v3/save_compressed.c',
    'overlays/v3/save_compressed.h','overlays/v3/console_save.c','overlays/v3/console_save.h',
    'overlays/v3/save_codec.h')

FUNCTIONS = (
    (0x2A298, 'mDi_strlen', 64, '155929c54d6763de8edd8f5d7fd5157628dba7178c8294df35aa38528917844f',
     'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    (0x2A2D8, 'mDi_clear_diary', 64, '32833286e3668ca4d10e3c639d70e46489731bc76ede0c2e0a970f98308689be',
     'b1bc20945a583d82218f229b2d614efd6ab19b7775fdc3803444b3c57d6605b9'),
    (0x2A318, 'mDi_init_diary', 32, '3e54da6ab1195bbebb1fadd073e321dc67f6e09021e60c74391213a9c0e88b3f',
     'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    (0x89FD4, 'mCD_set_init_diary_data', 108, '7a6a0c7538c170556417653c94cdd9bd81c17a73e86ecd3d60cb640b0df80331',
     '4aa9bdc208361c945e4990b4f87df9044879e29f07a236b4d06b89688c581d1a'),
    (0x2577D4, 'mCD_MVPL_day', 828, '4e8f626c88de5adfba8735bb25f79f8f14480223d0b698a1e6048ebfa25ad039',
     '1329f24b8c951f6f26a33b4509321a6fc51be562d9c98a97ccbe5406a1152d21'),
    (0x25FDEC, 'mDI_Play_read_to_write_scroll', 336, '6fafeb03afc9055f780eab9404d2cbb0ae787c86253fc08491a5e980c6a732ff',
     '52130c6f541dedf07b5f4e20439f8d0daab9ae2e7d8d3574822bf15b9bfeef01'),
    (0x260250, 'mDI_move_Obey', 216, 'f91bf0683552331a6cbff03d33e6ef3abf68d48ae25b5869d37cfc60f63b7b77',
     '729c6a4ccf0812b1605f35763feabe9e59a1003b1ad0faf9174b8c7c538931f3'),
    (0x260E58, 'mDI_diary_ovl_init', 256, 'a0cbbc703fae42bedfd2872435a364f1ce828bc2f7ae2e2d46b9063b946f5a9e',
     'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
)


def discover(source):
    consumers = {}
    for at, name, size, digest, reloc_digest in FUNCTIONS:
        raw, receipt = source.function(at)
        relocs = b''.join(struct.pack('>5I', p, *row) for p, row in sorted(receipt['relocations'].items()))
        if (receipt['symbol'] != name or len(raw) != size or sha256(raw) != digest
                or sha256(relocs) != reloc_digest):
            raise ValueError('Changed complete diary consumer: '+name)
        consumers[name] = receipt
    resources = {}
    for name, size, digest in (
        ('diary_price_table', 34, '03f03edc4e14b91a71ba9a9c5e03f2e1aa3b59807826e14730dfa36661d4030d'),
        ('itemName_dummy', 256, '9fbfe7577bb012797b573409ca63c14a803da4871f976d5a235ac8e92cc4622a'),
        ('edit_line$741', 16, '0113033996772a69a982c7a14656a797e9bac814d0eb4ddce1459dfde1bb6409'),
    ):
        at, n = source.symbol(name)
        raw = source.raw(name)
        if n != size or sha256(raw) != digest or source.pointers(at, n):
            raise ValueError('Changed complete diary resource: '+name)
        resources[name] = dict(symbol=name, offset=at, bytes=n, sha256=digest)
    aliases = room_aliases(source)
    rows = [row for row in aliases['rows'] if row['category'] == 'diary']
    if len(rows) != 16:
        raise ValueError('Incomplete diary-cover category')
    prices = struct.unpack('>17H', source.raw('diary_price_table'))
    if prices[-1] != 65535:
        raise ValueError('Missing diary-price terminator')
    imports = []
    for i, row in enumerate(rows):
        if int(row['parent_item_id'], 16) != 0x2B00+i:
            raise ValueError('Changed carried diary identities')
        imports.append(dict(row, price=prices[i], price_source_symbol='diary_price_table',
            price_source_index=i, selectable=False, runtime_installed=False,
            reason='Calendar/inventory/editor/save integration remains unfinished.'))
    return dict(format='AFV3-DIARIES-1', rows=imports, consumers=consumers, resources=resources,
        players=4, months=12, page_bytes=992, text_bytes=47616,
        calendar_bytes_per_player=104, serialized_bytes=48048,
        shared_across_styles=True, native_installed=False)


def prepare(base_lock, output):
    """Compile the connected category core once; do not install or enable it."""
    from v3_furniture_install import inputs
    from v3_furniture_pipeline import Source
    from v3_console_disk_install import reservations
    from v3_asset_loader import compile_part
    from v3_creature_save import INSECT_DEFINES
    from apply_translation import write_new
    base, prior = inputs(base_lock)
    if prior['save_codec']['format_version'] != 9 or prior['save_codec']['registry_version'] != 5:
        raise ValueError('Diaries require the complete format-nine creature/console save path')
    if not output.resolve().is_relative_to(ROOT/'build'):
        raise ValueError('Diary output must be an ignored local build')
    for name, row in LAYOUT.items():
        start, end = row['ram'], row['ram']+row['bytes']+(16 if name != 'code' else 0)
        if end > 0x807DA800 or any(a < end and start < b for a, b in reservations(prior)):
            raise ValueError('Diary preparation overlaps an existing RAM reservation: '+name)
        if name != 'code' and row['guard'] != row['ram']+row['bytes']:
            raise ValueError('Diary guard escapes the declared allocation')
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    report = discover(source)
    symbols = prior['save_codec']['active_codec_code']['symbols']
    helpers = prior['equipment_resources']['creature_fish']['world']['save']['helpers']['symbols']
    clear = prior['room_surfaces']['save']['helpers']['symbols']['af_v3_surface_player_clear']
    defines = INSECT_DEFINES+('AF_V3_CONSOLE_STORAGE=1','AF_V3_DIARY_STORAGE=1',
        'AF_V3_LINKED_CANONICAL=1',f'AF_CONSOLE_PRIOR_PLAYER_CLEAR=0x{clear:X}u',
        f'AF_DIARY_STATE_RAM=0x{LAYOUT["state"]["ram"]:X}u',
        f'AF_DIARY_SCRATCH_RAM=0x{LAYOUT["scratch"]["ram"]:X}u')
    bindings = {name: symbols[name] for name in ('af_v3_save_check_extended','af_v3_save_pack_extended')}
    bindings.update({name: helpers[name] for name in ('af_v3_creature_profile_byte','af_v3_creature_player_clear')})
    bindings.update(af_v3_original_save_read=0x8046BA60,af_v3_original_save_clear=0x8046BA70,
        af_v3_surface_profile_byte=0x804BC900)
    code, compiled = compile_part('diary_storage',output/'runtime',defines=defines,
        primary_source='overlays/v3/save_runtime.c',extra_sources=(
            'overlays/v3/console_storage.c','overlays/v3/save_compressed.c',
            'overlays/v3/console_save.c','overlays/v3/diary.c'),link_symbols=bindings)
    report.update(compiled=compiled,planned_memory=LAYOUT,base_rom_sha256=sha256(base),
        base_runtime_abi=prior['runtime_abi'],base_lock=str(base_lock.resolve().relative_to(ROOT)),
        disk_format=11,canonical_format=8,registry=5,bank_bytes=65536,flash_bytes=131072,
        code_file='runtime/code.bin',code_sha256=sha256(code),
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES},
        remaining_consumers=['Inventory identity/use and carried artwork',
            'Calendar selection, date/event maintenance, and donor menu artwork',
            'Native keyboard/read-view bindings and English UI provenance',
            'Resident loading, stable save dispatch, and profile/selector integration'])
    write_new(output/'diaries.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-lock',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = prepare(args.base_lock,args.output)
    print(json.dumps(dict(styles=len(report['rows']),compiled_bytes=report['compiled']['bytes'],
        installed=report['native_installed'],output=str(args.output))))


if __name__ == '__main__':
    main()
