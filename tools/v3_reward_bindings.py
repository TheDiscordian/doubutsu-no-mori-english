"""Checked shared exports and complete native bodies for the reward family.

This supplies real bindings, not substitutes for scene admission, gift masks,
Shrine lifetime, or dialogue. Missing consumers remain undefined at partial link.
"""
import struct

from aflib import sha256,by_vrom
from v3_asset_loader import ROOT
import re
from v3_registry import REWARD_PARTICIPANTS, SPECIAL_NPCS

RAM=0x807C9000
LAYOUT={
    'state': dict(ram=RAM,bytes=64),
    'storage': dict(ram=RAM+0x40,bytes=0x4000),
    'actors': dict(ram=RAM+0x4040,bytes=0x7000),
    'effects': dict(ram=RAM+0xB040,bytes=0x2000),
    'pools': dict(ram=RAM+0xD040,bytes=0x2000),
}


def layout(prior):
    """Reserve full storage, actors, effects, and pools in one checked packet."""
    from v3_console_disk_install import reservations
    import copy
    end=RAM+0xF040
    reserved=list(reservations(prior))
    if end>0x807DA800 or any(a<end and RAM<b for a,b in reserved):
        raise ValueError('Golden reward packet overlaps retained resident memory')
    # Only the new sixteen-byte scratch tail grows. All preceding save buffers
    # and records keep their owned addresses and extents.
    scratch=0x80682000
    before=scratch+120352
    after=scratch+120368
    if (not any(a==scratch and b==before for a,b in reserved) or
            any(a<after and before<b for a,b in reserved)):
        raise ValueError('Golden reward save scratch cannot grow safely')
    return dict(ram=RAM,bytes=end-RAM,components=copy.deepcopy(LAYOUT),installed=False,
        scratch=dict(ram=scratch,retained_bytes=120352,bytes=120368))

NATIVE = {
    'af_rw_native_spec_change':0x800FA92C,
    'af_rw_native_voice_emit':0x800F91FC,
    'af_rw_native_message': 0x8007B5C0,
    'af_rw_native_continue': 0x8009DBA4,
    'Actor_info_fgName_search': 0x800584E0,
    'mNpc_GetNpcLooks': 0x800AD084,
    'af_rw_native_wait': 0x800B2414,
    'af_rw_native_rank_condition': 0x80084D08,
    'af_rw_native_rank_set': 0x80084DA4,
    'af_rw_native_rank_get': 0x80084DE0,
    'lbRTC_IsOverTime': 0x800D52C0,
    'lbRTC_GetIntervalDays': 0x800D54DC,
    'lbRTC_TimeCopy': 0x800D5D6C,
    'af_rw_native_message_disappear': 0x8009E990,
    'af_rw_native_force_speak': 0x800B2244,
    'mPlib_Check_able_force_speak_label': 0x800B21F0,
    'mEv_CheckFirstJob': 0x8007D6E0,
    'mDemo_Set_talk_return_demo_wait': 0x8007B890,
    'af_rw_native_highest_friendship': 0x800A74A0,
    'af_rw_native_compare_player': 0x800B7A00,
    'af_rw_native_free_animal': 0x800A69C8,
    'mEv_CheckRealArbeit': 0x8007D5D4,
    'af_rw_native_actors_init': 0x80056E88,
    'af_rw_native_actors_move': 0x80057304,
    'af_rw_native_actors_destroy': 0x80057274,
}


