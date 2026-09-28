"""Prepare all shared diary/calendar/prompt artwork in one native UI packet."""
import argparse
import json
import struct
from pathlib import Path

from aflib import sha256
from apply_translation import write_new
from v3_furniture_pipeline import ROOT,Source,assemble_models
from map_artwork import compile_commands_batch
from v3_ui_art import Packet

MONTHS=('january','february','march','april','may','june','july','august',
        'september','october','november','december')
STATE=('needlework_before_model','cal_win_nen_before','cal_icon_yajirushi_model',
       'dia_init_mode','dia_init_mode_letter','lat_kakunin_DL_mode')
DIRECT=('cal_win_futi_model','cal_win_shita_model','cal_win_nitiyouT_model',
    'cal_win_doyouT_model','cal_win_hijituT_model','cal_icon_mark_model',
    'cal_icon_cursor_model','cal_icon_sakana_model','cal_hyouji_3DT_model',
    'cal_hyouji_shitaT_model','cal_hyouji_b2_model','cal_hyouji_amojiT_model',
    'cal_hyouji2_shitaT_model','cal_hyouji2_bt_model','cal_hyouji2_b2_model',
    'cal_hyouji2_amojiT_model','cal_hyouji2_bmojiT_model',
    'dia_win_wT_model','dia_win_fusenT_model','dia_win_moji_model',
    'dia_win2_wT_model','dia_win2_fusenT_model','dia_win3_wT_model','dia_win3_fusenT_model',
    'dia_win_bb_model','dia_win_mojiT_model','dia_att_winT_model','dia_att_cursor_model',
    'lat_kakunin_wakuT_model','lat_kakunin_c_model',
    'lat_sentaku2_winT_model','lat_sentaku2_c_model','lat_sentaku_winT_model','lat_sentaku_c_model')
INHERITED={
    'cal_win_tuki_model':((32,32,2,0),True),
    'cal_win_eventT_model':((32,64,3,1),False),
    'cal_win_monthT_model':((32,128,3,1),False),
    'cal_win_boxT_model':((32,32,3,1),False),
    'cal_win_suuji_model':((16,16,4,0),False),
    'cal_hyouji_stT_model':((64,64,3,1),False),
    'dia_win_tukiT_model':((16,64,3,1),False),
}
# Some revision-zero symbols have suffixed source labels but unsuffixed names
# in the link map. Bind the actual address, not a later revision's lookalike.
REVISION_MODELS=(('diary_read_button',0x4075A0),('diary_read_label',0x407620))


def source_tables(source):
    """Keep month ordering, palettes, colours, and lettering from real callers."""
    expected={
        'back_pal_table':[f'cal_win_tuki{i}_pal' for i in range(1,13)],
        'back_tex_table':['cal_win_tuki1_tex']+['cal_win_tuki2_tex']*11,
        'month_tex_table':[f'cal_win_{m}_tex_rgb_ia8' for m in MONTHS],
        'month_tex_table$867':[f'dia_win_{m}_tex_rgb_ia8' for m in MONTHS],
        'suuji_tex_table':[f'cal_win_suuji{i}_tex_rgb_i4' for i in range(1,32)],
        'cal_win_nen_txt_table':[f'cal_win_nen{i}_tex_rgb_i4' for i in range(10)],
        'cal_hyoji_txt_table':['cal_hyouji_st1_tex_rgb_ia8','cal_hyouji_st5_tex_rgb_ia8'],
        'cal_win_nen_table':[f'cal_win_nen{i}_model' for i in range(4,0,-1)],
    }
    result={}
    for name,targets in expected.items():
        at,n=source.symbol(name);raw=source.raw(name)
        pointers={at+i*4:source.symbol(target)[0] for i,target in enumerate(targets)}
        if n!=len(targets)*4 or raw!=bytes(n) or source.pointers(at,n)!=pointers:
            raise ValueError('Changed diary screen caller resource table: '+name)
        result[name]=dict(offset=at,bytes=n,sha256=sha256(raw),targets=targets)
    for name,n in (('box_prim_table',15),('box_env_table',15),('number_prim_table',15),
        ('number2_prim_table',15),('icon_mark_prim_table',9),('month_tex_adjust$868',48)):
        at,size=source.symbol(name);raw=source.raw(name)
        if size!=n or source.pointers(at,size):raise ValueError('Changed diary drawing table: '+name)
        values=list(struct.unpack('>12f',raw)) if n==48 else [list(raw[i:i+3]) for i in range(0,n,3)]
        result[name]=dict(offset=at,bytes=n,sha256=sha256(raw),values=values)
    return result


