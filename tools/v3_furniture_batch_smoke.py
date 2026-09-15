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