def resolve(base, prior, storage):
    """Reuse current complete service providers and pin each native body."""
    from v3_holiday_participants import bindings
    links, native = bindings(base, prior, extra=NATIVE)
    from aflib import CODE_RAM,CODE_VROM
    core=by_vrom(base)[CODE_VROM].extract(base)
    # The native complete speech bodies identify the shared spec and the two
    # 36-byte alternating voice records; these are not donor memory aliases.
    observed={0x800FA9FC:0x0C03BBA9,0x800FAA00:0xAC2B3840,
        0x800F9340:0x3C038011,0x800F9348:0x24633CF4,
        0x800F934C:0xE4600008,0x800F9350:0xE460002C,
        0x800F9354:0xE46C0014,0x800F935C:0xE46C0038}
    if any(struct.unpack_from('>I',core,at-CODE_RAM)[0]!=word for at,word in observed.items()):
        raise ValueError('Changed native speech record layout')
    # These complete native Shrine bodies remain loaded by its original
    # descriptor. Wrapper hooks change its callers/table, not its body entries.
    directory=(ROOT/'upstream/af/linker_scripts/jp/symbol_addrs_overlays.txt').read_text()
    starts=sorted({int(a,16) for a in re.findall(r'= 0x([0-9A-F]+);[^\n]*type:func',directory)})
    data=by_vrom(base)[0x8D8EC0].extract(base)
    for name,start in {'af_rw_native_shrine_ctor':0x80A0A240,
            'af_rw_native_shrine_dtor':0x80A0A358,'af_rw_native_shrine_talk':0x80A0A7A4,
            'af_rw_native_shrine_action':0x80A0AB44}.items():
        if start not in starts:raise ValueError('Incomplete native Shrine symbol boundary')
        end=next(a for a in starts if a>start)
        raw=data[start-0x80A0A1F0:end-0x80A0A1F0]
        if len(raw)!=end-start:raise ValueError('Truncated native Shrine callback')
        native.append(dict(name=name,start=start,end=end,vrom=0x8D8EC0,ram=0x80A0A1F0,
            sha256=sha256(raw),binding='actor-owned loaded descriptor, never an absolute VMA call'))
    # Observe the complete native clock-editor and reset callbacks. The former
    # compares year/month/day/hour/minute and sets Save's real cheated byte;
    # the latter clears that same byte after its normal acknowledgement.
    for name,vrom,ram,start,checks in (
            ('native_clock_edited_flag',0x78AE30,0x808831A0,0x80883308,
                {0x80883390:0x3C018013,0x808833D8:0xA0386734}),
            ('native_reset_clock_flag_clear',0x96C3A0,0x80AAC230,0x80AAC76C,
                {0x80AAC7B0:0x3C018013,0x80AAC7B4:0xA0206734})):
        if start not in starts:raise ValueError('Incomplete native clock callback')
        end=next(a for a in starts if a>start)
        data=by_vrom(base)[vrom].extract(base)
        if any(struct.unpack_from('>I',data,at-ram)[0]!=word for at,word in checks.items()):
            raise ValueError('Changed native saved clock-edit flag')
        native.append(dict(name=name,start=start,end=end,vrom=vrom,ram=ram,
            sha256=sha256(data[start-ram:end-ram]),binding='observation only',
            observed_saved_byte=0x80136734))
    equipment = prior['equipment_resources']
    carried = equipment['carried_items']['quest']['npc']
    # Registry-owned exports are rebuilt together. Binding any of them to the
    # old 23-owner implementation would split descriptor and callback ownership.
    owned = {'af_hp_admit', 'af_hp_owned', 'af_hp_ctor', 'af_hp_dtor',
        'af_hp_step', 'af_hp_draw', 'af_hp_save', 'af_hp_free', 'af_hp_descriptor',
        'af_hp_identity', 'af_hp_event_lookup', 'af_hp_event_unregister',
        'af_hp_events_clear', 'af_hp_resident_bind', 'af_hp_name_profile',
        'af_hp_constructed', 'af_hp_npc_callbacks', 'af_hp_owner_enabled',
        'af_hp_npc_services', 'af_hp_records', 'af_hp_spawn_profiles',
        'af_hp_spawn_profile', 'af_hp_manager_alloc', 'af_hp_countdown', 'af_hp_elapsed'}
    links.update(carried['bindings'])
    links.update(carried['code']['symbols'])
    links['af_hp_actor_info']=equipment['npc_extra']['events']['participants']['code']['symbols']['af_hp_actor_info']
    links.update(storage['symbols'])
    links.update(af_rw_native_weather=0x8013740C,
        af_hp_native_animals=0x80130DB8, af_hp_native_tools=0x80136F40,
        af_hp_native_shrine=0x80136F70)
    links.update(af_rw_native_scene=0x80126EB4,af_rw_native_demo_profile=0x80137656,
        af_rw_native_cheated=0x80136734,af_rw_native_voice_spec=0x80113840,
        af_rw_native_voices=0x80113CF4)
    # Wisp's translated message resolver cannot translate gift/Shrine messages.
    for name in owned | {'mDemo_Set_msg_num'}:
        links.pop(name, None)
    # Use the active owners, not retained older receipts with the same export.
    actions=equipment['player_actions']
    exports={
        'af_v3_creature_complete': equipment['creature_fish']['world']['creature_travel']['code'],
        'af_v3_player_selected_equipment': actions['code'],
        'af_v3_reward_event': actions['reward_actions']['requests'],
        'af_v3_reward_flag': actions['reward_state']['code'],
    }
    for name,owner in exports.items():
        if name not in owner['symbols']:
            raise ValueError('Missing installed reward export: '+name)
        links[name]=owner['symbols'][name]
    return links, native


