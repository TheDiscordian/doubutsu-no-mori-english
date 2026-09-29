"""Bounded native stationery readers and changed overlay loading; no old replay."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom,sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK
from shop_units import SHOPS,PRICE_BIASES
from v3_import_storage import jump
from v3_npc_draw_smoke import boot_proofs


def exercise(debug,rom_path,record):
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    paper=report['equipment_resources']['carried_items']['paper']['quantities']
    if sha256(image)!=report['output_sha256'] or not paper['installed']:
        raise ValueError('Stationery checks require the exact current installed cartridge')
    files=by_vrom(image);proofs=boot_proofs(image);checks=0
    def check(label,address,wanted):
        nonlocal checks
        actual=debug.read_memory(address,len(wanted));ok=actual==wanted
        record(dict(stationery_check=label,address=f'{address:08X}',bytes=len(wanted),passed=ok))
        if not ok:raise ValueError('Native stationery mismatch: '+label)
        checks+=1
    def call(address,args=(),expected=None,proof=None):
        result=debug.call(f'{address:08X}',list(args),return_address=MODULE_RAM+0x6480,
            verified_code=proof or proofs.get(address));record(result)
        if expected is not None and result['return_value']!=expected:
            raise ValueError(f'Native stationery return {address:08X}: {result["return_value"]}, expected {expected}')
        return result['return_value']
    p=paper['packet'];start=paper['ram']-p['ram'];code=paper['code'];symbols=code['symbols']
    check('complete new resident reader module',paper['ram'],
        image[p['physical']+start:p['physical']+start+code['bytes']])
    # Match native overlay loading: the town arena is not initialised on the
    # title screen. ovlmgr_Malloc selects the active arena without inventing one.
    allocator=0x80026240;at=allocator-0x80025C60+0x1060
    allocation=call(allocator,[0x15000],proof=(allocator,image[at:at+0x4C]))
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-0x15000:
        raise ValueError('Stationery fixture allocation is outside the native heap')
    owner_base,player,bridge=allocation+16,allocation+0x12000,allocation+0x14000
    edge=b'PAPR'*4;guards=(allocation,allocation+0x14FF0,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    def resident(name,args=(),expected=None):
        words=struct.pack('>2I',jump(symbols[name]),0)
        debug.write_memory(bridge,words)
        call(0x8002FE00,[bridge,len(words)]);call(0x80034CE0,[bridge,len(words)])
        return call(bridge,args,expected,proof=(bridge,words))
    # Change only this isolated execution's volatile mode word to exercise both
    # installed alternatives. The emulator checkpoint restores every write.
    mode_address=paper['choice']['ram'];saved_mode=debug.read_memory(mode_address,4)
    try:
        for mode in (0,1):
            debug.write_memory(mode_address,struct.pack('>I',mode))
            for style in (0,55,63):
                single=0x2000+style;item=0x2EC0+style if mode else single
                resident('af_carried_paper_obtain',[single],item)
                resident('af_carried_paper_catalogue_item',[style],item)
                resident('af_carried_paper_shop_category',[item],1)
                call(0x800A5630,[item],17)
            # Actual first-job creation uses the native possession writer; the
            # fixture supplies a blank private inventory, never a user's save.
            debug.write_memory(player,bytes(0xBD0))
            resident('af_carried_paper_first_job_give',[player,0x2037,0])
            check('first-job actual pocket quantity',player+0x14,struct.pack('>H',0x2EF7 if mode else 0x2037))
        debug.write_memory(mode_address,struct.pack('>I',1))
        saved_shop=debug.read_memory(0x80137944,4);debug.write_memory(0x80137944,bytes(4))
        for row in paper['native_consumers']:
            vrom,reloc=row['installed_vrom'],row['installed_reloc'];ram=row['ram']
            data,rel=files[vrom].extract(image),files[reloc].extract(image)
            if sha256(data)!=row['owner']['owner_sha256'] or sha256(rel)!=row['owner']['relocation_sha256']:
                raise ValueError('Changed complete stationery native owner')
            constants=(PRICE_BIASES[row['vrom']],) if row['vrom'] in PRICE_BIASES else ()
            sections=struct.unpack_from('>5I',rel)
            expected=relocate_verified_data(SimpleNamespace(ram=ram,resident_bytes=len(data),sections=sections),
                data,rel,owner_base,address_constants=constants)
            if len(data)+len(rel)>=0x11000:raise ValueError('Stationery owner exceeds bounded fixture')
            call(0x800262D0,[vrom,vrom+len(data),ram,ram+len(data),owner_base,owner_base+len(data),len(rel)])
            check('actual native relocation: '+row['name'],owner_base,expected)
            if row['name']=='shop-floor':
                saved_pointer=debug.read_memory(0x80101140,4)
                debug.write_memory(0x80101140,struct.pack('>I',owner_base))
                for item in (0x2000,0x203F,0x2E40,0x2E80,0x2EFF):
                    call(owner_base,[item],0x1F28,proof=(owner_base,expected))
                debug.write_memory(0x80101140,saved_pointer)
            elif row['name'].startswith('shop-'):
                spec=SHOPS[row['name'][5:]]
                # Execute the complete name/count/counter preparer on actual
                # native window storage, not a replacement implementation.
                call(owner_base+spec.handler-ram,[0x2EC0,2],proof=(owner_base,expected))
                check('shop count: '+row['name'],0x80142410+0x38+70,b'2'+b' '*9)
        debug.write_memory(0x80137944,saved_shop)
        for at in guards:check('fixture guard',at,edge)
        check('no faulted thread',0x8003CE34,bytes(4))
    finally:
        debug.write_memory(mode_address,saved_mode)
    return dict(stationery_native_checks=checks,quantity_modes=2,native_owners=8,
        ordinary_gameplay_verified=False,native_save_reload_verified=False,requires_checkpoint_restore=True)
