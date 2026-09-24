"""Apply source-backed timing reviews only while the reviewed feed data is unchanged."""
import copy
import json
from pathlib import Path

REVIEW_FILE = Path(__file__).resolve().parents[1] / 'ramen-tech-2026/data/time-reviews.json'
REVIEW_NOTE = '[主催者確認] '
STALE_NOTE = '[自動確認] 主催者確認後に公式データが変わりました。時刻の再確認が必要です。'

# This timetable item is the after-party, not the preceding main conference.
SCHEDULE_LINKS = {
    'ad088c2d-1bbb-434d-bd0e-4e4b29d12dca': 'event-auto-24c4d721f75f66',
}


def correct_source_links(catalog):
    events = {e['id']: e for e in catalog['events']}
    for key, target_id in SCHEDULE_LINKS.items():
        target = events.get(target_id)
        if not target:
            continue
        for event in events.values():
            if event['id'] == target_id:
                continue
            sync = event.get('sync', {})
            if key not in sync.get('scheduleKeys', []):
                continue
            dest = target.setdefault('sync', {})
            dest['scheduleKeys'] = sorted(set(dest.get('scheduleKeys', []) + [key]))
            value = sync.get('hashes', {}).pop('schedule:' + key, None)
            if value:
                dest.setdefault('hashes', {})['schedule:' + key] = value
            stamp = sync.get('seenAt', {}).get('schedule')
            if stamp:
                dest.setdefault('seenAt', {})['schedule'] = stamp
            sync['scheduleKeys'].remove(key)
            event['alsoSources'] = [u for u in event.get('alsoSources', []) if 'session=' + key not in u]
            target['alsoSources'] = list(dict.fromkeys(target.get('alsoSources', []) + [
                'https://ramentech2026.aishain.com/?session=' + key]))
            # These two diagnostics were produced by the wrong identity link.
            event['notes'] = [n for n in event.get('notes', []) if not (
                n.startswith('[自動確認]') and ('時間割 21:00–23:00' in n or '時間割「BUZZ' in n))]
            if not event['notes'] and not sync.get('manualBlock') and not sync.get('needsEditorialReview'):
                if event.get('status') == 'check':
                    event['status'] = 'published'
                    event.pop('calendarBlocked', None)
    return catalog


def apply_time_reviews(catalog, now, reviews=None):
    if reviews is None:
        reviews = json.loads(REVIEW_FILE.read_text())['reviews'] if REVIEW_FILE.exists() else []
    events = {e['id']: e for e in catalog['events']}
    results = []
    for review in reviews:
        event = events.get(review['eventId'])
        if not event:
            continue
        sync = event.get('sync', {})
        event['notes'] = [n for n in event.get('notes', []) if not n.startswith(REVIEW_NOTE) and n != STALE_NOTE]
        valid = bool(review.get('acceptedHashes')) and sync.get('hashes', {}) == review['acceptedHashes']
        valid = valid and event.get('dates') == review['dates']
        # A review can never hide cancellation, withdrawal, missing data or a new venue conflict.
        if not valid:
            event['timeReview'] = {**copy.deepcopy(review), 'status': 'needs-review'}
            event['status'] = 'check' if event.get('status') != 'cancelled' else 'cancelled'
            event['calendarBlocked'] = True
            event['notes'].append(STALE_NOTE)
            results.append({'id': event['id'], 'status': 'needs-review'})
            continue
        event['start'], event['end'] = review['start'], review['end']
        event.pop('slots', None)
        event['checkedAt'] = review['checkedAt'][:10]
        clears_prior_timing_block = review.get('clearsTimingReview') and any(
            n in review.get('supersededNotes', []) for n in event['notes'])
        event['notes'] = [n for n in event['notes'] if not (
            n.startswith('[自動確認] 時刻表記が不一致：') or n in review.get('supersededNotes', []))]
        remaining_block = any(n.startswith('[自動確認]') for n in event['notes'])
        if clears_prior_timing_block:
            sync['editorialReview'] = False
            sync['manualBlock'] = False
        if not remaining_block and not sync.get('manualBlock') and not sync.get('needsEditorialReview'):
            if event.get('status') == 'check':
                event['status'] = 'published'
                event.pop('calendarBlocked', None)
        event['notes'].append(REVIEW_NOTE + review['note'])
        event['timeReview'] = {**copy.deepcopy(review), 'status': 'applied'}
        event['alsoSources'] = list(dict.fromkeys(event.get('alsoSources', []) + [review['source']]))
        results.append({'id': event['id'], 'status': 'applied', 'start': event['start'], 'end': event['end']})
    catalog['meta']['timeReviews'] = results
    return catalog
