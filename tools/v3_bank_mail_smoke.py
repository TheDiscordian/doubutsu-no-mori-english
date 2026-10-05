"""Native account transactions and original mailed milestone delivery."""
import json
from pathlib import Path
import struct

from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_record import Field,Record,pack,unpack
from runtime_layout import TEST_RETURN
from v3_npc_draw_smoke import boot_proofs


def exercise(debug,rom_path,record,*,deliver_for_save=False):
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed savings cartridge')
    bank=report['equipment_resources']['bank'];mail=bank['mail'];packet=bank['packet']
    symbols=dict(bank['code']['symbols'],**mail['code']['symbols']);proofs=boot_proofs(image)
    read,write=debug.read_memory,debug.write_memory;checks=0

    def check(label,okay):
        nonlocal checks
        record(dict(savings_check=label,assertion='passed' if okay else 'failed'))
        if not okay:raise ValueError('Native savings mismatch: '+label)
        checks+=1

    def call(address,args=(),proof=None):
        result=debug.call(f'{address:08X}',list(args),return_address=TEST_RETURN,
            verified_code=proof or proofs.get(address));record(result)
        return result['return_value']

    code_ram=mail['reservation']['ram'];n=mail['code']['bytes']
    check('actual startup-loaded savings mail code',read(code_ram,n)==image[
        packet['physical']+code_ram-packet['ram']:packet['physical']+code_ram-packet['ram']+n])
    allocation=call(0x8009BFC0,[0x1000]);arena=report['equipment_resources']['scene_arena']['workspace']
    check('owned native probe workspace',not allocation&15 and arena['ram']+32<=allocation<=arena['end_guard']-0x1000)
    bridge=allocation+16;before=allocation+64;after=allocation+128
    original=allocation+192;next_wallet=allocation+256;tx=allocation+320
    from v3_import_storage import jump

    def invoke(name,args=()):
        code=struct.pack('>2I',jump(symbols[name]),0);write(bridge,code)
        call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
        return call(bridge,args,(bridge,code))

    ledger=bank['memory']['account']['ram'];mode=bank['account_mode']['address']
    players=mail['bindings']['af_bank_mail_players'];homes=mail['bindings']['af_bank_mail_homes']
    arrange=mail['bindings']['af_bank_home_arrangement']
    saved={SAVE_RAM:read(SAVE_RAM,SAVE_BYTES),ledger:read(ledger,64),mode:read(mode,4),
        0x80136EA3:read(0x80136EA3,1),0x80136FD8:read(0x80136FD8,4)}
    retain=False
    try:
        check('installed account pointer uses reviewed save owner',invoke('af_bank_native_account')==ledger)
        if deliver_for_save:
            player=saved[0x80136EA3][0]
            private=int.from_bytes(saved[0x80136FD8],'big')
            check('persistent test uses actual resident',player<4 and private==players+player*0xBD0)
            identity=read(private,16);home=(read(arrange,1)[0]>>(2*player))&3
            house=homes+home*0xB48
            check('persistent rewards use actual matching home',read(house,16)==identity)
            slots=[i for i in range(10) if read(house+0x478+i*164+38,1)==b'\xff']
            check('actual mailbox has room for four milestones',len(slots)>=4)
            check('persistent test starts with empty native accounts',read(ledger+16,32)==bytes(32))
            write(ledger+8,b'\x01')
            write(ledger+16+player*8,struct.pack('>I',999999999))
            for i,row in enumerate(mail['source']['rewards']):
                check('real mailbox receives persistent milestone',invoke('af_bank_mail_run')==1)
                letter=read(house+0x478+slots[i]*164,164)
                check('persistent original recipient and gift',letter[:16]==identity and
                    int.from_bytes(letter[36:38],'big')==int(row['destination_item'],16))
                check('persistent official letter template',unpack(letter[42:],expected_catalog=4).templates==(row['template'],))
            check('persistent earned flags prevent duplicates',read(ledger+20+player*8,1)==b'\x3c' and invoke('af_bank_mail_run')==0)
            retain=True
            return dict(savings_ready_for_native_save=True,native_savings_checks=checks,
                controlled_balance=True,actual_player_and_mailbox=True,player=player,
                balance=999999999,earned_rewards=4,ordinary_pelly_conversation=False,
                requires_checkpoint_restore=True)
        check('native account reset',invoke('af_bank_reset',[ledger,48])==1)
        town_pointer=call(mail['bindings']['af_bank_mail_town']);town=read(town_pointer,6)
        town_id=read(players+14,2);identities=[]
        for p in range(4):
            identity=b'Bank'+bytes([65+p])+b' '+town+struct.pack('>H',0x500+p)+town_id
            identities.append(identity);write(players+p*0xBD0,identity)
            write(homes+(3-p)*0xB48,identity)
            for slot in range(10):write(homes+(3-p)*0xB48+0x478+slot*164+38,b'\xff')
        write(arrange,b'\x1b');write(mode,b'\x01\0\0\0')
        write(0x80136EA3,b'\0');write(0x80136FD8,struct.pack('>I',players))
        write(players+0x14,bytes(36));write(players+0x38,struct.pack('>I',2000));write(players+0x3C,bytes(4))
        write(homes+3*0xB48+0x22,b'\x80')
        check('native paid-house account eligibility',invoke('af_bank_native_eligible')==1)
        write(0x80136EA3,b'\x04')
        check('visitor cannot use resident account',invoke('af_bank_native_eligible')==0)
        write(0x80136EA3,b'\0')
        for direction,expected_balance,expected_wallet in ((8,1000,1000),(4,0,2000)):
            write(before,read(ledger,48));write(after,read(ledger,48))
            check('real native wallet read',invoke('af_bank_native_wallet',[players,original])==1)
            write(next_wallet,read(original,52))
            check('complete source transaction opens',invoke('af_bank_begin',[after,48,0,1,next_wallet,tx])==1)
            write(tx+16,struct.pack('>I',2))
            check('source amount controller preview',invoke('af_bank_step',[after,48,0,1,next_wallet,tx,direction])==0)
            check('preview leaves real account intact',read(ledger,48)==read(before,48))
            check('source confirmation',invoke('af_bank_step',[after,48,0,1,next_wallet,tx,0x1000])==1)
            check('native atomic wallet/account publication',invoke('af_bank_native_commit',[
                ledger,before,after,players,original,next_wallet])==1)
            check('deposited/withdrawn Bells conserved',int.from_bytes(read(ledger+16,4),'big')==expected_balance and
                int.from_bytes(read(players+0x38,4),'big')==expected_wallet)
        invoke('af_bank_reset',[ledger,48]);write(ledger+8,b'\x01')
        for p in range(4):write(ledger+16+p*8,struct.pack('>I',999999999)+bytes(4))
        for milestone,row in enumerate(mail['source']['rewards']):
            check('four residents receive next source milestone',invoke('af_bank_mail_run')==4)
            for p in range(4):
                letter=read(homes+(3-p)*0xB48+0x478+milestone*164,164)
                check('original attached reward identity',int.from_bytes(letter[36:38],'big')==int(row['destination_item'],16))
                check('native recipient and received metadata',letter[:16]==identities[p] and letter[38:42]==b'\0\x80\x0a\0')
                snapshot=unpack(letter[42:],expected_catalog=4)
                check('complete official template and retained names',snapshot.templates==(row['template'],) and
                    snapshot.fields==((0,Field(town.rstrip(b' '))),(1,Field(identities[p][:6]))))
                check('success-only saved milestone receipt',read(ledger+20+p*8,1)==bytes([(4<<(milestone+1))-4]))
        check('earned rewards do not repeat',invoke('af_bank_mail_run')==0)
        invoke('af_bank_reset',[ledger,48]);write(ledger+8,b'\x01');write(ledger+16,struct.pack('>I',1000000))
        for slot in range(10):write(homes+3*0xB48+0x478+slot*164+38,b'\x03')
        for slot in range(5):write(0x80135E0C+slot*164+38,b'\x03')
        check('full native mailbox and queue refuse reward',invoke('af_bank_mail_run')==0)
        check('failed delivery keeps reward unearned',read(ledger+20,1)==b'\0')
        write(homes+3*0xB48+0x478+38,b'\xff')
        check('ordinary retry after freeing a mailbox space',invoke('af_bank_mail_run')==1)
        check('successful retry acknowledges exactly once',read(ledger+20,1)==b'\x04' and invoke('af_bank_mail_run')==0)
        write(mode,bytes(4));write(ledger+20,b'\0')
        check('disabled feature sends no rewards',invoke('af_bank_mail_run')==0 and read(ledger+20,1)==b'\0')
        check('new mail extension guard',read(mail['reservation']['ram']+mail['reservation']['bytes']-16,16)==b'AFBM'*4)
        return dict(native_savings_checks=checks,native_transactions=True,native_mail_submission=True,
            controlled_account_balances=True,ordinary_pelly_conversation=False,requires_checkpoint_restore=True)
    finally:
        if not retain:
            for address,data in saved.items():write(address,data)
        call(0x8009C040,[allocation])
