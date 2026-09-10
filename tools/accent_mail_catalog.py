#!/usr/bin/env python3
"""Frozen catalogue five retains all wording and opts into literal accent pairs."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from aflib import sha256
from accent_mail_format import CATALOG,SEMANTICS,VROM
from mail_catalog import verify_registered,templates as previous_templates,REGISTRY

PREVIOUS_SHA='76aa61189ccc1043ee4d91f3fd7a2d351b0914b4a932515b47b5bcbe426323bb'
SHA='26b2e95b10b8ae049853ecc6180e41c12b86efc677e39ee03f9742077e9005be'
SIZE=326288


def resource(previous):
    if sha256(previous)!=PREVIOUS_SHA or verify_registered(previous)['catalog']!=4:
        raise ValueError('Literal accents require the frozen complete preceding catalogue')
    result=bytearray(previous);struct.pack_into('>2I',result,8,CATALOG,SEMANTICS)
    if sha256(result)!=SHA:raise ValueError('Changed complete accent catalogue')
    return bytes(result)


def preceding(data):
    if len(data)!=SIZE or sha256(data)!=SHA:
        raise ValueError('Changed immutable accent catalogue')
    previous=bytearray(data);struct.pack_into('>2I',previous,8,4,2)
    if sha256(previous)!=PREVIOUS_SHA:raise ValueError('Changed accent wording or payload')
    return bytes(previous)


def verify(data):
    details=verify_registered(preceding(data))
    actual={**details,'catalog':CATALOG,'semantics':SEMANTICS,'sha256':SHA}
    registry=json.loads(REGISTRY.read_text())
    entries=[r for r in registry['catalogs'] if r['catalog']==CATALOG]
    if len(entries)!=1 or any(entries[0].get(k)!=v for k,v in actual.items()):
        raise ValueError('Unregistered accent catalogue semantics')
    return actual


def verify_shop_compatibility(original,data):
    """The selected catalogue-two sale wording must survive an accent upgrade."""
    from mail_record import Record
    if verify_registered(original)['catalog']!=2:raise ValueError('Shop compatibility requires catalogue two')
    verify(data)
    for identity in range(2,18):
        before=previous_templates(original,Record(2,0,(identity,),()))
        after=templates(data,Record(5,0,(identity,),()))
        if before.parts!=after.parts:raise ValueError('Accent upgrade changes existing shop leaflet wording')
    return 16


def templates(data,record):
    verify(data)
    if record.catalog!=CATALOG:raise ValueError('Accent template identity differs from the snapshot')
    return replace(previous_templates(preceding(data),replace(record,catalog=4)),catalog=CATALOG)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous',type=Path,default=Path('build/mail-glyph-catalog/catalog.bin'))
    p.add_argument('--output',type=Path,default=Path('build/accent-mail-catalog'))
    a=p.parse_args();data=resource(a.previous.read_bytes());report=verify(data)
    shop=verify_shop_compatibility(Path('build/mail-catalog/catalog.bin').read_bytes(),data)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'catalog.bin').write_bytes(data)
    (a.output/'catalog.json').write_text(json.dumps({**report,'vrom':f'{VROM:08X}',
        'registered':True,'installed':False,'previous_catalog_sha256':PREVIOUS_SHA,
        'unchanged_shop_templates':shop},indent=2)+'\n')
    print(json.dumps({'catalog':CATALOG,'bytes':SIZE,'sha256':SHA,'installed':False}))


if __name__=='__main__':main()
