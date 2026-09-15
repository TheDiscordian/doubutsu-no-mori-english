"""Verified school-desk identities, profiles, stock, and scoring for integration."""
import argparse
import json
from pathlib import Path
import re
import struct
from aflib import sha256
from apply_translation import write_new
from gc_names import rel_sections,symbol_data
from item_identity_sheet import SHEET_SHA,sheet_rows
from v3_asset_loader import ROOT
from v3_furniture_art import SCHOOL_DESKS,prepare,verify_sources

PROPERTIES={0x3200:(1240,'ftr_listA',0x4C058000,237,0),
            0x3204:(1240,'ftr_listB',0x4C058100,238,0),
            0x3220:(1580,'ftr_listB',0x4C050140,243,1)}


def metadata(rel,raw_symbols,worksheet):
    verify_sources(rel,raw_symbols)
    if sha256(worksheet.read_bytes())!=SHEET_SHA:raise ValueError('Changed item identity worksheet')
    sheet=list(sheet_rows(worksheet,'Items'))
    if any(sheet[0][1].get(k)!=v for k,v in {'C':'ID (AF)','E':'ID (AC)','H':'Name (AF)','J':'Name (English)'}.items()):
        raise ValueError('Changed identity columns')
    symbols=raw_symbols.decode();base=rel_sections(rel)[5][0]
    prices=symbol_data(rel,symbols,'ftr_price_table');catalogue=symbol_data(rel,symbols,'mCL_furniture_list')
    hra=rel[base+0x4FAFC:base+0x4FAFC+1266*4];feng=rel[base+0x4EBF0:base+0x4EBF0+1266*2]
    series=symbol_data(rel,symbols,'mMkRm_series_info');names=symbol_data(rel,symbols,'mMkRm_series_name')
    if (len(prices)!=1267*2 or sha256(hra)!='231d23625c126b048d95be99f397e2f05f564af23423c1f911d706acaec37f0e'
        or sha256(feng)!='5700370581b13dd85eb1102656f858c9c4dbb4752c646c3ad563893937a2517a'
        or sha256(catalogue)!='91bad7d2198f5da32b464547c3a3c15df9cc77e1969ad7eebc7c0fa45f66956f'
        or series[57:60]!=bytes.fromhex('020006') or names[304:320]!=b'school          '):
        raise ValueError('Changed complete price, scoring, school series, or catalogue sources')
    list_names=re.findall(r'^(ftr_list\w*) =',symbols,re.M)
    if len(list_names)!=23 or len(set(list_names))!=23:raise ValueError('Changed furniture stock inventory')
    lists={n:symbol_data(rel,symbols,n) for n in list_names};rows=[];records=bytearray()
    for pilot in SCHOOL_DESKS:
        # Full model/profile/relocation verification also rejects dropped chair behaviour.
        prepare(rel,raw_symbols,pilot)
        matches=[(n,c) for n,c in sheet[1:] if c.get('E')==f'{pilot.item:04X}']
        if len(matches)!=1 or matches[0][1].get('J')!=pilot.name or any(matches[0][1].get(k)!='-' for k in ('C','H','CG','CJ')):
            raise ValueError('Ambiguous school-desk native identity')
        price,stock,value,position,size=PROPERTIES[pilot.item];index=1024+(pilot.item-0x3000)//4
        members=[]
        for n,data in lists.items():
            if not data or len(data)%2:raise ValueError('Invalid stock list')
            ids=struct.unpack('>'+str(len(data)//2)+'H',data)
            if pilot.item in ids:members.append((n,ids.count(pilot.item)))
        if (int.from_bytes(prices[index*2:index*2+2],'big')!=price or members!=[(stock,1)]
            or hra[index*4:index*4+4]!=value.to_bytes(4,'big') or feng[index*2:index*2+2]!=bytes(2)
            or [(n,m) for n,(i,m) in enumerate(struct.iter_unpack('>HH',catalogue)) if i==index]!=[(position,0)]):
            raise ValueError('Changed school-desk stock, price, scoring, or preview')
        record=struct.pack('>HHHBB',index,pilot.item,price,size,1)+pilot.name.encode().ljust(16,b' ')+bytes(8)
        records.extend(record)
        birth,surface=value>>8&63,value>>6&3
        native=(value&0xFFFFC000)|(birth<<9)|(surface<<7)
        rows.append(dict(id=f'GAFE01-r0/item/{pilot.item:04X}',name=pilot.name,item_id=f'{pilot.item:04X}',
            runtime_index=index,price=price,stock_group='ABC'.index(stock[-1]),donor_list=stock,
            donor_list_sha256=sha256(lists[stock]),donor_catalogue_position=position,preview_mode=0,
            footprint='2x1' if size else '1x1',size_code=size,series=19,birth_category=birth,surface=surface,
            donor_hra_hex=f'{value:08x}',native_hra_hex=f'{native:08x}',feng_hex='0000',
            contact_action=pilot.contact_action,donor_profile=pilot.profile,
            donor_profile_sha256=sha256(symbol_data(rel,symbols,pilot.profile)),
            donor_name_sha256=sha256(pilot.name.encode().ljust(16,b' ')),record_sha256=sha256(record),
            identity_worksheet_row=matches[0][0],runtime_installed=False,selectable=False,
            remaining=['fixed runtime identity, model loader, names, stock, catalogue, scoring, and profile integration',
                       'native seating-reader verification' if pilot.contact_action else 'native two-cell placement verification',
                       'ordinary acquisition, interaction, and persistence']))
    return bytes(records),rows


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'build'):raise ValueError('Use a fresh ignored build directory')
    data,rows=metadata((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),ROOT/'build/item-identity-megasheet.xlsx')
    report=dict(format='AFV3-SCHOOL-DESKS-1',rows=rows,records_sha256=sha256(data),
                runtime_installed=False,source_worksheet_sha256=SHEET_SHA)
    out.mkdir(parents=True);write_new(out/'items.bin',data)
    write_new(out/'items.json',(json.dumps(report,indent=2)+'\n').encode());print(json.dumps(report,indent=2))


if __name__=='__main__':main()
