"""Complete native shop counters, with caller-bound ten-byte capacity."""

from dataclasses import dataclass
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from fortune_strings import source_entries, STRING_RELOCATION
from textcodec import encode, tokenize

FIRST, END = 0x566, 0x5DE
BASES = tuple(FIRST+15*i for i in range(8))
IDS = tuple(f'string:{i:04X}' for i in range(FIRST, END))
VALUES_SHA256 = '9804ff5a0878bbcc15279c11e5a2da4d33b435cbe0f88eda4e42b7abaa7f6ba1'
REFERENCE_SHA256 = 'f500d8011a7479422487158609a5df3540e430f61f87e73c9fdef0764c159205'
GRAPH_SHA256 = 'b3ce483e7d650ac8cb1580895a90ce197b40b7de5cbea1faa8033d5cfab7c156'
GRAPH_OFFSETS = (0,64,68,104,136,392,424,488,552,560,572,628,632,728,760,764)
# Pointer-bounded storage spans include possible alignment bytes; these are not
# claims that every index represents a valid item. Native fixtures use real IDs.
CATEGORY_SPANS = (64,4,36,32,256,32,64,64,8,12,56,4,96,32,4,4)
HELPERS = ((0x8009D6D0,0x8009D820,'24668491725962fd96b0a4dde298851aa9ed1400c6f7c9b7be9afc0d3f682332'),
           (0x8009D1F0,0x8009D200,'e4e54e5f3fc74caca37c6c0fdda0b5684e6e68d753495d23a868e75faf6af1f3'))


@dataclass(frozen=True)
class Shop:
    vrom: int
    ram: int
    relocation: int
    handler: int
    pointers: int
    file_bytes: int
    sections: tuple
    file_sha256: str
    relocation_sha256: str

    @property
    def resident_bytes(self):
        return self.file_bytes+self.sections[3]


SHOPS = {
    'cranny': Shop(0x8ADF40,0x809CA750,0x8B2140,0x809CB044,0x809CE5F8,16896,(14816,2064,16,0,342),
        'cffa2de7e3850b8608b806b75e420afb8271a0c803cb08c183e863e04132ee5c',
        'aca13f72fb84a95f73f8a173407f45579541b6254a290e59e78c18013f0f6fc4'),
    'conv': Shop(0x889440,0x809A5C30,0x88D780,0x809A6598,0x809A9C18,17216,(14928,2272,16,0,345),
        '4491f4bf651c5352d500f9efe69dc146380c217df7c1fcfde9e70b8412957cd1',
        '45d0548a6d6567c5bbd87f6977dd2857676e106fffe082cabf38f0f7476e498d'),
    'depart': Shop(0x88DD00,0x809AA4F0,0x892070,0x809AAEB8,0x809AE50C,17264,(15056,2192,16,0,348),
        '4edffe212239bb03eb6beb02993c380faf95d54f7cd53178938edd27ce8eebd5',
        '33ac536b54d38ec0ac45b78a528bb0bb0b3d9aa31ce7e4730e126e21c93931c4'),
    'mame': Shop(0x89A1B0,0x809B69B0,0x8A0B50,0x809B73C0,0x809BCFE0,27040,(14208,12816,16,16,381),
        '8ce80942bc3b2841364a3f4d5b189b7e2ddd0585751c2c96f2909b2184951c20',
        '0c198ae38e0a1d62312cc52d0589312570a67acaf22a8413d004b33d1b38fac9'),
    'super': Shop(0x8B2CE0,0x809CF4F0,0x8B7410,0x809CFF74,0x809D38CC,18224,(15216,2992,16,0,354),
        'd48e88f75a3916b055a33373e39def10eccc0d84ac39bab1844afdeccd5d2770',
        'a4051e054c92c163a10d61ebad86c8476d4b40f06992275ed3587f718c0ab67b'),
}

# Original relocation constants address a price table using the FULL item ID
# shifted by two. The effective 2F00..2F03 destinations are inside each actor.
PRICE_BIASES = {0x8ADF40:0x809C2BD0,0x889440:0x8099E1F0,0x88DD00:0x809A2AE4,
                0x89A1B0:0x809B15CC,0x8B2CE0:0x809C7EA4}


@dataclass(frozen=True)
class ShopUnitPermit:
    source_sha256: str
    encoded_sha256: str


def group_hash(values):
    return sha256(b''.join(struct.pack('>H',len(value))+value for value in values))


def verify_values(values, info):
    if (len(values) != 120 or group_hash(values) != VALUES_SHA256
            or any(len(value)>10 or any(t.kind!='text' for t in tokenize(value,info)) for value in values)):
        raise ValueError('Shop units require all 120 complete native-family English values')


