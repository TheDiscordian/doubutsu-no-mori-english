"""Convert reviewed static GC furniture into self-contained native N64 objects.

This builds local assets, not selectable or playable imports. Furniture loading,
item IDs, acquisition, placement, and saved-item readers are separate runtime work.
"""
import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import struct

from aflib import sha256
from gc_names import rel_sections
from map_artwork import compile_commands
from stall_model_source import packed
from title_assets import model_texture_shape, pack4, untile
from toolchain import IMAGE
from v3_import_catalog import DONOR, REL_SHA, ROOT, SYMBOLS_SHA, read_donor
from v3_villager_art import data_pointers, native_palette, normalise_vertex_flags, symbol_span

SEGMENT = 0x06000000
CONVERTER_VERSION = 12

# Complete compatible RDP expressions, selected by material commands, not IDs.
# These use one texture and retain source alpha; none introduces TEXEL1,
# noise, keying, or an unprovided external render dependency.
TRANSLUCENT_COMBINERS = {
    (0xFC11FE04,0xFF0FF3FF): ('TEXEL0','0','PRIMITIVE','0','0','0','0','TEXEL0',
        'COMBINED','0','SHADE','0','COMBINED','0','PRIMITIVE','0'),
    (0xFC341604,0x5FFEFFF8): ('PRIMITIVE','ENVIRONMENT','TEXEL0_ALPHA','ENVIRONMENT',
        'TEXEL0','0','PRIMITIVE','0','COMBINED','0','SHADE','0','0','0','0','COMBINED'),
    (0xFC119C04,0xFFFFF7F8): ('TEXEL0','0','PRIMITIVE','0','TEXEL0','0','PRIM_LOD_FRAC','PRIMITIVE',
        'COMBINED','0','SHADE','0','0','0','0','COMBINED'),
}

# Scrolling models supply every referenced tile, with the second cycle's texture
# input retaining the second tile. Expressions match the donor model sources.
SCROLL_COMBINERS = {
    (0xFC609C04,0xFFFDF7F8): ('1','0','TEXEL0','PRIMITIVE','TEXEL0','0','PRIM_LOD_FRAC','PRIMITIVE',
        'COMBINED','0','SHADE','0','0','0','0','COMBINED'),
    (0xFC30FE03,0x5F3AF3F0): ('PRIMITIVE','ENVIRONMENT','TEXEL0','ENVIRONMENT','0','0','0','TEXEL0',
        'COMBINED','0','PRIMITIVE','0','TEXEL0','1','PRIM_LOD_FRAC','COMBINED'),
    (0xFC309A04,0x5F06FFFF): ('PRIMITIVE','ENVIRONMENT','TEXEL0','ENVIRONMENT','TEXEL0','0','ENVIRONMENT','0',
        'COMBINED','0','SHADE','0','COMBINED','0','TEXEL0','0'),
    (0xFC254C04,0x1FFCFFF8): ('TEXEL1','TEXEL0','PRIMITIVE_ALPHA','TEXEL0','SHADE','0','PRIM_LOD_FRAC','0',
        'COMBINED','0','SHADE','0','0','0','0','COMBINED'),
    (0xFC3097FF,0x5F06FE3F): ('PRIMITIVE','ENVIRONMENT','TEXEL0','ENVIRONMENT','TEXEL0','0','PRIMITIVE','0',
        '0','0','0','COMBINED','COMBINED','0','TEXEL0','0'),
    (0xFC30FE04,0x5F3AFDF0): ('PRIMITIVE','ENVIRONMENT','TEXEL0','ENVIRONMENT','0','0','0','1',
        'COMBINED','0','SHADE','0','TEXEL0','1','PRIM_LOD_FRAC','COMBINED'),
    (0xFC3217FF,0xFF07FE3F): ('PRIMITIVE','0','SHADE','0','TEXEL0','0','PRIMITIVE','0',
        '0','0','0','COMBINED','COMBINED','0','TEXEL0','0'),
}


@dataclass(frozen=True)
class Pilot:
    key: str
    item: int
    name: str
    stem: str
    profile: str
    textures: tuple
    lighting_map: int
    vertex_count: int = 36
    models: tuple = (('opaque', '_model_b_model', 0, 0x98),
                     ('translucent', '_model_a_model', 8, 0x68))
    mirrored_s: bool = False
    height: float = 18.0
    garden: bool = False
    vertex_symbol: str | None = None
    western: bool = False
    texture_symbols: tuple = ()
    model_symbols: tuple = ()
    shape: int = 4
    collision: int = 0
    large_western: bool = False
    water_layer: bool = False
    camping: bool = False
    contact_action: int = 0
    school: bool = False


PILOTS = (
    Pilot('haz-mat-barrel', 0x3224, 'haz-mat barrel', 'int_iku_hazardous',
          'iam_iku_hazardous_top', (('mark', 32, 32), ('top', 32, 32), ('yoko', 64, 32)), 1),
    Pilot('oil-drum', 0x32B8, 'oil drum', 'int_iku_orange', 'iam_iku_orange',
          (('b', 32, 32), ('a', 32, 32), ('c', 64, 32)), 0),
)

