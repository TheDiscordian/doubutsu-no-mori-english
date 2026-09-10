"""Exact compiled accent adapters and retention of their preceding complete images."""
import struct
from aflib import sha256
from accent_mail_overlays import Overlay,source_hashes
from npc_mail_show import relocate_verified_data
from toolchain import profile_sha256

PROFILES={
    'creator':('3191836866095ec469c525c95e967aa3eef246d8a214a2a8dcba3bc6873b9a6a',
        '9eb9663c324fd4f120977b6249b67bb656544824e4c9a560431cbda7bbe00de9',
        'ecc48db26cc23b3c23fc8f120319563181948887be968f143f7d02b44cacc24c'),
    'notice':('eaf772494d66ff026be8debd45a4cfbc9786e913b71251a310e6121e982bf96a',
        'b7a187f3540edacaa0d66ec7bb602e2095ca7710b4987c0140d72461d8cb481d',
        '2dd2cc072227d26ed645184981f209b077b165db0f2b86e11c67be3896239168'),
    'event':('705d164da8e678a5948849c016c25b83a17d14cf66ad4f7d52312d7abe1bf88f',
        '8fcde6e3c4b2fb84c956e92043637091209c901f8d493c1cea5484aebe842e2b',
        '5e87254084e743ef9dbc0d4b4d7bc9faede2a8f2b7623ade973f210033a9011c'),
}
NAMES_SHA='693ef2c0749822d07062114ffff0b35b4bb8a56d3b2617c932d9220dcc92165b'
ARTICLES_SHA='b218119460fdbb472e641cbbc6d77ff809d489bda8b8622f0157562294d575ff'


def wrap(extension):
    result={**extension['previous_overlay'],'bytes':extension['bytes'],
        'overlay_sha256':extension['sha256'],'relocation_bytes':extension['relocation_bytes'],
        'relocation_sha256':extension['relocation_sha256'],'accent_mail':extension}
    if extension['kind']=='creator':
        result.update(item_names_sha256=NAMES_SHA,item_articles_sha256=ARTICLES_SHA)
    return result


def validate(kind,data,reloc,report):
    extension=report.get('accent_mail')
    if not isinstance(extension,dict) or kind not in PROFILES:raise ValueError('Missing accent overlay profile')
    if ((profile_sha256(extension),sha256(data),sha256(reloc))!=PROFILES[kind]
            or extension.get('sources')!=source_hashes() or report!=wrap(extension)):
        raise ValueError('Changed complete accent '+kind+' code, sources, or metadata')
    prefix=extension['prefix_bytes'];original=bytearray(data[:prefix]);changed=bytearray(prefix)
    for patch in extension['patches']:
        at=patch['at'];before=bytes.fromhex(patch['before']);after=bytes.fromhex(patch['after'])
        if len(before)!=len(after) or data[at:at+len(after)]!=after:
            raise ValueError('Missing installed accent entry or article data')
        original[at:at+len(before)]=before;changed[at:at+len(before)]=bytes([1])*len(before)
    original=bytes(original);oldrel=bytes.fromhex(extension['previous_relocation'])
    if (sha256(original)!=extension['previous_sha256'] or sha256(oldrel)!=extension['previous_relocation_sha256']):
        raise ValueError('Accent adapter changes unrelated preceding code/data')
    spec=Overlay(report['ram'],len(data),struct.unpack_from('>5I',reloc))
    old=Overlay(report['ram'],len(original),struct.unpack_from('>5I',oldrel))
    for base in (0x801A0010,0x802F8010):
        moved=relocate_verified_data(spec,data,reloc,base)
        retained=relocate_verified_data(old,original,oldrel,base)
        if any(a!=b and not changed[i] for i,(a,b) in enumerate(zip(moved[:prefix],retained))):
            raise ValueError('Accent relocation changes retained prefix instructions or data')
    return original,oldrel,extension['previous_overlay'],spec
