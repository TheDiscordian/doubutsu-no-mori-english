"""Bounded current-cartridge reward storage/admission and shovel probes.

This is not a completed NPC conversation, ordinary save/restart, or hardware
test. Fixture state is confined to an isolated checkpoint and restored by the
runner; no FlashRAM writes or audible playback are performed.
"""
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256
from runtime_layout import TEST_RETURN,TEST_STACK
from v3_asset_loader import BLOB,BLOB_RAM


def exercise(debug,rom_path,record,*,save_transaction=False):
    path=Path(rom_path);image=path.read_bytes()
    report=json.loads((path.parent/'build.json').read_bytes())
    e=report['equipment_resources'];reward=e['carried_items']['quest']['rewards']
    if (sha256(image)!=report['output_sha256'] or not reward['selectable'] or
            report['save_codec']['format_version']!=20):
        raise ValueError('Golden probes require the exact selectable format-20 cartridge')
    files=by_vrom(image);blob=files[BLOB].extract(image)
    p=reward['packet'];packet=image[p['physical']:p['physical']+p['bytes']]
    proofs={}

    def check(label,address,expected):
        actual=debug.read_memory(address,len(expected))
        record(dict(golden_reward_check=label,address=f'{address:08X}',bytes=len(expected),
            assertion='passed' if actual==expected else 'failed'))
        if actual!=expected:raise ValueError('Golden native mismatch: '+label)

    for key in ('storage','code'):
        row=reward[key];ram=row['ram'] if 'ram' in row else row['symbols']['AF_HI_STORAGE_RAM']
        end=row.get('code_bounds',[ram,ram+row['bytes']])[1]
        expected=packet[ram-p['ram']:end-p['ram']]
        check('complete installed '+key+' code',ram,expected)
        for name,address in row['symbols'].items():
            if ram<=address<end:proofs[name]=(address,(ram,expected))
    if not save_transaction:
        scene=e['scenery'];ram=scene['ram'];expected=blob[scene['blob_offset']:scene['blob_offset']+scene['bytes']]
        check('complete retained tree code and tables',ram,expected)
        for name,address in scene['code']['symbols'].items():
            if ram<=address<ram+len(expected):proofs[name]=(address,(ram,expected))
        actions=e['player_actions'];ram=e['ram']+actions['code_offset']
        start=e['blob_offset']+actions['code_offset'];expected=blob[start:start+actions['code']['bytes']]
        check('complete held selection code',ram,expected)
        name='af_v3_player_selected_equipment'
        proofs[name]=(actions['code']['symbols'][name],(ram,expected))

    def call(name,args=(),expected=None):
        address,proof=proofs[name]
        result=debug.call(f'{address:08X}',list(args),return_address=TEST_RETURN,verified_code=proof)
        record(dict(golden_reward_function=name,**result))
        if expected is not None and result['return_value']!=expected&0xFFFFFFFF:
            raise ValueError('Golden native return mismatch: '+name)
        return result['return_value']

    scratch=TEST_RETURN+0x200
    if scratch+128>TEST_STACK-0x800:raise ValueError('Golden fixture exceeds reserved test scratch')
    edge=b'GOLD'*4;debug.write_memory(scratch-16,edge);debug.write_memory(scratch+112,edge)
    cards=reward['storage']['symbols']['af_v3_card_state']
    blank_cards=debug.read_memory(cards,64)
    call('af_holiday_cards_valid',[cards],1)
    call('af_reward_first_present',[cards,3],0)
    call('af_reward_mark_first_present',[cards,1],1)
    call('af_reward_first_present',[cards,3],1)
    call('af_reward_mark_first_present',[cards,2],1)
    call('af_reward_first_present',[cards,3],3)
    for slot in range(4):
        gift=struct.pack('>2H',0xE010+slot,2026)
        debug.write_memory(scratch,gift)
        call('af_reward_birthday_set',[cards,slot,scratch],1)
        call('af_reward_birthday_get',[cards,slot,scratch+16],1)
        check('per-player birthday giver/year',scratch+16,gift)
    debug.write_memory(scratch,struct.pack('>2H',0xE010,2100))
    call('af_reward_birthday_set',[cards,0,scratch],0)
    call('af_reward_birthday_get',[cards,0,scratch+16],1)
    check('invalid birthday year preserves state',scratch+16,struct.pack('>2H',0xE010,2026))
    call('af_reward_first_present',[cards,3],3)
    call('af_holiday_cards_valid',[cards],1)
    if save_transaction:
        # Borrow the native save buffer only in this paused disposable machine.
        # Its whole contents and every other modified byte are restored from
        # the checkpoint before execution resumes. No allocator substitution
        # or physical save I/O is involved.
        from flash_mail import SAVE_RAM,SAVE_BYTES
        bank=bytearray(0x10000);bank[4:8]=b'NAFJ'
        bank[8:10]=bank[0x2F68:0x2F6A]=bytes.fromhex('3012')
        checksum=sum(struct.unpack('>'+str(SAVE_BYTES//2)+'H',bank[:SAVE_BYTES]))
        struct.pack_into('>H',bank,0x12,-checksum&65535)
        debug.write_memory(SAVE_RAM,bytes(bank))
        state=report['save_runtime']['state_ram']+16
        profile=BLOB_RAM+0x20
        saved_cards=debug.read_memory(cards,64)
        call('af_v3_save_pack',[SAVE_RAM,0x10000,state],1)
        check('saved disk version 20',SAVE_RAM+SAVE_BYTES+4,bytes.fromhex('00140680'))
        check('packing preserves all reward fields',cards,saved_cards)
        call('af_v3_save_check',[SAVE_RAM,0x10000,profile,0],1)
        debug.write_memory(cards,blank_cards)
        call('af_v3_console_storage_commit',[SAVE_RAM,profile,state,scratch+64],1)
        check('native complete save restores four birthdays and first flags',cards,saved_cards)
        saved_bank=debug.read_memory(SAVE_RAM,0x10000)
        native_profile=bytearray(debug.read_memory(profile,192))
        parent=next(r for r in e['parent_readers']['rows'] if r['item_id']=='2239')
        native_profile[parent['profile_byte']]&=~parent['profile_mask']
        debug.write_memory(scratch+256,bytes(native_profile))
        call('af_v3_save_check',[SAVE_RAM,0x10000,scratch+256,0],-7)
        check('missing golden net leaves saved bank intact',SAVE_RAM,saved_bank)
        check('missing golden net leaves owned reward state intact',cards,saved_cards)
        call('af_v3_console_storage_valid',[],1)
        check('native fault pointer',0x8003CE34,bytes(4))
        return dict(golden_save_transaction='passed',scope='actual native pack/check/commit, four birthday records, first-gift flags, and missing-tool rejection',
            physical_save_io_verified=False,ordinary_save_restart_verified=False,hardware_verified=False)
    for row in actions['equipment_selection']['rows']:
        if row['item_id'] in ('2239','223A','223B','223C'):
            call('af_v3_player_selected_equipment',[int(row['item_id'],16)],row['native_kind'])
    # The two-byte planting result is checked without constructing an acre
    # or replacing the native placement/consumption services.
    debug.write_memory(scratch+32,bytes(16))
    call('af_v3_tree_bury0',[0x2202,0x5D,0,scratch+32],1)
    check('shining-hole shovel becomes golden sapling',scratch+32,bytes.fromhex('0863'))
    call('af_v3_tree_grow',[0x863,20,4],0x867)
    call('af_v3_tree_grow',[0x867,100,4],0x867)
    check('shovel drop and spent-tree source record',scene['code']['symbols']['af_v3_tree_drops']+20*8,
          struct.pack('>4H',0x867,0x223B,0x868,1))
    check('fixture prefix guard',scratch-16,edge);check('fixture suffix guard',scratch+112,edge)
    check('native fault pointer',0x8003CE34,bytes(4))
    return dict(golden_rewards='passed',scope='loaded code, four selected tools, owned reward state, and shovel planting/growth/drop records',
        conversations_verified=False,ordinary_save_restart_verified=False,hardware_verified=False)
