"""Connect original savings milestones to native mail and optional selection."""
import copy
import json
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from apply_translation import write_new
from v3_asset_loader import BLOB, ROOT, compile_part
from v3_furniture_pipeline import Source
from v3_registry import furniture_identity, furniture_source_index

RAM, END = 0x807E8040, 0x807E9000
GUARD = b'AFBM'*4
SOURCES = ('tools/v3_bank_mail.py', 'overlays/v3/bank_mail.c',
    'overlays/v3/bank_mail.ld', 'runtime/mail/record.c', 'runtime/mail/record.h')
CONTRACTS = (
    (0x800B7680, 0x800B7700, '4890d2435fc8e7c964b8e9f3c324ba71c1d7ee1d2e4709048c6113a77ad82b5f'),
    (0x800B7560, 0x800B7624, '663f1af7187752f9cee0b4f6d5fdb5aaefd13aea2f34ff5115053f3f5da93590'),
    (0x800950D8, 0x800950E8, '61a617be4bea453b5d6d985cbad27d2006fb6c18a8233afdbf21005cc8a51ed3'))


def source_contract(source):
    from v3_post_office import discover
    from audit_mail_templates import template_fields
    from gc_text import decoder_tables
    from mail_reference import BANK_HASHES, DECODER_SHA256, transcode
    from textbanks import Bank
    _, report = discover(source)
    decoder = ROOT/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes()) != DECODER_SHA256:
        raise ValueError('Changed official letter decoder')
    tables = decoder_tables(decoder)
    provenance = {row['id']:row for row in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
    directory = ROOT/'build/gamecube/files/forest_1st.arc.unpacked/data'
    parts = []
    for name in ('super', 'mail', 'ps'):
        data = (directory/(name+'_data.bin')).read_bytes()
        table = (directory/(name+'_data_table.bin')).read_bytes()
        if (sha256(data), sha256(table)) != BANK_HASHES[name]:
            raise ValueError('Changed complete official savings letter bank')
        entries = Bank(name, 0, 0, data, table).entries()
        for row in report['rewards']:
            number = row['template']; raw = entries[number]
            encoded = transcode(raw, tables, extended_glyphs=True)
            if not template_fields(encoded, extended_glyphs=True) <= {0, 1}:
                raise ValueError('Unexpected original savings letter field')
            credit=provenance[f'GAFE01-r0/{name}:{number:04X}']['locales']['en']
            if credit['credit']!='official' or credit['encoded_sha256']!=sha256(encoded):
                raise ValueError('Savings letter lacks its existing official provenance')
            parts.append(dict(bank=name, template=number, reference_sha256=sha256(raw),
                encoded_sha256=sha256(encoded), bytes=len(encoded)))
    # The English source removes the Japanese village suffix entirely.
    suffix = Bank('string', 0, 0, (directory/'string_data.bin').read_bytes(),
        (directory/'string_data_table.bin').read_bytes()).entries()[484]
    if suffix:
        raise ValueError('Changed English town-name suffix')
    rows = [dict(row, destination_item=f'{furniture_identity(int(row["item"],16))[1]:04X}',
        index=furniture_identity(int(row['item'],16))[0]) for row in report['rewards']]
    return json.loads(json.dumps(dict(rewards=rows, table_sha256=report['reward_sha256'],
        function=report['mail_function'], parts=parts, english_town_suffix_sha256=sha256(suffix))))


def checked(source, image, report):
    owner = report.get('equipment_resources', {}).get('bank', {}).get('mail')
    if not owner:
        return None
    bank = report['equipment_resources']['bank']; packet = bank['packet']
    raw = image[packet['physical']:packet['physical']+packet['bytes']]
    if (not owner.get('installed') or owner['source'] != source_contract(source)
            or sha256(raw) != packet['sha256'] or zlib.crc32(raw) != packet['crc32']
            or raw[-16:] != GUARD or owner['reservation'] != dict(ram=RAM, bytes=END-RAM)
            or sha256(raw[RAM-packet['ram']:RAM-packet['ram']+owner['code']['bytes']]) != owner['code']['sha256']):
        raise ValueError('Changed complete savings mail provider')
    core = by_vrom(image)[CODE_VROM].extract(image)
    hook = owner['hook']
    if u32(core, hook['address']-CODE_RAM) != hook['after']:
        raise ValueError('Missing ordinary savings mail scheduler')
    from mail_catalog import parse
    catalog = parse(by_vrom(image)[0x030A0000].extract(image))[1]
    for row in owner['source']['parts']:
        if sha256(catalog[row['bank']][row['template']]) != row['encoded_sha256']:
            raise ValueError('Installed savings letter differs from official source')
    return owner['source']


def install(base, prior, blob, core, module, output):
    del module
    from mail_catalog import parse
    from mail_storage import evidence
    from v3_console_disk_install import reservations
    from v3_bank_install import replace_packet
    from v3_holiday_selection import refresh_receipts
    import v3_physical_resources as physical
    from v3_import_storage import jump
    equipment = copy.deepcopy(prior['equipment_resources']); bank = equipment['bank']
    if bank.get('mail') or not bank['installed'] or prior['save_codec']['format_version'] != 21:
        raise ValueError('Savings mail requires the installed format-21 account')
    if any(a < END and RAM < b for a,b in reservations(prior)):
        raise ValueError('Savings mail overlaps retained resident memory')
    old = copy.deepcopy(bank['packet']); raw = bytearray(base[old['physical']:old['physical']+old['bytes']])
    if old['ram']+old['bytes'] != RAM or sha256(raw) != old['sha256']:
        raise ValueError('Savings mail is not adjacent to its retained bank owner')
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    contract = source_contract(source)
    catalog = parse(by_vrom(base)[0x030A0000].extract(base))[1]
    for row in contract['parts']:
        if sha256(catalog[row['bank']][row['template']]) != row['encoded_sha256']:
            raise ValueError('Missing complete official savings letters')
    native = evidence(base)
    for first,last,digest in CONTRACTS:
        if sha256(core[first-CODE_RAM:last-CODE_RAM]) != digest:
            raise ValueError('Changed original savings scheduling dependency')
    rows = source.raw('l_mml_postoffice_info')
    generated = output/'bank_mail_records.S'
    write_new(generated, ('.section .rodata.bank_mail,"a",@progbits\n.balign 4\n'
        '.globl af_bank_mail_rows\naf_bank_mail_rows:\n.byte '+','.join(str(x) for x in rows)+
        '\n.globl af_bank_mail_items\naf_bank_mail_items:\n.half '+
        ','.join(str(int(row['destination_item'],16)) for row in contract['rewards'])+'\n').encode())
    symbols = bank['code']['symbols']
    bindings = dict(af_bank_send_rewards=symbols['af_bank_send_rewards'],
        af_bank_native_account=symbols['af_bank_native_account'],
        af_bank_account_mode=bank['account_mode']['address'],
        af_bank_mail_players=0x80126EC0, af_bank_mail_homes=0x8012A428,
        af_bank_home_arrangement=0x80135DFA,
        af_bank_mail_null=prior['equipment_resources']['player_travel']['compiled']['bindings']['af_pi_null_identity'],
        af_bank_mail_selected=0x80465000, af_bank_mail_town=0x800950D8,
        af_bank_mail_clear=0x8009C384, af_bank_mail_free=0x8009C534,
        af_bank_mail_copy=0x8009C67C, af_bank_mail_receipt=0x800B6A3C,
        af_bank_mail_first_delivery=0x800B7560)
    code, compiled = compile_part('bank_mail', output/'bank_mail',
        extra_sources=('runtime/mail/record.c', str(generated.relative_to(ROOT))), link_symbols=bindings)
    if len(code)>END-RAM-16:
        raise ValueError('Savings mail exceeds its owned extension')
    raw.extend(code.ljust(END-RAM-16,b'\0')+GUARD)
    mode=bank['account_mode']['address']; offset=mode-old['ram']
    if any(raw[offset:offset+4]) or mode+4!=bank['code']['bss_end']:
        raise ValueError('Savings configuration lacks its complete owned aligned word')
    raw[offset]=1
    # The retained console-visitor catalogue grows by sixteen bytes. Its two
    # parent bounds change, but that build omits the bank's whole-parent receipt.
    # Repair only that authenticated transition, never accept arbitrary changes.
    from v3_bank_resources import MENU_VROM
    parent=by_vrom(base)[MENU_VROM].extract(base)
    descriptor=bank['resources']['submenu_descriptor']
    if sha256(parent)!=descriptor['owner_sha256']:
        restored=bytearray(parent)
        for at in (0x2C94,0x2C9C):
            struct.pack_into('>I',restored,at,u32(restored,at)-16)
        if (descriptor['owner_sha256']!='7e65d57b58ba949d0a0ba8d33d26c6605accda33d0fe1dbfa681c6049ab62191' or
                sha256(restored)!=descriptor['owner_sha256'] or
                sha256(parent)!='710867c4452910ff16f6ddcc1ff7e73654f631b2a095de453178c4e78c7faa64'):
            raise ValueError('Changed complete retained menu parent')
        descriptor['owner_sha256']=sha256(parent)
    records = copy.deepcopy(prior['physical_resources']); physical.verify(base, records)
    allocation = physical.allocate(base, records, bytes(raw), 'post-office-bank-mail-GAFE01-r0',
        best_fit=True, excluded_spans=((by_vrom(base)[BLOB].pstart,by_vrom(base)[BLOB].pstart+len(blob)),))
    records.append(allocation)
    packet = dict(allocation, ram=old['ram'], crc32=zlib.crc32(raw), storage='physical-ROM')
    replace_packet(equipment,old['id'],packet)
    refresh_receipts(equipment,records,{packet['id']:raw})
    bank = equipment['bank']
    at = 0x800B76C4-CODE_RAM; before = jump(0x800B7560,link=True)
    if u32(core,at)!=before or u32(core,at+4):
        raise ValueError('Changed original initial mail delivery call')
    after = jump(compiled['symbols']['af_bank_mail_start'],link=True)
    struct.pack_into('>I',core,at,after)
    bank['mail'] = dict(installed=True,source=contract,code=compiled,
        reservation=dict(ram=RAM,bytes=END-RAM), native=native,bindings=bindings,
        hook=dict(address=0x800B76C4,before=before,after=after,delay_slot=0),
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES},
        native_delivery_tested=False,ordinary_gameplay_tested=False)
    bank['account_mode']['profile_control_installed']=True
    bank['account_mode']['initial_value']=1
    bank['pending']=['native banking, milestone delivery, and physical save/restart verification']
    bank['end']=END;bank['additional_resident_bytes']+=END-RAM
    groups=equipment['npc_extra']['events']['selection']['groups']
    groups.append(dict(id='savings-account',any_imports=[f'GAFE01-r0/item/{row["item"]}' for row in contract['rewards']],
        any_behaviours=[],fields=[dict(ram=mode,enabled=0x01000000,disabled=0)]))
    write_new(output/'bank_mail_packet.bin',raw)
    return equipment,{},dict(physical_resources=records),[(allocation,bytes(raw))]


