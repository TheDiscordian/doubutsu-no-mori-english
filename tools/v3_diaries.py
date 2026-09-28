"""One source/category contract for all sixteen carried diaries.

The prepared editing/save core does not enable imports. Inventory, calendar/UI,
native saving, and selector installation must be connected before availability.
"""
import struct
import argparse
import json
from pathlib import Path

from aflib import sha256,by_vrom,CODE_RAM,CODE_VROM
from v3_room_aliases import discover as room_aliases

ROOT = Path(__file__).resolve().parents[1]
LAYOUT = dict(code=dict(ram=0x80670000, bytes=0x6000),
    state=dict(ram=0x80676000, bytes=48048, guard=0x80681BB0),
    scratch=dict(ram=0x80682000, bytes=120112, guard=0x8069F530))
SOURCES = ('tools/v3_diaries.py','overlays/v3/diary.c','overlays/v3/diary.h',
    'tools/v3_furniture_pipeline.py','tools/v3_furniture_art.py','tools/map_artwork.py',
    'overlays/v3/diary_calendar.c','overlays/v3/diary_menu.c','overlays/v3/diary_menu.h',
    'overlays/v3/diary_room.c','overlays/v3/diary_room.h','overlays/v3/room_carry.h',
    'overlays/v3/room_carry.c','overlays/v3/room_carry_native.h','overlays/v3/room_rigs.h',
    'overlays/v3/room_goods.h','overlays/v3/furniture_tables.h',
    'overlays/v3/diary_storage.ld','overlays/v3/save_runtime.c','overlays/v3/save_runtime.h',
    'overlays/v3/console_storage.c','overlays/v3/console_storage.h','overlays/v3/save_compressed.c',
    'overlays/v3/save_compressed.h','overlays/v3/console_save.c','overlays/v3/console_save.h',
    'overlays/v3/save_codec.h','translations/provenance.json')

REFERENCES = {
    'src/game/m_calendar.c':'f6683884803ee1373b84ea55d9a4deca268dde4d4eb494a4138f6a1599f5e467',
    'src/game/m_calendar_ovl.c':'0c89cea3375ec0fad0721c628a2da2cc61fde9174987a9079fb4ae99be4df042',
    'src/game/m_diary_ovl.c':'b233e6c318d9f76000c4747dea182e1f12ae83583d7f76cc9097ca5e07b7b574',
    'src/game/m_cpwarning_ovl.c':'892757968b20f55d003c1b14f4f0683e59526659e9e9ff70316b887456cc6393',
    'src/game/m_editEndChk_ovl.c':'a3b353c7eb0c5316b272bf4caa87e1b99a612aef917f6bbd99b4d6d515ba95cb',
    'src/actor/ac_my_room_move.c_inc':'bf1243efb55b25afa4a75043ef38080292c79f308038dda0d287b919e0beaf3d',
}


def native_contract(image):
    files=by_vrom(image);core=files[CODE_VROM].extract(image)
    consumers=[]
    for address,size,digest in (
        (0x80078D30,72,'64caa4eba4dac0d0259e292053a2463d65322310384dd2e790a067ea10da8d77'),
        (0x80087C88,20,'404f3a26d8ea043750074135ccc347a02f695258299b86315e8c89bcfe1794ba'),
        (0x800B1C84,12,'f680a77d022740add2a8ead09c6438223d596b51cd655775b7a7ec0c80725404'),
        (0x800B7914,72,'c2711609a2ae0bb6da42780f6c2e6dc93e9439879c89ee19280ffe474925b2d5'),
        (0x800B7FD4,148,'1c99b0981b06a09b0470ed4d42a2527e74a7f3f25ae12f9cc263e306491ea30d'),
        (0x80094C44,104,'081dbe394fe97d09344d031bc35a68c66761e7843b1e442288d1d55d3b036740'),
    ):
        if sha256(core[address-CODE_RAM:address-CODE_RAM+size])!=digest:
            raise ValueError(f'Changed native diary interaction dependency {address:08X}')
        consumers.append(dict(address=address,bytes=size,sha256=digest))
    room,rel=(files[v].extract(image) for v in (0x82D7F0,0x844400))
    if (sha256(room[0x7454:0x7A68])!='31238d1ca85c2c538d726a15010b97b5d1628cfe05341ed54d97d8cbca186212'
            or room[0xB950:0xB958]!=bytes.fromhex('0c24f6d98fa70034')):
        raise ValueError('Changed complete native diary A-tap routine/caller')
    sections=struct.unpack_from('>5I',rel)
    rows=struct.unpack_from('>'+str(sections[4])+'I',rel,20)
    if rows.count(0x4400B950)!=1:
        raise ValueError('Missing unique native diary caller relocation')
    return dict(consumers=consumers,room_vrom=0x82D7F0,room_ram=0x80936710,
        owner_sha256=sha256(room),relocation_sha256=sha256(rel),
        hook_address=0x80942060,hook_before='0c24f6d98fa70034',remove_relocation=0x4400B950,
        house_base=0x8012A428,house_stride=0xB48,submenu_offset=0x1CBC,
        implemented_in_source=True,installed=False)

