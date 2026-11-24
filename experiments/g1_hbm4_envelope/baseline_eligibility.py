"""Guard against invalid cross-model, provisional, and provisioned-power comparisons."""
import json
from pathlib import Path

POWER_KINDS={'PROVISIONED_MLC_ESTIMATED','PROVISIONED_DECLARED','WALL_MEASURED','UNKNOWN'}
STATUSES={'Official','Provisional'}

def validate_record(record):
    fields=('result_id','system','gpu_count','publication_status','division',
            'power_kind','provisioned_power_kw','actual_wall_power_kw','task_throughput')
    if any(k not in record for k in fields):raise ValueError('missing data')
    if not isinstance(record['result_id'],str) or not record['result_id'].strip():
        raise ValueError('missing ID')
    if not isinstance(record['system'],str) or not record['system'].strip():
        raise ValueError('missing system')
    if type(record['gpu_count']) is not int or record['gpu_count']<1:
        raise ValueError('invalid GPU count')
    if record['publication_status'] not in STATUSES:raise ValueError('status')
    if record['division']!='Standardized':raise ValueError('division')
    if record['power_kind'] not in POWER_KINDS:raise ValueError('power kind')
    p=record['provisioned_power_kw'];w=record['actual_wall_power_kw']
    if p is not None and (type(p) not in (float,int) or not 0<p<1e6):
        raise ValueError('invalid provisioned power')
    if w is not None and (type(w) not in (float,int) or not 0<w<1e6):
        raise ValueError('invalid wall power')
    if record['power_kind']!='WALL_MEASURED' and w is not None:
        raise ValueError('wall power incorrectly assigned')
    if record['power_kind']=='WALL_MEASURED' and w is None:
        raise ValueError('no actual wall power evidence')
    if record['task_throughput'] is not None:
        raise ValueError('unverified throughput must remain null until exact run captured')
    return True

def load(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    if data['source']!='https://results.mlcommons.org/endpoints':
        raise ValueError('unexpected source')
    if data['model']!='deepseek-v4_1-flash':raise ValueError('model')
    ids=set()
    for row in data['records']:
        validate_record(row)
        if row['result_id'] in ids:raise ValueError('duplicate submission')
        ids.add(row['result_id'])
    return data

def comparison_status(record,source_model,target_model,
                      accuracy_match=False,measured_wall=False):
    validate_record(record)
    if record['publication_status']!='Official':
        return 'BLOCK_PROVISIONAL'
    if source_model!=target_model:
        return 'BLOCK_MODEL_MISMATCH'
    if not accuracy_match:
        return 'BLOCK_QUALITY_UNVERIFIED'
    if measured_wall and record['power_kind']!='WALL_MEASURED':
        return 'BLOCK_WALL_POWER_UNMEASURED'
    return 'PARTIAL_BENCHMARK_ELIGIBLE_NOT_SYSTEM_COMPARABLE'

if __name__=='__main__':
    data=load(Path(__file__).with_name('mlperf_endpoints_official_sample.json'))
    for record in data['records']:
        print(record['result_id'],comparison_status(record,data['model'],'Qwen2.5-32B'))
    print('PASS_OFFICIAL_ENDPOINTS_LEDGER entries='+str(len(data['records'])))
