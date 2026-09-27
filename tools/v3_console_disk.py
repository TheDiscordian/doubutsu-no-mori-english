"""Prepare donor-backed QD services and complete BIOS through console conversion."""
import json
import struct

from aflib import by_vrom,sha256,yaz0_decode
from apply_translation import write_new
from gamecube import rarc_files
from v3_villager_audio import DOL_SHA

ARCHIVE_SHA='3ac09f56fcd3d6cb0c3cad65a9343b951573d5713a6c88515b2afe12b662e9cf'
NOISE_SHA='e1364feb3964247056c6e507393b2860b5834bc46ac48ceb15e954278037cc6a'
DECODED_SHA='11d338e00df0a4dfa2487180be74a07b1d126bbfef941969b6764141599af97b'
BIOS_SHA='eef78986e952e1b3bdac95d9a627768632e75853f538d2fb17bb31b6c6ebce38'
BOOT_STATE_ADDRESS=0x800D6671
BOOT_STATE_BYTES=260
BOOT_STATE_SHA='05177da7b020892c9a592d39a9d67562661ece6958a79c71bedf0cf26e3f558b'
FUNCTIONS=(
    ('fast_load',0x80039DEC,0x1B0,'5c3368ed8f572d7bf54d1b4b024e01279df96e90ad47913d0dfaf8f8e538ac59'),
    ('fast_save',0x80039F9C,0x1A0,'312f6eade5dc8c1ff46f6e3102e10fc207c63810f11d7dee8f24f273314c4ad2'),
    ('reset',0x8003A1C8,0x7E8,'bdca7bf2cec18389ba3f61480091dfa76f307f33d7180df3ee025843fc372702'),
    ('load_io',0x8003BE64,0xC4,'6fbb1ca1533f9fed39c270d94518efd6b2b1ed9beeab6ea66ef5edfcd7c2d09d'),
    ('disk_wdm_irq_store',0x8003C32C,0x3C0,'d234394431358afe8d7a14a484a02cfc0bec3269583febee3d0108d32af9eaf0'),
    ('frame_disk',0x8003B3C0,0x84,'6bd4a8cdc701decd98634377876c6cb7d488b0a9e5fe33b0fc6114dbdf33fc91'))
SOURCES=('tools/v3_console_disk.py','tools/v3_console_games.py','tools/v3_asset_loader.py',
    'overlays/v3/console_disk.c','overlays/v3/console_disk.h','overlays/v3/console_disk.ld')
NATIVE_SOURCES=SOURCES+('overlays/v3/console_disk_native.c','overlays/v3/console_disk_native.h',
    'overlays/v3/console_disk_native.ld','overlays/v3/console_disk_bridge.S')


