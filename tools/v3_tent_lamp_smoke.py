"""Current lamp lifecycle through the complete native Effect_Control owner."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace
from aflib import by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, TEST_STACK
from v3_npc_draw_smoke import boot_proofs
import v3_tent_lamp as runtime


def exercise(debug, rom_path, record):
    path=Path(rom_path);rom=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(rom)!=report['output_sha256'] or report['runtime_abi']!=83:
        raise ValueError('Lamp probe requires the current ABI 83 cartridge')
    files=by_vrom(rom);blob=files[runtime.BLOB].extract(rom)
    symbols=report['tent_lamp']['code']['symbols'];boot=boot_proofs(rom)
    def check(label,at,expected):
        actual=debug.read_memory(at,len(expected));passed=actual==expected
        record(dict(tent_lamp_check=label,address=f'{at:08X}',bytes=len(expected),
            assertion='passed' if passed else 'failed',expected_sha256=sha256(expected),observed_sha256=sha256(actual)))
        if not passed:raise ValueError('Native lamp mismatch: '+label)
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,
                          verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    def word(at):return struct.unpack('>I',debug.read_memory(at,4))[0]
    def bounded(at,n):
        if at&15 or not MODULE_RAM+0x8000<=at<=0x80400000-n:
            raise ValueError(f'Lamp fixture allocation outside native heap: {at:08X}/{n}')
        return at
    source,n,crc,ram=struct.unpack_from('>4I',blob,0xE0)
    extra=blob[source-runtime.BLOB:source-runtime.BLOB+n]
    check('cold boot complete save code, lamp code, zero state, and guards',ram,extra)
    saved={at:debug.read_memory(at,n) for at,n in ((0x80126EA0,65536),(0x80136EA0,0x900),
        (0x801010C0,4),(0x8010EF90,4))}
    size=0x15000;allocation=bounded(call(0x8009BFC0,[size]),size)
    owner,game,actor,player=allocation+16,allocation+0x6000,allocation+0x9100,allocation+0x9400
    gfx,opa,xlu,pool,bridge=allocation+0xA800,allocation+0xAD00,allocation+0xB600,allocation+0xBF00,allocation+0x14F00
    edge=b'V3TL'*4
    for at in (allocation,game-16,actor-16,player-16,gfx-16,opa-16,xlu-16,pool-16,bridge-16,bridge+8,allocation+size-16,
               TEST_STACK-0x600,TEST_STACK+0x40):debug.write_memory(at,edge)
    source=files[runtime.VROM].extract(rom);reloc=files[runtime.RELOC].extract(rom)
    sections=struct.unpack_from('>5I',reloc);spec=SimpleNamespace(ram=runtime.RAM,resident_bytes=0x5510,sections=sections)
    expected=relocate_verified_data(spec,source,reloc,owner)
    call(0x800262D0,[runtime.VROM,runtime.VROM+len(source),runtime.RAM,runtime.RAM+0x5510,
                    owner,owner+0x5510,len(reloc)])
    check('complete real owner loading, relocation, and BSS',owner,expected)
    def resident(name,args):
        stub=runtime.words(runtime.jump(symbols[name]),0);debug.write_memory(bridge,stub)
        call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
        return call(bridge,args,(bridge,stub))
    debug.write_memory(game,bytes(0x3000));debug.write_memory(actor,bytes(0x1BC))
    debug.write_memory(player,bytes(0x1300));debug.write_memory(gfx,bytes(0x400))
    debug.write_memory(game,runtime.words(gfx));debug.write_memory(game+0x1C90,runtime.words(player))
    debug.write_memory(game+0x110+0x1800,runtime.words(pool,pool+0x5500))
    debug.write_memory(0x801010C0,runtime.words(owner));debug.write_memory(0x8010EF90,runtime.words(game))
    debug.write_memory(0x80136F10,bytes(8));debug.write_memory(0x80126EB4,runtime.words(35))
    debug.write_memory(0x80136EA2,b'\x01');debug.write_memory(0x80136FB8,runtime.words(64800))
    call(0x80097108,[game,game+0x1B98])
    resident('af_v3_lamp_ct',[actor,game])
    model=bounded(word(runtime.STATE+12),3280)
    check('native constructor owns lamp and night state',runtime.STATE,
          runtime.words(0x41464C50,actor,game,model)+struct.pack('>ffIII',1,1,1,0,0))
    check('complete model DMA and both allocation guards',model,
          runtime.words(*([0xAF1AC0DE]*4))+blob[0x2489000-runtime.BLOB:0x2489000-runtime.BLOB+3248]+runtime.words(*([0xAF1AC0DE]*4)))
    def arenas():
        debug.write_memory(opa,bytes(0x800));debug.write_memory(xlu,bytes(0x800))
        debug.write_memory(gfx+0x298,runtime.words(opa,opa+0x800))
        debug.write_memory(gfx+0x2A8,runtime.words(xlu,xlu+0x800))
    arenas();resident('af_v3_lamp_dw',[actor,game])
    end=word(gfx+0x298);frame=opa+0x800-64
    check('native lamp draw tail and full asset binding',end-32,
          runtime.words(0xDA380003,frame,0xDB060018,model+16,0xFA000000,0xFFFFFFFF,0xDE000000,0x06000B10))
    check('native matrix reservation',gfx+0x29C,runtime.words(frame))
    matrix=[0]*16;matrix[7]=1;matrix[8]=0x0CCC0000;matrix[10]=0xCCC;matrix[13]=0x0CCC0000
    check('complete native scale matrix',frame,runtime.words(*matrix))
    debug.write_memory(0x80136FB8,runtime.words(18000))
    resident('af_v3_lamp_mv',[actor,game])
    check('complete native dawn movement changes target and fade',runtime.STATE+16,
          struct.pack('>ffIII',0.985,1,0,0,0))
    call(0x800984CC,[game,game+0x1B98,game+0x1C60])
    check('actual environment dawn step',runtime.STATE+20,struct.pack('>f',0.99))
    check('actual environment point RGB',game+0x1B98+0x28,bytes((232,188,183)))
    debug.write_memory(game+0x1C3D,bytes((100,120,140)));arenas()
    call(0x800981B8,[game])
    check('native room primitive colour in both arenas',opa,runtime.words(0xE7000000,0,0xFA000080,0xD1C5D0FF))
    check('matching translucent room primitive colour',xlu,debug.read_memory(opa,16))
    debug.write_memory(0x80136FB8,runtime.words(64800));resident('af_v3_lamp_mv',[actor,game])
    check('native dusk movement restores night target',runtime.STATE+24,runtime.words(1,0,0))
    resident('af_v3_lamp_dt',[actor,game])
    check('native destructor clears all lamp ownership and state',runtime.STATE,bytes(48))
    check('original native effect destructor releases its clip',0x80136F3C,bytes(4))
    for at,data in saved.items():debug.write_memory(at,data)
    check('saved town restored',0x80126EA0,saved[0x80126EA0])
    check('complete extra code and guards restored',ram,extra)
    for at in (allocation,game-16,actor-16,player-16,gfx-16,opa-16,xlu-16,pool-16,bridge-16,bridge+8,allocation+size-16,
               TEST_STACK-0x600,TEST_STACK+0x40):check('private allocation/stack guard',at,edge)
    check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread',0x8003CE34,bytes(4));call(0x8009C040,[allocation])
    return dict(real_owner_loading=True,complete_native_callbacks=True,actual_model_dma=True,
        native_draw_commands=True,native_environment=True,cleanup=True,ordinary_scene=False,
        gpu_or_hardware=False,saved_data_written=False,requires_checkpoint_restore=True)
