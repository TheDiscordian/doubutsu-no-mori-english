"""Whole leaflet reference identities and native selected-field contracts."""

from pathlib import Path
import struct

from aflib import sha256,verified_rom
from audit_mail_templates import template_fields
from gc_names import symbol_data
from gc_text import decoder_tables
from leaflet_dates import ACTORS,source
from leaflet_date_scenario import REFERENCE_FUNCTIONS
from mail_catalog import parse,verify_registered
from mail_reference import BANK_HASHES,DECODER_SHA256,transcode
from textbanks import Bank,banks

ROOT = Path(__file__).resolve().parents[1]
SALE = tuple(range(2,18))
RENEWAL = (24,25,26)
REDD = (49,50,51)
TEMPLATES = SALE+RENEWAL+REDD
FUNCTIONS = {**REFERENCE_FUNCTIONS,
    'aEvMgr_actor_regist_handbill':(136,'7472f08a3eb26a6fac9ad715af7e2422fb6f2574e73d8f202e8dda8b6433ce61'),
    'aEvMgr_actor_regist_broker_handbill':(104,'6f2efd60012ea3475a27cbbbc757c159b0671bd34af2a79dd0949277ef34e254'),
    'init_sp_bargain':(784,'a6d82c5258438b1ee9b3e45091e9a46a3c6a44c2c2b62ca190f45156bab48eeb'),
    'init_sp_broker':(620,'d1b921ec994f767c0b4f64dc4065c10de2a06b54d444b50686deb059ff5ff036'),
}


def fields(number,*,native=False):
    if number in RENEWAL+REDD: return {0,1,2}
    if number not in SALE: raise ValueError('Unapproved leaflet template')
    result = {17,18,19}
    if number == 2: result.add(7)
    elif (native and (number-2)%4 != 3) or (not native and number in (3,4,10,14)):
        result.add(0)
    return result


def verify_templates(rom,catalog,root=ROOT):
    rom = verified_rom(rom)
    if verify_registered(catalog)['catalog'] != 2:
        raise ValueError('Leaflets require unchanged immutable catalogue two')
    installed = parse(catalog)[1]
    native = {b.name:b.entries() for b in banks(rom) if b.name in ('super','mail','ps')}
    actor = {}
    for name in ACTORS: actor[name] = source(rom,name)[0]
    for name,at,expected in (('renewal',0x80959064,(24,25,26,26)),
                            ('event',0x80961C04,REDD),('event',0x80961C20,SALE),
                            ('event',0x80961C10,(0,3,4,2))):
        if struct.unpack_from('>'+str(len(expected))+'I',actor[name],at-ACTORS[name].ram) != expected:
            raise ValueError('Changed native leaflet selection table')
    rel = (root/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (root/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(rel) != '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed supplied leaflet executable')
    for name,expected in FUNCTIONS.items():
        value = symbol_data(rel,symbols,name)
        if (len(value),sha256(value)) != expected:
            raise ValueError('Changed English leaflet selection/metadata reference')
    decoder = root/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes()) != DECODER_SHA256:
        raise ValueError('Changed English leaflet decoder')
    tables = decoder_tables(decoder)
    directory = root/'build/gamecube/files/forest_1st.arc.unpacked/data'
    rows = []
    for name in ('super','mail','ps'):
        data = (directory/(name+'_data.bin')).read_bytes()
        table = (directory/(name+'_data_table.bin')).read_bytes()
        if (sha256(data),sha256(table)) != BANK_HASHES[name]:
            raise ValueError('Changed supplied complete leaflet bank')
        reference = Bank(name,0,0,data,table).entries()
        for number in TEMPLATES:
            value = transcode(reference[number],tables)
            if installed[name][number] != value:
                raise ValueError('Incomplete or changed English leaflet part')
            for raw,old in ((value,False),(native[name][number],True)):
                expected = fields(number,native=old) if name == 'mail' else set()
                if template_fields(raw) != expected:
                    raise ValueError('Changed leaflet field identities')
            rows.append({'id':f'{name}:{number:04X}',
                         'source_sha256':sha256(native[name][number]),
                         'reference_sha256':sha256(reference[number]),'encoded_sha256':sha256(value),
                         'bytes':len(value),'fields':sorted(template_fields(value))})
    return {'parts':rows,'classic_templates':list(TEMPLATES),
            'reference_functions':FUNCTIONS,
            'renewal_date':'Capture the day before planned reopening, matching complete GC closed-day wording',
            'sale_item_source':'Complete selected sixteen-byte names before native truncation; source binding required',
            'native_delivery_installed':False}
