"""Checked moving-parent conversion; owner/loose-item hooks remain required."""
import json
import struct
from aflib import by_vrom,sha256

BLOCKS=(
    (0x10763C,124,'b2db13d06f5b51f7595bd018ee4bb571663dea60c0e993355875375bc76f541c','a77367984603eeaf8af0fd644afa784c444f0883736e3f687d3fbb4bc85d50c9'),
    (0x1076B8,188,'02a0caf84e4dc5d758ffc5556326e37c0ad9739dd1e6323f6678fe8733206f32','f08db5788d77729cc064fcba7de49c5f3aa1c76bc1028f524c40eebb272b69fd'),
    (0x107774,148,'8dfc36f3acee5c75d535bfe25e1fa29aa8ae5947c7d8a2a01671017dec9ba452','4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945'),
    (0x107808,892,'8762f92fcae495bc548f877925f5a12c289161d84724b1d1a1f5050b9bcd3e8e','af24c55eb565974034708888c12e2542a49b0e4c28e56f3fab99b4e6f90dea5f'),
    (0x107B84,544,'f45b2bfffb38fc29a14d359026abb5d82386aaffa4c93606a36299d8a3e79198','619ae273c9adbb8c2b4bd113f7b31f582237728a03922598f8fdc8424e499a0e'),
    (0x10CB54,268,'7b0c30fda6c2749a3aea8f5a9c34dd45ce9eac4f55643d5b89352ff106d6fdc0','a8a9bfe5ed2f63669ff49b699ea49b70535274fbb84618a97265c5427119f01a'),
    (0x103BF8,104,'64b45a3de3487f0074da5a40d98e556abca64f22aaabd6215fddf6d10e39929b','0cda855d265230b6c8260b51ce7070da60892772b85dcd9244fb5a8cc30ac58e'),
    (0x103C60,120,'d7f16d629f2e96ff2d04e1192e1c0397673ca1d736d57065806474e978ed8ffa','0cda855d265230b6c8260b51ce7070da60892772b85dcd9244fb5a8cc30ac58e'),
    (0x1121AC,260,'267ea86c1b4f80fb3e5052d951f0c5565fc0cd1aa8aab98cb2d7a3cfed91e03d','b3203569dde287c6c0842c5467694e14a31a72afa4bf8ea4001da866b4ef1fe2'),
    (0x1122B0,60,'b95c959875c2ad4e7f624e30ed44122063b4141715c04f31502e68893e2177fa','4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945'),
    (0x12D274,44,'13128e417a124f40b7d3f0a386a8d3ff10f7a806f666cce1180b78a417d0e4f5','4f247f00303aca88e1e50d4a833cb28f8a214c0bb683e41e1996fde59278bbcb'),
    (0x12D2A0,36,'2812bfa33995a075988bbc90e75ca4e98e268cb400a2d55ffbe6bd69bd53a942','4f247f00303aca88e1e50d4a833cb28f8a214c0bb683e41e1996fde59278bbcb'),
)
CONSTANTS={0x387C:'41a00000',0x3880:'42200000',0x3884:'00000000',
    0x3888:'4330000080000000',0x38AC:'42652ee0',0x38B0:'38c90fdb',0x39A8:'3c23d70a'}


def source_contract(source):
    functions={}
    for at,size,digest,relocations in BLOCKS:
        raw,row=source.function(at)
        if (len(raw)!=size or sha256(raw)!=digest or
                sha256(json.dumps(sorted(row['relocations'].items()),separators=(',',':')).encode())!=relocations):
            raise ValueError('Changed complete carrying dependency: '+row['symbol'])
        functions[row['symbol']]=row
    for at,value in CONSTANTS.items():
        base,size=source.sections[4];raw=bytes.fromhex(value)
        if at+len(raw)>size or source.rel[base+at:base+at+len(raw)]!=raw:
            raise ValueError(f'Changed carrying constant: {at:X}')
    shapes=[(2,0,-16,0,0),(2,0,-1,0,0),(2,0,16,0,0),
            (2,0,1,0,0),(1,0,0,0,0),(4,0,1,16,17)]
    raw=b''.join(struct.pack('>i4h',*row) for row in shapes)
    raw+=bytes(24)+struct.pack('>i3fiHh3f',0,0,0,0,-1,0,0,0,0,0)
    refs={at:ref for at,ref in source.relocations.items() if 0x3CB40<=at<0x3CB40+len(raw)}
    expected={0x3CB88+4*i:(1,True,5,0x3CB40+12*i) for i in range(6)}
    if source.data[0x3CB40:0x3CB40+len(raw)]!=raw or refs!=expected:
        raise ValueError('Changed carrying footprint/initializer data')
    return dict(category='moving-table-carrying',functions=functions,constants=CONSTANTS,
        footprints=shapes,state_bytes=152,slots=4,cell_units=40,grid=[16,16],
        duplicate_actor_scan='all occupied slots',registration='validate before detaching',
        restoration='retain active state on an invalid destination',
        loose_item_angles='transient 16 by 16 signed halfwords in the donor',
        callback_installed=False)


def native_contract(image):
    files=by_vrom(image);rows=[]
    for vrom,origin,blocks in (
        (0x82D7F0,0x80936710,(
            ('occupied_top',0x8093C5C0,544,'924933baa31f99590994532c8cf7da6b8c44b048502fc5f776cbe04d5a8b0d5d'),
            ('contact_top',0x8093E190,116,'1c706c762e2bd42d23b9931bec17d0247551f9c0ea8410e8550a7eea58d49c52'),
            ('set_foreground',0x80943C10,996,'be05da3e4b7378f4bad328337c6d614c4463935c8a3ad55bcbbf9c53d080bb89'),
            ('set_place',0x80937ABC,200,'42840028460b29a0cc4e964787e1e5dc021e5e1a6e4dc909596f355d31748b96'),
            ('lookup_child',0x80945ED8,324,'d2e3b24574df7c3c011baa019acf111a78d112aaf7d039f0c7ee6283cd104eda'))),
        (0x8576C0,0x80962A20,(
            ('single_draw',0x80963320,56,'455e4575a3073ede0ca55e9216d1e6eebc2c5b57ca41dc5e5f9372eead3b400e'),
            ('single_matrix',0x809630C8,600,'45474ba4c57794383c1bde3d2714252499f3bc869f6730aae49d8df672dc1787'),
            ('shop_ctor',0x80963438,272,'e85472b8cbaf0eff3a0a9f5865191b04a1039dd768aeb7a194312edbbd277be6')))):
        owner=files[vrom].extract(image)
        for name,at,size,digest in blocks:
            raw=owner[at-origin:at-origin+size]
            if len(raw)!=size or sha256(raw)!=digest:
                raise ValueError('Changed carrying native dependency: '+name)
            rows.append(dict(name=name,vrom=vrom,origin=origin,address=at,bytes=size,sha256=digest))
    return dict(blocks=rows,actor_id_offset=4,base_position_offset=0x40,
        angle_offset=0x124,layer_offset=0x738,kept_item_offset=0x73A,
        owner_original_bytes=0x4E0,actor_stride=0x740,actor_capacity=48,
        shop_clip_pointer=0x80136F58,shop_clip_original_bytes=8,
        loose_item_angle_callbacks_present=False,loose_item_rotation_present=False,
        movement_calls=[0x8093F18C,0x8093F598,0x80941524],
        installed=False)
