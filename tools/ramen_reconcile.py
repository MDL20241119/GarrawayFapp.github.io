"""Reviewed identity links, not fuzzy title matching. Keep every saved event ID."""
import copy

# Registration and old timetable entries for the same six Garraway F events.
LOCAL_LINKS = {
    'coffee-7': ('event-auto-7bd3ec9d852008', 'slot-f7ecd6ad-9115-45e5-8149-f6fdd21f5a92'),
    'coffee-8': ('event-auto-d1d5566cf63aa0', 'slot-3d2c7cf3-a576-4798-8852-2493b8a00ed8'),
    'coffee-9': ('event-auto-06eda404ca50b7',),
    'welcome-7': ('event-auto-892814984038a9', 'slot-892041fd-22fc-4f05-a18c-4c1023dae69b'),
    'connect-8': ('event-auto-808f774ad30b19', 'slot-89b77644-050f-4b4a-80de-5962e63efc6f'),
    'next-9': ('event-auto-52e0a9ccd23300', 'slot-10e5cfc3-fa2f-443b-a2c5-889663bad4f9'),
}
PUBLIC_FIELDS = ('title', 'dates', 'start', 'end', 'slots', 'venue', 'url', 'autoCheckedAt')

def reconcile_local(catalog):
    events = {e['id']: e for e in catalog['events']}
    for canonical_id, aliases in LOCAL_LINKS.items():
        canonical, official = events.get(canonical_id), events.get(aliases[0])
        if not canonical or not official:
            continue
        # Preserve author-supplied participation/room notes and their real review date.
        local_notes = [n for n in canonical.get('notes', []) if not n.startswith('[自動確認]')]
        for field in PUBLIC_FIELDS:
            if field in official:
                canonical[field] = copy.deepcopy(official[field])
            elif field == 'slots':
                canonical.pop(field, None)
        canonical['notes'] = list(dict.fromkeys(local_notes + official.get('notes', [])))
        canonical['status'] = official.get('status', 'published')
        if canonical_id == 'welcome-7' and canonical['status'] == 'published':
            canonical['status'] = 'check'  # simultaneous room use still needs organizer confirmation
        if official.get('calendarBlocked'):
            canonical['calendarBlocked'] = True
        else:
            canonical.pop('calendarBlocked', None)
        canonical['alsoSources'] = list(dict.fromkeys(canonical.get('alsoSources', []) + [official['source'], official['url']]))
        # Keep old IDs for bookmarks/plans. Their public fields follow the same event.
        for alias in aliases:
            event = events.get(alias)
            if event:
                event['duplicateOf'] = canonical_id
                if alias != aliases[0]:
                    for field in PUBLIC_FIELDS:
                        if field in canonical:
                            event[field] = copy.deepcopy(canonical[field])
                    event['notes'] = copy.deepcopy(canonical['notes'])
                    event['status'] = canonical['status']
                    if canonical.get('calendarBlocked'):
                        event['calendarBlocked'] = True
                    else:
                        event.pop('calendarBlocked', None)
    visible = [e for e in catalog['events'] if not e.get('duplicateOf')]
    catalog['meta']['displayEventCount'] = len(visible)
    catalog['meta']['duplicateAliases'] = len(catalog['events']) - len(visible)
    return catalog
