"""Conservative Fantrax standings refresh: no fabricated scores or stories."""
import json,urllib.request,pathlib,datetime,sys
ROOT=pathlib.Path(__file__).resolve().parent
URL='https://www.fantrax.com/fxea/general/getStandings?leagueId=0y5fcudbmtrhry3l'
def main():
    req=urllib.request.Request(URL,headers={'User-Agent':'TheFantasyWire/1.0 (league standings refresh)'})
    with urllib.request.urlopen(req,timeout=25) as res: incoming=json.load(res)
    # Refuse to overwrite good data if Fantrax responds with an unexpected shape.
    if isinstance(incoming,dict):
        for key in ('standings','data','results'):
            if isinstance(incoming.get(key),list):incoming=incoming[key];break
    if not isinstance(incoming,list) or len(incoming)!=14:raise ValueError('Unexpected standings response: not 14 clubs')
    data=json.loads((ROOT/'data.json').read_text())
    byid={t['id']:t for t in data['teams']}
    if {t.get('teamId') for t in incoming}!={t['id'] for t in data['teams']}:raise ValueError('Team ID mismatch; refusing update')
    for r in incoming:
        t=byid[r['teamId']];t['rank']=int(r['rank']);t['points']=float(r['totalPointsFor']);t['record']=str(r['points'])
    data['teams'].sort(key=lambda t:t['rank'])
    data['updated']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    data['snapshot']='Automated Fantrax standings refresh; roster and editorial content may be older'
    (ROOT/'data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    print('Standings refreshed successfully')
if __name__=='__main__':
    try:main()
    except Exception as exc:print('Refresh skipped:',exc,file=sys.stderr);sys.exit(1)
