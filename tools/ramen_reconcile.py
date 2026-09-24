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
PUBLIC_ALIASES = {
    'event-opening-party-1': 'event-auto-a9c0fbcac6e01a',
    'slot-2764a1f0-ac99-42f2-a8f5-0437dc0a035d': 'event-auto-13137f63c4f92c',
    'event-auto-8f5afd81da4e47': 'event-auto-49680bc454c757',
    'slot-6dd77578-6a52-405d-86b8-edd22470d8db': 'event-auto-ad6841522a37be',
    'slot-ecf1679b-0b2b-43d7-aa6a-0f757452f600': 'event-auto-efdb0d135bec9c',
    'slot-5242948f-6d0c-48e5-9c37-69abcd19bd36': 'event-auto-ea97d90564f660',
    'slot-members-insight-seekers-hackathon-final': 'event-auto-bf400d4f47c5f8',
    'slot-22c1a9b1-067c-46a9-965e-a64bf2696d40': 'event-auto-5ffd1712236c22',
    'slot-d1175f61-2138-4b4f-bde3-afe5f954d561': 'event-auto-19997cde841681',
    'slot-members-founders-padel': 'event-auto-6d7aca132617f6',
    'slot-32abb078-d46a-43cc-ab38-339712e43299': 'event-auto-a51579550a0f01',
    'slot-64183ef4-0fdb-4b32-a10b-75192468dd33': 'event-auto-358715ff9850e7',
    'slot-4873a7f8-7bcd-4901-a5c3-ff5c5524635f': 'event-auto-04eac30ce8f5da',
}

# Whole programs and their distinct daily/venue sessions stay separate, grouped in the UI.
PARENT_LINKS = {
    'slot-4c0fb517-fe50-40ee-9875-7c1faa8f48d5': 'event-auto-d34e29e3a5f3c2',
    'slot-fbef8463-938a-4d5e-9641-a42972d40bb9': 'event-auto-6281b2f1e4e0f6',
}

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
    for old_id, current_id in PUBLIC_ALIASES.items():
        old, current = events.get(old_id), events.get(current_id)
        if not old or not current:
            continue
        current['alsoSources'] = list(dict.fromkeys(current.get('alsoSources', []) + [old.get('source', ''), old.get('url', '')]))
        for field in ('description', 'speaker', 'company'):
            if not current.get(field) and old.get(field):
                current[field] = copy.deepcopy(old[field])
        current['tags'] = list(dict.fromkeys(current.get('tags', []) + old.get('tags', [])))
        current['notes'] = list(dict.fromkeys(current.get('notes', []) + [n for n in old.get('notes', []) if not n.startswith('[自動確認]')]))
        if not current.get('room') and old.get('room'):
            current['room'] = old['room']
        for field in (*PUBLIC_FIELDS, 'notes', 'status', 'fee'):
            if field in current:
                old[field] = copy.deepcopy(current[field])
            elif field == 'slots':
                old.pop(field, None)
        old['duplicateOf'] = current_id
        if current.get('calendarBlocked'):
            old['calendarBlocked'] = True
        else:
            old.pop('calendarBlocked', None)
    for child_id, parent_id in PARENT_LINKS.items():
        if child_id in events and parent_id in events:
            events[child_id]['parent'] = parent_id
            events[child_id]['parentTitle'] = events[parent_id]['title']
    visible = [e for e in catalog['events'] if not e.get('duplicateOf')]
    catalog['meta']['displayEventCount'] = len(visible)
    catalog['meta']['duplicateAliases'] = len(catalog['events']) - len(visible)
    return catalog
