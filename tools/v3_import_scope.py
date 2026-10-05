"""V3 eligibility from installed pools and verified existing-system acquisition.

The full development catalogue remains available to resource verifiers. This
policy limits user-facing selections without treating all rewards as V4.
"""

DEVELOPMENT = 'development'
PIPELINE = 'v3-pipeline'
SCOPES = (PIPELINE, DEVELOPMENT)
UNAVAILABLE_BEHAVIOURS = frozenset(('tournament-measurements',
                                  'birthday-presentation'))


def check_scope(scope):
    if scope not in SCOPES:
        raise ValueError('Unknown import scope: '+str(scope))


def availability(catalog, report):
    """Use the checked cartridge's actual pool membership for every category."""
    # Group five is the existing native lottery, with checked donor lottery
    # membership and retained native selection code. No new feature is needed.
    # Native Redd initialization selects group three for all three stock slots.
    # Group four still needs the existing fixed-ID seasonal stock adapter;
    # membership in the donor's train-named list does not install that route.
    shops = {r['item_id'] for r in report['shops']['imports'] if r['group'] in (0, 1, 2, 3, 5)}
    seasonal = report.get('equipment_resources', {}).get('seasonal_stock', {})
    if seasonal.get('installed'):
        shops.update(r['item_id'] for r in seasonal['source']['imports'])
    from v3_furniture_rewards import existing_system_items
    shops.update(existing_system_items(report))
    from v3_holiday_acquisition import installed_items
    shops.update(installed_items(report))
    from v3_hra_rewards import installed_items as hra_items
    shops.update(hra_items(report))
    from v3_password_acquisition import installed_items as password_items, carried_items as password_carried
    password_ids=password_items(report)
    carried_codes=password_carried(report)
    from v3_holiday_acquisition import exercise_items
    exercise=exercise_items(report)
    from v3_harvest_acquisition import installed_items as harvest_items
    harvest=harvest_items(report)
    from v3_carried_selection import quest_items
    spirits=quest_items(report)
    summer_rewards = {r['item_id'] for r in report.get('furniture_rewards', {}).get('imports', [])
                      if r['route'] == 23}
    postal_rewards = {r['item_id'] for r in report['furniture']['imports']
                      if r.get('donor_list') == 'ftr_listPostoffice'}
    shirts = {item for group in report['clothing']['stock']['groups']
              for item in group['items']}
    surfaces = {r['id'] for group in report.get('room_surfaces', {}).get('stock', {}).get('resources', [])
                for r in group['imports']}
    e = report.get('equipment_resources', {})
    normal=e.get('normal_acquisition',{})
    cedar=normal.get('cedars',{})
    passive = {r['id'] for r in e.get('player_actions', {}).get('equipment_selection', {}).get('rows', [])
               if r['passive']}
    equipment = set(passive)
    golden = e.get('golden_tools', {})
    rewards = e.get('carried_items', {}).get('quest', {}).get('rewards', {})
    if (golden.get('shared_behaviour_installed') and rewards.get('installed')
            and rewards.get('selectable')):
        # These installed collection, Shrine, and tree routes extend existing
        # systems. Their registry admission follows tool selection, not the
        # optional holiday, Wisp, birthday, or savings-account activation.
        from v3_held_catalogue import parent_readiness
        ready, _ = parent_readiness(e)
        equipment.update(ready)
    carried = {r['id']: r for r in e.get('carried_items', {}).get('rows', []) if not r['state_index']}
    outfits = {key for row in catalog.values() if row['kind'] == 'villager'
               for key in row['dependencies'] if catalog[key]['kind'] == 'clothing'}
    result = {}
    for key, row in catalog.items():
        kind = row['kind']
        dependency_only = False
        if kind == 'furniture':
            ready = row['item_id'] in shops or key in password_ids or key in exercise or key in harvest
        elif kind == 'clothing':
            ready = int(row['item_id'], 16) in shirts
            # A villager's authentic starting outfit is part of that villager's
            # resources, not a separately offered exclusive-item import.
            dependency_only = not ready and key in outfits
        elif kind in ('floor', 'wall'):
            ready = key in surfaces or key in password_ids or key in harvest
        elif kind == 'equipment':
            ready = key in equipment
        elif kind == 'carried':
            # A fruit/sapling category proves behaviour, not acquisition.
            # Cedar and stationery require their normal stock consumers.
            # Retain the existing coconut code route; island acquisition is a
            # separate dependency on the unavailable island system.
            ready = (carried[key]['native_category']==49 and normal.get('paper',{}).get('installed')) or (
                carried[key]['native_category']==48 and cedar.get('shop_installed') and cedar.get('new_town_installed')
            ) or (
                carried[key]['native_category']==50 and key in carried_codes
            ) or key in exercise or key in harvest or key in spirits
        elif kind == 'diary':
            ready=normal.get('diaries',{}).get('installed') and key in normal['diaries']['identities']
        elif kind in ('villager', 'fish', 'insect'):
            ready = True
        else:
            raise ValueError('Unreviewed V3 selection category: '+kind)
        result[key] = dict(selectable=ready, dependency_only=dependency_only,
            reason=('Included only as an authentic villager starting-outfit resource; not a standalone item choice.'
                    if dependency_only else '' if ready else
                    'Original normal shop stock and its connected purchase consumers are not installed.'
                    if kind=='diary' or kind=='carried' and carried[key]['native_category'] in (48,49) else
                    'The complete installed summer-camping acquisition providers are unavailable.'
                    if kind == 'furniture' and row['item_id'] in summer_rewards else
                    'Postal reward delivery is unbound: the retained helper has no game-side caller or native mail submission binding.'
                    if kind == 'furniture' and row['item_id'] in postal_rewards else
                    'Acquisition is not admitted by the current V3 selection policy; existing-system reward routes require individual review.'))
    for key, row in catalog.items():
        if result[key]['selectable']:
            for child in row['dependencies']+[k for k,r in catalog.items()
                    if k!=key and row.get('selection_group') and
                    r.get('selection_group')==row['selection_group']]:
                if not (result[child]['selectable'] or result[child]['dependency_only']):
                    raise ValueError('V3 import requires unavailable acquisition: '+key+' -> '+child)
    return result


def requested_options(catalog, report):
    return [key for key, row in availability(catalog, report).items() if row['selectable']]


def check_requests(catalog, report, requested, behaviours):
    states = availability(catalog, report)
    unavailable = [key for key in requested if key in states and not states[key]['selectable']]
    if unavailable:
        raise ValueError('Unavailable standalone V3 import: '+', '.join(unavailable))
    if set(behaviours or {}) & UNAVAILABLE_BEHAVIOURS:
        raise ValueError('Behaviour setting is not admitted by the current V3 selection policy')
    return states
