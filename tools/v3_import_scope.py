"""V3 eligibility from installed pools and verified existing-system acquisition.

The full development catalogue remains available to resource verifiers. This
policy limits user-facing selections without treating all rewards as V4.
"""

DEVELOPMENT = 'development'
PIPELINE = 'v3-pipeline'
SCOPES = (PIPELINE, DEVELOPMENT)
FEATURE_CHOICES = frozenset(('holiday-calendar', 'tournament-measurements',
                             'birthday-presentation'))


def check_scope(scope):
    if scope not in SCOPES:
        raise ValueError('Unknown import scope: '+str(scope))


def availability(catalog, report):
    """Use the checked cartridge's actual pool membership for every category."""
    # Group five is the existing native lottery, with checked donor lottery
    # membership and retained native selection code. No new feature is needed.
    # Event/train membership alone does not establish each item's specific route.
    shops = {r['item_id'] for r in report['shops']['imports'] if r['group'] in (0, 1, 2, 5)}
    shirts = {item for group in report['clothing']['stock']['groups']
              for item in group['items']}
    surfaces = {r['id'] for group in report.get('room_surfaces', {}).get('stock', {}).get('resources', [])
                for r in group['imports']}
    e = report.get('equipment_resources', {})
    passive = {r['id'] for r in e.get('player_actions', {}).get('equipment_selection', {}).get('rows', [])
               if r['passive']}
    carried = {r['id']: r for r in e.get('carried_items', {}).get('rows', []) if not r['state_index']}
    outfits = {key for row in catalog.values() if row['kind'] == 'villager'
               for key in row['dependencies'] if catalog[key]['kind'] == 'clothing'}
    result = {}
    for key, row in catalog.items():
        kind = row['kind']
        dependency_only = False
        if kind == 'furniture':
            ready = row['item_id'] in shops
        elif kind == 'clothing':
            ready = int(row['item_id'], 16) in shirts
            # A villager's authentic starting outfit is part of that villager's
            # resources, not a separately offered exclusive-item import.
            dependency_only = not ready and key in outfits
        elif kind in ('floor', 'wall'):
            ready = key in surfaces
        elif kind == 'equipment':
            ready = key in passive
        elif kind == 'carried':
            # Installed native categories: saplings, stationery, and fruit.
            # Event cards, cutlery, and spirit quests are not regular pools.
            ready = carried[key]['native_category'] in (48, 49, 50)
        elif kind in ('villager', 'fish', 'insect', 'diary'):
            ready = True
        else:
            raise ValueError('Unreviewed V3 selection category: '+kind)
        result[key] = dict(selectable=ready, dependency_only=dependency_only,
            reason=('Included only as an authentic villager starting-outfit resource; not a standalone item choice.'
                    if dependency_only else '' if ready else
                    'Acquisition is not admitted by the current V3 selection policy; existing-system reward routes require individual review.'))
    for key, row in catalog.items():
        if result[key]['selectable']:
            for child in row['dependencies']:
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
    if set(behaviours or {}) & FEATURE_CHOICES:
        raise ValueError('GameCube feature settings are outside the V3 import pipeline')
    return states
