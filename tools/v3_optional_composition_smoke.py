"""One current-profile runtime check; no navigation, save writes, or audio calls."""
import json
from pathlib import Path

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from runtime_layout import MODULE_RAM
from v3_asset_loader import BLOB
from v3_optional_composition import catalogue, inputs, resolve


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    image = path.read_bytes()
    report = json.loads((path.parent/'build.json').read_text())
    receipt = report['composition']
    if sha256(image)!=report['output_sha256'] or sha256(image)!=receipt['output_sha256']:
        raise ValueError('Optional runtime check requires its exact composed cartridge')
    base, prior = inputs()
    catalog = catalogue(base, prior)
    selection = resolve(catalog, receipt['requested'])
    if any(receipt[key]!=value for key,value in selection.items()):
        raise ValueError('Changed optional-selection receipt')
    files = by_vrom(image)
    prefix = files[BLOB].extract(image)[:0xC000]
    def check(label, address, expected):
        actual = debug.read_memory(address,len(expected))
        record({'optional_profile_check':label,'address':f'{address:08X}','bytes':len(expected),
                'assertion':'passed' if actual==expected else 'failed'})
        if actual!=expected: raise ValueError('Optional runtime mismatch: '+label)
    def call(address, arguments, expected):
        result = debug.call(f'{address:08X}',arguments,return_address=MODULE_RAM+0x6480)
        record(result)
        if result['return_value']!=expected:
            raise ValueError(f'Optional runtime return at {address:08X}: {result["return_value"]} != {expected}')
    check('startup ready',0x8019ACD0,b'\0\0\0\1')
    check('selected profile',0x80460020,bytes.fromhex(selection['profile_hex']))
    check('selected town flags',0x80461E60,prefix[0x1E60:0x1E74])
    check('complete selected text/default metadata',0x80462C00,prefix[0x2C00:0x2E80])
    state = debug.read_memory(0x8046C000,864)
    history = debug.read_memory(0x8013670C,32)
    scratch = MODULE_RAM+0x6500
    try:
        # Count otherwise-unseen candidates, without changing resident identities.
        debug.write_memory(0x8013670C,bytes(32))
        native_looks = files[CODE_VROM].extract(image)[0x8010AF58-CODE_RAM:0x8010AF58-CODE_RAM+216]
        selected = [row for row in report['villager_text']['imports'] if row['selected_for_profile']]
        for personality in range(6):
            expected = native_looks.count(personality)+sum(row['personality']==personality for row in selected)
            call(0x800AA3A4,[personality],expected)
        for key,row in catalog.items():
            active = key in selection['enabled']
            if row['kind']=='villager':
                if active:
                    debug.write_memory(scratch,b'\xA5'*32)
                    call(0x80196044,[scratch,8,int(row['actor_id'],16)],1)
                    check('selected full name '+row['name'],scratch,row['name'].encode().ljust(8,b' ')+b'\xA5'*24)
                continue
            call(0x800A5630,[int(row['item_id'],16)],(12 if row['kind']=='clothing' else 10) if active else 0)
            if row['kind']=='clothing':
                call(0x800A5630,[int(row['display_item_id'],16)],10 if active else 0)
        call(0x800A5630,[0x24BF],12)
        call(0x800A5630,[0x1000],10)
    finally:
        debug.write_memory(0x8013670C,history)
    check('appearance history restored',0x8013670C,history)
    check('runtime save/profile state retained',0x8046C000,state)
    check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    check('save guard',0x8046C350,bytes.fromhex('AF53C0DE')*4)
    check('resident guard',0x8046BFF0,bytes.fromhex('AF33C0DE')*4)
    check('accessory/audio guard',0x80481FF0,bytes.fromhex('AFACC0DE')*4)
    check('no fault',0x8003CE34,bytes(4))
    return {'optional_runtime_selection':selection['requested'],
            'required_dependencies':selection['required'], 'requires_checkpoint_restore':True,
            'ordinary_arrival_save_or_audio_test':False, 'web_patcher_updated':False}