def registry(base, prior, source):
    """Retain every installed owner and append all four gift roles together."""
    equipment = prior['equipment_resources']
    carried = equipment['carried_items']['quest']['npc']
    retained = carried['registry']['rows']
    if (len(retained) != 23 or carried['registry']['resident_count'] != 18 or
            carried['registry']['live_count'] != 25 or prior['object_capacity'] != 458):
        raise ValueError('Changed connected reward registry baseline')
    names = {r['name'] + i for r in retained for i in range(r['count'])}
    profiles = {r['profile'] for r in retained}
    npc = equipment['npc_extra']
    extra = [npc['record']['identity']] + [
        row['identity'] for row in npc['prepared_characters'].values() if row['actor_installed']]
    if len(extra) != 6:
        raise ValueError('Changed complete special-character registry')
    names.update(r['name'] for r in extra)
    profiles.update(r['profile'] for r in extra)
    donors = {'present_demo': 'Present_Demo_Profile', 'present_npc': 'Present_Npc_Profile',
        'npc_hem': 'Npc_Hem_Profile', 'present_tortimer': 'Present_Npc_Profile'}
    rows = [dict(row) for row in retained]
    for stem, identity in REWARD_PARTICIPANTS.items():
        if identity['profile'] in profiles or (identity['name'] and identity['name'] in names):
            raise ValueError('Reward identity overlaps an installed owner: ' + stem)
        raw = source.raw(donors[stem])
        if len(raw) != 36 or struct.unpack_from('>H', raw)[0] != {
                'present_demo': 0xC6, 'present_npc': 0xC7, 'npc_hem': 0xF2,
                'present_tortimer': 0xC7}[stem]:
            raise ValueError('Changed complete donor gift profile: ' + stem)
        row = dict(identity, stem=stem, donor_profile=donors[stem],
            part=3 if identity['count'] else 7, flags=struct.unpack_from('>I', raw, 4)[0],
            donor_profile_sha256=sha256(raw))
        rows.append(row)
        names.add(identity['name'])
        profiles.add(identity['profile'])
    # Both Tortimer draw rows are identical in the pinned donor. Reusing the
    # already installed full banks preserves the gift actor's exact appearance.
    table = source.raw('npc_draw_data_tbl')
    if table[348*108:349*108] != table[354*108:355*108]:
        raise ValueError('Gift Tortimer no longer shares complete installed artwork')
    if SPECIAL_NPCS['GAFE01-r0/npc/hem']['model_bank'] != 458:
        raise ValueError('Changed additive Farley bank reservation')
    profiles_text = '\n'.join('extern ACTOR_PROFILE ' + name + ';'
        for name in sorted({r['donor_profile'] for r in rows}))
    records = ',\n'.join('    {' + ','.join(str(r[k]) for k in
        ('source', 'name', 'profile', 'event', 'save', 'count', 'part', 'kind')) +
        ',&' + r['donor_profile'] + ',' + str(r['flags']) + '}' for r in rows)
    spawn = [0] * (0xD0D1-0xD0A0)
    for row in rows:
        for i in range(row['count']):
            at = row['name'] + i - 0xD0A0
            if not 0 <= at < len(spawn) or spawn[at]:
                raise ValueError('Invalid complete gift spawn table')
            spawn[at] = row['profile']
    generated = '#include "holiday_participants.h"\n' + profiles_text + '\n' + \
        'const AFHPRecord af_hp_records[AF_HP_OWNER_COUNT]={\n' + records + '\n};\n' + \
        'const s16 af_hp_spawn_profiles[]={' + ','.join(map(str, spawn)) + '};\n'
    # Native whole-entry redirects are required for older callbacks that use
    # the shared registry. No old source callback needs recompilation.
    redirects = {n: carried['code']['symbols'][n] for n in (
        'af_hp_admit', 'af_hp_owned', 'af_hp_ctor', 'af_hp_dtor', 'af_hp_step',
        'af_hp_draw', 'af_hp_save', 'af_hp_free', 'af_hp_descriptor', 'af_hp_identity',
        'af_hp_event_lookup', 'af_hp_event_unregister', 'af_hp_events_clear',
        'af_hp_resident_bind', 'af_hp_name_profile', 'af_hp_constructed', 'af_hp_npc_callbacks')}
    return generated, dict(rows=rows, owner_count=27, resident_count=19, live_count=28,
        redirects=redirects, installed=False)
