"""Exact startup-owned literal-mail profile; saved interpretations remain immutable."""
import struct
from aflib import sha256

PROFILE={
    'bytes':11344,'relocation_bytes':672,
    'image_sha256':'f2bbd23684cb682ef38712e6d2dc5b5b971b5f8ec2c1e2feb756b09631078d98',
    'relocation_sha256':'6c9fda4a52beb4dfbe5aa57e1e39693f2ce2d67be8edcc26e24048216a11d657',
    'symbols':{'af_world_reset':1896,'af_world_load':1976,'af_world_measure':2100,
        'af_world_draw':2268,'af_world_font_install':2368,'world_hooks':10808,
        'world_pixels':11320,'world_name':11324,'af_accent_mail_format':4080,
        'af_accent_catalog_header_valid':4772,'af_accent_mail_restore':5060,
        'af_accent_capture_reset':6484,'af_accent_capture_set':6520,
        'af_accent_mail_generate':6916,'af_accent_item_literal':8196,
        'af_accent_next_line':8352,'af_accent_font_install':8772,'mail_hooks':11248},
}
IMPORTS={'af_crc32':0x80195938,'af_mail_record_pack':0x80198DD4,'af_mail_record_unpack':0x80198FDC}
HOOKS={
    0x80197654:(0x27BDFB38,0xAFBF04C4,'af_accent_mail_format'),
    0x80196C28:(0x14800003,0,'af_accent_mail_restore'),
    0x80196B34:(0x1080003A,0x1025,'af_accent_catalog_header_valid'),
    0x801992A8:(0x14800003,0x1025,'af_accent_next_line'),
}


def validate(data,reloc,report):
    if (report.get('mail_literals') is not True or report.get('imports')!=IMPORTS
            or len(data)!=PROFILE['bytes'] or len(reloc)!=PROFILE['relocation_bytes']
            or sha256(data)!=PROFILE['image_sha256'] or sha256(reloc)!=PROFILE['relocation_sha256']):
        raise ValueError('Changed exact literal-mail font profile')
    symbols=report['symbols']
    if any(symbols.get(k)!=v for k,v in PROFILE['symbols'].items()):
        raise ValueError('Changed complete literal-mail symbol layout')
    rows=b''.join(struct.pack('>4I',address,first,second,0x80C00000+symbols[target])
                  for address,(first,second,target) in HOOKS.items())
    at=symbols['mail_hooks']
    if data[at:at+len(rows)]!=rows:raise ValueError('Changed complete literal-mail startup guards')
    if data[:8]!=struct.pack('>2I',0x08000000|((0x80C00000+symbols['af_accent_font_install'])>>2)&0x3FFFFFF,0):
        raise ValueError('Missing atomic literal-mail startup entry')