# Keep the original loader's default two-object batch unchanged. These reviewed
# opaque-only profiles form a separate batch until their item runtime is installed.
CONSTRUCTION_PILOTS = (
    Pilot('wet-roadway-sign', 0x31F4, 'wet roadway sign', 'int_iku_slip', 'iam_iku_slip',
          (('all', 32, 64),), 0, 94, (('opaque', '_model_model', 0, 0xC0),)),
    Pilot('detour-sign', 0x31F8, 'detour sign', 'int_iku_ukai', 'iam_iku_ukai',
          (('all', 64, 32),), 1, 94, (('opaque', '_mode_a_model', 0, 0xC0),)),
    Pilot('men-at-work-sign', 0x31FC, 'men at work sign', 'int_iku_work', 'iam_iku_work',
          (('all', 32, 64),), 0, 94, (('opaque', '_model_model', 0, 0xC0),)),
    Pilot('flagman-sign', 0x320C, 'flagman sign', 'int_iku_flagman', 'iam_iku_flagman',
          (('all', 32, 64),), 0, 94, (('opaque', '_model_model', 0, 0xC0),)),
    Pilot('jersey-barrier', 0x3214, 'jersey barrier', 'int_iku_jersey', 'iam_iku_jersey',
          (('mae', 32, 32), ('yoko', 16, 32)), 0, 44,
          (('opaque', '_model_model', 0, 0xB0),), True),
    Pilot('speed-sign', 0x3218, 'speed sign', 'int_iku_reducespeed', 'iam_iku_reducespeed',
          (('all', 32, 64),), 0, 77, (('opaque', '_model_model', 0, 0xC0),)),
    Pilot('saw-horse', 0x322C, 'saw horse', 'int_iku_sawhorsev', 'iam_iku_sawhousev',
          (('a', 32, 32), ('b', 32, 32), ('c', 16, 32), ('d', 16, 32)), 0, 103,
          (('opaque', '_model_model', 0, 0x138),), True),
)
GARDEN_PILOTS = (
    Pilot('birdhouse', 0x3268, 'birdhouse', 'int_yaz_b_house', 'iam_yaz_b_house',
          (('kabu', 16, 32), ('kabe01', 32, 40), ('kabe02', 32, 40),
           ('ita', 32, 16), ('pole', 16, 32)), 1, 79,
          (('opaque', '_body_model', 0, 0x158),), height=42.43, garden=True),
    Pilot('bird-feeder', 0x3284, 'bird feeder', 'int_yaz_b_feeder', 'iam_yos_b_feeder',
          (('pole', 16, 56), ('ana', 16, 48), ('ura', 16, 48), ('wood', 16, 16),
           ('yane', 16, 16), ('wa', 32, 32)), 1, 65,
          (('opaque', '_body_model', 0, 0x178),), height=42.43, garden=True,
          vertex_symbol='int_yos_b_feeder_v'),
    Pilot('mr-flamingo', 0x3290, 'Mr. Flamingo', 'int_yos_flamingo', 'iam_yos_flamingo',
          (('kao', 64, 32), ('dou', 64, 32)), 1, 69,
          (('opaque', '_body_model', 0, 0x110),), height=42.43, garden=True),
    Pilot('mailbox', 0x3294, 'mailbox', 'int_yos_mailbox', 'iam_yos_mailbox',
          (('mae', 32, 48), ('ana', 32, 16), ('sokumen', 32, 48), ('rabel', 32, 16)),
          1, 52, (('opaque', '_body_model', 0, 0xF8),), height=42.43, garden=True),
    Pilot('garden-gnome', 0x32A0, 'garden gnome', 'int_yos_gnome', 'iam_yos_gnome',
          (('all', 64, 64),), 1, 72,
          (('opaque', '_body_model', 0, 0x150),), height=42.43, garden=True),
    Pilot('mrs-flamingo', 0x32A4, 'Mrs. Flamingo', 'int_yos_flamingo2', 'iam_yos_flamingo2',
          (('kao', 64, 32), ('dou', 64, 32)), 1, 69,
          (('opaque', '_body_model', 0, 0x110),), height=42.43, garden=True),
)
WESTERN_PILOTS = (
    Pilot('tumbleweed', 0x32B0, 'tumbleweed', 'int_iku_tumble', 'iam_iku_tumble',
          (('', 64, 64),), 0, 53, (('opaque', '_model', 0, 0xB8),)),
    Pilot('cow-skull', 0x32B4, 'cow skull', 'int_iku_cow', 'iam_iku_cow',
          (('5', 16, 32), ('1', 64, 32), ('4', 32, 16), ('3', 16, 32), ('2', 32, 16)),
          0, 54, (('opaque', '_model', 0, 0x130),),
          texture_symbols=(('1', 'int_iku_cow1_tex_txt'),)),
    Pilot('saddle-fence', 0x32BC, 'saddle fence', 'int_iku_saku_a', 'iam_iku_saku_a',
          (('b', 16, 16), ('a', 32, 32), ('c', 16, 16), ('h', 16, 32),
           ('g', 64, 32), ('f', 16, 16), ('d', 16, 32), ('e', 16, 32)),
          0, 90, (('opaque', '_model_b_model', 0, 0x128),
                  ('opaque1', '_model_a_model', 4, 0xC8)), western=True),
    Pilot('western-fence', 0x32C0, 'western fence', 'int_iku_saku_b', 'iam_iku_saku_b',
          (('b', 16, 16), ('a', 32, 32), ('c', 16, 16)), 0, 42,
          (('opaque', '_model_model', 0, 0xC8),)),
    Pilot('desert-cactus', 0x3328, 'desert cactus', 'int_yos_cactus', 'iam_yos_cactus',
          (('bou', 64, 32),), 0, 56, (('opaque', '_obj_model', 0, 0xB0),), height=42.43),
    Pilot('wagon-wheel', 0x3330, 'wagon wheel', 'int_yos_wheel', 'iam_yos_wheel',
          (('nakatyu', 32, 16), ('tyu', 16, 16), ('bo', 64, 8), ('sotowa', 32, 32)),
          0, 56, (('opaque', '_obj_model', 0, 0x118),), height=42.43),
    Pilot('well', 0x3334, 'well', 'int_iku_ido', 'iam_iku_ido',
          (('ab', 32, 32), ('i', 16, 16), ('h', 16, 16), ('g', 16, 16), ('f', 32, 32),
           ('e', 16, 16), ('c', 16, 16), ('b', 16, 32), ('j', 32, 8), ('d', 16, 16)),
          0, 112, (('opaque', '_model', 0, 0x1D8),), western=True),
)
LARGE_WESTERN_PILOTS = (
    Pilot('watering-trough', 0x32C4, 'watering trough', 'int_yaz_tub', 'iam_yaz_tub',
          (('wood2', 32, 32), ('wood', 64, 32), ('water', 32, 16)), 2, 88,
          (('opaque', '_body_model', 0, 0xC8), ('translucent', '_water_model', 8, 0x58)),
          height=42.43, shape=3, collision=1, water_layer=True,
          texture_symbols=(('wood2', 'int_yaz_tub_wood2_txt'), ('wood', 'int_yaz_tub_wood_txt'),
                           ('water', 'int_yaz_tub_water_4i4_pic_i4'))),
    Pilot('covered-wagon', 0x32D4, 'covered wagon', 'int_yaz_wagon', 'iam_yaz_wagon',
          (('wood', 32, 32), ('jiku', 8, 8), ('horo2', 24, 24), ('horo', 48, 32),
           ('wheel', 32, 32)), 0, 93, (('opaque', '_body_model', 0, 0x140),),
          height=42.43, shape=3, collision=1,
          model_symbols=(('opaque', 'int_wagon_body_model'),)),
    Pilot('storefront', 0x32D8, 'storefront', 'int_yos_terrace', 'iam_yos_terrace',
          (('yuka', 32, 32), ('yane', 32, 32), ('yuka_yoko', 16, 8), ('kabe', 32, 32),
           ('enshita', 16, 8)), 0, 112, (('opaque', '_obj_model', 0, 0x198),),
          height=42.43, shape=3, collision=1, large_western=True),
)
CAMPING_PILOTS = (
    Pilot('kayak', 0x3364, 'kayak', 'int_ike_tent_kayak01', 'iam_ike_tent_kayak01',
          (('topr', 48, 16), ('topf', 48, 16), ('under', 16, 16),
           ('chair', 32, 16), ('pab', 64, 16)), 0, 46,
          (('opaque', '_on_model', 0, 0x100), ('opaque1', '_onT_model', 4, 0x80)),
          height=15.7, shape=3, collision=1, camping=True,
          texture_symbols=tuple((n, 'int_ike_tent_kayak_' + n) for n in
                                ('topr', 'topf', 'under', 'chair', 'pab'))),
    Pilot('backpack', 0x3370, 'backpack', 'int_ike_tent_knap01', 'iam_ike_tent_knap01',
          (('frontside', 32, 8), ('top', 32, 16), ('base', 16, 32), ('topback', 32, 16),
           ('side', 32, 8), ('back', 16, 32), ('front', 16, 32), ('topside', 16, 16)),
          0, 100, (('opaque', '_model', 0, 0x1F8),), height=15.7, camping=True,
          texture_symbols=tuple((n, 'int_ike_tent_knap_' + n + '_txt') for n in
              ('frontside', 'top', 'base', 'topback', 'side', 'back', 'front', 'topside'))),
    Pilot('lantern', 0x339C, 'lantern', 'int_tak_tent_lamp', 'iam_tak_tent_lamp',
          (('', 16, 64),), 0, 70, (('opaque', '_offT_model', 0, 0xD8),), camping=True,
          texture_symbols=(('', 'int_tak_tent_lamp_tex'),),
          model_symbols=(('opaque', 'obj_tent_lamp_offT_model'),)),
    Pilot('cooler', 0x33A4, 'cooler', 'int_tak_tent_box', 'iam_tak_tent_box',
          (('1', 32, 64), ('2', 16, 16)), 0, 65, (('opaque', '_on_model', 0, 0xD8),), camping=True,
          texture_symbols=(('1', 'int_tak_tent_box_1_tex'), ('2', 'int_tak_tent_box_2_tex'))),
    Pilot('mountain-bike', 0x33A8, 'mountain bike', 'int_ike_tent_bike01', 'iam_ike_tent_bike01',
          (('tire1', 32, 32), ('tire2', 32, 8), ('pedal1', 16, 8), ('tire3', 32, 16),
           ('handle2', 32, 8), ('frame2', 32, 8), ('handle1', 32, 8), ('chiar1', 16, 8),
           ('chiar2', 16, 8), ('frame1', 64, 32)), 0, 105,
          (('opaque', '_model', 0, 0x268),), height=15.7, shape=3, collision=1, camping=True,
          texture_symbols=tuple((n, 'int_ike_tent_bike_' + n + '_tex_txt') for n in
              ('tire1', 'tire2', 'pedal1', 'tire3', 'handle2', 'frame2', 'handle1', 'chiar1', 'chiar2', 'frame1'))),
    Pilot('sleeping-bag', 0x33AC, 'sleeping bag', 'int_ike_tent_sleepbag01', 'iam_ike_tent_sleepbag01',
          (('side1', 64, 32), ('in1', 16, 16)), 0, 27, (('opaque', '_model', 0, 0xB0),),
          height=15.7, shape=3, collision=1, camping=True,
          texture_symbols=(('side1', 'int_ike_tent_sleepbag_side1_tex_txt'),
                           ('in1', 'int_ike_tent_sleepbag_in1_tex_txt'))),
    Pilot('propane-stove', 0x33B0, 'propane stove', 'int_nog_burner', 'iam_nog_burner',
          (('top', 16, 64), ('side', 32, 64), ('gas', 16, 32)), 0, 111,
          (('opaque', '_model', 0, 0x150),), height=15.7, camping=True,
          texture_symbols=tuple((n, 'int_nog_burner_' + n + '_tex') for n in ('top', 'side', 'gas'))),
)
SCHOOL_DESKS = (
    Pilot('lefty-desk', 0x3200, 'lefty desk', 'int_hos_deskL', 'iam_hos_deskL',
          (('', 64, 64),), 0, 89, (('opaque', '_model_model', 0, 0xF0),), contact_action=1, school=True),
    Pilot('righty-desk', 0x3204, 'righty desk', 'int_hos_deskR', 'iam_hos_deskR',
          (('', 64, 64),), 0, 97, (('opaque', '_model_model', 0, 0x100),), contact_action=1, school=True),
    Pilot('teachers-desk', 0x3220, "teacher's desk", 'int_hos_Tdesk', 'iam_hos_Tdesk',
          (('body', 32, 32), ('hiki', 32, 32), ('top', 32, 32), ('side', 16, 32)),
          0, 32, (('opaque', '_base_model', 0, 0x110),), school=True,
          height=30.5, shape=3, collision=1,
          texture_symbols=tuple((n, 'int_hos_T_desk_' + n + '_tex_txt')
                                for n in ('body', 'hiki', 'top', 'side'))),
)
REVIEWED = (PILOTS + CONSTRUCTION_PILOTS + GARDEN_PILOTS + WESTERN_PILOTS
            + LARGE_WESTERN_PILOTS + CAMPING_PILOTS + SCHOOL_DESKS)


