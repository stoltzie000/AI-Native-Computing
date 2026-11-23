"""Generate deterministic, labelled E1 scenario reports."""
import json
from dataclasses import replace
from model import DecodeWorkload, analyze, generic_roofline
from scenarios import architectures


def report():
    report_data = {'evidence_level': 'E1_ONLY', 'model_version': '0.2.0',
                   'not_measured': True, 'model_proxy': 'Qwen2.5-32B-Instruct; approximate 32.5B parameters',
                   'assumptions': '100/40 TOPS and all efficiency factors are unmeasured; full peak utilization; memory channels and compute overlap perfectly; communication serial',
                   'comparison_policy': 'Do not rank predicted systems as measured winners; GPU published bandwidth is not real inference TPS',
                   'cases': []}
    base = DecodeWorkload()
    for context in (4096, 32768):
        work = replace(base, context=context)
        report_data['cases'].append({'context': context, 'batch': work.batch,
                                     'results': [analyze(work, a) for a in architectures()]})
    # Stress-test the speculative SRAM proposal: cache placement is not guaranteed,
    # and its capacity/bandwidth estimates have no physical validation.
    sram = next(a for a in architectures() if a.name.startswith('SRAM-centric'))
    report_data['sram_sensitivity_32k'] = []
    for fraction in (1.0, .75, .5, .25, 0.0):
        stressed = replace(sram, weight_fast_fraction=fraction, kv_fast_fraction=fraction)
        report_data['sram_sensitivity_32k'].append({'fast_residency_fraction': fraction,
                                                     'result': analyze(base, stressed)})
    for bw_factor in (.25, .5, 1.0):
        stressed = replace(sram, fast_gbs_per_module=sram.fast_gbs_per_module * bw_factor)
        report_data['sram_sensitivity_32k'].append({'fast_bandwidth_factor': bw_factor,
                                                     'result': analyze(base, stressed)})
    report_data['generic_kernel_example'] = {
        'description': 'Artificial 1-TOP / 10-GB transfer kernel; NOT quality-matched AI task',
        'results': {a.name: generic_roofline(1e12, 10e9, 20, a)
                    for a in architectures()}}
    return report_data


if __name__ == '__main__':
    print(json.dumps(report(), indent=2, allow_nan=False))
