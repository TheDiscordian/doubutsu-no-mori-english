"""Reusable representative furniture reader/DMA/acquisition check from a build manifest."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace
from aflib import by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM
from v3_npc_draw_smoke import boot_proofs
import v3_furniture_install as runtime
import v3_furniture_runtime as furniture
import v3_catalogue as catalogue


def representatives(rows):
    """Cover each footprint, stock, and layer category, not each item identity."""
    result, covered = [], set()
    for row in sorted(rows,key=lambda r:(-r['object_bytes'],r['item_id'])):
        features={('size',row['size_code']),('stock',row['stock_group']),('sound',row.get('action_sound',0)),
                  ('placement',row.get('layer_type',0)),('interaction',row.get('interaction_flags',0)),
                  ('preview',row.get('preview_mode',0)),
                  ('lighting',bytes.fromhex(row['native_profile_scalar_hex'])[11]),
                  ('contact',bytes.fromhex(row['native_profile_scalar_hex'])[12]),
                  ('layers',tuple(sorted(row.get('model_offsets',{}))))}
        if features-covered: result.append(row); covered.update(features)
    if len(result)>12: raise ValueError('Split new behaviour categories into bounded smoke passes')
    return result


def exercise(debug, rom_path, record, *, section='automatic_furniture'):
    path = Path(rom_path)
    image = path.read_bytes()
    report = json.loads((path.parent / 'build.json').read_bytes())
    if sha256(image) != report['output_sha256'] or report['runtime_abi'] < 84:
        raise ValueError('Furniture probe requires its current checked cartridge')
    rows = representatives(report[section]['imports'])
    record(dict(representative_furniture=[r['item_id'] for r in rows],
                categories=['stock','footprint','display-list layers','action sounds','placement layers',
                            'interaction flags','preview framing','lighting','contact behaviour']))
    files, boot = by_vrom(image), boot_proofs(image)
    blob = files[runtime.BLOB].extract(image)

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record(dict(furniture_batch_check=label, address=f'{address:08X}', bytes=len(expected),
                    assertion='passed' if actual == expected else 'failed',
                    expected_sha256=sha256(expected), observed_sha256=sha256(actual)))
        if actual != expected: raise ValueError('Native furniture mismatch: ' + label)

    def call(address, args=(), expected=None, proof=None):
        result = debug.call(f'{address:08X}', list(args), return_address=MODULE_RAM + 0x6480,
                            verified_code=proof or boot.get(address))
        if expected is not None:
            result['assertion'] = 'passed' if result['return_value'] == expected else 'failed'
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Native furniture call {address:08X}: unexpected result')
        return result['return_value']

    check('current startup and profile', 0x80460000, blob[:0x100])
    if 'furniture_placement' in report:
        placement=report['furniture_placement'];start=placement['reservation_start'];end=placement['reservation_end']
        at=runtime.PACKAGE+start-runtime.PACKAGE_RAM
        check('complete placement table and guards',start,blob[at:at+end-start])
    if 'catalogue_preview_records' in report:
        preview=report['catalogue_preview_records'];start=preview['reservation_start'];end=preview['reservation_end']
        at=runtime.PACKAGE+start-runtime.PACKAGE_RAM
        check('complete catalogue framing table and guards',start,blob[at:at+end-start])
    saved = {at: debug.read_memory(at, n) for at, n in (
        (0x80100DF0, 32), (0x8046C000, 864), (0x80126EC0, 0xBD0),
        (0x80136FD8, 4), (0x80135B1C, 1), (0x80135C00, 2), (0x801458B8, 4))}
    pool = report['furniture']['bank_pool']
    bank, bank_size = pool['data'], pool['bank_bytes']
    bank_before = debug.read_memory(bank, bank_size)
    index_ram = int(report['furniture']['expanded_tables']['bank_index_ram'], 16)
    for row in rows:
        at = index_ram + row['runtime_index']; saved[at] = debug.read_memory(at, 1)
    size = 0x21000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM + 0x8000 <= allocation <= 0x80400000 - size:
        raise ValueError('Furniture fixture allocation outside native heap')
    owner, scratch, bridge = allocation + 16, allocation + 0x20000, allocation + 0x20F00
    edge = b'V3SD' * 4
    guards = (allocation, scratch - 16, scratch + 0x100, bridge - 16, bridge + 8, allocation + size - 16)
    for at in guards: debug.write_memory(at, edge)

    def load(vrom, reloc_vrom, ram, resident):
        source, reloc = files[vrom].extract(image), files[reloc_vrom].extract(image)
        sections = struct.unpack_from('>5I', reloc)
        if resident + len(reloc) >= scratch - owner - 16:
            raise ValueError('Native furniture owner exceeds its fixture reservation')
        spec = SimpleNamespace(ram=ram, resident_bytes=resident, sections=sections)
        expected = relocate_verified_data(spec, source, reloc, owner)
        call(0x800262D0, [vrom, vrom+len(source), ram, ram+resident, owner, owner+resident, len(reloc)])
        check('complete actual owner load and relocations', owner, expected)
        return expected, (owner, expected[:sections[0]])

    loaded, furniture_proof = load(furniture.VROM, furniture.RELOC, furniture.RAM, furniture.RESIDENT)
    check('native directional chair table after relocation', owner+0x8094CFF8-furniture.RAM,
          loaded[0x8094CFF8-furniture.RAM:0x8094D028-furniture.RAM])
    debug.write_memory(0x80100E00, struct.pack('>I', owner))
    debug.write_memory(owner+0x18D68, struct.pack('>I', bank))
    public = next(r for r in report['furniture']['expanded_tables']['public_entries']
                  if r['name'] == 'af_v3_furniture_import_dma')
    check('installed furniture DMA public entry', public['entry'], bytes.fromhex(public['after']))
    stub = struct.pack('>II', 0x08000000 | ((public['entry'] >> 2) & 0x3FFFFFF), 0)
    debug.write_memory(bridge, stub)
    call(0x8002FE00, [bridge, 8]); call(0x80034CE0, [bridge, 8])
    try:
        if 'furniture_behaviours' in report:
            from v3_furniture_behaviours import RAM as SOUND_RAM,ENTRY as SOUND_ENTRY,NATIVE_CATEGORIES
            from aflib import CODE_RAM,CODE_VROM
            behaviour=report['furniture_behaviours']
            at=runtime.PACKAGE+SOUND_RAM-runtime.PACKAGE_RAM
            check('complete shared behaviour code',SOUND_RAM,blob[at:at+behaviour['code']['bytes']])
            original_types=files[CODE_VROM].extract(image)[NATIVE_CATEGORIES-CODE_RAM:NATIVE_CATEGORIES-CODE_RAM+947]
            for category in (0,1,2):
                index=original_types.index(category)
                call(SOUND_ENTRY,[index,0],(0xFFFFFFFF,0x41F,0x420)[category])
            audible=[r for r in behaviour['imports'] if r['action_sound']]
            for row in audible:
                for mode in (0,1):
                    call(SOUND_ENTRY,[row['runtime_index'],mode],((0x41F,0x422),(0x420,0x423))[row['action_sound']-1][mode])
            if audible:
                row=audible[0]
                profile=next(r for r in report['furniture']['imports'] if r['item_id']==row['item_id'])
                enable=int(profile['profile_ram'],16)-4;saved[enable]=debug.read_memory(enable,4)
                debug.write_memory(enable,bytes(4));call(SOUND_ENTRY,[row['runtime_index'],0],0xFFFFFFFF)
                debug.write_memory(enable,saved[enable])
                for mode in (0xFFFFFFFF,2):call(SOUND_ENTRY,[row['runtime_index'],mode],0xFFFFFFFF)
            for index in (947,1023,2048,0xFFFFFFFF):call(SOUND_ENTRY,[index,0],0xFFFFFFFF)
        for row in rows:
            item, index = int(row['item_id'], 16), row['runtime_index']
            if bytes.fromhex(row['native_profile_scalar_hex'])[12] == 8:
                from v3_furniture_behaviours import BED_HEAD,BED_FOOT_SIDES,BED_PILLOW_SIDES
                actor=scratch+0x200;actor_data=bytearray(0x740)
                struct.pack_into('>H',actor_data,0,index)
                struct.pack_into('>fff',actor_data,8,100,7,200)
                # One representative per contact category: actual native
                # geometry consumes its imported profile and all rotations.
                for rotation,(cosine,sine) in enumerate(((1,0),(0,1),(-1,0),(0,-1))):
                    struct.pack_into('>H',actor_data,0x124,rotation*0x4000)
                    debug.write_memory(actor,actor_data)
                    call(owner+BED_HEAD-furniture.RAM,[actor],(1,2,3,0)[rotation],furniture_proof)
                    for entry,x in ((BED_FOOT_SIDES,40),(BED_PILLOW_SIDES,0)):
                        debug.write_memory(scratch,b'\xA5'*24)
                        call(owner+entry-furniture.RAM,[scratch,scratch+12,actor,1],1,furniture_proof)
                        expected=[v for z in (-40,40) for v in
                                  (100+x*cosine+z*sine,7,200-x*sine+z*cosine)]
                        actual=struct.unpack('>6f',debug.read_memory(scratch,24))
                        passed=all(abs(a-b)<.02 for a,b in zip(actual,expected))
                        record(dict(furniture_batch_check='native bed sides',item=row['item_id'],
                            rotation=rotation,entry=f'{entry:08X}',expected=expected,observed=actual,
                            assertion='passed' if passed else 'failed'))
                        if not passed: raise ValueError('Native imported bed positioning differs')
                for entry in (BED_FOOT_SIDES,BED_PILLOW_SIDES):
                    call(owner+entry-furniture.RAM,[scratch,scratch+12,actor,0],0,furniture_proof)
                    check('inactive bed has no entry/exit positions',scratch,bytes(24))
                check('native bed helpers preserve complete actor',actor,actor_data)
            if row.get('interaction_flags',0)&0x10:
                from v3_furniture_placement import REGISTER
                # The actual native registration routine must skip collision in
                # an ordinary field, retaining its shop exceptions unchanged.
                call(0x80087E14,[],0)
                if call(0x80087C88)==0x3002: raise ValueError('Furniture fixture is in the broker shop')
                actor=scratch+0x200;expected=bytearray(0x740)
                struct.pack_into('>H',expected,0,index);debug.write_memory(actor,expected)
                call(owner+REGISTER-furniture.RAM,[actor,int(row['profile_ram'],16)],1,furniture_proof)
                struct.pack_into('>i',expected,0xD0,-1)
                check(row['name']+' complete native no-collision registration',actor,expected)
            debug.write_memory(scratch, bytes(0x100))
            call(0x801969C8, [scratch, 16, item], 1)
            check(row['name'] + ' full English name', scratch, row['name'].encode().ljust(16, b' '))
            call(0x800A5630, [item | 3], 10)
            call(0x800C0194, [item | 3], row['price'])
            call(0x800BE69C, [item | 3], row['size_code'])
            for rotation in (range(4) if row['size_code'] else (0,)):
                call(0x800BE72C, [item | rotation, 5, 6, scratch+32], row['size_code'])
                cells = [(1, 5, 6)]
                dx, dz = ((1, 0), (0, -1), (-1, 0), (0, 1))[rotation]
                if row['size_code']>1: raise ValueError('Add four-cell category to shared smoke expectations')
                cells.append((1, 5+dx, 6+dz) if row['size_code'] else (0, 5, 6))
                cells += [(0, 5, 6)] * 2
                check(row['name'] + f' complete footprint rotation {rotation}', scratch+32,
                      b''.join(struct.pack('>iii', *c) for c in cells))
            at = int(row['object_vrom'], 16)-runtime.BLOB
            asset = blob[at:at+row['object_bytes']]
            debug.write_memory(bank, b'\xA5' * bank_size)
            debug.write_memory(index_ram+index, b'\xFF')
            call(bridge, [index, item, bank, 0], 1, (bridge, stub))
            check(row['name'] + ' complete DMA and untouched bank tail', bank,
                  asset+b'\xA5'*(bank_size-len(asset)))
            check(row['name'] + ' bank assignment', index_ram+index, b'\x00')
        loaded, proof = load(catalogue.VROM, catalogue.RELOC, catalogue.RAM, files[catalogue.VROM].size)
        available = owner + report['catalogue']['code']['symbols']['af_v3_catalogue_available'] - catalogue.RAM
        if 'catalogue_preview_records' in report:
            frame=owner+report['catalogue']['code']['symbols']['af_v3_catalogue_frame']-catalogue.RAM
            preview=scratch+0x200; before=b'\xA5'*0x760
            for row in rows:
                expected=bytearray(before);scalar=bytes.fromhex(row['donor_preview_scalar_hex'])
                expected[0xC:0x10]=scalar[4:];expected[0x758:0x75C]=scalar[:4]
                debug.write_memory(preview,before)
                call(frame,[preview,int(row['item_id'],16)|3],proof=proof)
                check(row['name']+' source framing and untouched preview fields',preview,expected)
            row=rows[0];item=int(row['item_id'],16)
            enable=int(row['profile_ram'],16)-4;saved[enable]=debug.read_memory(enable,4)
            debug.write_memory(enable,bytes(4));debug.write_memory(preview,before)
            call(frame,[preview,item],proof=proof);check('disabled preview untouched',preview,before)
            debug.write_memory(enable,saved[enable])
            selector=0x80498000+runtime.slot(item)*32+26;saved[selector]=debug.read_memory(selector,1)
            debug.write_memory(selector,b'\xFF')
            call(frame,[preview,item],proof=proof);check('invalid preview selector untouched',preview,before)
            debug.write_memory(selector,saved[selector])
            call(frame,[preview,0x1000],proof=proof);check('native preview untouched',preview,before)
        # Existing native list membership, acquisition, and ownership functions
        # use temporary state restored below; no FlashRAM write is requested.
        debug.write_memory(0x80135B1C, b'\x18')
        debug.write_memory(0x80135C00, bytes(2))
        debug.write_memory(0x80136FD8, struct.pack('>I', 0x80126EC0))
        debug.write_memory(0x80126ED4, bytes(0x24))
        debug.write_memory(0x8046C000+208, bytes(640))
        ownership = bytearray(128)
        for n, row in enumerate(rows):
            item = int(row['item_id'], 16)
            for group in sorted({0,row['stock_group']}):
                call(0x800C0490, [item, 0, group, 0], int(group == row['stock_group']))
            call(available, [item, 0, row['stock_group'], 0], 1, proof)
            call(available, [item, 1, row['stock_group'], 0], 0, proof)
            call(available, [item, 0, 6, 0], 0, proof)
            if row['stock_group']>=3: call(available,[item,0,0,0],0,proof)
            call(0x800B8B8C, [0x80126EC0, item, 0], 1)
            check(row['name'] + ' acquired full pocket identity', 0x80126ED4+n*2, struct.pack('>H', item))
            bit = runtime.slot(item); ownership[bit//8] |= 1 << (bit & 7)
            check(row['name'] + ' saved catalogue ownership', 0x8046C000+208, ownership)
        check('no faulted CPU thread', 0x8003CE34, bytes(4))
        check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
        check('resident package guard', 0x804A2FF0, bytes.fromhex('AFACC0DE')*4)
        for at in guards: check('private allocation guard', at, edge)
    finally:
        debug.write_memory(bank, bank_before)
        for at, value in saved.items(): debug.write_memory(at, value)
    check('complete save state restored', 0x8046C000, saved[0x8046C000])
    check('native owner descriptor restored', 0x80100DF0, saved[0x80100DF0])
    call(0x8009C040, [allocation])
    return dict(native_furniture_batch_readers=True, complete_native_model_dma=True,
                native_preview_framing='catalogue_preview_records' in report,
                full_catalogue_initialization_tested=False,
                rotated_two_cell_placement=True, native_stock_membership=True,
                native_acquisition_and_ownership=True, ordinary_seating_tested=False,
                native_bed_geometry_tested=any(bytes.fromhex(r['native_profile_scalar_hex'])[12]==8 for r in rows),
                ordinary_bed_gameplay_tested=False,
                gpu_or_hardware_tested=False, flash_written=False, requires_checkpoint_restore=True)
