"""Validate an exact, externally published MLCommons Rubin Endpoints v1.0 Pareto fixture."""
import csv
from pathlib import Path
FILE=Path(__file__).with_name('mlperf_rubin_official_v10_pareto.csv')
SOURCE='https://results.mlcommons.org/endpoints/report?source=phase2&submission=618254e9-a8b8-47e6-8851-d21dd6b4af51'
UUID='618254e9-a8b8-47e6-8851-d21dd6b4af51'
def load():
    with FILE.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
    if len(rows)!=10:raise ValueError('expected ten audited run points')
    if sorted(int(r['run']) for r in rows)!=list(range(1,11)):raise ValueError('run numbers')
    for r in rows:
        if r['submission_uuid']!=UUID or r['source_url']!=SOURCE:
            raise ValueError('wrong submission/source')
        if r['power_kind']!='PROVISIONED_DECLARED' or r['accuracy_score']!='UNKNOWN':
            raise ValueError('do not invent measured watts or accuracy')
        if float(r['provisioned_power_kw'])!=12.61:
            raise ValueError('provisioned power mismatch')
        c=int(r['concurrency']);through=float(r['system_tps'])
        per=float(r['interactivity_tps_per_user'])
        if c<1 or through<=0 or per<=0 or float(r['ttft_p90_ms'])<=0:
            raise ValueError('nonpositive metric')
        if abs(through/c-per)>.12:
            raise ValueError('per-user throughput inconsistent')
    return sorted(rows,key=lambda x:int(x['run']))
def constrained_points(ttft_limit_ms):
    if type(ttft_limit_ms) not in (int,float) or ttft_limit_ms<=0:raise ValueError('limit')
    return [r for r in load() if float(r['ttft_p90_ms'])<=ttft_limit_ms]
if __name__=='__main__':
    rows=load()
    print('PASS_RUBIN_PARETO rows='+str(len(rows))+' max_tps='+str(rows[-1]['system_tps']))
    print('ILLUSTRATIVE_TTFT_P90_LE_200MS',len(constrained_points(200)))
