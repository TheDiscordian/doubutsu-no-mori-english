"""Bounded native stock, purchase, reserve, and cedar-generation execution."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from npc_mail_show import relocate_verified_data
from runtime_layout import TEST_RETURN
from v3_npc_draw_smoke import boot_proofs


def exercise(debug, rom_path, record):
    path = Path(rom_path); image = path.read_bytes()
    report = json.loads((path.parent/'build.json').read_bytes())
    if sha256(image) != report['output_sha256']:
        raise ValueError('Changed normal acquisition cartridge')
    normal = report['equipment_resources']['normal_acquisition']
    packet = normal['packet']; code = normal['code']; symbols = code['symbols']
    files = by_vrom(image); core = files[CODE_VROM].extract(image); proofs = boot_proofs(image)
    checks = 0

    def check(label, okay, **detail):
        nonlocal checks
        record(dict(normal_acquisition_check=label, assertion='passed' if okay else 'failed', **detail))
        if not okay: raise ValueError('Native normal acquisition mismatch: '+label)
        checks += 1

    def memory(label, address, wanted):
        observed = debug.read_memory(address, len(wanted))
        check(label, observed == wanted, address=f'{address:08X}', bytes=len(wanted),
            expected_sha256=sha256(wanted), observed_sha256=sha256(observed))

    def call(address, args=(), proof=None):
        result = debug.call(f'{address:08X}', list(args), return_address=TEST_RETURN,
            verified_code=proof or proofs.get(address)); record(result)
        return result['return_value']

    start = code['ram']-packet['ram']
    resident = image[packet['physical']+start:packet['physical']+start+code['bytes']]
    memory('actual startup-loaded acquisition code', code['ram'], resident)
    # Ordinary gameplay's native allocator uses the installed scene arena.
    # Validate against that actual declared arena, not an obsolete 4-MiB bound.
    arena = report['equipment_resources']['scene_arena']['workspace']
    allocation = call(0x8009BFC0, [0x10000])
    check('native isolated overlay allocation', not allocation&15 and
        arena['ram']+32 <= allocation <= arena['end_guard']-0x10000)
    root, bridge, table = allocation+16, allocation+0xE000, allocation+0xE100
    saved = {at: debug.read_memory(at,n) for at,n in
        ((0x80135BC2,0x52),(0x8012D148,30*512),(0x80101140,4),(0x80137944,4),(0x80136FBC,16))}
    edge = b'NORM'*4
    for at in (allocation, allocation+0xFFF0): debug.write_memory(at,edge)
    debug.write_memory(table,bytes([0,0,0,0,0,0,1,0,2,0,0,0]))
    profiles=report['equipment_resources']['diaries']['ui_compiled']['bindings']['af_diary_native_profiles']
    diary_words=[profiles+(63+style)*80+4 for style in range(16)]
    paper_mode=report['equipment_resources']['carried_items']['paper']['quantities']['choice']['ram']
    for at in diary_words: saved[at]=debug.read_memory(at,4)
    for at,n in ((paper_mode,4),(0x8013A248,4),(0x80136F00,4)):
        saved[at]=debug.read_memory(at,n)

    def diary_mask(mask):
        for style,at in enumerate(diary_words):
            debug.write_memory(at,struct.pack('>I',int(bool(mask&(1<<style)))))

    def resident_call(name, args=()):
        from v3_import_storage import jump
        words = struct.pack('>2I',jump(symbols[name]),0)
        debug.write_memory(bridge,words)
        call(0x8002FE00,[bridge,8]); call(0x80034CE0,[bridge,8])
        return call(bridge,args,proof=(bridge,words))

    try:
        # Exercise the actual installed shared selector and its original paper
        # allocation/RNG bridge. No substitute list or selection function.
        diary_mask(0xffff)
        for level in (1,2,3):
            native_info=struct.unpack('>H',saved[0x80135BC2][-2:])[0]
            debug.write_memory(0x80135C12,struct.pack('>H',(native_info&0x3fff)|(level<<14)))
            count=(2,3,5)[level-1]
            debug.write_memory(0x80135BC2,bytes(62))
            call(0x800BFCF0,[0,0x80135BC2,count,0,0,1,8],proof=(0x800BFCF0,core[0x800BFCF0-CODE_RAM:0x800BFCF0-CODE_RAM+8]))
            current=struct.unpack('>31H',debug.read_memory(0x80135BC2,62))
            check('diary uses last existing paper space at larger shops',
                all(0x2000<=item<0x2044 for item in current[:count-int(level>=2)]) and
                (0x2B10<=current[count-1]<0x2B20 if level>=2 else True) and not any(current[count:]),shop_level=level)
        diary_mask(0)
        debug.write_memory(0x80135BC2,bytes(62))
        call(0x800BFCF0,[0,0x80135BC2,5,0,0,1,8],proof=(0x800BFCF0,core[0x800BFCF0-CODE_RAM:0x800BFCF0-CODE_RAM+8]))
        check('no diary selection preserves all native paper spaces',
            all(0x2000<=item<0x2044 for item in struct.unpack('>5H',debug.read_memory(0x80135BC2,10))))
        diary_mask(0xffff)
        for level in (1,2,3):
            # Preserve all shop notice bits and set only the native level bits.
            native_info=struct.unpack('>H',saved[0x80135BC2][-2:])[0]
            debug.write_memory(0x80135C12,struct.pack('>H',(native_info&0x3fff)|(level<<14)))
            stock = struct.pack('>31H',*([0x1004]*25+[0]*6))
            debug.write_memory(0x80135BC2,stock)
            resident_call('af_normal_shop_plants',[0x80135C08,table,1])
            current=debug.read_memory(0x80135BC2,62)
            check('cedar stock at correct shop sizes',current==stock[:50]+struct.pack('>H',0x290A if level>=2 else 0)+stock[52:],shop_level=level)
            counts=debug.read_memory(0x80135C08,10)
            check('one existing sapling space replaced',counts[0]==(1 if level>=2 else 2),shop_level=level)
            memory('purchase leaves saved shop level intact',0x80135C12,struct.pack('>H',(native_info&0x3fff)|(level<<14)))
        # Actual native removal follows the ordinary saved stock path, not the
        # plant-quantity index beyond the end of its ten-byte array.
        stock=debug.read_memory(0x80135BC2,62);counts=debug.read_memory(0x80135C08,10)
        result=call(0x800BFFC0,[0x290A,0x80135BC2,31,0x1F39],proof=(0x800BFFC0,core[0x800BFFC0-CODE_RAM:0x800C0194-CODE_RAM]))
        check('actual native purchase removal',result==0)
        memory('sold cedar retained in saved goods',0x80135BC2,stock[:50]+struct.pack('>H',0x1F39)+stock[52:])
        memory('purchase does not change flower counts or shop info',0x80135C08,counts+struct.pack('>H',(native_info&0x3fff)|(3<<14)))
        row=next(r for r in normal['cedars']['consumers'] if r['name']=='shop-floor')
        data,rel=files[row['vrom']].extract(image),files[row['reloc']].extract(image)
        ram=row['ram'];sections=struct.unpack_from('>5I',rel)
        loaded=relocate_verified_data(SimpleNamespace(ram=ram,resident_bytes=len(data),sections=sections),data,rel,root,memory_end=0x80800000)
        call(0x800262D0,[row['vrom'],row['vrom']+len(data),ram,ram+len(data),root,root+len(data),len(rel)])
        memory('complete actual native-relocated shop floor',root,loaded)
        debug.write_memory(0x80101140,struct.pack('>I',root));debug.write_memory(0x80137944,bytes(4))
        check('cedar uses the existing sapling reserve',call(root,[0x290A],proof=(root,loaded))==0x1F2D)
        check('ordinary sapling reserve preserved',call(root,[0x2900],proof=(root,loaded))==0x1F2D)
        for item in (0x2B10,0x2B1F):
            check('diary uses existing paper reserve',call(root,[item],proof=(root,loaded))==0x1F28,item=f'{item:04X}')
        field,block,grid,actor,clip=(allocation+n for n in (0x8000,0x8300,0x8B00,0x8E00,0x9000))
        for at,n in ((field,0x200),(block,0x700),(grid,512),(actor,0x200),(clip,32)):
            debug.write_memory(at,bytes(n))
        debug.write_memory(0x8013A248,struct.pack('>I',field))
        debug.write_memory(field+0x148,struct.pack('>I',block))
        debug.write_memory(field+0x166,bytes((1,1)))
        debug.write_memory(block+0x584,struct.pack('>I',grid))
        debug.write_memory(clip,struct.pack('>I',actor))
        debug.write_memory(actor+0x174,struct.pack('>I',0x80135BC2))
        debug.write_memory(actor+0x17C,struct.pack('>I',31))
        debug.write_memory(0x80136F00,struct.pack('>I',clip))
        for item,marker,repeat in ((0x2B10,0x1F34,False),(0x290A,0x1F39,False),(0x2040,0x2040,True)):
            debug.write_memory(grid+84*2,struct.pack('>H',item))
            debug.write_memory(0x80135BC2,struct.pack('>H',item)+bytes(60))
            check('actual floor selector preserves imported identity',
                call(root+0x809547E4-ram,[4,5],proof=(root,loaded))==item,item=f'{item:04X}')
            result=call(root+0x80954970-ram,[4,5],proof=(root,loaded))
            check('actual sale repeat/removal agrees with original rule',result==int(repeat),item=f'{item:04X}')
            memory('sale retains correct saved-stock marker',0x80135BC2,struct.pack('>H',marker))
            memory('sale retains correct floor marker',grid+84*2,struct.pack('>H',marker))
        from shop_units import SHOPS, PRICE_BIASES
        for row in normal['cedars']['consumers']:
            if row['name'] == 'shop-floor': continue
            name = row['name'][5:]; spec = SHOPS[name]
            data, rel = files[row['vrom']].extract(image), files[row['reloc']].extract(image)
            ram = row['ram']; sections = struct.unpack_from('>5I', rel)
            check('shop owner fits isolated allocation',len(data)+len(rel)<0xDFC0,shop=name)
            loaded = relocate_verified_data(SimpleNamespace(ram=ram,resident_bytes=len(data),sections=sections),
                data,rel,root,address_constants=(PRICE_BIASES[spec.vrom],),memory_end=0x80800000)
            call(0x800262D0,[row['vrom'],row['vrom']+len(data),ram,ram+len(data),root,root+len(data),len(rel)])
            memory('complete native-relocated shop counter: '+name,root,loaded)
            call(root+spec.handler-ram,[0x290A,2],proof=(root,loaded))
            memory('cedar counter quantity: '+name,0x80142410+0x38+70,b'2'+b' '*9)
            call(root+spec.handler-ram,[0x2B10,1],proof=(root,loaded))
            memory('diary counter quantity: '+name,0x80142410+0x38+70,b'1'+b' '*9)
        town=struct.pack('>256H',*([0x0804]*16+[0x7777]*240))*30
        debug.write_memory(0x8012D148,town)
        resident_call('af_normal_new_town')
        after=struct.unpack('>7680H',debug.read_memory(0x8012D148,len(town)))
        for acre in range(30):
            block=after[acre*256:(acre+1)*256]
            check('original northern-acre cedar count',block.count(0x0861)==([6,4,2][acre//5] if acre<15 else 0),acre=acre)
            check('new-town generation preserves unrelated foreground',block[16:]==(0x7777,)*240,acre=acre)
        for at in (allocation,allocation+0xFFF0): memory('isolated native allocation guard',at,edge)
        memory('no faulted thread',0x8003CE34,bytes(4))
    finally:
        for at,raw in saved.items(): debug.write_memory(at,raw)
    return dict(normal_acquisition_native_checks=checks,ordinary_gameplay_verified=False,
        save_reload_verified=False,requires_checkpoint_restore=True)
