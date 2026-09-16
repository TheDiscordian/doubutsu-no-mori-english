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
    if section=='equipment_resources':return equipment_resources(debug,rom_path,record)
    if section=='player_motion':return player_motion(debug,rom_path,record)
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
        (0x80136FD8, 4), (0x80135B1C, 1), (0x80135C00, 2), (0x801458B8, 4),
        (0x8003C590,4),(0x80126EB4,4),(0x80137000,15*56))}
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
    tested_beds=set()
    tested_palettes=[]
    def palette_callbacks(row, asset, *, legacy=False):
        """One actual callback-category check, plus its unchanged-asset compatibility path."""
        receipt=report['furniture_palette_fade'];symbols=receipt['code']['symbols']
        at=runtime.PACKAGE+receipt['ram']-runtime.PACKAGE_RAM
        check('complete shared palette code, tables, and layout',receipt['ram'],blob[at:at+receipt['bytes']])
        layout=bytes.fromhex(receipt['legacy_layout_hex']) if legacy else asset[:32]
        _,n,count,on,off,*models=struct.unpack('>IHH6I',layout)
        if n!=len(asset):raise ValueError('Palette test layout differs from complete object')
        actor,gfx,game,arena=(scratch+x for x in (0x120,0x900,0xC00,0xC80))
        actor_data=bytearray(b'\xA5'*0x740);actor_data[0x12C]=0
        debug.write_memory(actor,actor_data);debug.write_memory(game,struct.pack('>I',gfx))
        debug.write_memory(gfx+0x298,struct.pack('>II',arena,arena+0x200))
        debug.write_memory(arena-16,edge);debug.write_memory(arena+0x200,edge)
        def callback(role):
            name='af_v3_palette_fade_dw' if role=='dw' and not legacy else 'af_v3_tent_model_'+role
            entry=symbols[name];jump=struct.pack('>II',0x08000000|(entry>>2&0x3FFFFFF),0)
            debug.write_memory(bridge,jump)
            call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
            call(bridge,[actor,bank] if role in ('ct','dt') else [actor,0,game,bank],proof=(bridge,jump))
        callback('ct');actor_data[0x1A4:0x1A8]=bytes(4)
        check('palette constructor preserves complete actor',actor,actor_data)
        palettes=[]
        for step in (0,1):
            if step:
                debug.write_memory(actor+0x12C,b'\x01');actor_data[0x12C]=1
                callback('mv');actor_data[0x1A4:0x1A8]=struct.pack('>f',.1)
            check('palette movement preserves complete actor',actor,actor_data)
            head,tail=struct.unpack('>II',debug.read_memory(gfx+0x298,8));allocation=(tail-96)&~31
            callback('dw')
            expected=[0xDA380003,allocation,0xDB060020,allocation+64]
            for model in models[:count]:expected.extend((0xDE000000,model))
            check('every palette model in actual draw order',head,struct.pack('>'+str(len(expected))+'I',*expected))
            check('bounded palette arena endpoints',gfx+0x298,struct.pack('>II',head+(count+2)*8,allocation))
            fade=struct.unpack('>f',actor_data[0x1A4:0x1A8])[0]
            ons,offs=struct.unpack_from('>16H',asset,on),struct.unpack_from('>16H',asset,off)
            values=[(a&1)|sum(int((a>>s&31)+fade*((b>>s&31)-(a>>s&31)))<<s for s in (1,6,11))
                    for a,b in zip(offs,ons)]
            palette=struct.pack('>16H',*values);check('all interpolated native colours',allocation+64,palette)
            palettes.append((allocation+64,palette))
        callback('dt');actor_data[0x1A4:0x1A8]=bytes(4)
        check('palette destructor preserves complete actor',actor,actor_data)
        for address,palette in palettes:check('submitted palette survives movement and destruction',address,palette)
        check('palette draw retains complete source asset',bank,asset)
        check('palette arena leading guard',arena-16,edge);check('palette arena trailing guard',arena+0x200,edge)
        tested_palettes.append(row['item_id'])
        debug.write_memory(bridge,stub);call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
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
            # Changed records, not every previously installed chair. Their
            # unchanged code/audio evidence is retained by the build contract.
            audible=[r for r in rows if r.get('action_sound',0)]
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
            contact=bytes.fromhex(row['native_profile_scalar_hex'])[12]
            if contact in (8,16) and contact not in tested_beds:
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
                    # Both native branches are profile-driven: a double bed
                    # has a wider side span and a half-cell pillow offset.
                    foot,pillow,side=(40,0,40) if contact==8 else (20,-20,60)
                    for entry,x in ((BED_FOOT_SIDES,foot),(BED_PILLOW_SIDES,pillow)):
                        debug.write_memory(scratch,b'\xA5'*24)
                        call(owner+entry-furniture.RAM,[scratch,scratch+12,actor,1],1,furniture_proof)
                        expected=[v for z in (-side,side) for v in
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
                tested_beds.add(contact)
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
                if row['size_code']==2:
                    cells=[(1,5,6),(1,6,6),(1,6,7),(1,5,7)]
                else:
                    cells = [(1, 5, 6)]
                    dx, dz = ((1, 0), (0, -1), (-1, 0), (0, 1))[rotation]
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
            if (not tested_palettes and
                    row.get('profile',{}).get('callback_adapter',{}).get('category')=='switch-palette-fade'):
                palette_callbacks(row,asset)
                previous=next(r for r in report['tent_model']['imports'] if r['item_id']=='336C')
                old_index=previous['runtime_index'];address=index_ram+old_index
                saved.setdefault(address,debug.read_memory(address,1));debug.write_memory(address,b'\xFF')
                call(bridge,[old_index,int(previous['item_id'],16),bank,0],1,(bridge,stub))
                at=int(previous['object_vrom'],16)-runtime.BLOB
                old_asset=blob[at:at+previous['object_bytes']]
                check('legacy palette model complete DMA',bank,old_asset)
                palette_callbacks(previous,old_asset,legacy=True)
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
            groups={0} if row.get('reward_route') else {0,row['stock_group']}
            for group in sorted(groups):
                call(0x800C0490, [item, 0, group, 0], int(not row.get('reward_route') and group == row['stock_group']))
            call(available, [item, 0, row['stock_group'], 0], int(row['catalogue_orderable']), proof)
            call(available, [item, 1, row['stock_group'], 0], 0, proof)
            call(available, [item, 0, 6, 0], 0, proof)
            if row['stock_group']>=3: call(available,[item,0,0,0],0,proof)
            call(0x800B8B8C, [0x80126EC0, item, 0], 1)
            check(row['name'] + ' acquired full pocket identity', 0x80126ED4+n*2, struct.pack('>H', item))
            bit = runtime.slot(item); ownership[bit//8] |= 1 << (bit & 7)
            check(row['name'] + ' saved catalogue ownership', 0x8046C000+208, ownership)
        if 'furniture_rewards' in report and any(r.get('reward_route') for r in rows):
            reward=report['furniture_rewards'];entry=reward['entry']
            first,last=reward['reservation_start'],reward['reservation_end']
            offset=runtime.PACKAGE+first-runtime.PACKAGE_RAM
            check('complete shared reward helper and guards',first,blob[offset:offset+last-first])
            # The debugger's direct-call proof is deliberately limited to
            # native low RAM. Reuse the checked low-RAM bridge, as model DMA
            # already does, to execute the actual upper-memory helper.
            reward_stub=struct.pack('>II',0x08000000|((entry>>2)&0x3FFFFFF),0)
            debug.write_memory(bridge,reward_stub)
            call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
            reward_proof=(bridge,reward_stub)
            for route in reward['routes']+reward.get('trade_routes',[]):
                if 'vrom' in route:
                    loaded,_=load(route['vrom'],route['reloc'],route['ram'],route['resident'])
                    for patch in route['patches']:
                        check('native reward call after actual relocation',owner+patch['address']-route['ram'],
                              struct.pack('>I',patch['after']))
                members=[r for r in reward['imports'] if r['route']==route['route']]
                enables=[]
                for member in members:
                    address=runtime.ROWS_RAM+runtime.slot(int(member['item_id'],16))*80+4
                    saved[address]=debug.read_memory(address,4);enables.append(address)
                    debug.write_memory(address,bytes(4))
                # One isolated candidate, then a different sparse candidate:
                # neither can be selected by prefix count or list position.
                for selected in sorted({0,len(members)-1}):
                    debug.write_memory(enables[selected],struct.pack('>I',1))
                    call(bridge,[0,scratch,1,0,0,0,route['encoded']],proof=reward_proof)
                    check('selected-only native reward',scratch,bytes.fromhex(members[selected]['item_id']))
                    debug.write_memory(enables[selected],bytes(4))
                call(bridge,[0,scratch,1,0,0,0,route['encoded']],proof=reward_proof)
                fallback=struct.unpack('>H',debug.read_memory(scratch,2))[0]
                if fallback in {int(r['item_id'],16) for r in members}:
                    raise ValueError('Empty reward profile returned a disabled import')
                groups=(0,1,2) if route['fallback']==8 else (route['fallback'],)
                membership=[call(0x800C0490,[fallback,0,g,0]) for g in groups]
                passed=any(membership)
                record(dict(furniture_batch_check='native fallback stock membership',
                            route=route['route'],item=f'{fallback:04X}',assertion='passed' if passed else 'failed'))
                if not passed:raise ValueError('Optional reward fallback is outside native stock')
                for address in enables:debug.write_memory(address,saved[address])
            check('reward reservation unchanged',first,blob[offset:offset+last-first])
            if report['camper_trade'].get('shared_reward_categories') and any(r.get('reward_route') in (19,23) for r in rows):
                from v3_villager_rewards_smoke import ordinal
                trade=report['camper_trade'];loaded,proof=load(trade['vrom'],trade['relocation_vrom'],trade['ram'],trade['bytes'])
                picker=owner+0x8091ED64-trade['ram'];common=owner+0x8091EFDC-trade['ram']
                state=owner+0x80921DE8-trade['ram']
                private,animal,categories=owner+0x7000,owner+0x7B00,scratch+0x40
                debug.write_memory(animal,bytes.fromhex('E0EA')+bytes(0x526))
                debug.write_memory(categories,struct.pack('>3I',0,3,4))
                debug.write_memory(0x80136FD8,struct.pack('>I',private))
                def wanted(seed,threshold):
                    _,seed=ordinal(seed,1);r,seed=ordinal(seed,100);house,_=ordinal(seed,10)
                    return r>=threshold and house>0
                for route,scene,threshold in ((19,31,90),(23,35,80)):
                    members=[r for r in reward['imports'] if r['route']==route]
                    if not members:continue
                    chosen=members[-1];item=int(chosen['item_id'],16);enables=[]
                    for member in members:
                        address=runtime.ROWS_RAM+runtime.slot(int(member['item_id'],16))*80+4
                        saved.setdefault(address,debug.read_memory(address,4));enables.append(address)
                        debug.write_memory(address,struct.pack('>I',member==chosen))
                    seed=next(s for s in range(10000) if wanted(s,threshold))
                    for disabled in ((False,True) if route==19 else (False,)):
                        if disabled:
                            for address in enables:debug.write_memory(address,bytes(4))
                        data=bytearray(0xA80);struct.pack_into('>H',data,0x14,0x3224)
                        struct.pack_into('>H',data,0xA78,0x34BF);debug.write_memory(private,data)
                        debug.write_memory(state,bytes(0x30));debug.write_memory(0x8003C590,struct.pack('>I',seed))
                        debug.write_memory(0x80126EB4,struct.pack('>I',scene))
                        call(common,[picker,animal,categories,3,1],proof=proof)
                        check('complete camping trade retains input slot',state+12,bytes(4))
                        check('complete camping trade retains full input',state+0x14,bytes.fromhex('3224'))
                        check('complete camping trade retains pitfall mode',state+0x1C,bytes.fromhex('2512'))
                        if not disabled:check('source-category reward through full native trade',state+0x16,struct.pack('>H',item))
                        else:
                            actual=struct.unpack('>H',debug.read_memory(state+0x16,2))[0]
                            if actual in {int(r['item_id'],16) for r in members}:
                                raise ValueError('Unselected winter reward escaped native fallback')
                        other=struct.unpack('>2H',debug.read_memory(state+0x18,4))
                        passed=other[0]>>8==0x26 and other[1]>>8==0x27
                        record(dict(furniture_batch_check='complete seasonal trade categories',route=route,
                                    disabled=disabled,seed=seed,assertion='passed' if passed else 'failed'))
                        if not passed:raise ValueError('Camping trade lost native carpet/wall categories')
                    for address in enables:debug.write_memory(address,saved[address])
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
                native_footprint_sizes=sorted({r['size_code'] for r in rows}), native_stock_membership=True,
                native_acquisition_and_ownership=True, ordinary_seating_tested=False,
                native_optional_rewards_tested='furniture_rewards' in report and any(r.get('reward_route') for r in rows),
                ordinary_npc_gift_handover_tested=False,
                native_shared_camping_trade_tested=bool(report['camper_trade'].get('shared_reward_categories')) and any(r.get('reward_route') in (19,23) for r in rows),
                native_bed_geometry_tested=bool(tested_beds),native_bed_contact_actions=sorted(tested_beds),
                native_palette_callbacks=tested_palettes,
                ordinary_bed_gameplay_tested=False,
                gpu_or_hardware_tested=False, flash_written=False, requires_checkpoint_restore=True)


def equipment_resources(debug,rom_path,record):
    """Exercise source-derived resource categories through the real item DMA."""
    import v3_equipment_runtime as equipment
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed equipment cartridge')
    resources=report['equipment_resources'];files=by_vrom(image);blob=files[runtime.BLOB].extract(image)
    assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(equipment_check=label,address=f'{at:08X}',bytes=len(want),
                    assertion='passed' if passed else 'failed',observed_sha256=sha256(got),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Equipment mismatch: '+label)
        assertions+=1
    def call(at,args=(),want=None):
        nonlocal assertions
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480)
        if want is not None:
            result['assertion']='passed' if result['return_value']==want else 'failed';assertions+=1
        record(result)
        if want is not None and result['return_value']!=want:raise ValueError(f'Equipment call {at:08X} mismatch')
        return result['return_value']
    at=resources['blob_offset']
    check('complete startup-loaded code and resource table',equipment.RAM,blob[at:at+equipment.SIZE])
    saved=debug.read_memory(0x8046C000,864)
    # Largest transfer in each distinct category, plus original native categories.
    selected={}
    for row in resources['records']:
        key=(row['kind'],row['type'])
        if key not in selected or row['bytes']>selected[key]['bytes']:selected[key]=row
    rows=list(selected.values());contract=resources['native_contract']
    original=files[0x00B8B000].extract(image)
    for i in (0,1,2,16):
        origin=contract['bounds'][i]-0x06000000+8;n=contract['sizes'][i]
        rows.append(dict(index=i,pointer=contract['pointers'][i],type=contract['types'][i],bytes=n,
            vrom=0x00B8B000+origin,origin=origin,expected=original[origin:origin+n]))
    size=0x1200;allocation=call(0x8009BFC0,[size]);target=allocation+16
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Equipment scratch allocation outside native heap')
    edge=b'V3HR'*4;end=target+equipment.CAPACITY
    debug.write_memory(allocation,edge);debug.write_memory(end,edge)
    try:
        for row in rows:
            index=row['index'];origin=row.get('origin',0)
            for address,want in ((0x800B12C8,row['pointer']),(0x800B12F4,row['type']),
                    (0x800B131C,row['bytes']),(0x800B1614,origin),(0x800B1650,row['vrom'])):
                call(address,[index],want)
            fill=bytes([0xA5])*equipment.CAPACITY;debug.write_memory(target,fill)
            call(0x800B167C,[target,index])
            expected=row.get('expected')
            if expected is None:expected=blob[row['blob_offset']:row['blob_offset']+row['bytes']]
            check('complete held resource DMA',target,expected+fill[len(expected):])
            call(0x800B16D0,[index,target],target-origin)
            check('resource DMA left guard',allocation,edge);check('resource DMA right guard',end,edge)
        missing=next(i for i in range(equipment.COUNT) if equipment.FIRST+i not in {r['index'] for r in resources['records']})
        for index in (0xFFFFFFFF,equipment.FIRST+equipment.COUNT,equipment.FIRST+missing):
            call(0x800B131C,[index],0);call(0x800B12C8,[index],0)
        check('save/profile unchanged',0x8046C000,saved)
        check('no faulted CPU thread',0x8003CE34,bytes(4))
        check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
        check('resident package guard',0x804A2FF0,bytes.fromhex('AFACC0DE')*4)
        check('equipment module guard',equipment.RAM+equipment.SIZE-16,struct.pack('>4I',*([equipment.GUARD]*4)))
    finally:call(0x8009C040,[allocation])
    return dict(native_equipment_resources=True,representative_transfers=len(rows),assertions=assertions,
        imported_categories=len(selected),ordinary_menu_reload_tested=False,player_actions_tested=False,
        hardware_tested=False,flash_written=False,requires_checkpoint_restore=True)


def sound_programs_probe(debug,image,resources,check,call,record):
    """Exercise one representative of the shared single-layer sound format."""
    from aflib import CODE_VROM,u32
    from v3_sound_programs import installed_resource
    sound=resources['sound_programs'];row=sound['imports'][0]
    code=by_vrom(image)[CODE_VROM].extract(image)
    def word(at):return u32(debug.read_memory(at,4),0)
    def bounded(at,n):
        if at&3 or not 0x80000400<=at<=0x80400000-n:
            raise ValueError('Shared sound pointer escapes native RAM')
        return at
    seq=sound['sequence'];data=image[seq['physical']:seq['physical']+seq['bytes']]
    header=bytearray.fromhex(seq['header_after']);struct.pack_into('>I',header,0,seq['physical'])
    check('shared sound loaded header',seq['header_address'],header)
    sequence=bounded(word(0x8014CBA8),seq['bytes'])
    check('shared sound complete program and envelope',sequence+row['offset'],
          data[row['offset']:row['offset']+row['bytes']])
    table=struct.unpack_from('>H',data,0x18A)[0];sid=row['native_sound_id']
    check('shared sound registered dispatch',sequence+table+(sid&255)*2,struct.pack('>H',row['offset']))
    start,current,size,count=struct.unpack('>4I',debug.read_memory(0x8014C260,16))
    bounded(start,size)
    if size!=sound['after_budget']['capacity'] or not start<=current<=start+size or not count:
        raise ValueError('Shared sound permanent allocation exceeds its checked heap')
    record(dict(shared_sound_heap_capacity=size,used=current-start,remaining=start+size-current,
        conservative_spare=sound['after_budget']['conservative_spare'],assertion='passed'))
    bank,entry,_=installed_resource(image,code,'bank',row['native_bank'])
    _,_,wave=installed_resource(image,code,'wave',entry[10])
    instrument=u32(bank,8+row['native_instrument']*4)
    sample=u32(bank,instrument+16);sample_bytes=u32(bank,sample)&0xFFFFFF
    sample_start=wave+u32(bank,sample+4)
    if sample_bytes!=row['instrument_identity']['samples'][1]['sample_bytes']:
        raise ValueError('Shared sound representative needs its checked middle sample')
    call(0x800F8D5C,[sid])
    slots=debug.read_memory(0x80113C34,6*32)
    matches=[i for i in range(6) if struct.unpack_from('>H',slots,i*32)[0]==sid]
    if len(matches)!=1:raise ValueError('Shared sound did not allocate its native trigger slot')
    check('shared sound original priority',0x80113C34+matches[0]*32+28,bytes((row['trigger_priority'],)))
    observations=0
    for frame in range(8):
        record(debug.advance_game_frame())
        count=word(0x8014BB20)
        if not 0<count<=256:raise ValueError('Unbounded sound sample-DMA list')
        entries=debug.read_memory(bounded(word(0x8014BB1C),count*16),count*16)
        for i in range(count):
            r=entries[i*16:(i+1)*16];ram,device=struct.unpack_from('>2I',r)
            n=struct.unpack_from('>H',r,10)[0]
            first,last=max(device,sample_start),min(device+n,sample_start+sample_bytes)
            if first>=last or not r[14]:continue
            got=debug.read_memory(bounded(ram,n)+first-device,last-first)
            if got==image[first:last]:
                observations+=1
                record(dict(shared_sound_sample_dma=True,frame=frame+1,slot=i,
                    first=first-sample_start,last=last-sample_start,sha256=sha256(got),assertion='passed'))
    if not observations:raise ValueError('No complete sample transfer observed for shared sound')
    check('shared sound retains program after playback',sequence+row['offset'],
          data[row['offset']:row['offset']+row['bytes']])
    return dict(sound_id=sid,native_loader_trigger_and_sample_dma=True,observations=observations,
                physical_audio_played=False,pcm_or_listening_verified=False)


def player_motion(debug,rom_path,record):
    """Load the actual player owner and exercise its shared animation category."""
    import v3_equipment_runtime as equipment
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed player-motion cartridge')
    resources=report['equipment_resources'];motion=resources['player_motion']
    files=by_vrom(image);blob=files[runtime.BLOB].extract(image);boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        got=debug.read_memory(at,len(want));passed=got==want
        record(dict(player_motion_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',observed_sha256=sha256(got),expected_sha256=sha256(want)))
        if not passed:raise ValueError('Player motion mismatch: '+label)
        assertions+=1
    def call(at,args=(),want=None,proof=None):
        nonlocal assertions
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        if want is not None:
            result['assertion']='passed' if result['return_value']==want else 'failed';assertions+=1
        record(result)
        if want is not None and result['return_value']!=want:raise ValueError(f'Player motion call {at:08X} mismatch')
        return result['return_value']
    at=resources['blob_offset'];check('complete extended resident module',equipment.RAM,blob[at:at+resources['bytes']])
    saved=debug.read_memory(0x8046C000,864)
    constructor=struct.unpack('>I',debug.read_memory(0x80143900,4))[0]
    owner=constructor-(0x808DD748-equipment.PLAYER_RAM)
    data=files[equipment.PLAYER_VROM].extract(image);reloc=files[equipment.PLAYER_RELOC].extract(image)
    if owner&15 or not MODULE_RAM+0x8000<=owner<=0x80400000-len(data):
        raise ValueError('Native player constructor does not identify a loaded owner')
    controls=resources.get('player_actions',{}).get('fan_control_flow')
    size=0x6100 if controls else 0x1100
    allocation=call(0x8009BFC0,[size]);target=allocation+16
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Player-motion allocation outside native heap')
    sections=struct.unpack_from('>5I',reloc)
    spec=SimpleNamespace(ram=equipment.PLAYER_RAM,resident_bytes=len(data),sections=sections)
    expected=relocate_verified_data(spec,data,reloc,owner)
    edge=b'V3PM'*4;end=target+(0x12D8 if controls else equipment.PLAYER_CAPACITY)
    for address in (allocation,target-16,end,allocation+size-16):debug.write_memory(address,edge)
    try:
        check('actual game-loaded player code and relocations',owner,expected[:sections[0]])
        record(dict(game_loaded_player_owner=f'{owner:08X}',constructor=f'{constructor:08X}'))
        actions=resources.get('player_actions')
        if controls:
            # Exercise new control/setup code in this same category probe.
            # The fake game owns an isolated full-size actor, two native-sized
            # animation banks, and a player pointer. No live actor is edited.
            game=allocation+0x2000;upper=allocation+0x4000;lower=allocation+0x5000
            game_data=bytearray(0x1E00)
            struct.pack_into('>I',game_data,0x1C90,target)
            for index,bank in enumerate((upper,lower)):
                struct.pack_into('>I',game_data,0x114+84*index,bank)
                debug.write_memory(bank,bytes([0xA5])*equipment.PLAYER_CAPACITY)
                debug.write_memory(bank-16,edge);debug.write_memory(bank+equipment.PLAYER_CAPACITY,edge)
            debug.write_memory(game,game_data)
            actor=bytearray(0x12D8)
            struct.pack_into('>I',actor,0xCF0,7)
            struct.pack_into('>2h',actor,0xDA0,0,1)
            for field in (0xDAC,0xDB0,0xDB4):struct.pack_into('>i',actor,field,-1)
            # Suppress held equipment through the real native override flag;
            # fan inventory selection is deliberately not installed yet.
            actor[0xE64]=1
            debug.write_memory(target,actor)
            symbols=actions['code']['symbols'];bridge=allocation+0x1400
            debug.write_memory(bridge-16,edge);debug.write_memory(bridge+8,edge)
            def control_call(name,args,want=None):
                # The existing debugger's verified-call range is low RAM.
                # Its ordinary eight-byte jump bridge reaches the independently
                # compared cartridge-loaded Expansion Pak code above.
                stub=struct.pack('>2I',equipment.jump(symbols[name]),0)
                debug.write_memory(bridge,stub)
                call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
                return call(bridge,args,want,(bridge,stub))
            for trigger in (0,1):control_call('af_v3_player_fan_controller',[game,trigger],0)
            check('missing or hidden fan does not change actor',target,actor)
            control_call('af_v3_player_fan_request',[game,1,4],1)
            check('fan request fields',target+0xD00,struct.pack('>3I',109,4,1))
            check('fan request union',target+0xD58,struct.pack('>2I',1,0))
            rejected=debug.read_memory(target,len(actor))
            control_call('af_v3_player_fan_request',[game,0,4],0)
            check('equal-priority request leaves actor unchanged',target,rejected)
            segment=debug.read_memory(0x801458B8,4)
            control_call('af_v3_player_fan_setup',[target,game])
            check('fan setup and prior action',target+0xCF0,struct.pack('>2I',109,7))
            check('fan eye pattern',target+0xCE8,struct.pack('>I',5))
            check('full upper animation frame control',target+0x174,
                  struct.pack('>5fI',1,9,9,controls['frame_speed'],1,1))
            check('fan upper morph',target+0x194,struct.pack('>f',-5))
            check('fan explicit part mask',target+0x10FC,bytes.fromhex(motion['mask_hex']))
            swing=next(r for r in motion['records'] if r['index']==270)
            check('complete swing DMA inside private bank',upper,
                blob[swing['blob_offset']:swing['blob_offset']+swing['bytes']]+bytes([0xA5])*(equipment.PLAYER_CAPACITY-swing['bytes']))
            check('native segment-six binding restored',0x801458B8,segment)
            debug.write_memory(target+0xD58,bytes(4));debug.write_memory(target+0x1F4,struct.pack('>f',12.5))
            control_call('af_v3_player_fan_setup',[target,game])
            check('repeat preserves lower frame',target+0x1F4,struct.pack('>f',12.5))
            check('repeat removes upper morph',target+0x194,bytes(4))
            check('repeat removes lower morph',target+0x204,bytes(4))
            debug.write_memory(target+0x184,struct.pack('>f',7.5))
            control_call('af_v3_player_fan_finish',[target,game])
            check('fan bee response timing',target+0x11B7,b'\x01')
            # Title-demo movement remains live even though this isolated actor
            # is not in the scene. Match the real controller, not assumed idle.
            if call(0x8007D90C):controller=call(0x800B593C)
            else:controller=struct.unpack('>I',debug.read_memory(0x8010EF90,4))[0]+0xA8
            axes=struct.unpack('>2f',debug.read_memory(controller,8));moving=any(axes)
            record(dict(fan_transition_controller_axes=list(axes),expected_action=8 if moving else 7))
            debug.write_memory(target+0x184,struct.pack('>f',8.5))
            control_call('af_v3_player_fan_finish',[target,game])
            check('released fan respects movement and request priority',target+0xD00,struct.pack('>3I',8 if moving else 7,1,1))
            if moving:check('native walk argument adaptation',target+0xD64,struct.pack('>fI',-5,0))
            else:check('native wait argument adaptation',target+0xD58,struct.pack('>fI',-5,2))
            sound_result=None;frame_result=None
            if actions.get('fan_frame_flow'):
                sound_result=sound_programs_probe(debug,image,resources,check,call,record)
                check('player owner retained across audio frames',0x80143900,struct.pack('>I',constructor))
                real_game=struct.unpack('>I',debug.read_memory(0x8010EF90,4))[0]
                if real_game&3 or not 0x80000400<=real_game<=0x80400000-0x1E00:
                    raise ValueError('Per-frame probe requires the live play-game owner')
                real_actor=struct.unpack('>I',debug.read_memory(real_game+0x1C90,4))[0]
                if real_actor&3 or not 0x80000400<=real_actor<=0x80400000-0x12D8:
                    raise ValueError('Per-frame probe requires the actual initialized player')
                # Collision and skeleton updates require a real actor. The
                # enclosing checkpoint isolates this call; restore its actor
                # and both animation banks before returning to ordinary play.
                actor_before=debug.read_memory(real_actor,0x12D8);banks={}
                for index in struct.unpack_from('>2h',actor_before,0xDA0):
                    if not 0<=index<8:raise ValueError('Unbounded live animation-bank selector')
                    address=struct.unpack('>I',debug.read_memory(real_game+0x114+84*index,4))[0]
                    if address&15 or not 0x80000400<=address<=0x80400000-equipment.PLAYER_CAPACITY:
                        raise ValueError('Live animation bank escapes native RAM')
                    banks[address]=debug.read_memory(address,equipment.PLAYER_CAPACITY)
                try:
                    debug.write_memory(real_actor+0xE64,b'\x01')
                    debug.write_memory(real_actor+0xD00,struct.pack('>3I',109,4,1))
                    debug.write_memory(real_actor+0xD58,struct.pack('>I',1))
                    control_call('af_v3_player_fan_setup',[real_actor,real_game])
                    control_call('af_v3_player_fan_main',[real_actor,real_game])
                    check('per-frame native animation advancement',real_actor+0x184,struct.pack('>f',2))
                    check('per-frame native morph advancement',real_actor+0x194,struct.pack('>f',-4))
                    check('per-frame action remains fan',real_actor+0xCF0,struct.pack('>I',109))
                    check('per-frame callback has no CPU fault',0x8003CE34,bytes(4))
                    frame_result=dict(native_main_called=True,live_collision_and_skeleton=True,
                        action_table_dispatched=False,ordinary_equipped_fan_tested=False)
                finally:
                    for address,value in banks.items():debug.write_memory(address,value)
                    debug.write_memory(real_actor,actor_before)
                check('live player restored after per-frame check',real_actor,actor_before)
                for address,value in banks.items():check('live animation bank restored',address,value)
            for bank in (upper,lower):
                for address in (bank-16,bank+equipment.PLAYER_CAPACITY):check('private animation bank guard',address,edge)
            for address in (bridge-16,bridge+8):check('private call bridge guard',address,edge)
            for address in (allocation,target-16,end,allocation+size-16):check('private actor/game guard',address,edge)
            check('saved profile unchanged',0x8046C000,saved)
            check('no CPU fault',0x8003CE34,bytes(4))
            check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
            check('equipment guard',equipment.RAM+equipment.SIZE-16,struct.pack('>4I',*([equipment.GUARD]*4)))
            check('extended module footer',equipment.RAM+resources['bytes']-16,struct.pack('>4I',*([equipment.GUARD]*4)))
            return dict(native_fan_controls_setup_transitions=True,assertions=assertions,
                shared_sound=sound_result,per_frame_callback=frame_result,
                positive_equipped_controller_tested=False,fan_action_dispatched=False,
                ordinary_gameplay_tested=False,hardware_tested=False,flash_written=False,
                requires_checkpoint_restore=True)
        if actions:
            # Reuse this loaded-owner probe for the shared action-table category.
            # No live player, save, or callback table is edited.
            def owner_call(entry,args=(),want=None):
                finish=next((t['native_end'] for t in actions['tables'] if t['native_entry']==entry),None)
                if finish is None:raise ValueError('Action probe needs a complete consumer binding')
                address=owner+entry-equipment.PLAYER_RAM
                return call(address,args,want,(address,expected[entry-equipment.PLAYER_RAM:finish-equipment.PLAYER_RAM]))
            for entry,missing in ((0x808B35C8,-1),(0x808B63B4,0),(0x808B87C8,0)):
                table=next(t for t in actions['tables'] if t['native_entry']==entry)
                values=blob[at+table['offset']:at+table['offset']+table['bytes']]
                for index in (7,104,105,109,120,121,0xFFFFFFFF):
                    value=values[index] if index<121 else missing
                    if value>=128:value-=256
                    owner_call(entry,[index],value&0xFFFFFFFF)
            for index in (105,109,120,121,0xFFFFFFFF):
                actor=bytearray(equipment.PLAYER_CAPACITY)
                struct.pack_into('>I',actor,0xD00,index);struct.pack_into('>I',actor,0xD08,1)
                debug.write_memory(target,actor)
                owner_call(0x808DDA18,[target,0],0)
                check('unfinished action cannot start or change its actor',target,actor)
            # Compare one real original net dispatch with the same native
            # callback called directly. Its scratch actor uses no live state.
            actor=bytearray(equipment.PLAYER_CAPACITY);struct.pack_into('>I',actor,0xCF0,7)
            debug.write_memory(target,actor)
            linked=struct.unpack_from('>I',data,0x808DF628-equipment.PLAYER_RAM+7*4)[0]
            if linked!=0x808BE140:raise ValueError('Changed representative native action callback')
            callback=owner+linked-equipment.PLAYER_RAM
            call(callback,[target],proof=(callback,expected[callback-owner:callback-owner+68]))
            direct=debug.read_memory(target,len(actor));debug.write_memory(target,actor)
            owner_call(0x808BE620,[target]);check('original callback through relocated shared dispatch',target,direct)
            # Exercise both call-register variants with a native linked target
            # and a resident imported target. Only these 16-byte call bridges
            # are uploaded; all getters and dispatch code come from the ROM.
            bridge=allocation+0x1000
            priority=next(t for t in actions['tables'] if t['native_entry']==0x808B35C8)
            native_want=blob[at+priority['offset']+7]
            extra_want=next(r for r in resources['kind_readers']['rows'] if r['native_kind']==44)['fields'][0]
            for register,name in ((2,'af_v3_player_action_v0'),(25,'af_v3_player_action_t9')):
                for dest,args,want in ((0x808B35C8,[7],native_want),
                        (resources['code']['symbols']['af_v3_equipment_kind_field'],[44,0],extra_want)):
                    stub=struct.pack('>4I',0x3C000000|register<<16|dest>>16,
                        0x34000000|register<<21|register<<16|dest&65535,
                        equipment.jump(actions['code']['symbols'][name]),0)
                    debug.write_memory(bridge,stub)
                    call(0x8002FE00,[bridge,len(stub)]);call(0x80034CE0,[bridge,len(stub)])
                    call(bridge,args,want&0xFFFFFFFF,(bridge,stub))
            check('extended module footer',equipment.RAM+resources['bytes']-16,struct.pack('>4I',*([equipment.GUARD]*4)))
        pointer=owner+0x808B468C-equipment.PLAYER_RAM;part=owner+0x808B5B38-equipment.PLAYER_RAM
        pointer_proof=(pointer,expected[pointer-owner:pointer-owner+56])
        part_proof=(part,expected[part-owner:part-owner+40])
        kinds=resources.get('kind_readers')
        if kinds:
            kind_rows={r['native_kind']:r for r in kinds['rows']}
            for hook in kinds['owner_hooks']:
                address=owner+hook['entry']-equipment.PLAYER_RAM
                proof=(address,expected[address-owner:address-owner+40])
                # Shared reader categories, original tools, and both invalid bounds.
                for kind in (0,1,35,44,99,107,0xFFFFFFFF,115):
                    if kind<36:
                        value=bytes.fromhex(hook['table_hex'])[kind]
                        if hook['field']!='player_animation' and value>=128:value-=256
                    elif kind in kind_rows:value=kind_rows[kind]['fields'][hook['column']]
                    else:value=hook['missing']
                    call(address,[kind],value&0xFFFFFFFF,proof)
        # New transition motions when present; otherwise representative holding,
        # toy, idle, and waving resources. Preserve prior unchanged DMA evidence.
        selected={}
        for row in kinds['new_player_motions'] if kinds else motion['records']:
            key=(bool(row['source']['keyed_channels']),row['type'],row['source']['duration'])
            selected.setdefault(key,row)
        rows=list(selected.values());native=files[0x00B36000].extract(image)
        for index in (0,129):
            origin=motion['bounds'][index]-0x06000000+8;n=motion['bounds'][index+1]-motion['bounds'][index]-8
            rows.append(dict(index=index,origin=origin,bytes=n,vrom=0x00B36000+origin,
                pointer=struct.unpack_from('>I',data,0x808DE268-equipment.PLAYER_RAM+4*index)[0],
                type=data[0x808DE4C4-equipment.PLAYER_RAM+index],expected=native[origin:origin+n]))
        for row in rows:
            index=row['index'];origin=row.get('origin',0)
            call(pointer,[index],row['pointer'],pointer_proof);call(part,[index],row['type'],part_proof)
            for address,want in ((0x800B11B0,row['bytes']),(0x800B1264,origin),(0x800B1D68,row['vrom'])):
                call(address,[index],want)
            fill=bytes([0xA5])*equipment.PLAYER_CAPACITY;debug.write_memory(target,fill)
            call(0x800B1D94,[target,index])
            wanted=row.get('expected')
            if wanted is None:wanted=blob[row['blob_offset']:row['blob_offset']+row['bytes']]
            check('complete player animation DMA and untouched tail',target,wanted+fill[len(wanted):])
            call(0x800B12A0,[index,target],target-origin)
        masks=files[0x00B8A000].extract(image)
        for index in range(5):
            debug.write_memory(target,bytes([0xA5])*32);call(0x800B1DE8,[target,index])
            mask=masks[index*28:index*28+27] if index<4 else bytes.fromhex(motion['mask_hex'])
            check('native or donor split-body mask',target,mask+bytes([0xA5])*5)
        for index in (0xFFFFFFFF,130,287):
            call(pointer,[index],0,pointer_proof);call(part,[index],0xFFFFFFFF,part_proof);call(0x800B11B0,[index],0)
        for row in (resources['records'][0],):
            call(0x800B12C8,[row['index']],row['pointer']);call(0x800B131C,[row['index']],row['bytes'])
        call(0x800B12C8,[0],resources['native_contract']['pointers'][0])
        for address in (allocation,target-16,end,allocation+size-16):check('private owner or animation guard',address,edge)
        check('saved profile unchanged',0x8046C000,saved)
        check('no CPU fault',0x8003CE34,bytes(4));check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
        check('equipment guard',equipment.RAM+equipment.SIZE-16,struct.pack('>4I',*([equipment.GUARD]*4)))
    finally:call(0x8009C040,[allocation])
    return dict(native_player_motion_resources=True,representative_transfers=len(rows),part_masks=5,
        assertions=assertions,player_actions_tested=False,ordinary_menu_reload_tested=False,
        kind_readers_tested=bool(resources.get('kind_readers')),
        extended_action_tables_tested=bool(resources.get('player_actions')),
        hardware_tested=False,flash_written=False,requires_checkpoint_restore=True)
