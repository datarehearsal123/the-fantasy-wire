"""Refresh verified Fantrax standings and publish one daily standings roundup.

Only standings and total fantasy points are verified by this script. It does not
report live scores, trades, player performances or final matchup results.
"""
import datetime as dt
import json
import pathlib
import re
import sys
import urllib.request
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent
URL = 'https://www.fantrax.com/fxea/general/getStandings?leagueId=0y5fcudbmtrhry3l'
PACIFIC = ZoneInfo('America/Vancouver')


def get_standings():
    req = urllib.request.Request(URL, headers={'User-Agent': 'TheFantasyWire/1.0 (league standings refresh)'})
    with urllib.request.urlopen(req, timeout=25) as response:
        incoming = json.load(response)
    if isinstance(incoming, dict):
        for key in ('standings', 'data', 'results'):
            if isinstance(incoming.get(key), list):
                incoming = incoming[key]
                break
    if not isinstance(incoming, list) or len(incoming) != 14:
        raise ValueError('Unexpected standings response: expected 14 clubs')
    return incoming


def main():
    incoming = get_standings()
    data_path = ROOT / 'data.json'
    stories_path = ROOT / 'stories.json'
    data = json.loads(data_path.read_text(encoding='utf-8'))
    stories = json.loads(stories_path.read_text(encoding='utf-8'))
    if not isinstance(stories, list) or not isinstance(data.get('teams'), list) or len(data['teams']) != 14:
        raise ValueError('Unexpected local data format')

    by_id = {str(t['id']): t for t in data['teams']}
    if len(by_id) != 14 or {str(r.get('teamId')) for r in incoming} != set(by_id):
        raise ValueError('Team ID mismatch; refusing to update')
    ranks = [int(r['rank']) for r in incoming]
    if sorted(ranks) != list(range(1, 15)):
        raise ValueError('Unexpected or duplicated ranks')

    for r in incoming:
        team = by_id[str(r['teamId'])]
        points = float(r['totalPointsFor'])
        if not 0 <= points < 100000:
            raise ValueError('Invalid fantasy points total')
        team['rank'] = int(r['rank'])
        team['points'] = points
        team['record'] = str(r['points'])
    data['teams'].sort(key=lambda t: t['rank'])
    now = dt.datetime.now(dt.timezone.utc)
    data['updated'] = now.isoformat()
    data['snapshot'] = 'Automated Fantrax standings refresh; rosters and editorial may be older'

    local_date = now.astimezone(PACIFIC).date()
    date_str = local_date.isoformat()
    story_id = 'daily-roundup-' + date_str
    leader = data['teams'][0]
    runner_up = data['teams'][1]
    bottom = data['teams'][-1]
    high_scorers = sorted(data['teams'], key=lambda t: (-t['points'], t['rank']))
    scoring_leader = high_scorers[0]
    scoring_second = high_scorers[1]
    points_gap = scoring_leader['points'] - scoring_second['points']
    standings_gap = leader['points'] - runner_up['points']
    scoring_rank = next(i + 1 for i, t in enumerate(high_scorers) if t['id'] == leader['id'])
    top_scorer_standings_rank = scoring_leader['rank']

    # Rankings and accumulated points are confirmed. Records may be encoded as
    # league points by Fantrax, so we do not infer wins/losses from 'record'.
    paragraphs = [
        f"The latest verified Hit the Road Hockey standings put {leader['name']} in first place among 14 clubs, "
        f"with {leader['points']:.1f} accumulated fantasy points. {runner_up['name']} sits second "
        f"with {runner_up['points']:.1f}. Those are standings positions at the time of this refresh, "
        "not a declaration that any in-progress weekly matchup is over.",
        f"The standings race is worth watching: {leader['name']} is {abs(standings_gap):.1f} "
        f"fantasy points {'ahead of' if standings_gap >= 0 else 'behind'} {runner_up['name']} in cumulative production. "
        "In head-to-head fantasy hockey, overall production and weekly victories are different things. "
        "A healthy points total may impress the group chat, but it cannot negotiate with the schedule.",
        f"On pure accumulated scoring, {scoring_leader['name']} leads the league with "
        f"{scoring_leader['points']:.1f} fantasy points. {scoring_second['name']} follows at "
        f"{scoring_second['points']:.1f}, a gap of {points_gap:.1f}. "
        f"The top scorer is currently {top_scorer_standings_rank}{ordinal_suffix(top_scorer_standings_rank)} "
        f"in the official standings; the standings leader ranks {scoring_rank}{ordinal_suffix(scoring_rank)} "
        "by accumulated fantasy points. That's why the league has both a standings table and a calculator.",
        f"At the other end of the standings, {bottom['name']} is in 14th place with "
        f"{bottom['points']:.1f} accumulated fantasy points. That is a tough position to occupy "
        "when 13 rival front offices are available to provide unsolicited advice. "
        "The rankings are a snapshot, though, not a forecast of where anyone will finish.",
        "The Fantasy Wire's daily report is based on Fantrax's verified standings feed. "
        "It does not yet have a validated feed for individual player fantasy points, transactions "
        "or live matchup scores, so it will not invent a hero, a goat or a final score. "
        "When those feeds are verified, the reporting can get considerably more personal."
    ]
    article = {
        'id': story_id,
        'category': 'DAILY ROUNDUP',
        'title': f"The Daily Wire: {leader['name']} tops the table",
        'dek': f"{leader['name']} leads the 14-team standings, while {scoring_leader['name']} sets the pace in accumulated fantasy points. Here's the latest verified league snapshot.",
        'date': date_str,
        'status': 'Automated standings snapshot',
        'paragraphs': paragraphs,
    }
    # Replace today's edition if the workflow is run twice, rather than duplicate it.
    stories = [s for s in stories if not (isinstance(s, dict) and s.get('id') == story_id)]
    stories.insert(0, article)
    # Only write files after both payloads are validated and the article is built.
    data_path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    stories_path.write_text(json.dumps(stories, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Standings refreshed and daily roundup published for {date_str}')


def ordinal_suffix(n):
    if 10 <= n % 100 <= 20:
        return 'th'
    return {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Refresh skipped:', exc, file=sys.stderr)
        sys.exit(1)