def verify_sources(rel, symbols):
    if sha256(rel) != REL_SHA or sha256(symbols) != SYMBOLS_SHA:
        raise ValueError('Furniture conversion requires the pinned English donor and symbols')


def scalar_profile(pilot):
    # Height, scale, exact shape/collision, rotation, lighting, contact,
    # padding, and interaction. No rig, texture animation, or callback table.
    return struct.pack('>ff6BH', pilot.height, 0.01, pilot.shape, pilot.collision,
                       0, pilot.lighting_map, pilot.contact_action, 0, 0)


def parse_model(raw, start, pointers, palette, textures, vertex, vertex_size, *, speed_bag=False,
                accessory=False, mirrored_s=False, garden=False, western=False,
                large_western=False, water=False, camping=False, tent=False,
                campfire_body=False, fire_effect=0, school=False, static_materials=False,
                palette_bindings=None, palette_fade=False, joint_matrices=0,
                inherited_palette_slot=None, inherited_vertices=0, material_bindings=None, scrolling=None):
    """Decode supported static materials and explicit dynamic dependencies, never GX loads."""
    if not raw or len(raw) % 8 or sum(map(bool, (speed_bag, accessory, mirrored_s,
                                              garden, western, large_western, water, camping,
                                              tent, campfire_body, fire_effect, school, static_materials))) > 1 or fire_effect not in (0, 1, 2):
        raise ValueError('Incomplete furniture display list')
    palette_bindings = {} if palette_bindings is None else palette_bindings
    if inherited_palette_slot is not None and (
            type(inherited_palette_slot) is not int or not 0 <= inherited_palette_slot <= 15
            or not static_materials or palette or palette_bindings or palette_fade):
        raise ValueError('Inherited palette requires an exclusive bounded static caller binding')
    if (type(inherited_vertices) is not int or not 0 <= inherited_vertices <= 32
            or inherited_vertices and (not static_materials or joint_matrices
                                      or vertex_size != inherited_vertices * 16)):
        raise ValueError('Inherited vertices require a complete bounded caller array')
    if (type(joint_matrices) is not int or not 0 <= joint_matrices <= 255
            or joint_matrices and not static_materials):
        raise ValueError('Joint matrices require a bounded shared skeleton material')
    material_bindings={} if material_bindings is None else material_bindings
    if scrolling is not None and (not static_materials or material_bindings or palette_fade or palette_bindings or
            inherited_palette_slot is not None or set(scrolling)!={'segment','dimensions'} or
            scrolling['segment'] not in (0x08000000,0x09000000) or
            not 1<=len(scrolling['dimensions'])<=2 or
            any(len(shape)!=2 or any(type(n) is not int or n<8 or n>64 or n&(n-1) for n in shape)
                for shape in scrolling['dimensions'])):
        raise ValueError('Invalid complete scrolling-material binding')
    if material_bindings and (not static_materials or palette_fade or palette_bindings or
            inherited_palette_slot is not None or
            any(address not in (0x08000000,0x09000000) or kind not in ('texture','palette') or
                type(target) is not int or target<0
                for address,(kind,target) in material_bindings.items())):
        raise ValueError('Invalid dynamic material-frame bindings')
    if palette_fade and (not static_materials or palette_bindings):
        raise ValueError('Palette fade requires the shared materials and no constant binding')
    if palette_bindings and (not static_materials or set(palette_bindings) != {0x08000000}
                             or any(p not in palette for p in palette_bindings.values())):
        raise ValueError('Unsupported constant furniture palette binding')
    result, used = [], set()
    at, loaded, first_vertex, material, have_palette = (
        0, inherited_vertices, 0, None, inherited_palette_slot is not None)
    material_wrap, material_direct = None, False
    vertex_cache = [None]*32
    fire_tiles, fire_scroll = 0, False
    scroll_tiles, scroll_call, scroll_tmem, scroll_format = 0, False, 0, None
    while at < len(raw):
        a, b = struct.unpack_from('>II', raw, at)
        op = a >> 24
        row = {'words': (a, b), 'opcode': op}
        binding=material_bindings.get(b)
        framed_palette=op==0xF0 and binding is not None and binding[0]=='palette'
        framed_texture=op==0xFD and binding is not None and binding[0]=='texture'
        if binding and not (framed_palette or framed_texture):
            raise ValueError('Dynamic material binding used with the wrong command')
        dynamic_palette = framed_palette or (tent or palette_fade) and op == 0xF0 and b == 0x08000000
        if dynamic_palette:
            if start+at+4 in pointers:
                raise ValueError('Dynamic furniture palette also has a relocation')
            if framed_palette and binding[1] not in palette:
                raise ValueError('Dynamic palette has no complete frame resource')
            row['dynamic_palette'] = b
        elif framed_texture:
            if start+at+4 in pointers:
                raise ValueError('Dynamic material texture also has a relocation')
            row.update(target=binding[1],dynamic_texture=b)
        elif op == 0xF0 and b in palette_bindings:
            if start+at+4 in pointers:
                raise ValueError('Constant furniture palette binding also has a relocation')
            row.update(target=palette_bindings[b], bound_segment=b)
        elif op in (0xF0, 0xFD, 0x01):
            fixup = start + at + 4
            if b or fixup not in pointers:
                raise ValueError('Missing or nonzero furniture data relocation')
            row['target'] = pointers[fixup]
            used.add(fixup)
        if op == 0xD7:
            if static_materials:
                if (a not in (0xD7000000,0xD7000002) or a==0xD7000000 and b or
                        b and (not b>>16 or not b&65535)):
                    raise ValueError('Unsupported static texture scale')
                if a==0xD7000000:row['texture_disabled']=True
                if b: row['texture_scale']=(b>>16,b&65535)
            elif water and (a, b) != (0xD7000002, 0x0FA00FA0):
                raise ValueError('Unsupported water texture scale')
            elif (speed_bag or water) and (a, b) == (0xD7000002, 0x0FA00FA0):
                row['texture_scale'] = (4000, 4000)
            elif (a, b) != (0xD7000002, 0):
                raise ValueError('Unsupported furniture texture scale')
        elif op == 0xF0:
            if inherited_palette_slot is not None:
                raise ValueError('Model overwrites its inherited palette contract')
            allowed_palettes = palette if (campfire_body or static_materials) and isinstance(palette, tuple) else (palette,)
            if water or fire_effect or a != 0xF08F4010 or (not dynamic_palette and row['target'] not in allowed_palettes):
                raise ValueError('Unsupported furniture palette load')
            have_palette = True
        elif op == 0xFD:
            shape = model_texture_shape(raw[at:at + 8])
            target = row['target']
            intensity=bool(water or fire_effect or static_materials and shape[2:]==(4,0))
            rgba16=bool(static_materials and shape[2:]==(0,2))
            ia8=bool(static_materials and shape[2:]==(3,1))
            ia16=bool(static_materials and shape[2:]==(3,2))
            expected=(0,2) if rgba16 else (3,2) if ia16 else (3,1) if ia8 else (4 if intensity else 2,0)
            if (target not in textures or (not (intensity or rgba16 or ia8 or ia16) and not have_palette) or
                    shape != (*textures[target], *expected) or
                    water and shape[:2] != (32, 16)):
                raise ValueError('Unsupported furniture texture or palette')
            if intensity:
                row['intensity'] = True
            if rgba16:
                row['rgba16'] = True
            if ia8:
                row['ia8'] = True
            if ia16:
                row['ia16'] = True
            # Consume the paired Dolphin tile command. Additional wrap modes
            # require an explicit reviewed model mode; the default clamps both axes.
            tile = raw[at + 8:at + 16]
            if static_materials:
                if len(tile) != 8:
                    raise ValueError('Truncated static material tile')
                word, reserved = struct.unpack('>II', tile)
                wraps = (word >> 10 & 3, word >> 8 & 3)
                pal=word>>12&15
                tile_index=word>>16&7
                if (word & (0xFFF80000 if scrolling else 0xFFFF0000) != 0xD2F00000 or reserved or 3 in wraps
                        or pal not in ((0,15) if intensity or rgba16 or ia8 or ia16 else
                                       (15 if inherited_palette_slot is None else inherited_palette_slot,))):
                    raise ValueError('Static material needs tile 0, a supported palette, and clamp/repeat/mirror')
                row['wrap_modes'] = wraps
                row['tile_shifts'] = (word>>4&15,word&15)
                if scrolling:
                    if (scroll_call or tile_index!=scroll_tiles or scroll_tiles>=len(scrolling['dimensions']) or
                            tuple(shape[:2])!=tuple(scrolling['dimensions'][scroll_tiles]) or
                            shape[2:] not in ((2,0),(4,0)) or scroll_format not in (None,shape[2:])):
                        raise ValueError('Incomplete, reordered, or mismatched scrolling texture layers')
                    row.update(scroll_tile=tile_index,scroll_tmem=scroll_tmem)
                    scroll_tmem+=((shape[0]+15)//16)*shape[1]
                    if scroll_tmem>256:raise ValueError('Scrolling textures overlap palette TMEM')
                    scroll_tiles+=1;scroll_format=shape[2:]
                if inherited_palette_slot is not None and not (intensity or rgba16 or ia8 or ia16):
                    row['palette_slot'] = inherited_palette_slot
            elif fire_effect:
                shapes = ((32, 64), (32, 32) if fire_effect == 1 else (64, 32))
                tiles = ((0xD2F0F500, 0xD2F1F500) if fire_effect == 1 else (0xD2F0F511, 0xD2F1F520))
                shifts = ((0, 0), (0, 0)) if fire_effect == 1 else ((1, 1), (2, 0))
                if fire_tiles >= 2 or shape[:2] != shapes[fire_tiles] or tile != struct.pack('>II', tiles[fire_tiles], 0):
                    raise ValueError('Unsupported paired fire texture or tile state')
                row.update(wrap_modes=(1, 1), fire_tile=fire_tiles, fire_shifts=shifts[fire_tiles])
                fire_tiles += 1
            elif water:
                if tile != struct.pack('>II', 0xD2F0F511, 0):
                    raise ValueError('Unsupported water texture wrapping or shifts')
                row.update(wrap_modes=(1, 1), water_shift=1)
            elif camping and tile in (struct.pack('>II', word, 0) for word in
                                      (0xD2F0F000, 0xD2F0F800, 0xD2F0FA00, 0xD2F0F200)):
                word = struct.unpack_from('>I', tile)[0]
                row['wrap_modes'] = (word >> 10 & 3, word >> 8 & 3)
            elif tent and tile in (struct.pack('>II', word, 0) for word in (0xD2F0F500, 0xD2F0F800)):
                word = struct.unpack_from('>I', tile)[0]
                row['wrap_modes'] = (word >> 10 & 3, word >> 8 & 3)
            elif campfire_body and tile in (struct.pack('>II', word, 0) for word in (0xD2F0F000, 0xD2F0F100)):
                word = struct.unpack_from('>I', tile)[0]
                row['wrap_modes'] = (word >> 10 & 3, word >> 8 & 3)
            elif large_western and tile in (struct.pack('>II', word, 0)
                                           for word in (0xD2F0F000, 0xD2F0F400)):
                word = struct.unpack_from('>I', tile)[0]
                row['wrap_modes'] = (word >> 10 & 3, word >> 8 & 3)
            elif western and tile in (struct.pack('>II', word, 0)
                                    for word in (0xD2F0F000, 0xD2F0F800, 0xD2F0FA00)):
                word = struct.unpack_from('>I', tile)[0]
                row['wrap_modes'] = (word >> 10 & 3, word >> 8 & 3)
            elif garden and tile in (struct.pack('>II', word, 0)
                                  for word in (0xD2F0F000, 0xD2F0F800, 0xD2F0F100)):
                word = struct.unpack_from('>I', tile)[0]
                row['wrap_modes'] = (word >> 10 & 3, word >> 8 & 3)
            elif accessory and tile in (struct.pack('>II', word, 0)
                                      for word in (0xD2F0F000, 0xD2F0F800, 0xD2F0F900)):
                word = struct.unpack_from('>I', tile)[0]
                row['wrap_modes'] = (word >> 10 & 3, word >> 8 & 3)
            elif (mirrored_s or school) and tile == struct.pack('>II', 0xD2F0F800, 0):
                row['wrap_modes'] = (2, 0)
            elif speed_bag and tile == struct.pack('>II', 0xD2F0F522, 0) and shape[:2] == (16, 16):
                row['repeat_shift'] = 2
            elif at + 16 > len(raw) or tile != struct.pack('>II', 0xD2F0F000, 0):
                raise ValueError('Unsupported furniture wrap mode')
            row['shape'] = shape[:2]
            material = target
            material_direct=intensity or rgba16 or ia8 or ia16
            material_wrap = row.get('wrap_modes')
            at += 8
        elif op == 0xD2:
            # Birdhouse reuses its current CI4 image with explicit GX C4 format
            # and mirrored S. This is a material update, not a native command.
            if static_materials and material is not None:
                pal = 15 if inherited_palette_slot is None else inherited_palette_slot
                if (material_direct or (a & 0xFFFFF0FF) != (0xD2800000 | pal << 12)
                        or b or 3 in (a >> 10 & 3, a >> 8 & 3)):
                    raise ValueError('Unsupported static CI4 material update')
                material_wrap = (a >> 10 & 3, a >> 8 & 3)
                row['static_materials'] = True
                if inherited_palette_slot is not None: row['palette_slot'] = inherited_palette_slot
            elif (garden and (a, b) == (0xD280F800, 0)
                    and textures.get(material) == (32, 40) and material_wrap == (0, 0)):
                material_wrap = (2, 0)
            elif (large_western and (a, b) == (0xD280F900, 0)
                    and textures.get(material) == (32, 32) and material_wrap == (0, 0)):
                material_wrap = (2, 1)
            elif (camping and (a, b) == (0xD280F000, 0)
                    and textures.get(material) == (16, 32) and material_wrap == (2, 0)):
                material_wrap = (0, 0)
            else:
                raise ValueError('Unsupported standalone furniture tile update')
            row.update(shape=textures[material], wrap_modes=material_wrap)
        elif op == 0x01:
            if inherited_vertices:
                raise ValueError('Model overwrites its inherited vertex contract')
            count = a >> 12 & 255
            offset = row['target'] - vertex
            end = (a & 255)//2
            slot = end-count
            if (not 1 <= count <= 32 or not 0 <= slot <= 32-count
                    or slot and not joint_matrices or a != 0x01000000 | count << 12 | end << 1 or
                    offset < 0 or offset % 16 or offset + count * 16 > vertex_size):
                raise ValueError('Furniture vertex load escapes its array')
            loaded, first_vertex = count, offset // 16
            row.update(count=count, first_vertex=first_vertex)
            if slot: row['vertex_slot'] = slot
            vertex_cache[slot:slot+count] = range(first_vertex,first_vertex+count)
        elif op == 0x0A:
            if not loaded or material is None or fire_effect and not fire_scroll or scrolling and not scroll_call:
                raise ValueError('Furniture triangles lack vertices or a material')
            count = (a >> 17 & 127) + 1
            size = (1 + (max(0, count - 3) + 3) // 4) * 8
            if at + size > len(raw):
                raise ValueError('Furniture triangles escape the display list')
            row['triangles'] = packed(raw[at:at + size], 32 if joint_matrices else loaded)
            if joint_matrices:
                if any(vertex_cache[v] is None for t in row['triangles'] for v in t):
                    raise ValueError('Skeleton triangle reads an unloaded vertex-cache slot')
                row['global_triangles'] = [tuple(vertex_cache[v] for v in t) for t in row['triangles']]
            else:
                row['global_triangles'] = [tuple(v + first_vertex for v in t) for t in row['triangles']]
            row['material'] = material
            at += size - 8
        elif op == 0xFC:
            # Two-cycle unlit CI4: cycle one passes texture RGBA through;
            # cycle two multiplies RGB by primitive colour and preserves alpha.
            # The donor uses this for several material parts, independently of
            # the furniture's name or theme. No extra texture/state is needed.
            unlit = static_materials and (a, b) == (0xFCFFFE60, 0xFFFCF3F8)
            translucent = TRANSLUCENT_COMBINERS.get((a,b)) if static_materials else None
            scroll_combiner=SCROLL_COMBINERS.get((a,b)) if scrolling else None
            modes = (((0xFC30FE03, 0x5F1AF3E9 if fire_effect == 1 else 0x5F06F3FF),)
                if fire_effect else ((0xFC309C04, 0x5FFEF7F8),) if water else (
                (0xFC127E60, 0xFFFFF3F8), (0xFC11FE04, 0xFFFFF3F8)))
            if static_materials: modes += ((0xFC309C04,0x5FFEF7F8),(0xFC309604,0x5FFEFFF8),
                                     (0xFC30FE04,0x5FFEFDF8),(0xFC3217FF,0xFFFFFE38),
                                     (0xFC30FE04,0x5FFEF3F8),(0xFC327FFF,0xFFFFFC38))
            # FC327FFF/FFFFFC38 multiplies primitive RGB by shade, sets
            # alpha to one, then passes the combined result through cycle two.
            # It has no texture dependency; explicit texture-off commands stay.
            if not unlit and not translucent and not scroll_combiner and (a, b) not in modes:
                raise ValueError('Unsupported furniture colour combiner')
            if unlit: row['unlit_texture_primitive'] = True
            if translucent: row['combine_lerp'] = list(translucent)
            if scroll_combiner:
                if (a,b)!=(0xFC609C04,0xFFFDF7F8) and len(scrolling['dimensions'])!=2:
                    raise ValueError('Scrolling combiner needs both complete texture layers')
                row['scroll_combine_lerp']=list(scroll_combiner)
        elif op == 0xE2:
            modes = ((0xC81049D8 if fire_effect == 1 else 0xC8104A50,) if fire_effect else
                (0xC8104A50,) if water else ((0xC8112078, 0xC8113078)
                if accessory else (0xC8113078, 0xC8104DD8)))
            if static_materials: modes += (0xC8104A50,0xC81049D8)
            if a != 0xE200001C or b not in modes:
                raise ValueError('Unsupported furniture render mode')
        elif op == 0xFA:
            colours = ((0xFFFFFFFF, 0xB2B2B2FF) if accessory or school else
                       (0xFFFFFFFF, 0xFFFDFFFF) if camping else (0xFFFFFFFF,))
            if static_materials:
                if a&0xFFFFFF00 != 0xFA000000:
                    raise ValueError('Unsupported static primitive LOD state')
            elif ((a, b) != ((0xFA000064, 0xFFD264FF) if fire_effect == 1 else (0xFA00008C, 0xFFF01EFF)) if fire_effect else
                    (a, b) != (0xFA00001E, 0x9B9BC864) if water else
                    (a not in (0xFA000080, 0xFA0000FF) or b not in colours)):
                raise ValueError('Unsupported furniture primitive colour')
        elif op == 0xFB:
            expected = (0xFB000000, 0xFF5000FF if fire_effect == 1 else 0xDC1E0078) if fire_effect else (0xFB000000, 0x6464AFFF)
            if (a!=0xFB000000 if static_materials else not (water or fire_effect) or (a, b) != expected):
                raise ValueError('Unsupported furniture environment colour')
        elif op == 0xF2:
            # Native F2 extents are already RDP coordinates, not texture DMA
            # lengths. Preserve bounded tile-zero coordinates for all static
            # materials; no object-specific texture-size exception is needed.
            static_extent = (static_materials and material is not None and a == 0xF2000000
                             and b & 0xFF000000 == 0 and b & 0x003003 == 0)
            school_extent = school and b == {
                ((32, 32), (2, 0)): 0x000FC07C,
                ((16, 32), (2, 0)): 0x0007C07C,
            }.get((textures.get(material), material_wrap))
            # The two construction models extend a mirrored 16x32 material
            # across a 32x32 tile. Retain the explicit extent after loading it.
            construction_extent = (mirrored_s and material_wrap == (2, 0)
                                   and textures.get(material) == (16, 32)
                                   and b == 0x0007C07C)
            garden_extent = garden and b == {
                ((16, 32), (2, 0)): 0x0007C07C,
                ((32, 40), (2, 0)): 0x000FC09C,
                ((32, 16), (0, 1)): 0x0007C07C,
                ((16, 48), (2, 0)): 0x0007C0BC,
                ((16, 16), (2, 0)): 0x0007C03C,
            }.get((textures.get(material), material_wrap))
            western_extent = western and b == {
                ((16, 32), (2, 0)): 0x0007C07C,
                ((16, 16), (2, 0)): 0x0007C03C,
                ((16, 16), (2, 2)): 0x0007C07C,
            }.get((textures.get(material), material_wrap))
            large_extent = large_western and b in {
                ((32, 32), (1, 0)): (0x000FC07C,),
                ((16, 8), (1, 0)): (0x001BC01C, 0x000BC01C),
                ((32, 32), (2, 1)): (0x000FC0FC,),
            }.get((textures.get(material), material_wrap), ())
            camping_extent = camping and b == {
                ((32, 16), (2, 0)): 0x000FC03C,
                ((16, 32), (2, 0)): 0x0007C07C,
                ((16, 32), (0, 0)): 0x0003C07C,
                ((32, 32), (2, 2)): 0x000FC0FC,
                ((32, 8), (2, 0)): 0x000FC01C,
                ((16, 8), (0, 2)): 0x0003C03C,
            }.get((textures.get(material), material_wrap))
            fire_extent = (campfire_body and textures.get(material) == (16, 16)
                           and material_wrap == (0, 1) and b == 0x0003C07C)
            if (material is None or a != 0xF2000000 or not
                    (static_extent or construction_extent or garden_extent or western_extent or large_extent or camping_extent or fire_extent or school_extent
                     or accessory and b in (0x0007C07C, 0x000FC07C))):
                raise ValueError('Unsupported explicit native tile extent')
        elif op == 0xD9:
            modes = (0x210005,) if fire_effect else (0x270405,) if water else ((0x230405, 0x230005, 0x210405, 0x210005)
                if camping or tent or static_materials else (0x230405, 0x230005, 0x270405)
                if speed_bag else (0x230405, 0x230005))
            if static_materials: modes += (0x270405,0x270005,0x2F0405,0x2F0005)
            if a != 0xD9000000 or b not in modes:
                raise ValueError('Unsupported furniture geometry mode')
        elif op == 0xDE:
            if scrolling:
                if (scroll_tiles!=len(scrolling['dimensions']) or scroll_call or
                        (a,b)!=(0xDE000000,scrolling['segment']) or start+at+4 in pointers):
                    raise ValueError('Invalid or incomplete dynamic scroll call')
                scroll_call=True;row['dynamic_scroll']=b
            elif not fire_effect or fire_tiles != 2 or fire_scroll or (a, b) != (0xDE000000, 0x09000000):
                raise ValueError('Unsupported dynamic furniture display-list dependency')
            else:
                fire_scroll = True
                row['dynamic_scroll'] = 0x09000000
        elif op == 0xDA:
            if (not joint_matrices or a != 0xDA380003 or b >> 24 != 13
                    or b & 63 or (b & 0xFFFFFF)//64 >= joint_matrices):
                raise ValueError('Skeleton matrix references an unavailable visible joint')
            row['joint_matrix'] = (b & 0xFFFFFF)//64
        elif op == 0xDF:
            if (a, b) != (0xDF000000, 0) or at + 8 != len(raw):
                raise ValueError('Invalid furniture display-list terminator')
        else:
            raise ValueError(f'Unsupported furniture graphics opcode {op:02X}')
        result.append(row)
        at += 8
    if result[-1]['opcode'] != 0xDF or not any('triangles' in r for r in result):
        raise ValueError('Furniture model lacks triangles or termination')
    if used != set(pointers):
        raise ValueError('Unaccounted furniture data relocation')
    if fire_effect and (fire_tiles != 2 or not fire_scroll):
        raise ValueError('Incomplete two-texture fire effect')
    if scrolling and not scroll_call:raise ValueError('Unused dynamic scroll binding')
    return result


def prepare(rel, symbols_bytes, pilot):
    verify_sources(rel, symbols_bytes)
    if pilot not in REVIEWED:
        raise ValueError('Unreviewed furniture pilot')
    symbols = symbols_bytes.decode()
    base = rel_sections(rel)[5][0]
    profile_at, profile_size = symbol_span(symbols, pilot.profile)
    index = 1024 + (pilot.item - 0x3000) // 4
    quality = re.findall(r'^furniture_quality = \.data:0x([0-9A-F]+);[^\n]* size:0x13C8 ', symbols, re.M)
    if sorted(int(a, 16) for a in quality) != [0x39FB4, 0x7B5B0]:
        raise ValueError('Changed donor furniture profile tables')
    for table in quality:
        entry = int(table, 16) + index * 4
        if data_pointers(rel, entry, 4) != {entry: profile_at}:
            raise ValueError('Furniture item does not resolve to its reviewed profile')
    profile_raw = rel[base + profile_at:base + profile_at + profile_size]
    if profile_raw != bytes(32) + scalar_profile(pilot) + bytes(4):
        raise ValueError('Furniture profile needs unported behaviour or changed dimensions')

    body = bytearray()
    resources, offsets, texture_shapes = [], {}, {}

    def add(name, size, convert):
        at, actual_size = symbol_span(symbols, name)
        if actual_size != size:
            raise ValueError('Changed furniture resource size')
        source = rel[base + at:base + at + size]
        converted = convert(source)
        if len(converted) != size:
            raise ValueError('Furniture resource changes its expected allocation')
        body.extend(bytes((-len(body)) % 32))
        offset = len(body)
        offsets[at] = offset
        body.extend(converted)
        resources.append({'symbol': name, 'donor_offset': at, 'native_offset': offset,
                          'bytes': size, 'source_sha256': sha256(source),
                          'output_sha256': sha256(converted)})
        return at

    pal = add(pilot.stem + '_pal', 32, native_palette)
    for suffix, w, h in pilot.textures:
        name = dict(pilot.texture_symbols).get(suffix,
            pilot.stem + ('_' + suffix if suffix else '') + '_tex_txt')
        at = add(name, w * h // 2,
                 lambda data, w=w, h=h: pack4(untile(data, w, h, 4)))
        texture_shapes[at] = (w, h)
    vertex_size = pilot.vertex_count * 16
    vertex = add(pilot.vertex_symbol or pilot.stem + '_v', vertex_size,
                 lambda data: normalise_vertex_flags(data)[0])
    # These are plain arrays, not containers of unconverted pointers.
    for resource in resources:
        if data_pointers(rel, resource['donor_offset'], resource['bytes']):
            raise ValueError('Unexpected relocation in furniture texels or vertices')
    models = {}
    profile_pointers = {}
    for label, suffix, slot, size in pilot.models:
        name = dict(pilot.model_symbols).get(label, pilot.stem + suffix)
        at, actual_size = symbol_span(symbols, name)
        if actual_size != size:
            raise ValueError('Changed furniture model size')
        raw = rel[base + at:base + at + size]
        pointers = data_pointers(rel, at, size)
        models[label] = {'symbol': name, 'donor_offset': at, 'source_sha256': sha256(raw),
                         'rows': parse_model(raw, at, pointers, pal, texture_shapes, vertex,
                                             vertex_size, mirrored_s=pilot.mirrored_s,
                                             garden=pilot.garden, western=pilot.western,
                                             large_western=pilot.large_western,
                                             water=pilot.water_layer and label == 'translucent',
                                             camping=pilot.camping, school=pilot.school)}
        profile_pointers[profile_at + slot] = at
    if data_pointers(rel, profile_at, profile_size) != profile_pointers:
        raise ValueError('Furniture profile has missing, extra, or unported dependencies')
    names_at, names_size = symbol_span(symbols, 'ftrName2_table')
    name_at = base + names_at + (pilot.item - 0x3000) // 4 * 16
    if names_size != 242 * 16 or rel[name_at:name_at + 16] != pilot.name.encode().ljust(16, b' '):
        raise ValueError('Furniture name and reviewed donor item identity disagree')
    return bytes(body), resources, offsets, models


def command_source(models, offsets):
    output = ['/* Generated from local donor data; not a distribution asset. */', '#include <PR/mbi.h>']
    sections = []

    def tile_fields(shape, wraps):
        modes = {0: 'G_TX_CLAMP', 1: 'G_TX_WRAP', 2: 'G_TX_MIRROR | G_TX_WRAP'}
        if len(wraps) != 2 or any(w not in modes for w in wraps):
            raise ValueError('Unsupported furniture tile wrapping')
        masks = []
        for size, wrap in zip(shape, wraps, strict=True):
            if type(size) is not int or not 1 <= size <= 1024:
                raise ValueError('Unsupported furniture texture dimension')
            power_two = size & (size - 1) == 0
            if wrap and not power_two:
                raise ValueError('Repeated furniture texture needs a power-of-two axis')
            # Masking a clamped 40/48/56-pixel axis to 32 would crop its tail.
            masks.append(size.bit_length() - 1 if power_two else 0)
        return *(modes[wrap] for wrap in wraps), *masks

    for label, model in models.items():
        values, count = [], 0

        def emit(value, commands=1):
            nonlocal count
            values.append('    ' + value + ',')
            count += commands

        inherited=model.get('inherited_material',False)
        if inherited and any(row['opcode'] not in (0x01,0x0A,0xDF) for row in model['rows']):
            raise ValueError('Inherited material is limited to validated geometry lists')
        if not inherited:emit('gsDPPipeSync()')
        direct = next((bool(row.get('intensity') or row.get('rgba16') or row.get('ia8') or row.get('ia16'))
                       for row in model['rows'] if row['opcode']==0xFD),False)
        if not inherited:
            emit('gsDPSetTextureLUT(G_TT_NONE)' if direct else 'gsDPSetTextureLUT(G_TT_RGBA16)')
        for row in model['rows']:
            op = row['opcode']
            if op == 0xD7:
                # GX zero means its normal scale; native zero collapses UVs.
                if row.get('texture_disabled'):
                    if row['words']!=(0xD7000000,0) or 'texture_scale' in row:
                        raise ValueError('Changed disabled texture state')
                    emit('gsSPTexture(0, 0, 0, G_TX_RENDERTILE, G_OFF)')
                elif 'texture_scale' in row:
                    if (len(row['texture_scale'])!=2 or
                            any(type(n) is not int or not 0<n<=65535 for n in row['texture_scale'])):
                        raise ValueError('Unsupported furniture environment-map scale')
                    s,t=row['texture_scale']
                    emit(f'gsSPTexture({s}, {t}, 0, G_TX_RENDERTILE, G_ON)')
                else:
                    emit('gsSPTexture(0xFFFF, 0xFFFF, 0, G_TX_RENDERTILE, G_ON)')
            elif op == 0xF0:
                emit('gsDPPipeSync()')
                palette = row['dynamic_palette'] if 'dynamic_palette' in row else SEGMENT + offsets[row['target']]
                if 'dynamic_palette' in row and palette not in (0x08000000,0x09000000):
                    raise ValueError('Unreviewed dynamic palette segment')
                emit(f"gsDPLoadTLUT_pal16(15, 0x{palette:08X})", 6)
            elif op == 0xFD:
                texture=row.get('dynamic_texture',SEGMENT+offsets[row['target']])
                if 'dynamic_texture' in row and texture not in (0x08000000,0x09000000):
                    raise ValueError('Unreviewed dynamic texture segment')
                w, h = row['shape']
                rgba16=bool(row.get('rgba16'))
                ia8=bool(row.get('ia8'))
                ia16=bool(row.get('ia16'))
                # Keep upper TMEM intact for CI palettes across mixed-format lists.
                if (w*h*(4 if rgba16 or ia16 else 2 if ia8 else 1)//2 > 2048
                        or sum(map(bool,(rgba16,ia8,ia16,row.get('intensity'))))>1):
                    raise ValueError('Furniture texture exceeds shared TMEM capacity or has conflicting formats')
                emit('gsDPPipeSync()')
                wanted=bool(row.get('intensity') or rgba16 or ia8 or ia16)
                if wanted!=direct:
                    emit('gsDPSetTextureLUT(G_TT_NONE)' if wanted else 'gsDPSetTextureLUT(G_TT_RGBA16)')
                    direct=wanted
                wrap_s, wrap_t, mask_s, mask_t = tile_fields((w, h), row.get('wrap_modes', (0, 0)))
                shift = 0
                if 'repeat_shift' in row:
                    if row['repeat_shift'] != 2 or (w, h) != (16, 16):
                        raise ValueError('Unsupported furniture environment-map tile')
                    wrap_s, wrap_t, shift = 'G_TX_WRAP', 'G_TX_WRAP', 2
                if 'water_shift' in row:
                    if not row.get('intensity') or (w, h) != (32, 16) or row['water_shift'] != 1:
                        raise ValueError('Unsupported furniture water tile')
                    shift = 1
                inherited_pal = row.get('palette_slot', 15)
                if type(inherited_pal) is not int or not 0 <= inherited_pal <= 15:
                    raise ValueError('Invalid native palette slot')
                fmt, pal = (('G_IM_FMT_RGBA',0) if rgba16 else
                            ('G_IM_FMT_IA',0) if ia8 or ia16 else
                            ('G_IM_FMT_I',0) if row.get('intensity') else ('G_IM_FMT_CI',inherited_pal))
                if 'fire_tile' in row:
                    tile = row['fire_tile']
                    shifts = row['fire_shifts']
                    if (not row.get('intensity') or tile not in (0, 1) or row['wrap_modes'] != (1, 1)
                            or (tile == 0 and (w, h) != (32, 64))
                            or (tile == 1 and (w, h) not in ((32, 32), (64, 32)))
                            or shifts not in ((0, 0), (1, 1), (2, 0))):
                        raise ValueError('Unreviewed fire multi-texture allocation')
                    args = (f'{tile * 128}, {tile}, G_IM_FMT_I, {w}, {h}, 0, G_TX_WRAP, G_TX_WRAP, '
                            f'{mask_s}, {mask_t}, {shifts[0]}, {shifts[1]}')
                    emit(f"gsDPLoadMultiBlock_4b(0x{texture:08X}, {args})", 7)
                    continue
                shifts=row.get('tile_shifts',(shift,shift))
                if len(shifts)!=2 or any(type(n) is not int or not 0<=n<=15 for n in shifts):
                    raise ValueError('Invalid native texture tile shifts')
                if 'scroll_tile' in row:
                    tile,tmem=row['scroll_tile'],row['scroll_tmem']
                    if (rgba16 or ia8 or ia16 or type(tile) is not int or tile not in (0,1) or
                            type(tmem) is not int or not 0<=tmem<=256-((w+15)//16)*h or
                            (tile==0)!=(tmem==0)):
                        raise ValueError('Invalid complete scrolling texture allocation')
                    args=(f'{tmem}, {tile}, {fmt}, {w}, {h}, '+
                          (f'0, 0, {w-1}, {h-1}, ' if w%16 else '')+
                          f'{pal}, {wrap_s}, {wrap_t}, {mask_s}, {mask_t}, {shifts[0]}, {shifts[1]}')
                    macro='gsDPLoadMultiTile_4b' if w%16 else 'gsDPLoadMultiBlock_4b'
                    emit(f'{macro}(0x{texture:08X}, {args})',7)
                    continue
                if rgba16 or ia8 or ia16:
                    if w%(4 if rgba16 or ia16 else 8) or h%4:
                        raise ValueError('Direct texture needs complete GX blocks')
                    size='G_IM_SIZ_16b' if rgba16 or ia16 else 'G_IM_SIZ_8b'
                    args=(f'{fmt}, {size}, {w}, {h}, 0, {wrap_s}, {wrap_t}, '
                          f'{mask_s}, {mask_t}, {shifts[0]}, {shifts[1]}')
                    emit(f"gsDPLoadTextureBlock(0x{texture:08X}, {args})",7)
                    continue
                args = (f'{fmt}, {w}, {h}, ' + (f'0, 0, {w - 1}, {h - 1}, ' if w % 16 else '') +
                        f'{pal}, {wrap_s}, {wrap_t}, {mask_s}, {mask_t}, {shifts[0]}, {shifts[1]}')
                # A 24-pixel row has a 12-byte source pitch but occupies two
                # 8-byte TMEM words. Tile DMA preserves that distinction; block
                # DMA would pack rows together and corrupt the padded stride.
                macro = 'gsDPLoadTextureTile_4b' if w % 16 else 'gsDPLoadTextureBlock_4b'
                emit(f"{macro}(0x{texture:08X}, {args})", 7)
            elif op == 0xD2:
                if not row.get('static_materials') and (row['shape'], row['wrap_modes']) not in (((32, 40), (2, 0)), ((32, 32), (2, 1)),
                                                           ((16, 32), (0, 0))):
                    raise ValueError('Unreviewed furniture tile update in compiler input')
                w, h = row['shape']
                wrap_s, wrap_t, mask_s, mask_t = tile_fields((w, h), row['wrap_modes'])
                pal = row.get('palette_slot', 15)
                if type(pal) is not int or not 0 <= pal <= 15:
                    raise ValueError('Invalid native palette slot')
                emit('gsDPTileSync()')
                emit(f'gsDPSetTile(G_IM_FMT_CI, G_IM_SIZ_4b, {(w+15) // 16}, 0, '
                     f'G_TX_RENDERTILE, {pal}, {wrap_t}, {mask_t}, 0, {wrap_s}, {mask_s}, 0)')
                emit(f'gsDPSetTileSize(G_TX_RENDERTILE, 0, 0, {(w - 1) * 4}, {(h - 1) * 4})')
            elif op == 0x01:
                # The donor pointer can address the middle of the vertex array.
                first = row['first_vertex']
                target = offsets[row['target'] - first * 16] + first * 16
                slot=row.get('vertex_slot',0)
                if not 0 <= slot <= 32-row['count']:
                    raise ValueError('Native vertex load escapes the cache')
                emit(f"gsSPVertex(0x{SEGMENT + target:08X}, {row['count']}, {slot})")
            elif op == 0x0A:
                triangles = row['triangles']
                for i in range(0, len(triangles), 2):
                    if i + 1 < len(triangles):
                        args = (*triangles[i], 0, *triangles[i + 1], 0)
                        emit('gsSP2Triangles(' + ', '.join(map(str, args)) + ')')
                    else:
                        emit('gsSP1Triangle(' + ', '.join(map(str, (*triangles[i], 0))) + ')')
            elif op == 0xDE:
                segment=row.get('dynamic_scroll')
                if segment not in (0x08000000,0x09000000) or row['words'] != (0xDE000000,segment):
                    raise ValueError('Unreviewed dynamic scroll list')
                emit(f'gsSPDisplayList(0x{segment:08X})')
            elif op == 0xDA:
                index=row.get('joint_matrix')
                if (type(index) is not int or not 0 <= index < 255
                        or row['words'] != (0xDA380003,0x0D000000+index*64)):
                    raise ValueError('Changed skeleton matrix in native compiler input')
                emit(f'gsSPMatrix(0x{0x0D000000+index*64:08X}, G_MTX_NOPUSH | G_MTX_LOAD | G_MTX_MODELVIEW)')
            elif op == 0xFC and row.get('scroll_combine_lerp'):
                expression=SCROLL_COMBINERS.get(tuple(row['words']))
                if expression is None or list(expression)!=row['scroll_combine_lerp']:
                    raise ValueError('Changed scrolling colour combiner')
                emit('gsDPSetCombineLERP('+', '.join(expression)+')')
            elif op == 0xFC and row.get('combine_lerp'):
                expression=TRANSLUCENT_COMBINERS.get(tuple(row['words']))
                if expression is None or list(expression)!=row['combine_lerp']:
                    raise ValueError('Changed translucent colour combiner')
                emit('gsDPSetCombineLERP('+', '.join(expression)+')')
            elif op == 0xFC and row.get('unlit_texture_primitive'):
                if row['words'] != (0xFCFFFE60, 0xFFFCF3F8):
                    raise ValueError('Changed unlit texture/primitive combiner')
                # Compile the actual native expression; shared asset checks
                # compare its complete words with the donor command.
                emit('gsDPSetCombineLERP(0, 0, 0, TEXEL0, 0, 0, 0, TEXEL0, '
                     'PRIMITIVE, 0, COMBINED, 0, 0, 0, 0, COMBINED)')
            elif op in (0xFC, 0xE2, 0xFA, 0xFB, 0xD9, 0xDF, 0xF2):
                # Only the explicitly decoded compatible F3DEX2 state/end
                # commands reach here; Dolphin loads and packed triangles do not.
                a, b = row['words']
                emit(f'{{{{0x{a:08X}, 0x{b:08X}}}}}')
            else:
                raise ValueError('Unconverted furniture command in native compiler input')
        output.append(f'const Gfx furniture_{label}[] __attribute__((section(".{label}"), aligned(8))) = {{')
        output.extend(values)
        output.append('};')
        sections.append((label, count * 8))
    return '\n'.join(output) + '\n', tuple(sections)


def native_profile(pilot, object_size, model_offsets, vrom_start):
    """Bind an installed object's verified VROM; this does not register an item."""
    if (pilot not in REVIEWED or type(object_size) is not int or
            not 0 < object_size < 0x1000000 or object_size % 16 or
            type(vrom_start) is not int or not 0 < vrom_start <= 0x4000000 - object_size or
            vrom_start % 16 or set(model_offsets) != {row[0] for row in pilot.models} or
            any(type(at) is not int or at < 0 or at % 8 or at + 8 > object_size for at in model_offsets.values())):
        raise ValueError('Furniture profile exceeds its native object bounds')
    slots = {0: 'opaque', 4: 'opaque1', 8: 'translucent', 12: 'translucent1'}
    if (any(slots.get(slot) != label for label, _, slot, _ in pilot.models)
            or len({row[2] for row in pilot.models}) != len(pilot.models)):
        raise ValueError('Furniture model uses an unsupported or duplicated profile slot')
    models = [SEGMENT + model_offsets[label] if label in model_offsets else 0
              for label in slots.values()]
    words = (vrom_start, vrom_start + object_size, SEGMENT, SEGMENT + object_size,
             *models, 0, 0, 0, 0)
    return struct.pack('>12I', *words) + scalar_profile(pilot) + bytes(4)


def build_objects(rel, symbols, out, pilots=PILOTS):
    verify_sources(rel, symbols)
    if not pilots or len(set(pilots)) != len(pilots) or any(p not in REVIEWED for p in pilots):
        raise ValueError('Choose a nonempty, unique batch of reviewed furniture')
    out.mkdir(parents=True, exist_ok=False)
    report = {'format': 'AFV3-FURNITURE-ART-1', 'converter_version': CONVERTER_VERSION,
              'donor': DONOR, 'source_rel_sha256': REL_SHA, 'source_symbols_sha256': SYMBOLS_SHA,
              'compiler_image': IMAGE, 'objects': [], 'runtime_installed': False,
              'status': 'converted_static_assets_not_playable_imports'}
    for pilot in pilots:
        body, resources, offsets, models = prepare(rel, symbols, pilot)
        source, sections = command_source(models, offsets)
        directory = out / pilot.key
        directory.mkdir()
        source_file = directory / 'commands.c'
        source_file.write_text(source)
        compiled = compile_commands(directory / 'gbi', source_file, sections)
        asset, destinations, model_report = bytearray(body), {}, []
        for label, model in models.items():
            asset.extend(bytes((-len(asset)) % 8))
            at = len(asset)
            destinations[label] = at
            asset.extend(compiled[label])
            model_report.append({'layer': label, 'symbol': model['symbol'],
                                 'source_sha256': model['source_sha256'], 'native_offset': at,
                                 'bytes': len(compiled[label]), 'output_sha256': sha256(compiled[label]),
                                 'triangles': sum(len(r.get('triangles', ())) for r in model['rows'])})
        asset.extend(bytes((-len(asset)) % 16))
        name = pilot.key + '.n64obj.bin'
        (out / name).write_bytes(asset)
        report['objects'].append({'id': f'{DONOR}/item/{pilot.item:04X}', 'name': pilot.name,
                                  'target_item_id': None, 'selectable': False, 'object_file': name,
                                  'object_bytes': len(asset), 'object_sha256': sha256(asset),
                                  'segment': f'{SEGMENT:08X}', 'resources': resources, 'models': model_report,
                                  'native_profile_scalar_hex': scalar_profile(pilot).hex(),
                                  'profile_symbol': pilot.profile, 'model_offsets': destinations,
                                  'command_source_sha256': sha256(source.encode())})
    (out / 'art.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disc', type=Path, default=ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    parser.add_argument('--symbols', type=Path, default=ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--batch', choices=('pilots', 'construction', 'garden', 'western', 'western-large', 'camping', 'school-desks'), default='pilots')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a fresh output directory; existing builds are preserved')
    pilots = {'pilots': PILOTS, 'construction': CONSTRUCTION_PILOTS,
              'garden': GARDEN_PILOTS, 'western': WESTERN_PILOTS,
              'western-large': LARGE_WESTERN_PILOTS, 'camping': CAMPING_PILOTS,
              'school-desks': SCHOOL_DESKS}[args.batch]
    report = build_objects(read_donor(args.disc)['rel'], args.symbols.read_bytes(), args.output.resolve(), pilots)
    print(json.dumps({'output': str(args.output), 'objects': [
        {'name': r['name'], 'bytes': r['object_bytes'], 'sha256': r['object_sha256']} for r in report['objects']],
        'runtime_installed': False}, indent=2))


if __name__ == '__main__':
    main()