def verify_shop(spec, data, reloc):
    if (spec not in SHOPS.values() or len(data)!=spec.file_bytes
            or sha256(data)!=spec.file_sha256 or sha256(reloc)!=spec.relocation_sha256
            or struct.unpack_from('>5I',reloc)!=spec.sections):
        raise ValueError('Changed native shop actor or relocation')
    at=spec.pointers-spec.ram
    pointers=struct.unpack_from('>16I',data,at)
    if (pointers!=tuple(spec.pointers-0x300+offset for offset in GRAPH_OFFSETS)
            or sha256(data[at-0x300:at])!=GRAPH_SHA256
            or struct.unpack_from('>8I',data,at+0xA0)!=BASES):
        raise ValueError('Changed native shop category/counter mapping')
    # Native quantity is converted to a zero-based index before either path.
    words={0:0x27BDFFC8,0x38:0x24C6FFFF,0x48:0x27A4002C,0x9C:0x2405000A,
           0xA0:0x0C030FDC,0xB4:0x24050008,0xB8:0x27A6002C,
           0xBC:0x0C0275B4,0xC0:0x2407000A,0xC8:0x27BD0038}
    for offset,expected in words.items():
        if struct.unpack_from('>I',data,spec.handler-spec.ram+offset)[0]!=expected:
            raise ValueError('Changed shop count arithmetic or ten-byte temporary/free field')
    price_offset=PRICE_BIASES[spec.vrom]+(0x2F00<<2)-spec.ram
    if struct.unpack_from('>4I',data,price_offset)!=(10,50,100,0):
        raise ValueError('Changed full-item-indexed native turnip price table')
    return tuple(data[p-spec.ram:p-spec.ram+length] for p,length in zip(pointers,CATEGORY_SPANS))


def verify_callers(rom, replacements=None):
    files=by_vrom(rom);replacements=replacements or {}
    for spec in SHOPS.values():
        verify_shop(spec,replacements.get(spec.vrom,files[spec.vrom].extract(rom)),
                    replacements.get(spec.relocation,files[spec.relocation].extract(rom)))
    code=replacements.get(CODE_VROM,files[CODE_VROM].extract(rom))
    for start,end,digest in HELPERS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM])!=digest:
            raise ValueError('Changed shop free-string capacity or window consumer')


def unit_id(spec, data, reloc, item, count):
    categories=verify_shop(spec,data,reloc)
    if type(count) is not int or not 1<=count<=15 or type(item) is not int or not 0<=item<=0xFFFF:
        raise ValueError('Shop fixture requires a native item and count from one through fifteen')
    family=0
    if item>>12==2:
        category,index=(item>>8)&15,item&255
        if index>=len(categories[category]):
            raise ValueError('Shop item index exceeds its pointer-bounded category storage')
        family=categories[category][index]
    return BASES[family]+count-1


def candidates(rom, references, inventory, info):
    verify_callers(rom)
    originals=source_entries(rom);result={};values=[]
    for index,id in enumerate(IDS):
        original=originals[FIRST+index];row=inventory.get(id)
        if not row or row['id']!=id or row['source_sha256']!=sha256(original):
            raise ValueError('Stale native shop-unit inventory')
        if index<105:
            reference=references.get(id)
            if not reference or reference['id']!=id:
                raise ValueError('Missing complete English shop-unit reference')
            value=encode(reference['text'],info)
            if reference['sha256']!=sha256(value) or encode(row['legacy'],info)!=value:
                raise ValueError('Changed shop-unit reference or complete legacy agreement')
            edit={'translation':reference['text'],'status':'mechanically_validated_candidate_not_reviewed',
                  'provenance':{'source':'user-supplied GAFE01 revision 0 disc','reference_id':id,
                    'reference_sha256':reference['sha256'],
                    'match_basis':'native_shop_counter_family_and_complete_legacy_agreement'}}
        else:
            # Native category 29 index zero is the sole sapling, not turnips.
            text='sapling' if index==105 else 'saplings';value=encode(text,info)
            edit={'translation':text,'status':'draft','shop_unit_kind':'native_sapling_counter',
                  'provenance':'Original English translation of the native sapling counter',
                  'notes':'Native category 29 index zero selects this family. The same-ID English turnip counter describes a different item; retain singular/plural sapling meaning.'}
        values.append(value)
        result[id]={'id':id,'source_sha256':sha256(original),'control_policy':'exact',**edit}
    if group_hash(values[:105])!=REFERENCE_SHA256:
        raise ValueError('Incomplete seven-family English counter reference')
    verify_values(values,info)
    return result


def permits(rom, edits, info):
    verify_callers(rom);originals=source_entries(rom)
    selected=[e for e in edits if e.get('id') in IDS]
    if len(selected)!=120 or {e['id'] for e in selected}!=set(IDS):
        raise ValueError('English shop units require the complete unique 120-record group')
    by_id={e['id']:e for e in selected}
    values=[encode(by_id[id]['translation'],info) for id in IDS]
    verify_values(values,info);result={}
    for id,value in zip(IDS,values):
        digest=sha256(originals[int(id[7:],16)])
        if by_id[id].get('source_sha256')!=digest or by_id[id].get('control_policy','exact')!='exact':
            raise ValueError('Changed shop-unit source or control policy')
        result[id]=ShopUnitPermit(digest,sha256(value))
    return result
