"""Publish date-specific schedules from Fukuoka Airport's public timetable.

The endpoint and request header match the airport's schedule.js. No credentials,
live seat availability, inferred operating dates or copied September times for
October. A complete date is marked only after every published route succeeds.
"""
import argparse
import concurrent.futures
import datetime as dt
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

BASE = 'https://www.fukuoka-airport.jp/'
HEADERS = {'X-Requested-With': 'XMLHttpRequest', 'Referer': BASE + 'flight/schedule/'}


def fetch(params):
    url = BASE + 'api/get_flight_schedule.json?' + urllib.parse.urlencode({'lang': 'ja', **params})
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=45) as response:
        data = json.load(response)
    if not isinstance(data, dict) or 'ScheduleStatuses' not in data:
        raise ValueError('Invalid airport timetable response')
    return data


def values(data):
    return list(data.values()) if isinstance(data, dict) else data or []


def time(value):
    if not re.fullmatch(r'\d{4}', value or '') or int(value[:2]) > 23 or int(value[2:]) > 59:
        raise ValueError('Invalid timetable time')
    return value[:2] + ':' + value[2:]


def normalize(row, code, kind, international):
    carrier = row['acd'].strip()
    number = str(row['flight_no']).strip()
    shares = [{'carrier': x['acd'].strip(), 'name': x['acd'].strip() + ' ' + str(x['flight_no']).strip()} for x in row.get('share', [])]
    return {'id': code + '-' + carrier + number, 'airport': code, 'name': carrier + ' ' + number,
            'carrier': carrier, 'operator': row['airline'], 'dep': '--:--' if row['departure_time']==row['arrival_time']=='0000' else time(row['departure_time']),
            'arr': '--:--' if row['departure_time']==row['arrival_time']=='0000' else time(row['arrival_time']), 'depDiff': {'1':'前日','2':'同日','3':'翌日'}.get(str(row.get('departure_diff')), ''),
            'arrDiff': {'1':'前日','2':'同日','3':'翌日'}.get(str(row.get('arrival_diff')), ''), 'suspended': bool(row.get('suspension')),
            'international': international, 'shares': shares, 'kind': kind,
            'waypoint': (row.get('waypoint') or {}).get('waypoint_name', '') if isinstance(row.get('waypoint'), dict) else '',
            'source': 'airport'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default=str(Path(__file__).resolve().parents[1] / 'flight-data.js'))
    parser.add_argument('--cache', help='Optional local research cache directory')
    args = parser.parse_args()
    cache = Path(args.cache) if args.cache else None
    if cache:
        cache.mkdir(parents=True, exist_ok=True)
    index = fetch({'type': 'index'})
    status = index['ScheduleStatuses']
    routes = index['masterRoutesDom'] + index['masterRoutesInt']
    # Daily overview plus the event week, including the day before and after.
    requested = {status['current_date'], *('2026-10-' + str(day).zfill(2) for day in range(6, 11))}
    dates = sorted(day for day in requested if status['minDate'] <= day < status['maxDate'])
    output = Path(args.output)
    old = {}
    if output.exists():
        try:
            old = json.loads(output.read_text().split('window.RamenFlightData=', 1)[1].rstrip(';\n'))
        except (ValueError, IndexError):
            pass
    data = {'checked': dt.datetime.now(dt.timezone.utc).date().isoformat(), 'sourceUpdated': status['infDate'],
            'source': BASE + 'flight/schedule/', 'airports': old.get('airports', {}),
            'dates': old.get('dates', {}), 'completeDates': old.get('completeDates', [])}
    completed = {day: set() for day in dates}
    results = {day: {} for day in dates}
    errors = []

    def get(job):
        day, route = job
        path = cache / (day + '-' + route['id'] + '.json') if cache else None
        if path and path.exists():
            result = json.loads(path.read_text())
        else:
            result = fetch({'type': 'detail', 'place': route['id'], 'date': day})
            if path:
                path.write_text(json.dumps(result, ensure_ascii=False))
        info = result.get('flightInformation')
        if not info or not info.get('place') or result['ScheduleStatuses']['current_date'] != day:
            raise ValueError('Missing route or mismatched date')
        place = info['place']
        code = place['title'].strip()
        airport = {'name': place['route_name'].strip(), 'international': place['flight_type'] == 2,
                   'difference': place.get('time_difference') or '', 'place': route['id']}
        legs = {kind: [normalize(row, code, kind, airport['international']) for row in values(info.get(key))]
                for kind, key in [('outbound', 'flightScheduleArr'), ('return', 'flightScheduleDep')]}
        return day, route['id'], code, airport, legs

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        jobs = {executor.submit(get, (day, route)): (day, route) for day in dates for route in routes}
        for future in concurrent.futures.as_completed(jobs):
            day, route = jobs[future]
            try:
                day, route_id, code, airport, legs = future.result()
                data['airports'][code] = airport
                results[day][code] = legs
                completed[day].add(route_id)
            except Exception as error:
                errors.append(f"{day} {route['title']}: {error}")
    for day in dates:
        # Do not replace a previously complete date with a partial refresh.
        if len(completed[day]) == len(routes):
            data['dates'][day] = results[day]
            data['completeDates'] = sorted(set(data['completeDates']) | {day})
        elif day not in data['completeDates'] and results[day]:
            data['dates'][day] = {**data['dates'].get(day, {}), **results[day]}
    if not data['airports'] or not data['dates']:
        raise RuntimeError('No verified flight data; preserving the existing file. ' + '; '.join(errors[:3]))
    text = '/* Fukuoka Airport official timetable snapshots; dates are never extrapolated. */\nwindow.RamenFlightData=' + json.dumps(data, ensure_ascii=False, separators=(',', ':'), sort_keys=True) + ';\n'
    temporary = output.with_suffix('.tmp')
    temporary.write_text(text)
    temporary.replace(output)
    count = sum(len(rows) for date in data['dates'].values() for route in date.values() for rows in route.values())
    print(f"Flight timetable: {len(data['airports'])} airports, {count} rows, complete dates {data['completeDates']}")
    for error in errors[:10]:
        print('Timetable source unavailable:', error)


if __name__ == '__main__':
    main()
