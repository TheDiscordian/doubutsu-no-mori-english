"""Reserve and preload the shared disk engine without enabling unfinished games."""
import copy
import json
import zlib

from aflib import sha256
from v3_asset_loader import BLOB,ROOT
from v3_console_disk import BIOS_SHA,BOOT_STATE_SHA,NATIVE_SOURCES
from v3_furniture_capacity import checked as checked_model_capacity

RAM,END=0x80630000,0x80646010
LAYOUT=dict(code=dict(ram=RAM,bytes=0x6000),
    immutable_bios=dict(ram=0x80636000,bytes=8192),context=dict(ram=0x80638000,bytes=512),
    boot_state=dict(ram=0x80638200,bytes=260),program=dict(ram=0x8063A000,bytes=32768),
    characters=dict(ram=0x80642000,bytes=8192),private_bios=dict(ram=0x80644000,bytes=8192),
    guard=dict(ram=0x80646000,bytes=16))
SOURCES=('tools/v3_console_disk_install.py','tools/v3_furniture_install.py',
    'tools/v3_room_goods.py','overlays/v3/surface_bootstrap.c')


def reservations(value):
    if isinstance(value,dict):
        if type(value.get('ram')) is int and type(value.get('bytes')) is int:
            yield value['ram'],value['ram']+value['bytes']
        if type(value.get('start')) is int and type(value.get('end')) is int:
            yield value['start'],value['end']
        # Some native buffers carry a code-function byte count alongside their
        # RAM destination/end. The byte count is not their data reservation.
        for first,last in (('ram','end'),('pixels_ram','pixels_end')):
            if (type(value.get(first)) is int and type(value.get(last)) is int
                    and 0x80000000<=value[first]<value[last]<=0x80800000):
                yield value[first],value[last]
        for v in value.values():yield from reservations(v)
    elif isinstance(value,list):
        for v in value:yield from reservations(v)


def packet(directory):
    receipt=json.loads((directory/'console_disk_native/binding.json').read_bytes())
    code=(directory/'console_disk_native/code.bin').read_bytes()
    bios=(directory/'console_disk/bios.bin').read_bytes()
    boot=(directory/'console_disk/boot-state.bin').read_bytes()
    if (receipt['planned_memory']!=LAYOUT or receipt['linked_ram']!=RAM or
            not 0<len(code)<=LAYOUT['code']['bytes'] or receipt['bytes']!=len(code) or
            sha256(code)!=receipt['sha256'] or len(bios)!=8192 or sha256(bios)!=BIOS_SHA or
            len(boot)!=260 or sha256(boot)!=BOOT_STATE_SHA or
            set(receipt['sources'])!=set(NATIVE_SOURCES)):
        raise ValueError('Changed complete prepared disk module/resources')
    for path,digest in receipt['sources'].items():
        if sha256((ROOT/path).read_bytes())!=digest:raise ValueError('Stale disk module source: '+path)
    raw=bytearray(END-RAM)
    for name,data in [('code',code),('immutable_bios',bios),('boot_state',boot),('private_bios',bios)]:
        at=LAYOUT[name]['ram']-RAM;raw[at:at+len(data)]=data
    raw[-16:]=bytes.fromhex('51444721')*4
    return bytes(raw),receipt


def install(base,prior,blob,output,directory):
    del output # The shared refresh owns output files and bootstrap compilation.
    checked_model_capacity(base,prior)
    equipment=copy.deepcopy(prior['equipment_resources'])
    if equipment.get('console_disk') or not equipment.get('console_images',{}).get('emulator',{}).get('installed'):
        raise ValueError('Disk module requires installed console lifecycle and a fresh reservation')
    if (prior['furniture']['bank_pool']['end']>RAM or END>0x807DA800 or
            any(a<END and RAM<b for a,b in reservations(prior))):
        raise ValueError('Disk module overlaps retained resident memory')
    raw,prepared=packet(directory)
    blob.extend(bytes(-len(blob)%16));at=len(blob);blob.extend(raw)
    equipment['console_disk']=dict(format='AFV3-CONSOLE-DISK-RESIDENT-1',
        packet=dict(ram=RAM,bytes=len(raw),blob_offset=at,vrom=BLOB+at,
            sha256=sha256(raw),crc32=zlib.crc32(raw)),
        layout=copy.deepcopy(LAYOUT),prepared=prepared,
        installed=True,session_hooks_installed=False,native_execution_tested=False,
        choice_eligible=False,choices_added=0,save_format_changed=False,
        pending=['audio/DPCM and initialization/reset hooks','image-extent consumer',
                 'session/frame/reset/return persistence and ordinary gameplay'],
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return equipment,{}