def furniture(source,item,index,lists):
    if not any(name=='ftr_listPostoffice' for name,digest in lists):return None
    contract=source_contract(source)
    reward=next((r for r in contract['rewards'] if int(r['item'],16)==item),None)
    if reward is None:return None
    if index!=furniture_source_index(item) or lists != [('ftr_listPostoffice',sha256(source.raw('ftr_listPostoffice')))]:
        raise ValueError('Changed original savings reward identity or stock membership')
    binding=getattr(source,'bank_acquisition',None)
    if binding is None:
        from v3_furniture_pipeline import ReviewRequired
        raise ReviewRequired('acquisition needs an adapter: complete savings account and reward mail')
    return dict(donor_list=lists[0][0],donor_list_sha256=lists[0][1],catalogue_orderable=False,
        bank_acquisition=dict(route='savings',destination_item=reward['destination_item'],
            template=reward['template'],balance=reward['balance'],dependencies=[],native_delivery_installed=True))


def installed_items(report):
    bank=report.get('equipment_resources',{}).get('bank',{})
    if not bank.get('mail',{}).get('installed') or not bank.get('account_mode',{}).get('profile_control_installed'):
        return set()
    expected={r['destination_item']:r for r in bank['mail']['source']['rewards']}
    return {r['item_id'] for r in report['furniture']['imports']
        if r['item_id'] in expected and r.get('runtime_installed') and
        r.get('donor_list')=='ftr_listPostoffice' and not r.get('catalogue_orderable')}
