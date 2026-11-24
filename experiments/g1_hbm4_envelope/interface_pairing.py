"""Conditional controller/stack matching; never implies proven HBM4 PHY compatibility."""
from dataclasses import dataclass
from math import isfinite
def positive(x):
    if type(x) not in (float,int) or not isfinite(x) or x<=0:
        raise ValueError('positive finite numeric required')
    return float(x)
@dataclass(frozen=True)
class Pair:
    stacks:int
    data_pins:int
    controller_gbps:float
    memory_gbps:float|None=None
    compatible:bool|None=None
    def __post_init__(self):
        if type(self.stacks) is not int or self.stacks<1:raise ValueError('stack count')
        if type(self.data_pins) is not int or self.data_pins<1:raise ValueError('data pin count')
        positive(self.controller_gbps)
        if self.memory_gbps is not None:positive(self.memory_gbps)
        if self.compatible is not None and type(self.compatible) is not bool:
            raise ValueError('compatibility must be bool or unknown')
    def evaluate(self):
        raw=self.stacks*self.data_pins*self.controller_gbps/8000
        if self.memory_gbps is None or self.compatible is not True:
            return {'controller_only_tb_s':raw,
             'conditional_joint_limit_tb_s':None,
             'compatible':self.compatible,
             'status':'REJECT_INCOMPATIBLE' if self.compatible is False else 'BLOCK_COMPATIBILITY_OR_MEMORY_SPEED_UNKNOWN',
             'physical_gate':'OPEN'}
        matching=min(self.controller_gbps,self.memory_gbps)
        return {'controller_only_tb_s':raw,
          'conditional_joint_limit_tb_s':self.stacks*self.data_pins*matching/8000,
          'bottleneck': 'controller' if self.controller_gbps<=self.memory_gbps else 'memory',
          'compatible':True,'status':'UNVERIFIED_SUSTAINED_PHY_POWER_THERMAL',
          'physical_gate':'OPEN'}
