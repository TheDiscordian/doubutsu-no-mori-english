"""Current native tent construction, complete DMA/draw, and real pool cleanup."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM
from v3_asset_loader import BLOB, BLOB_RAM
from v3_npc_draw_smoke import boot_proofs
import v3_campsite_exterior as runtime


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_bytes())
    if sha256(rom) != report['output_sha256'] or report['runtime_abi'] != 72:
        raise ValueError('Exterior probe requires the current ABI 72 cartridge')
    files, boot = by_vrom(rom), boot_proofs(rom)
    blob, code = files[BLOB].extract(rom), files[CODE_VROM].extract(rom)
    symbols = report['campsite_exterior']['code']['symbols']

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'tent_check':label, 'address':f'{address:08X}', 'bytes':len(expected),
            'assertion':'passed' if actual == expected else 'failed',
            'expected_sha256':sha256(expected), 'observed_sha256':sha256(actual)})
        if actual != expected:
            raise ValueError('Native exterior mismatch: ' + label)

    def call(address, args, expected=None, proof=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM+0x6480,
                            verified_code=proof or boot.get(address))
        if expected is not None:
            result['assertion'] = 'passed' if result['return_value'] == expected else 'failed'
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Unexpected native exterior return value')
        return result['return_value']

    def word(address):
        return struct.unpack('>I',debug.read_memory(address,4))[0]

    def bounded(address, size):
        if address & 15 or not MODULE_RAM+0x8000 <= address <= 0x80400000-size:
            record({'tent_allocation_rejected':f'{address:08X}', 'bytes':size, 'assertion':'failed'})
            raise ValueError(f'Exterior fixture allocation {address:08X} / {size} outside native heap')
        return address

    package = blob[runtime.PACKAGE:runtime.PACKAGE+runtime.PACKAGE_SIZE]
    check('complete resident package',runtime.PACKAGE_RAM,package)
    saved = {at:debug.read_memory(at,size) for at,size in (
        (0x8013A248,4),(0x80126EB4,4),(0x80136F38,4),(0x80136FB8,4),
        (0x80100C90+0x45*32+16,4),(0x8046C000,864))}
    size = 0x21000
    allocation = bounded(call(0x8009BFC0,[size]),size)
    owner, game, gfx = allocation+16, allocation+0x19000, allocation+0x1C000
    opa, shadow, bridge = allocation+0x1D000, allocation+0x1E000, allocation+0x20F00
    edge = b'V3TE'*4
    for address in (allocation,game-16,gfx-16,opa-16,shadow-16,bridge-16,bridge+8,allocation+size-16):
        debug.write_memory(address,edge)
    source, reloc = files[runtime.STRUCTURE].extract(rom), files[runtime.RELOC].extract(rom)
    sections = struct.unpack_from('>5I',reloc)
    spec = SimpleNamespace(ram=runtime.STRUCTURE_RAM, resident_bytes=len(source)+sections[3],sections=sections)
    if owner+spec.resident_bytes+len(reloc) >= game-16:
        raise ValueError('Complete Structure owner exceeds fixture reservation')
    # Native 8-byte setup-table bias (809E987C - 5800*8), and the unrolled
    # overlay-pointer loop's terminal value. Neither is dereferenced directly.
    expected_owner = relocate_verified_data(spec,source,reloc,owner,
        address_constants=(runtime.STRUCTURE_RAM+spec.resident_bytes,0x809BD87C,0x80A03528))
    call(0x800262D0,[runtime.STRUCTURE,runtime.STRUCTURE+len(source),runtime.STRUCTURE_RAM,
        runtime.STRUCTURE_RAM+spec.resident_bytes,owner,owner+spec.resident_bytes,len(reloc)])
    check('complete relocated Structure owner and BSS',owner,expected_owner)
    owner_proof = (owner,expected_owner[:sections[0]])

    def resident(name, args, expected=None):
        target = symbols[name]
        stub = struct.pack('>II',0x08000000 | ((target>>2)&0x3FFFFFF),0)
        debug.write_memory(bridge,stub)
        call(0x8002FE00,[bridge,8]); call(0x80034CE0,[bridge,8])
        return call(bridge,args,expected,(bridge,stub))

    resident('af_v3_campsite_actor_descriptor',[0x45],0x80100C90+0x45*32)
    resident('af_v3_campsite_actor_descriptor',[0xCA],runtime.PACKET+0x20)
    debug.write_memory(game,bytes(0x2410)); debug.write_memory(gfx,bytes(0x400))
    debug.write_memory(game,struct.pack('>I',gfx))
    # A private ready keep-bank row; no title actor lists or live game state.
    debug.write_memory(game+0x110,struct.pack('>H',3))
    debug.write_memory(game+0x114,struct.pack('>I',allocation+0x20000))
    debug.write_memory(game+0xE4,bytes((0,0)))
    debug.write_memory(0x80136F38,bytes(4))
    debug.write_memory(0x80100C90+0x45*32+16,struct.pack('>I',owner))
    call(owner+0x809E93C8-runtime.STRUCTURE_RAM,[game],proof=owner_proof)
    clip = bounded(word(0x80136F38),0xC14)
    check('actual installed Structure setup callback',clip,struct.pack('>I',symbols['af_v3_campsite_structure_setup']))
    actor = word(clip+0x14)
    if not owner <= actor <= owner+spec.resident_bytes-9*0x2D8:
        raise ValueError('Actual native structure pool outside complete owner')
    check('all nine actor pool slots unused',clip+0x38,bytes(36))
    debug.write_memory(0x80126EB4,struct.pack('>I',35))
    field = bounded(call(0x800867F0,[35,0xA000,1]),0x168)
    debug.write_memory(0x8013A248,struct.pack('>I',field))
    block = bounded(word(field+0x148),0x614)
    fg = bounded(word(block+0x584),512)
    background = bounded(word(field+0x38),0xA000)
    # Clear only the private entrance tile: constructor recovery has its own
    # sanitised full-ID/buried-item coverage, without editing a live inventory.
    debug.write_memory(fg+2*(5*16+3),bytes(2))
    debug.write_memory(0x80136FB8,struct.pack('>I',64800))
    pos = struct.unpack('>I',struct.pack('>f',140.0))[0]
    resident('af_v3_campsite_structure_setup',[game,0x5849,pos,pos,7],actor)
    check('native actor class and foreground',actor,bytes.fromhex('00ca000000005849'))
    check('native exact fixed pool allocation',clip+0x38,struct.pack('>I',1)+bytes(32))
    check('neighbour actor intact',actor+0x2D8,bytes(0x2D8))
    check('native installed owner pointer',actor+0x170,struct.pack('>I',runtime.PACKET+0x20))
    check('native installed movement/draw callbacks',actor+0x164,struct.pack('>II',
        symbols['af_v3_campsite_exterior_init'],symbols['af_v3_campsite_exterior_dw']))
    assets = bounded(word(actor+0x2B8),0x1E60)
    exterior = blob[0x0248A000-BLOB:0x0248A000-BLOB+6960]
    shadow_art = blob[0x0248C000-BLOB:0x0248C000-BLOB+800]
    check('actual full exterior and shadow DMA plus allocation guard',assets,exterior+shadow_art+b'\xCD'*16)
    check('night window fade',actor+0x2C8,struct.pack('>f',1))
    check('foreground actor handoff',fg+2*(3*16+3),bytes.fromhex('ffff'))
    # Execute the real initial movement with no player in the private actor list.
    resident('af_v3_campsite_exterior_init',[actor,game])
    check('additive temporary tent foreground',fg+2*(3*16+3),bytes.fromhex('f127'))
    check('initial callback becomes ordinary movement',actor+0x164,
        struct.pack('>I',symbols['af_v3_campsite_exterior_mv']))
    debug.write_memory(opa,b'\xA5'*2048); debug.write_memory(shadow,b'\xA5'*256)
    debug.write_memory(gfx+0x298,struct.pack('>II',opa,opa+2048))
    debug.write_memory(gfx+0x2C8,struct.pack('>II',shadow,shadow+256))
    debug.write_memory(game+0x1C3A,bytes((11,22,33)))
    debug.write_memory(game+0x1C50,struct.pack('>f',-0.25)+bytes((44,)))
    resident('af_v3_campsite_exterior_dw',[actor,game])
    frame = opa+2048-528
    check('complete opaque command count and frame reservation',gfx+0x298,struct.pack('>II',opa+40,frame))
    check('complete shadow command count and unchanged tail',gfx+0x2C8,struct.pack('>II',shadow+56,shadow+256))
    check('opaque segment bindings and model',opa+8,struct.pack('>8I',0xDA380003,frame,
        0xDB060018,assets,0xDB060020,frame+64,0xDE000000,0x060017D0))
    check('window frame commands',frame+64,bytes.fromhex('fa0000ffffff96ffdf00000000000000'))
    projected = bytearray(shadow_art[0x80:0x240])
    for i, flag in enumerate(shadow_art[0x240:0x25C]):
        if flag:
            x = struct.unpack_from('>h',projected,i*16)[0]
            struct.pack_into('>H',projected,i*16,(x-15)&65535)
    check('all native projected shadow vertices',frame+80,projected)
    check('complete shadow state and model',shadow+8,struct.pack('>12I',0xE7000000,0,
        0xDA380003,frame,0xDB060018,assets+0x1B30,0xDB060020,frame+80,
        0xFA00002C,0x0B16212C,0xDE000000,0x06000260))
    # Native destruction restores the real foreground, runs the destructor,
    # returns the exact actor slot, and drops the keep-bank reference.
    call(0x8005832C,[game+0x1C78,actor,game],0,
         (0x8005832C,code[0x8005832C-CODE_RAM:0x80058428-CODE_RAM]))
    check('native actor pool fully released',clip+0x38,bytes(36))
    check('asset ownership released',actor+0x2B8,bytes(4))
    check('native actor list empty',game+0x1C78,bytes(0x44))
    check('real foreground restored by native destruction',fg+2*(3*16+3),bytes.fromhex('5849'))
    check('entrance reservation released',fg+2*(5*16+3),bytes(2))
    check('keep-bank reference released',game+0x160,bytes(2))
    call(owner+0x809E96E8-runtime.STRUCTURE_RAM,[],proof=owner_proof)
    check('native structure clip released',0x80136F38,bytes(4))
    # Native resident actors increment an unused load count without decrementing
    # it (the same path as existing resident actors). Restore checkpoint-owned data.
    debug.write_memory(runtime.PACKET+0x3E,bytes(1))
    for at,data in saved.items(): debug.write_memory(at,data)
    for address in (allocation,game-16,gfx-16,opa-16,shadow-16,bridge-16,bridge+8,allocation+size-16):
        check('private fixture guard',address,edge)
    check('resident prefix retained',BLOB_RAM,blob[:0xC000])
    check('complete resident package retained',runtime.PACKAGE_RAM,package)
    check('save runtime retained',0x8046C000,saved[0x8046C000])
    check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread',0x8003CE34,bytes(4))
    for owned in (fg,background,block,field,allocation): call(0x8009C040,[owned])
    return {'actual_structure_registration':True,'native_tent_actor_construction':True,
        'actual_complete_exterior_dma':True,'native_draw_commands':True,'native_pool_cleanup':True,
        'natural_event_entry_or_persistence_tested':False,'gpu_or_hardware_tested':False,
        'requires_checkpoint_restore':True}
