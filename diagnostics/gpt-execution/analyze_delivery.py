"""Analyze observed client delivery outcomes. UNKNOWN never becomes success."""
import csv
import datetime as dt
import json
import math
import sys
from collections import defaultdict
FIELDS={'session_id','variant','started_at_utc','ended_at_utc','delivery_outcome'}
OUTCOMES={'success','timeout','other_error','unknown'}
def parse_time(v):
    try: t=dt.datetime.fromisoformat(v.replace('Z','+00:00'))
    except (TypeError,ValueError) as exc: raise ValueError('invalid timestamp') from exc
    if t.tzinfo is None: raise ValueError('timezone required')
    return t.astimezone(dt.timezone.utc)
def interval(k,n):
    if n==0: return None
    z=1.959963984540054;p=k/n;d=1+z*z/n
    c=(p+z*z/(2*n))/d;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [max(0.,c-h),min(1.,c+h)]
def analyze(path):
    groups=defaultdict(lambda:{'success':0,'timeout':0,'other_error':0,'unknown':0,'observed_seconds':0.})
    seen=set()
    with open(path,newline='',encoding='utf-8') as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames is None or not FIELDS.issubset(reader.fieldnames):
            raise ValueError('missing required fields')
        for line,row in enumerate(reader,2):
            key=row['session_id'].strip();group=row['variant'].strip()
            outcome=row['delivery_outcome'].strip()
            if not key or not group or key in seen or outcome not in OUTCOMES:
                raise ValueError(f'invalid or repeated session line {line}')
            seen.add(key);g=groups[group];g[outcome]+=1
            start=row['started_at_utc'].strip();end=row['ended_at_utc'].strip()
            if bool(start)!=bool(end): raise ValueError('both timestamps needed')
            if start:
                duration=(parse_time(end)-parse_time(start)).total_seconds()
                if duration<0: raise ValueError('negative exposure duration')
                g['observed_seconds']+=duration
    result={}
    for name,g in sorted(groups.items()):
        n=g['success']+g['timeout']+g['other_error']
        result[name]=dict(g,observed_delivery_count=n,
            observed_timeout_rate=g['timeout']/n if n else None,
            timeout_wilson95=interval(g['timeout'],n),
            timeout_per_observed_hour=3600*g['timeout']/g['observed_seconds'] if g['observed_seconds'] else None)
    return result
if __name__=='__main__':
    if len(sys.argv)!=2: sys.exit('Usage: python analyze_delivery.py sessions.csv')
    print(json.dumps(analyze(sys.argv[1]),sort_keys=True,indent=2))