UI_TEXT = (
    ('privacy-question-1','mCW_mes0','5d14c83f9124111801cd4af5569f9b94c8289cf06c4866c4fe9ba4d615aeafef'),
    ('privacy-question-2','mCW_mes1','ec4b29768ad7aa566a015d79078fda11728a46da8556225070e0a42a7fd5ff2b'),
    ('privacy-yes','mCW_yes_mes','85a39ab345d672ff8ca9b9c6876f3adcacf45ee7c1e2dbd2408fd338bd55e07e'),
    ('privacy-no','mCW_no_mes','1ea442a134b2a184bd5d40104401f2a37fbc09ccf3f4bc9da161c6099be3691d'),
    ('finish-question','mEE_str_table','1dd5dcf392e405944dec1fd72108dadfd55244db0856d595c1a3b965757f86f1'),
    ('finish-yes','mEE_str_data0','85a39ab345d672ff8ca9b9c6876f3adcacf45ee7c1e2dbd2408fd338bd55e07e'),
    ('finish-rewrite','mEE_str_data1','272f25fe45d2ccccd07a01366d2a0206bfd61c7deeeab7a69e2a0cd1d770ac50'),
    ('locked','wr_This_diary_is_locked','3940402d222ef0e514c9db572d3e5bda1024264fcd0aacce903565167d971690'),
)


