"""Bind selected house-model palettes to the actual native home colour."""
import json
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from v3_asset_loader import ROOT
from v3_tent_model import native_contract as palette_contract
from v3_villager_art import native_palette

CATEGORY='selected-palette-fade-assets'
BLOCKS=(
    ('field_id',0x80087C88,20,'404f3a26d8ea043750074135ccc347a02f695258299b86315e8c89bcfe1794ba'),
    ('home_arrangement',0x80094BF4,28,'38b7988cd8bb517b6904ecaa2845f73022f20e662a2e1bf82bd7ce0162424176'),
    ('home_initialization',0x80094520,368,'f567fa8e97fffe0beec1b6177054c2c2eff4f0b36325d67ddc2621eda7aaa61a'),
    ('home_upgrade_colour',0x80094A90,336,'f959b3ee7cabbdf4db3b19bfae7862c6375157d6973fc61d47e1e10ec5cb347b'),
    ('current_player_home',0x800946D0,116,'c060162287b6282b01c432b74f604e5401ca54fa05de1cc0d851064f203b376a'),
)
SOURCES=('tools/v3_furniture_roofs.py','overlays/v3/room_palettes.c','overlays/v3/tent_model.c')


def lifecycle(profile):
    adapter=profile.get('callback_adapter',{})
    if (adapter.get('category')!=CATEGORY or adapter.get('palette_count')!=12 or
            set(adapter.get('functions',{}))!={'create','move','draw','destroy'} or
            adapter.get('selection')!='current-room-home-or-preview-player-roof'):
        raise ValueError('Unimplemented selected house-colour native lifecycle')
    return dict(category=CATEGORY,mode=7,palette_count=12,selection=adapter['selection'],
        source_selector=json.loads(json.dumps(adapter['selector'])),private_fade_offset=0x1A4,
        private_colour_offset=0x1A8,heap_bytes=0,palette_lifetime='submitted graphics frame')


def profile_lifecycle(profile,installed):
    return installed is not None and installed==lifecycle(profile)


def native_contract(source,base):
    """Check compiled consumers, not decompilation field names or guessed offsets."""
    original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
    contract=palette_contract(original,base,expected_sha=sha256(base))
    contract.pop('current_source_sha256')
    files=by_vrom(base);core=files[CODE_VROM].extract(base);blocks=[]
    for name,address,n,digest in BLOCKS:
        if sha256(core[address-CODE_RAM:address-CODE_RAM+n])!=digest:
            raise ValueError('Changed native house-colour dependency: '+name)
        blocks.append(dict(name=name,address=address,bytes=n,sha256=digest))
    house=files[0x8D4A20].extract(base)[:0x238]
    if sha256(house)!='ca848eaa988cba68ce912220fb783e05e037e21236c5fe103763db20e8ec0209':
        raise ValueError('Changed native exterior home-colour constructor')
    # The real native exterior index is 25 + homes[slot].byte_24. Its summer
    # and winter pointer tables retain the same twelve colour identities.
    pointers=files[0xD5D000].extract(base);palettes=files[0xD5B000].extract(base)
    table=source.raw('fFTR_myhome_off_pal_table')
    model=b''.join(native_palette(table[i:i+32]) for i in range(0,len(table),32))
    correspondence=[]
    for index,letter in enumerate('abcdefghijkl'):
        entry=dict(native_index=index,donor_index=index,seasons=[])
        for season,table_at in (('s',8),('w',0x174)):
            pointer=struct.unpack_from('>I',pointers,table_at+(25+index)*4)[0]
            at=pointer&0xFFFFFF
            if pointer>>24!=6 or at+32>len(palettes):
                raise ValueError('Invalid native roof-palette pointer')
            donor=native_palette(source.raw('obj_'+season+'_myhome_'+letter+'_pal'))
            # Summer roof shades occupy 10..12, versus furniture 11..13.
            # Winter covers the first two shades with snow; shade 12 retains
            # the colour identity. The full exterior colours except the first
            # transparent entry match the corresponding official palette.
            first=20 if season=='s' else 24
            if (palettes[at+2:at+32]!=donor[2:32] or
                    donor[first:26]!=model[index*32+first+2:index*32+28]):
                raise ValueError('Native/donor roof colour ordering differs')
            entry['seasons'].append(dict(season=season,pointer=pointer,
                native_sha256=sha256(palettes[at:at+32]),donor_sha256=sha256(donor)))
        correspondence.append(entry)
    return dict(palette=contract,blocks=blocks,exterior_constructor_sha256=sha256(house),
        common=0x80126EA0,player_offset=0x10003,homes_offset=0x3588,home_stride=0xB48,
        roof_offset=0x24,field_pointer=0x8013A248,player_field_type=0x6000,
        gameplay_control=1,cottage='absent from native N64 scenes',
        colour_correspondence=correspondence)
