"""Shared tree-effect integration, preserving native animation/effect owners."""
import struct
from aflib import by_vrom,sha256,u32
from v3_import_storage import jump
from v3_npc_clothing import guard_incoming
from v3_player_actions import native_references

PLANT=(
    ('cherry',0x143340,'102d3ac460eeebb10f08e4cd36694b59c4e50acb17beed641d96bcd2cfba358e',
        '1a1bb795f6d6805fe2b345c8138b588bd6f889cd78a96a618628976962fa3c75'),
    ('winter',0x1521BC,'b8b7e20a464e1246f4e85bcb144edca86cf3a474809b40bb1c86f7ed6098e772',
        '73907e7edd98d3bfa02d7dd4acb07e0dea3bdf406ebae30b6d99ab2a90717eb0'),
    ('xmas',0x1595D4,'856ed6d05535bece026e7ce832052784d069bbac36aa21a8f31f59986483bcc8',
        '5694908595f295ee987b0c624d909b4c719612b9a402509b17819a43250d822f'),
    ('ordinary',0x14A6C4,'9d6c5f1e1644e3c80048f843a666defe101247ca3748cae307370dc70cb96748',
        '356c726a0ddbbb3212cb99783111c4af81bbef4f5269cb29e1882ea040ce4d9d'))
SPARKLE=((0x2A3598,'d048ee7f7ac87b856f5cfdb583a705796a8c825169d55eb249f9b32f85a8123f'),
    (0x2A3768,'4f6ab56834414a4c89b9beb3d3f6409722d522daefab97e4dc5db46ad0d4eef7'),
    (0x2A37DC,'acc0c3c45390bd53ab2082502ebfaef32e2f00541c9b0f42a114861c550107f2'),
    (0x2A38B4,'02d53f6f38047ab7e8a457354a6ccb56f3da45802c6fdb50c32c4393ebcfaaee'))
EFFECT_VROM,EFFECT_RELOC,EFFECT_RAM=0x8F98E0,0x8F9CE0,0x80A31E40


def planting_contract(source,base,original,scenery):
    files=by_vrom(base);retail=by_vrom(original);owners=[];sources=[]
    for row,(role,offset,digest,native_digest) in zip(scenery['owners'],PLANT,strict=True):
        raw,receipt=source.function(offset)
        if row['role']!=role or sha256(raw)!=digest:raise ValueError('Changed complete source planting consumer')
        position=[]
        for hi,lo in ((334,342),(338,358),(354,374)):
            reference=receipt['relocations'][hi]
            if reference[:3]!=(6,1,4) or receipt['relocations'][lo]!=(4,*reference[1:]):
                raise ValueError('Changed source planting effect position binding')
            position.append(struct.unpack_from('>f',source.rel,source.sections[4][0]+reference[3])[0])
        if position!=([12.,27.,10.] if role=='cherry' else [13.,33.,10.]):
            raise ValueError('Changed seasonal planting effect position')
        owner=files[row['vrom']].extract(base);rel=files[row['reloc']].extract(base)
        native=retail[row['vrom']].extract(original)
        if (sha256(owner)!=row['output_sha256'] or sha256(rel)!=row['output_reloc_sha256']
                or sha256(owner[0x3928:0x3A84])!=native_digest or owner[0x3928:0x3A84]!=native[0x3928:0x3A84]
                or u32(owner,0x3A5C)!=jump(0x8008AA24,link=True)):
            raise ValueError('Changed complete native planting consumer')
        sections=struct.unpack_from('>4I',rel)
        _,_,_,locations,_=native_references(owner,rel,expected_sections=sections)
        if 0x3A5C in locations:raise ValueError('Core foreground commit unexpectedly relocates')
        guard_incoming(owner,sections[0],row['ram'],[(0x3A5C,4)])
        owners.append(dict(role=role,vrom=row['vrom'],ram=row['ram'],entry=0x3928,end=0x3A84,
            call=0x3A5C,source=receipt,native_sha256=native_digest,position=position))
    for offset,digest in SPARKLE:
        raw,receipt=source.function(offset)
        if sha256(raw)!=digest:raise ValueError('Changed complete source sparkle')
        sources.append(receipt)
    native=[]
    for v,digest in ((EFFECT_VROM,'61e868468597dcb83dff869cfa0a3d9edd0b31bde1cdc80eae023d01b67e5ac9'),
            (EFFECT_RELOC,'63235a3382d354d1c555b17a3bfcf7a42b371fb0a6b888139cfdca0e11a71246')):
        data=files[v].extract(base)
        if sha256(data)!=digest or data!=retail[v].extract(original):raise ValueError('Changed complete native sparkle owner')
        native.append(dict(vrom=v,bytes=len(data),sha256=digest))
    controller=files[0x8E0A30].extract(base)
    for a,b,digest in ((0x1028,0x11B4,'b7da6c5965ce5c9339a7c7e258cd439e1af39f3a24de472e856ef1ea58200539'),
            (0x1668,0x1754,'9539f6f3fd2c757a404c14fbe57b4c9880797d06539daa54ac5afc79b0442777')):
        if sha256(controller[a:b])!=digest:raise ValueError('Changed native effect dispatch/clip setup')
    if controller[0x2A00+87*20:0x2A00+88*20]!=bytes.fromhex('008f98e0008f9ce080a31e4080a3224080a32210'):
        raise ValueError('Changed native KIGAE_LIGHT identity')
    return dict(owners=owners,sources=sources,native_effect=native,native_type=87,donor_type=86,
        native_lifetime_frames=15,donor_lifetime_frames=30,additional_resident_bytes=0,
        additional_scene_resident_bytes=0,ordinary_gameplay_tested=False,native_test='pending')