def prepare(source):
    source_tables(source)
    packet=Packet(source)
    for name in STATE:packet.model(name,[name],state_only=True)
    for name in DIRECT:packet.model(name,[name])
    for label,at in REVISION_MODELS:
        packet.model(label,[source.containing(at,exact=True)])
    for name,(shape,palette) in INHERITED.items():
        packet.model(name,[name],texture=shape,palette=palette)
    for i in range(1,5):
        name=f'cal_win_nen{i}_model'
        packet.model(name,[name],texture=(16,16,4,0),combiner=(0xFCFFFFFF,0xFFFDF238))
    for name in ('cal_icon_yajirushi_gfx','cal_icon_yajirushi_gfx2'):
        packet.model(name,['cal_icon_yajirushi_model',name])
    for name in ('cal_hyoji_yajiA_gfx','cal_hyoji_yajiB_gfx'):
        packet.model(name,['cal_hyoji_yaji1T_model',name])
    for i,month in enumerate(MONTHS):
        packet.material(f'calendar_palette_{i}',f'cal_win_tuki{i+1}_pal')
        packet.material(f'calendar_month_{i}',f'cal_win_{month}_tex_rgb_ia8',(32,128,3,1))
        packet.material(f'diary_month_{i}',f'dia_win_{month}_tex_rgb_ia8',(16,64,3,1))
    for i in (1,2):packet.material(f'calendar_background_{i}',f'cal_win_tuki{i}_tex',(32,32,2,0))
    for i in range(1,32):packet.material(f'calendar_day_{i}',f'cal_win_suuji{i}_tex_rgb_i4',(16,16,4,0))
    for i in range(10):packet.material(f'calendar_year_{i}',f'cal_win_nen{i}_tex_rgb_i4',(16,16,4,0))
    for label,name,shape in (
        ('calendar_box','cal_win_box_tex_rgb_ia8',(32,32,3,1)),
        ('calendar_box_selected','cal_win_box2_tex_rgb_ia8',(32,32,3,1)),
        ('calendar_event','cal_win_event_tex',(32,64,3,1)),
        ('calendar_stick','cal_hyouji_st1_tex_rgb_ia8',(64,64,3,1)),
        ('calendar_stick_tilt','cal_hyouji_st5_tex_rgb_ia8',(64,64,3,1)),
    ):packet.material(label,name,shape)
    return packet.prepared()


