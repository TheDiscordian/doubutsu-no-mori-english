"""Install an isolated font comparison, retain guards/saves, and restore it."""
import json
import struct

from aflib import by_vrom,sha256,CODE_RAM,CODE_VROM
from flash_mail import SAVE_RAM,SAVE_BYTES
from font_sampling_preview import ROOT,ROM_SHA,SOURCES,padded_fixture
from runtime_layout import GUARD_ADDRESS,GUARD_WORD
from title_start_smoke import locate
from texture_preview import rgba5551,png_rgba
from catalogue_names import Image
from npc_mail_show import relocate_verified_data

CODE,META=0x80500000,0x80503000
EDGE=b'FNTG'*4
def words(*v): return struct.pack('>'+'I'*len(v),*v)

def exercise(debug,request,rom,state):
    read,write=debug.read_memory,debug.write_memory
    expected_sha=ROM_SHA
    installed=None
    if request.get('corrected_build'):
        from font_polygon_edges import source_hashes,RAM,VROM,MODULE
        directory=(ROOT/request['corrected_build']).resolve()
        if not directory.is_relative_to(ROOT/'build'): raise ValueError('Unowned corrected font directory')
        report=json.loads((directory/'fixes.json').read_text())
        expected_sha=report['output_sha256']
        if report['sources']!=source_hashes(): raise ValueError('Stale installed font source')
        files=by_vrom(rom);blob=files[VROM].extract(rom)
        if sha256(blob)!=report['font_blob_sha256'] or sha256(files[MODULE].extract(rom))!=report['module_sha256']:
            raise ValueError('Installed font/module do not match report')
        size=report['font']['bytes'];rel=blob[size:];data=blob[:size]
        font_base=int.from_bytes(read(0x80199F04,4),'big')
        if font_base&15 or not 0x8019C8E0<=font_base<=0x80400000-len(blob):
            raise ValueError('Bordered font has no bounded persistent allocation')
        moved=bytearray(relocate_verified_data(Image(RAM,size,struct.unpack_from('>5I',rel)),data,rel,font_base))
        struct.pack_into('>I',moved,11316,font_base+8992)
        # af_world_reset initializes the 16-byte town-name buffer to spaces.
        # Require that exact title-state value; do not ignore mutable regions.
        moved[11324:11340]=b' '*16
        live=read(font_base,size)
        if live!=moved:
            offsets=[i for i in range(size) if live[i]!=moved[i]]
            raise ValueError(f'Live bordered font differs at {len(offsets)} bytes: {offsets[:16]}')
        hook=words(0x08000000|((font_base+report['font']['symbols']['af_border_poly'])>>2&0x3FFFFFF),0)
        if read(0x800911E8,8)!=hook: raise ValueError('Polygon hook not installed')
        installed=hook
    if sha256(rom)!=expected_sha or read(0x80000318,4)!=words(0x800000):
        raise ValueError('Font comparison requires exact V1RC2 with eight MiB')
    if read(GUARD_ADDRESS,16)!=words(*([GUARD_WORD]*4)) or read(0x800418D8,4)!=bytes(4):
        raise ValueError('Resident guard changed or native fault')
    _,actor,base,_=locate(debug,memory_end=0x80800000)
    if base!=0x80400010: raise ValueError('Unexpected title allocation')
    for at in (0x80400000,0x804475F0):
        if read(at,16)!=words(*([0xAF54C0DE]*4)): raise ValueError('Title guard changed')
    if request.get('setup'):
        if state: raise ValueError('Font preview already installed')
        directory=(ROOT/request['build']).resolve()
        if not directory.is_relative_to(ROOT/'build'): raise ValueError('Unowned font fixture directory')
        code=(directory/'preview.bin').read_bytes()
        report=json.loads((directory/'preview.json').read_text())
        if (not 4<=len(code)<=0x2000 or len(code)%4 or sha256(code)!=report['code_sha256']
            or report['sources']!={p:sha256((ROOT/p).read_bytes()) for p in SOURCES}):
            raise ValueError('Stale font comparison fixture')
        original=by_vrom(rom)[CODE_VROM].extract(rom)
        for start,end in ((0x8009113C,0x800913D4),(0x800903E4,0x8009040C)):
            expected=bytearray(original[start-CODE_RAM:end-CODE_RAM])
            if installed and start<=0x800911E8<end: expected[0x800911E8-start:0x800911F0-start]=installed
            if read(start,end-start)!=expected:
                raise ValueError('Font draw code does not match cartridge')
        textures=padded_fixture(rom)
        regions=((CODE,len(code)),(META,32),(0x80504000,len(textures)))
        for start,size in regions:
            if read(start-16,size+32)!=bytes(size+32): raise ValueError('Font scratch RAM is in use')
        callback=read(actor+0x168,4)
        if not base<=int.from_bytes(callback,'big')<0x804475F0: raise ValueError('Unexpected title callback')
        saved=read(SAVE_RAM,SAVE_BYTES)
        guards=tuple(at for start,size in regions for at in (start-16,start+size))
        write(CODE,code)
        write(0x80504000,textures)
        for at in guards: write(at,EDGE)
        write(META,bytes(32));write(actor+0x168,words(CODE))
        state.update(actor=actor,callback=callback,code=code,guards=guards,saved=saved,textures=textures)
        return {'font_preview_installed':True,'code_sha256':sha256(code),'checkpoint_restore_required':True,
                'bordered_font_cartridge_loaded':bool(installed)}
    if not state or actor!=state['actor']: raise ValueError('Missing font comparison state')
    if 'select' in request:
        if request['select']!=1 or read(actor+0x168,4)!=words(CODE):
            raise ValueError('Unexpected font preview selection')
        write(META,words(1,0,0))
        return {'font_preview_scale':1}
    if request.get('verify'):
        mode,draws,error=struct.unpack('>3I',read(META,12))
        if draws<2 or error or read(actor+0x168,4)!=words(CODE): raise ValueError('Native font preview did not draw safely')
        if read(CODE,len(state['code']))!=state['code']: raise ValueError('Font preview modified its code')
        if read(0x80504000,len(state['textures']))!=state['textures']: raise ValueError('Bordered fixture pixels changed')
        for at in state['guards']:
            if read(at,16)!=EDGE: raise ValueError('Font preview scratch overflow')
        if read(SAVE_RAM,SAVE_BYTES)!=state['saved']: raise ValueError('Font preview changed save data')
        directory=(ROOT/request['build']).resolve()
        address=int.from_bytes(read(META+20,4),'big')|0x80000000
        if not 0x80000000<=address<=0x80800000-153600: raise ValueError('Invalid native framebuffer')
        frame=b''.join(read(address+i,min(4096,153600-i)) for i in range(0,153600,4096))
        with (directory/f'framebuffer-{mode}.bin').open('xb') as output: output.write(frame)
        rgba=b''.join(rgba5551(v) for (v,) in struct.iter_unpack('>H',frame))
        with (directory/f'framebuffer-{mode}.png').open('xb') as output:
            output.write(png_rgba(320,240,rgba,3))
        return {'font_preview_draws':draws,'guards_intact':True,'save_unchanged':True,'visual_acceptance':False}
    if request.get('restored'):
        if read(actor+0x168,4)!=state['callback']: raise ValueError('Title callback not restored')
        for at in state['guards']:
            if read(at,16)!=bytes(16): raise ValueError('Font fixture scratch not restored')
        if read(SAVE_RAM,SAVE_BYTES)!=state['saved']: raise ValueError('Restored save differs')
        return {'font_preview_checkpoint_restored':True}
    raise ValueError('Unknown font preview action')
