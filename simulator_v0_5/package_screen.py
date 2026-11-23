"""Conditional package thermal/concentration screen, NOT engineering sign-off.

E1 comparison holds total heat assumptions fixed, redistributes them among N
compute packages, excludes unverified PHY/voltage regulation heat. Selects only
conditional survivors; status always labels unresolved physical implementation.
"""
from __future__ import annotations
from dataclasses import dataclass
from constraints import finite


@dataclass(frozen=True)
class PackageHeatHypothesis:
    total_compute_w:float
    hbm_stack_w:float
    total_stacks:int
    per_package_heat_limit_w:float
    link_phy_w_per_package:float | None = None

    def __post_init__(self):
        for n in ('total_compute_w','hbm_stack_w','per_package_heat_limit_w'):
            finite(n,getattr(self,n))
        if type(self.total_stacks) is not int or self.total_stacks<1:
            raise ValueError('total_stacks positive integer')
        if self.link_phy_w_per_package is not None:
            finite('link_phy_w_per_package',self.link_phy_w_per_package,allow_zero=True)

    def evaluate(self, packages:int) -> dict:
        if type(packages) is not int or packages<1 or self.total_stacks%packages:
            raise ValueError('packages must divide total_stacks')
        compute_per=self.total_compute_w/packages
        memory_per=self.hbm_stack_w*self.total_stacks/packages
        known=compute_per+memory_per
        phy=self.link_phy_w_per_package
        assumed=known+(phy or 0)
        return {'packages':packages,
                'compute_w_per_package':compute_per,
                'hbm_w_per_package':memory_per,
                'partial_heat_w_per_package':known,
                'including_assumed_phy_w_per_package':assumed if phy is not None else None,
                'package_heat_limit_w':self.per_package_heat_limit_w,
                'status': ('REJECT_ASSUMED_PACKAGE_HEAT' if known>self.per_package_heat_limit_w
                           else 'UNKNOWN_PHY_AND_OTHER_HEAT' if phy is None
                           else 'REJECT_ASSUMED_PACKAGE_HEAT' if assumed>self.per_package_heat_limit_w
                           else 'ONLY_ASSUMPTION_LEVEL_NONREJECTION'),
                'unmodeled':'Power delivery losses, interface controllers, leakage, hot spots, heat flux, cooling contact area, supply tolerances, die area and cooling hardware.'}


def conditional_best(all_rows:list, heat:PackageHeatHypothesis):
    choices=[]
    for r in all_rows:
        h=heat.evaluate(r['packages'])
        choices.append({'packages':r['packages'],'heat':h,
                        'conditional_steps_per_second':r['result'].get('conditional_steps_per_second')})
    eligible=[x for x in choices if x['heat']['status'] == 'ONLY_ASSUMPTION_LEVEL_NONREJECTION'
              and x['conditional_steps_per_second'] is not None]
    best=max(eligible,key=lambda x:x['conditional_steps_per_second']) if eligible else None
    return {'status':'ASSUMED_SCREEN_ONLY_NOT_HARDWARE_SELECTION','best_conditional_packages':best['packages'] if best else None,
            'rows':choices}


def hidden_overhead_crossover_ms(one_a:dict, one_b:dict)->float:
    """How much EXTRA delay A can tolerate before matching B's step time."""
    if not all(x.get('result',{}).get('step_ms') for x in (one_a,one_b)):
        raise ValueError('both scenarios require positive step_ms')
    return one_b['result']['step_ms']-one_a['result']['step_ms']
