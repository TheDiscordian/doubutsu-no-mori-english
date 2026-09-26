"""Changed model allocators and DMA with isolated, sparse owner work fields."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM
from v3_furniture_batch_smoke import boot_proofs
import v3_furniture_capacity as capacity
import v3_catalogue as catalogue
from v3_asset_loader import BLOB


def exercise(debug, rom_path, record):
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed model-capacity cartridge')
    capacity.checked(image,report)
    files=by_vrom(image);blob=files[BLOB].extract(image);boot=boot_proofs(image)
    pool=report['furniture']['bank_pool'];code=report['furniture']['expanded_tables']['expanded_code']
    assertions=0
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(model_capacity_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Native model capacity: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,
            verified_code=proof or boot.get(at));record(result);return result['return_value']
    def put(at,*values):debug.write_memory(at,struct.pack('>'+str(len(values))+'I',*values))
    def flush(at,n):call(0x8002FE00,[at,n]);call(0x80034CE0,[at,n])
    allocation=call(0x8009BFC0,[0x3000])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-0x3000:
        raise ValueError('Sparse model-capacity fixture outside native heap')
    actor,table,menu,previews,end_model,submenu,wrapper,bridge=(allocation+n for n in
        (0x10,0x500,0x700,0xE40,0x1D20,0x1D40,0x2000,0x2F00))
    live=table-0x18D68
    if live<0x8019C8E0 or live>0x80400000-0x18F00 or live&7:
        raise ValueError('Sparse model table has no valid native owner base')
    debug.write_memory(allocation,bytes(0x3000));edge=b'V3MC'*4
    guards=(allocation,actor+0x4D0,table-16,table+400,menu-16,previews-16,
            previews+0xEC0,end_model+16,submenu+0x40,wrapper-16,bridge-16,allocation+0x2FF0)
    for at in guards:debug.write_memory(at,edge)
    index_ram=int(report['furniture']['expanded_tables']['bank_index_ram'],16)
    row=max(report['automatic_furniture']['imports'],key=lambda r:r['object_bytes'])
    saved={at:debug.read_memory(at,n) for at,n in
        ((0x80100DF0,32),(pool['start'],16),(pool['guard'],16),
         (pool['data'],pool['bank_bytes']),(pool['data']+99*pool['bank_bytes'],pool['bank_bytes']),
         (index_ram+row['runtime_index'],1))}
    save=report['save_runtime'];saved_game=debug.read_memory(save['state_ram'],save['state_bytes'])
    def run(symbol,args):
        target=code['symbols'][symbol]
        stub=struct.pack('>2I',0x08000000|(target>>2&0x3FFFFFF),0)
        debug.write_memory(bridge,stub);flush(bridge,8)
        return call(bridge,args,(bridge,stub))
    try:
        check('complete installed helper',0x80465800,blob[0x5800:0x5800+code['bytes']])
        put(0x80100DF8,0x80936710,0x8094F610,live)
        for first,second in ((0,0),(99,1)):
            put(actor+0x4C0,first,second)
            run('af_v3_furniture_secure_banks',[actor])
            check('native count and heap-free ownership',actor+0x4C0,struct.pack('>2I',first+second,0))
            pointers=[pool['data']+i*pool['bank_bytes'] if i<first+second else 0 for i in range(100)]
            check('complete native bank table',table,struct.pack('>100I',*pointers))
            for at in (pool['start'],pool['guard']):check('native pool guard',at,struct.pack('>I',pool['guard_word'])*4)
        at=int(row['object_vrom'],16)-BLOB;asset=blob[at:at+row['object_bytes']]
        for number in (0,99):
            bank=pool['data']+number*pool['bank_bytes'];debug.write_memory(bank,b'\xA5'*pool['bank_bytes'])
            returned=run('af_v3_furniture_import_dma',[row['runtime_index'],int(row['item_id'],16),bank,number])
            if returned!=1:raise ValueError('Complete native model DMA rejected')
            check('complete model and untouched bank tail',bank,asset+b'\xA5'*(pool['bank_bytes']-len(asset)))
            check('native bank ownership',index_ram+row['runtime_index'],bytes((number,)))
        # Execute the exact checked native two-preview allocation loop. Its
        # owner fields are private; no full catalogue construction is claimed.
        cat=files[catalogue.VROM].extract(image)
        loop=cat[capacity.ALLOC_FIRST-catalogue.RAM:capacity.ALLOC_END-catalogue.RAM]
        prefix=struct.pack('>7I',0x27BDFFE8,0xAFB00000,0xAFB10004,0xAFB20008,
                           0x00808025,0x00A08825,0x00C09025)
        suffix=struct.pack('>5I',0x8FB00000,0x8FB10004,0x8FB20008,0x03E00008,0x27BD0018)
        code_loop=prefix+loop+suffix;debug.write_memory(wrapper,code_loop);flush(wrapper,len(code_loop))
        put(menu,pool['data']);put(menu+0x720,previews);put(submenu+0x28,0x80200000)
        call(wrapper,[menu,end_model-0x10000,submenu],(wrapper,code_loop))
        for number in (0,1):
            check('native separate preview programme/model buffers',previews+number*0x760+0x748,
                  struct.pack('>2I',0x80200000+number*8192,pool['data']+number*pool['bank_bytes']))
        check('native total model allocation',end_model,struct.pack('>I',pool['data']+2*pool['bank_bytes']))
        check('native programme allocation unchanged',submenu+0x28,struct.pack('>I',0x80204000))
        check('saved game untouched',save['state_ram'],saved_game)
        check('no CPU fault',0x8003CE34,bytes(4))
        for at in guards:check('sparse fixture guard',at,edge)
    finally:
        for at,data in saved.items():debug.write_memory(at,data)
        call(0x8009C040,[allocation])
    return dict(native_model_capacity=True,assertions=assertions,complete_model_dma=True,
        native_bank_constructor=True,native_preview_allocation_loop=True,
        complete_room_or_catalogue_construction_tested=False,gpu_or_hardware_tested=False,
        flash_written=False,requires_checkpoint_restore=True)
