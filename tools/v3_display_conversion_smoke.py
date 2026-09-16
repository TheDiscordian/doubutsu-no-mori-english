"""Actual current native conversion entries, profile rejection, and retained code."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_npc_draw_smoke import boot_proofs


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['clothing']['display'].get('conversion'):
        raise ValueError('Conversion check requires the exact current cartridge')
    blob = by_vrom(rom)[BLOB].extract(rom)
    boot=boot_proofs(rom)

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'display_conversion_check': label, 'address': f'{address:08X}',
                'bytes': len(expected), 'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected: raise ValueError('Conversion check failed: '+label)

    def invoke(address, args, expected=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM+0x6480,
                            verified_code=boot.get(address))
        if expected is not None:
            result['assertion']='passed' if result['return_value']==expected else 'failed'
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Conversion {address:08X} args {args}: '
                             f'{result["return_value"]} != {expected}')
        return result['return_value']

    def call(address,item,expected): return invoke(address,[item],expected)

    display=report['clothing']['display']
    for at,code in ((0x6C00,display['readers']['code']),(0x6270,display['conversion']['code']),
                    (0x6380,display['roster_code'])):
        check('complete changed alias code',BLOB_RAM+at,blob[at:at+code['bytes']])
    aliases=report.get('display_aliases')
    if aliases:
        from v3_display_aliases import OFFSET
        check('complete forward alias index',aliases['table_ram'],blob[OFFSET:OFFSET+aliases['table_bytes']])
    edge = b'V3DC'*4
    for address in (TEST_STACK-0x800, TEST_STACK+0x40): debug.write_memory(address, edge)
    scratch=invoke(0x8009BFC0,[256])
    if scratch&15 or not MODULE_RAM+0x8000<=scratch<0x80400000-256:
        raise ValueError('Alias fixture allocation outside native heap')
    for at in (scratch,scratch+240):debug.write_memory(at,edge)
    parents={r['item_id']:r for r in report['clothing']['imports']}
    saved={}
    try:
        for row in display['imports']:
            item,parent=int(row['item_id'],16),int(row['pocket_item_id'],16)
            source=parents[row['pocket_item_id']]
            call(0x800BEFCC,parent,item);call(0x800BEFCC,0xABCD0000|parent,item)
            for rotation in range(4):
                value=item|rotation
                call(0x800BF10C,value,parent);call(0x800BF10C,0xABCD0000|value,parent)
                invoke(0x801969C8,[scratch+16,16,value],1)
                check('display uses parent English name',scratch+16,source['name'].encode().ljust(16,b' '))
                call(0x800A5630,value,10);call(0x800C0194,value,source['price'])
                invoke(0x800BE72C,[value,4,7,scratch+48],0)
                invoke(0x800BE72C,[0x17AC|rotation,4,7,scratch+112],0)
                check('complete native footprint retained',scratch+48,debug.read_memory(scratch+112,48))
            # Parent selection, display selection, and garment metadata enable
            # are independent requirements. Each returns the native fallback.
            parent_index=parent-0x3400;display_index=row['runtime_index']-1024
            metadata=0x80462820+32*report['clothing']['imports'].index(source)+10
            for at,mask in ((BLOB_RAM+0x20+160+parent_index//8,1<<(parent_index&7)),
                            (BLOB_RAM+0x20+32+display_index//8,1<<(display_index&7)),
                            (metadata,1)):
                selected=debug.read_memory(at,1);saved[at]=selected
                debug.write_memory(at,bytes([selected[0]&~mask]))
                call(0x800BEFCC,parent,parent);call(0x800BF10C,item,item)
                debug.write_memory(at,selected)
    finally:
        for at,data in saved.items():debug.write_memory(at,data)
    check('fixture leading guard',scratch,edge);check('fixture trailing guard',scratch+240,edge)
    invoke(0x8009C040,[scratch])
    # Actual original functions retain every conversion group and its bounds.
    for item, expected in ((0x2400, 0x17AC), (0x24BF, 0x1AA8), (0x24FE, 0x1BA4),
                           (0x24FF, 0x1BA8), (0x2500, 0x2500), (0x2D00, 0x1BA8),
                           (0x2D20, 0x1C28), (0x2300, 0x1C28), (0x2320, 0x1CA8),
                           (0x2204, 0x1CA8), (0x2223, 0x1D24), (0x2224, 0x2224),
                           (0x3224, 0x3224), (0x32BB, 0x32BB), (0, 0), (0xFFFF, 0xFFFF)):
        call(0x800BEFCC, item, expected)
    for item, expected in ((0x17AB, 0x17AB), (0x17AC, 0x2400), (0x1BAB, 0x2D00),
                           (0x1BA7, 0x24FE), (0x1C27, 0x2D1F), (0x1C28, 0x2300),
                           (0x1CA7, 0x231F), (0x1CA8, 0x2204), (0x1D27, 0x2223),
                           (0x1D28, 0x1D28), (0x3227, 0x3227), (0x32B8, 0x32B8),
                           (0x34BF, 0x34BF), (0x3AFB, 0x3AFB), (0x3B00, 0x3B00)):
        call(0x800BF10C, item, expected)
    for address in (TEST_STACK-0x800, TEST_STACK+0x40): check('stack guard', address, edge)
    check('complete selected profile restored',BLOB_RAM+0x20,blob[0x20:0xE0])
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    return {'native_global_conversions': True, 'all_four_display_rotations': True,
            'native_fallbacks_and_missing_dependencies': True,
            'ordinary_placement_pickup_tested': False, 'requires_checkpoint_restore': True}