def ui_text(source):
    entries={e['id']:e for e in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
    result={}
    for key,symbol,digest in UI_TEXT:
        at,size=source.symbol(symbol);raw=source.raw(symbol)
        record=entries['v3/diary/'+key]['locales']['en']
        if (sha256(raw)!=digest or source.pointers(at,size) or record['credit']!='official'
                or record['source']['symbol']!=symbol or record['source']['data_offset']!=f'{at:08X}'
                or record['encoded_sha256']!=digest or record['text'].encode('ascii')!=raw):
            raise ValueError('Changed official diary UI/provenance: '+key)
        result[key]=dict(symbol=symbol,offset=at,bytes=size,sha256=digest,encoded=raw.hex(),
            provenance_id='v3/diary/'+key)
    for key in ('capacity','invalid','changed'):
        record=entries['v3/diary/'+key]['locales']['en']
        raw=record['text'].encode('ascii').replace(b'\n',b'\xCD')
        if record['credit']!='assistant' or sha256(raw)!=record['encoded_sha256']:
            raise ValueError('Changed project diary UI/provenance: '+key)
        result[key]=dict(bytes=len(raw),sha256=sha256(raw),encoded=raw.hex(),provenance_id='v3/diary/'+key)
    return result

FUNCTIONS = (
    (52968, 'mCD_calendar_clear_interval', 368, 'e941bb59aaf783445bc99db19e5279b29ed9e039baf7036c2c9f6101fcabe2b7', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    (53336, 'mCD_calendar_clear_day', 528, '837e713b90fef3597b96285cb4e964276458986f4d080d9a04724e788f4a1551', 'e7174da200c3b3be320bcacdcd3370a5e289c7501e628c2389f89dd3cda28da0'),
    (54064, 'mCD_calendar_check_delete', 216, 'eaeb5557e1129a2c738921539362ca1f23e554d6ec569678cdd133439b55045c', '1c6206d0c80a48396a9f47a664162eaddca322431ab63a43899862330ec466a0'),
    (54280, 'mCD_calendar_wellcome_on', 152, '26338a958871ab913fd3360d35a92cc83a0840dccb8a8f6dddd6d998f190fa36', '86486c89ef6806e4ef06cbf4b8d2e5becef579e02ea4cbe04c13051bc3a85636'),
    (54432, 'mCD_calendar_event_on', 388, 'e24536cd21cbe965a92d86388e66bcb7a206819a275089270e69fbc95162ad12', 'b7f2da23933e6b46108bdecbff4be61dd835977445d65e2d3817a016eaf8a063'),
    (1086324, 'aMR_CheckDiaryOnMe', 448, '99816b218667c2a7b39ba50cf709f94af1e19806737c2cb2a126ab89bd661259', 'c462c7c9719ba18d00a6456a579e82b3812998b4f6ab44165bff648f542309d3'),
    (1086772, 'aMR_ManageMoveBottun', 1864, 'a01addf06702e1dffbd70e36043fa299c515001be393272a7d7f61c5633b3173', 'a6b56d628b274b3f4f61873edd0275d49a15e5cb2b803544309d541a8cc3ba0a'),
    (2450836, 'mCD_sp_soncho_chk', 332, '583b6fed96b706b2f94c5f72a24e1235bc8b0fac3c8843b407410b7218de6761', '9faa8d4fad1f8ec9c90e1480f2c65d0b6a6d8273c8ea8fa3ee7e170ce7f33ee1'),
    (2451344, 'mCD_make_icon', 164, '19d88aac4df7f40ad242eb13578225c09753123962f8d181cf9af6e7422c8d9f', 'a0741c5b1c2a9d894873b0d0f533668f970d40d89f6d46ef3cafceaf12f42c0a'),
    (2454232, 'mCD_MVPL_select', 444, '8e393d21e8a6776399c924d658310f0b6ca0a16658ccc12967cf4ddcaabab527', '16d11ef5be8ccfa64e43821820589ae8a21e9582c9993a4faeefb27f73baa662'),
    (2484832, 'mCW_move_Play', 392, '54f4e65907387f3d88bb2810648c1bdbc6a2898bcdf447670d7dd95f8b058d86', 'ea310360602c786323a41dfd9b8f81dc4488d6d6244913130a3651d337786717'),
    (2521064, 'mEE_move_Play', 588, '496a18d792afb51574aba528d98f29532d9b21a1da4c1dcf59b2271230961190', '1d758d01d98db35159a4502c0a13bbe9be11927db8f8081a17516ef34fa844e1'),
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
    for path,digest in REFERENCES.items():
        if sha256((ROOT/'local/ac-decomp'/path).read_bytes())!=digest:
            raise ValueError('Changed diary behaviour reference: '+path)
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
        shared_across_styles=True, native_installed=False,ui_text=ui_text(source),references=REFERENCES)


def prepare(base_lock, output):
    """Compile the connected category core once; do not install or enable it."""
    from v3_furniture_install import inputs
    from v3_furniture_pipeline import Source,prepare_material_pair,compile_models
    from v3_console_disk_install import reservations
    from v3_asset_loader import compile_part
    from v3_creature_save import INSECT_DEFINES
    from apply_translation import write_new
    output=output.resolve();base_lock=base_lock.resolve()
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
    report['native_interaction']=native_contract(base)
    # One shared room/pocket representation for every diary style. Reuse the
    # general split material/geometry converter; cover artwork is separate.
    parts=[(name,*source.symbol(name)) for name in ('obj_item_diaryT_mat_model','obj_item_diaryT_gfx_model')]
    prepared=prepare_material_pair(source,parts)
    (output/'carried').mkdir(parents=True,exist_ok=False)
    artwork,offsets,models,_=compile_models(output/'carried',prepared)
    write_new(output/'carried.bin',artwork)
    report['carried_artwork']=dict(file='carried.bin',bytes=len(artwork),sha256=sha256(artwork),
        models=models,offsets=offsets,resources=prepared[2],shared_styles=16,installed=False)
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
            'overlays/v3/console_save.c','overlays/v3/diary.c',
            'overlays/v3/diary_calendar.c','overlays/v3/diary_menu.c'),link_symbols=bindings)
    report.update(compiled=compiled,planned_memory=LAYOUT,base_rom_sha256=sha256(base),
        base_runtime_abi=prior['runtime_abi'],base_lock=str(base_lock.resolve().relative_to(ROOT)),
        disk_format=11,canonical_format=8,registry=5,bank_bytes=65536,flash_bytes=131072,
        code_file='runtime/code.bin',code_sha256=sha256(code),
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES},
        remaining_consumers=['Inventory identity/use and carried artwork',
            'Native calendar/date/event bindings and donor menu artwork',
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
