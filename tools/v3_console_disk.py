"""Prepare donor-backed QD services and complete BIOS through console conversion."""
import json

from aflib import sha256,yaz0_decode
from apply_translation import write_new
from gamecube import rarc_files
from v3_villager_audio import DOL_SHA

ARCHIVE_SHA='3ac09f56fcd3d6cb0c3cad65a9343b951573d5713a6c88515b2afe12b662e9cf'
NOISE_SHA='e1364feb3964247056c6e507393b2860b5834bc46ac48ceb15e954278037cc6a'
DECODED_SHA='11d338e00df0a4dfa2487180be74a07b1d126bbfef941969b6764141599af97b'
BIOS_SHA='eef78986e952e1b3bdac95d9a627768632e75853f538d2fb17bb31b6c6ebce38'
FUNCTIONS=(
    ('fast_load',0x80039DEC,0x1B0,'5c3368ed8f572d7bf54d1b4b024e01279df96e90ad47913d0dfaf8f8e538ac59'),
    ('fast_save',0x80039F9C,0x1A0,'312f6eade5dc8c1ff46f6e3102e10fc207c63810f11d7dee8f24f273314c4ad2'),
    ('reset',0x8003A1C8,0x7E8,'bdca7bf2cec18389ba3f61480091dfa76f307f33d7180df3ee025843fc372702'),
    ('load_io',0x8003BE64,0xC4,'6fbb1ca1533f9fed39c270d94518efd6b2b1ed9beeab6ea66ef5edfcd7c2d09d'),
    ('disk_wdm_irq_store',0x8003C32C,0x3C0,'d234394431358afe8d7a14a484a02cfc0bec3269583febee3d0108d32af9eaf0'),
    ('frame_disk',0x8003B3C0,0x84,'6bd4a8cdc701decd98634377876c6cb7d488b0a9e5fe33b0fc6114dbdf33fc91'))
SOURCES=('tools/v3_console_disk.py','tools/v3_console_games.py','tools/v3_asset_loader.py',
    'overlays/v3/console_disk.c','overlays/v3/console_disk.h','overlays/v3/console_disk.ld')


def donor_resources(dol,archive):
    if sha256(dol.data)!=DOL_SHA or sha256(archive)!=ARCHIVE_SHA:
        raise ValueError('Changed complete QD donor executable/archive')
    for name,address,size,digest in FUNCTIONS:
        if sha256(dol.read(address,size))!=digest:raise ValueError('Changed QD source function: '+name)
    files=dict(rarc_files(archive));packed=files.get('noise.bin.szs',b'')
    if sha256(packed)!=NOISE_SHA:raise ValueError('Changed complete donor noise/BIOS resource')
    decoded=yaz0_decode(packed);bios=decoded[:8192]
    if len(decoded)!=0x7F000 or sha256(decoded)!=DECODED_SHA or sha256(bios)!=BIOS_SHA:
        raise ValueError('Changed complete decoded noise/BIOS resource')
    return dict(donor='GAFE01-r0',source_dol_sha256=DOL_SHA,source_archive_sha256=ARCHIVE_SHA,
        functions=[dict(name=n,address=a,bytes=s,sha256=h) for n,a,s,h in FUNCTIONS],
        bios=dict(path='noise.bin.szs',source_bytes=len(packed),source_sha256=NOISE_SHA,
            decoded_bytes=len(decoded),decoded_sha256=DECODED_SHA,offset=0,bytes=len(bios),sha256=BIOS_SHA,
            runtime_address=0xE000,vectors=[int.from_bytes(bios[p:p+2],'little') for p in (0x1FFA,0x1FFC,0x1FFE)],
            private_reset_patches=[dict(offset=0xEBD,value=0x42),dict(offset=0x1A0,default=0x7F,koro=0xFF)])),bios


def prepare(dol,archive,output):
    from v3_asset_loader import ROOT,compile_part
    source,bios=donor_resources(dol,archive)
    code,compiled=compile_part('console_disk',output/'console_disk')
    write_new(output/'console_disk/bios.bin',bios)
    report=dict(format='AFV3-CONSOLE-DISK-1',source=source,compiled=compiled,
        bytes=len(code),sha256=sha256(code),linked_ram=0,
        memory=dict(side_bytes=65536,maximum_sides=4,work_bytes=2048,program_bytes=32768,
            character_bytes=8192,bios_bytes=8192),
        prepared=['complete donor BIOS','bounded boot loading','bounded BIOS save requests',
            'disk register reads/writes','source scanline IRQ state','source frame/ready/motor state'],
        pending=['native disk-state allocation and reset mapping','BIOS WDM instruction bridge',
            'CPU/PPU register and scanline bindings','character conversion','expansion sound and motor synchronization',
            'native startup and normal room return'],
        native_hooks_installed=False,choice_eligible=False,
        sources={s:sha256((ROOT/s).read_bytes()) for s in SOURCES})
    write_new(output/'console_disk/disk.json',(json.dumps(report,indent=2)+'\n').encode())
    return report
