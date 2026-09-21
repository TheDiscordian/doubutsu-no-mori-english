"""Prepare the complete donor password codec; gameplay delivery is separate."""
import json
import struct

from aflib import sha256, u32
from apply_translation import write_new
from v3_asset_loader import ROOT
from v3_holiday_rewards import compile_kernel

SOURCE_FILE='local/ac-decomp/src/game/m_mail_password_check.c'
SOURCE_SHA='aad4e6de15db2d48b579456e981c139ff1501e199227443fb4f5c4d308218405'
CODE_START,CODE_END=0x4CFA8,0x4E160
CODE_SHA='2e50485a272ebe4a91092da7d36d7e01e72b8caf5664c5216c6df8dc91917449'
SOURCES=('tools/v3_password.py','tools/v3_furniture_pipeline.py','tools/v3_holiday_rewards.py',
         'overlays/v3/password.c','overlays/v3/password.h')


def discover(source):
    # Whole REL and symbol identities are checked when Source is constructed;
    # keep the complete codec range and relocation dependencies in its receipt.
    a=source.sections[1][0]
    if sha256(source.rel[a+CODE_START:a+CODE_END])!=CODE_SHA:
        raise ValueError('Changed complete source password codec')
    functions=[];cursor=CODE_START
    while cursor<CODE_END:
        raw,receipt=source.function(cursor);functions.append(receipt);cursor+=len(raw)
    if cursor!=CODE_END:raise ValueError('Incomplete source codec function inventory')
    alphabet=source.raw('usable_to_fontnum');sub=source.raw('mMpswd_chg_code_table')
    primes=source.raw('mMpswd_prime_number')
    if (sha256(alphabet)!='81e513acbeb2fb39379ab4ea24a050a68168d205b45d378c8915fa8a59bfa7d3'
            or sha256(sub)!='0357fd40d05a2df59b5b6beaf27a6273d1531c3d9fc92e3101a7e53025b16fbe'
            or sha256(primes)!='ae340f81bf655819a675aa646917872dfb7c730abac1eb08ec4fa4070c3749df'):
        raise ValueError('Changed complete password alphabet, substitution, or primes')
    strings=[];selectors=[];dependencies=[]
    at,n=source.symbol('mMpswd_transposition_cipher_char_table')
    roots={loc-at:target for loc,target in source.pointers(at,n).items()}
    if n!=8 or roots!={i*4:source.symbol(f'mMpswd_transposition_cipher_char{i}_table')[0] for i in range(2)}:
        raise ValueError('Changed complete source cipher directory roots')
    if source.raw('key_idx$688')!=struct.pack('>2I',18,9):
        raise ValueError('Changed source transposition key positions')
    for stage in range(2):
        table=f'mMpswd_transposition_cipher_char{stage}_table'
        at,n=source.symbol(table);raw=source.raw(table)
        refs={loc-at:target for loc,target in source.pointers(at,n).items()}
        if n!=128 or set(refs)!=set(range(0,128,8)):
            raise ValueError('Incomplete source transposition directory')
        for index in range(16):
            name=f'mMpswd_transposition_cipher_char{stage}_{index}'
            start,length=source.symbol(name);value=source.raw(name)
            if refs[index*8]!=start or u32(raw,index*8+4)!=length or not 1<=length<=32:
                raise ValueError('Changed complete source cipher key binding')
            strings.append(value);dependencies.append(dict(symbol=name,offset=start,bytes=length,sha256=sha256(value)))
    at,n=source.symbol('mMpswd_select_idx_table')
    refs={loc-at:target for loc,target in source.pointers(at,n).items()}
    if n!=64 or set(refs)!=set(range(0,64,4)):raise ValueError('Incomplete source selector directory')
    for index in range(16):
        name=f'mMpswd_select_idx{index}';start,length=source.symbol(name);raw=source.raw(name)
        values=struct.unpack('>8I',raw)
        if (refs[index*4]!=start or length!=32 or len(set(values))!=8
                or any(v>19 or v in (5,13,15) for v in values)):
            raise ValueError('Invalid complete RSA/shuffle selector')
        selectors.extend(values);dependencies.append(dict(symbol=name,offset=start,bytes=length,sha256=sha256(raw)))
    prime_values=struct.unpack('>256I',primes)
    if any(p<17 or p>1667 or any(p%d==0 for d in range(2,int(p**.5)+1)) for p in prime_values):
        raise ValueError('Invalid donor RSA prime')
    # Header, alphabet, substitution, 16-bit primes, byte selectors, key directory.
    offset=1120;directory=bytearray();text=bytearray()
    for value in strings:
        directory.extend(struct.pack('>HH',offset+len(text),len(value)));text.extend(value)
    data=(struct.pack('>4s14H',b'AFPW',1,offset+len(text),64,256,16,32,offset,len(text),0,0,0,0,0,0)
          +alphabet+sub+struct.pack('>256H',*prime_values)+bytes(selectors)+directory+text)
    if len(data)!=offset+len(text):raise ValueError('Incomplete password table packet')
    lists=[]
    for name in ('ftr_listHomePage','carpet_listHomePage','wall_listHomePage'):
        raw=source.raw(name);items=list(struct.unpack('>'+str(len(raw)//2)+'H',raw))
        if not items or items[-1] or any(not i for i in items[:-1]):
            raise ValueError('Invalid complete HomePage acquisition list')
        lists.append(dict(symbol=name,source_items=[f'{i:04X}' for i in items[:-1]],sha256=sha256(raw)))
    return data,dict(format='AFV3-PASSWORD-CODEC-1',bytes=len(data),sha256=sha256(data),
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()),
        code_start=CODE_START,code_end=CODE_END,code_sha256=CODE_SHA,functions=functions,
        tables=dependencies,source_lists=lists,text_length=28,payload_bytes=21,meaningful_payload_bytes=20,
        name_field_bytes=8,types=6,ascii_hash_to_donor=209,zero_alias='O',one_alias='l',
        runtime_installed=False,keyboard_installed=False,eligibility_installed=False,acquisition_installed=False)


def prepare(source,output):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):raise ValueError('Use a fresh ignored password output')
    data,report=discover(source)
    output.mkdir(parents=True);write_new(output/'password-tables.bin',data)
    report['kernel']=compile_kernel(output,name='password')
    report['sources']={p:sha256((ROOT/p).read_bytes()) for p in SOURCES}
    write_new(output/'password.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    return report