def provenance(resources):
    entries={r['id']:r for r in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
    ids=[]
    for row in resources:
        if row['kind']!='texture':continue
        key=f"v3/diary/art/{row['symbol']}/{row['donor_offset']:08X}";credit=entries[key]['locales']['en']
        if (credit['credit']!='official' or credit['encoded_sha256']!=row['output_sha256'] or
                credit['source']['symbol']!=row['symbol'] or
                credit['source']['reference_sha256']!=row['source_sha256'] or
                credit['source']['data_offset']!=f"{row['donor_offset']:08X}"):
            raise ValueError('Changed diary bitmap lettering provenance: '+key)
        ids.append(key)
    return ids


def draw_header(source,offsets):
    """Original bindings for the shared native renderer, with no ROM addresses."""
    from v3_diaries import ui_text
    lines=['/* Generated local donor bindings; not a distribution asset. */']
    for name,at in offsets.items():lines.append(f'#define ART_{name} 0x{0x06000000+at:08X}u')
    for name,labels in (
        ('calendar_palettes',[f'calendar_palette_{i}' for i in range(12)]),
        ('calendar_months',[f'calendar_month_{i}' for i in range(12)]),
        ('diary_months',[f'diary_month_{i}' for i in range(12)]),
        ('calendar_days',[f'calendar_day_{i}' for i in range(1,32)]),
        ('calendar_years',[f'calendar_year_{i}' for i in range(10)]),
        ('calendar_year_models',[f'cal_win_nen{i}_model' for i in range(4,0,-1)])):
        lines.append('static const unsigned int '+name+'[]={'+','.join('ART_'+n for n in labels)+'};')
    for name,row in source_tables(source).items():
        if 'values' not in row:continue
        if name=='month_tex_adjust$868':
            lines.append('static const float diary_month_adjust[]={'+','.join(str(v)+'f' for v in row['values'])+'};')
        else:
            lines.append('static const unsigned char '+name+'[][3]={'+
                ','.join('{'+','.join(map(str,v))+'}' for v in row['values'])+'};')
    for name,row in ui_text(source).items():
        lines.append('static const unsigned char diary_text_'+name.replace('-','_')+'[]={'+
                     ','.join(map(str,bytes.fromhex(row['encoded'])))+'};')
    return ('\n'.join(lines)+'\n').encode()


def build(output,reuse=None):
    output=Path(output).resolve()
    if not output.is_relative_to(ROOT/'build') or output.exists():
        raise ValueError('Screen output must be a new ignored build directory')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    prepared=prepare(source)
    credits=provenance(prepared[2])
    output.mkdir(parents=True)
    commands=output/'commands.c';write_new(commands,prepared[5].encode())
    reused=None
    if reuse is None:
        compiled=compile_commands_batch(output/'gbi',[('screen',commands,prepared[6])])['screen']
    else:
        reuse=Path(reuse).resolve();previous=json.loads((reuse/'screen.json').read_bytes())
        old=(reuse/previous['file']).read_bytes()
        if (not reuse.is_relative_to(ROOT/'build') or sha256(old)!=previous['sha256'] or
                previous['source_rel_sha256']!=sha256(source.rel) or
                previous['source_symbols_sha256']!=sha256(source.symbols.encode()) or
                previous['resources']!=prepared[2] or (reuse/'commands.c').read_text()!=prepared[5]):
            raise ValueError('Prepared UI packet differs from complete current resources/commands')
        compiled={}
        for model in previous['models']:
            label=model['layer'];at=model['native_offset'];n=model['bytes'];code=old[at:at+n]
            if label in compiled or sha256(code)!=model['output_sha256']:
                raise ValueError('Prepared UI model is incomplete or duplicated')
            compiled[label]=code
        reused=dict(report=str((reuse/'screen.json').relative_to(ROOT)),sha256=sha256(old))
    data,offsets,models,_=assemble_models(prepared,compiled)
    write_new(output/'screen.bin',data)
    header=draw_header(source,offsets);write_new(output/'diary-art.inc',header)
    report=dict(format='AFV3-DIARY-SCREEN-1',bytes=len(data),sha256=sha256(data),file='screen.bin',
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()),
        resources=prepared[2],models=models,offsets=offsets,source_tables=source_tables(source),
        provenance_ids=credits,
        caller_contracts={name:model.get('caller') for name,model in prepared[4].items() if 'caller' in model},
        native_installed=False,rendered=False,reused=reused,draw_header_sha256=sha256(header),
        sources={p:sha256((ROOT/p).read_bytes()) for p in (
            'tools/v3_ui_art.py','tools/v3_diary_screen.py','tools/v3_furniture_art.py',
            'tools/v3_furniture_pipeline.py','tools/map_artwork.py','translations/provenance.json')})
    write_new(output/'screen.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reuse',type=Path)
    args=parser.parse_args();result=build(args.output,args.reuse)
    print(json.dumps({k:result[k] for k in ('bytes','sha256','native_installed','rendered')},indent=2))