def prepare_native(output,native,dol):
    from v3_asset_loader import ROOT,compile_part
    from v3_console_games import NATIVE_RAM,NATIVE_SHA
    row=native[0x80836770-NATIVE_RAM+0x42*16:0x80836770-NATIVE_RAM+0x43*16]
    if sha256(native)!=NATIVE_SHA or row.hex()!='80832810000000000000000002ff0200':
        raise ValueError('Changed complete native interpreter/WDM encoding')
    reset_sha='87f7bbad2466c41410365bb23a5f6aeebf8cfe0df5d7863f79a7a5bef2c8e4f5'
    if sha256(dol.read(0x8003A13C,0x8C))!=reset_sha:
        raise ValueError('Changed complete donor reset-button function')
    motor_sha='179bb2cfb701d076fa3a77236c2e139f2a586933216370d9b15291f47d064858'
    if sha256(dol.read(0x80039D58,0x94))!=motor_sha:
        raise ValueError('Changed complete donor disk motor/audio synchronization')
    io=[struct.unpack_from('>I',native,0x80835DD0-NATIVE_RAM+p)[0] for p in (0xC8,0xEC)]
    if io!=[0x808308C4,0x808303E0]:raise ValueError('Changed native bank-2 I/O callbacks')
    code,compiled=compile_part('console_disk_native',output/'console_disk_native',
        extra_sources=('overlays/v3/console_disk.c','overlays/v3/console_disk_bridge.S'))
    receipt=dict(format='AFV3-CONSOLE-DISK-NATIVE-1',compiled=compiled,
        source_native_sha256=NATIVE_SHA,source_wdm_row=row.hex(),
        source_reset_button=dict(address=0x8003A13C,bytes=0x8C,sha256=reset_sha),
        source_motor_sync=dict(address=0x80039D58,bytes=0x94,sha256=motor_sha),
        source_io_callbacks=dict(store=io[0],load=io[1]),
        planned_memory=dict(code=dict(ram=0x80630000,bytes=0x6000),
            immutable_bios=dict(ram=0x80636000,bytes=8192),context=dict(ram=0x80638000,bytes=512),
            boot_state=dict(ram=0x80638200,bytes=260),program=dict(ram=0x8063A000,bytes=32768),
            characters=dict(ram=0x80642000,bytes=8192),private_bios=dict(ram=0x80644000,bytes=8192),
            guard=dict(ram=0x80646000,bytes=16)),
        bytes=len(code),sha256=sha256(code),linked_ram=0x80630000,
        native_state_bytes=0x16F90,minimum_graphics_bytes=0x6008,bridge_stack_bytes=288,
        prepared=['bounded disjoint native buffers','full native CPU bank mapping',
            'four writable programme banks and read-only BIOS','per-instance WDM row',
            'full-width WDM/RAM/read/write/IRQ register bridges','native working/transfer CHR buffers',
            'RSP wait and data-cache writeback calls','cold native state and instruction-table initialization',
            'donor reset-button RAM/PPU/BIOS retention','native disk I/O and scanline IRQ routes',
            'native nametable mirroring','native timed motor audio events and timer waits'],
        pending=['checked startup allocation/packet loading','session initialization and reset call hooks',
            'native image-extent correction','audio initialization/DPCM banks and expansion synthesis',
            'frame/reset/close persistence and ordinary gameplay'],
        installed=False,native_execution_tested=False,
        sources={p:sha256((ROOT/p).read_bytes()) for p in NATIVE_SOURCES})
    write_new(output/'console_disk_native/binding.json',(json.dumps(receipt,indent=2)+'\n').encode())
    return receipt


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
    if sha256(dol.read(BOOT_STATE_ADDRESS,BOOT_STATE_BYTES))!=BOOT_STATE_SHA:
        raise ValueError('Changed complete BIOS fast-boot initialization span')
    return dict(donor='GAFE01-r0',source_dol_sha256=DOL_SHA,source_archive_sha256=ARCHIVE_SHA,
        boot_state=dict(address=BOOT_STATE_ADDRESS,bytes=BOOT_STATE_BYTES,sha256=BOOT_STATE_SHA,
            destination=0xFA,instruction_range=[0x8003C4B4,0x8003C4D0],
            note='Actual loop reads 260 bytes from symbol+1, beyond its eleven-byte declaration'),
        functions=[dict(name=n,address=a,bytes=s,sha256=h) for n,a,s,h in FUNCTIONS],
        bios=dict(path='noise.bin.szs',source_bytes=len(packed),source_sha256=NOISE_SHA,
            decoded_bytes=len(decoded),decoded_sha256=DECODED_SHA,offset=0,bytes=len(bios),sha256=BIOS_SHA,
            runtime_address=0xE000,vectors=[int.from_bytes(bios[p:p+2],'little') for p in (0x1FFA,0x1FFC,0x1FFE)],
            private_reset_patches=[dict(offset=0xEBD,value=0x42),dict(offset=0x1A0,default=0x7F,koro=0xFF)])),bios


def prepare(dol,archive,output,original_rom):
    from v3_asset_loader import ROOT,compile_part
    from v3_console_games import NATIVE_VROM,NATIVE_RAM,NATIVE_SHA
    source,bios=donor_resources(dol,archive)
    native=by_vrom(original_rom)[NATIVE_VROM].extract(original_rom)
    at=0x808328DC-NATIVE_RAM;digest='9fa9e3ec527d580461933ab99d188678992496f44d8dc15e1ba9d92a1c162126'
    if sha256(native)!=NATIVE_SHA or sha256(native[at:at+0x58])!=digest:
        raise ValueError('Changed complete native CHR converter dependency')
    source['native_character_converter']=dict(address=0x808328DC,bytes=0x58,sha256=digest,
        source_vrom=NATIVE_VROM,source_sha256=NATIVE_SHA)
    code,compiled=compile_part('console_disk',output/'console_disk')
    write_new(output/'console_disk/bios.bin',bios)
    write_new(output/'console_disk/boot-state.bin',dol.read(BOOT_STATE_ADDRESS,BOOT_STATE_BYTES))
    report=dict(format='AFV3-CONSOLE-DISK-1',source=source,compiled=compiled,
        bytes=len(code),sha256=sha256(code),linked_ram=0,
        memory=dict(side_bytes=65536,maximum_sides=4,work_bytes=2048,program_bytes=32768,
            character_bytes=8192,bios_bytes=8192,boot_state_bytes=BOOT_STATE_BYTES),
        prepared=['complete donor BIOS','bounded boot loading','bounded BIOS save requests',
            'complete fast-boot initialization span','private BIOS reset patches','five BIOS WDM services',
            'complete native CHR tile conversion',
            'disk register reads/writes','source scanline IRQ state','source frame/ready/motor state'],
        pending=['installation of prepared native module and complete buffer allocations',
            'audio initialization/DPCM banks and expansion synthesis',
            'native image-extent and session hooks','native startup and normal room return'],
        native_hooks_installed=False,choice_eligible=False,
        sources={s:sha256((ROOT/s).read_bytes()) for s in SOURCES})
    report['native_binding']=prepare_native(output,native,dol)
    write_new(output/'console_disk/disk.json',(json.dumps(report,indent=2)+'\n').encode())
    return report
