"""Independent integer arithmetic oracle; does NOT simulate Verilog."""
from dataclasses import dataclass

def signed(value:int,bits:int)->int:
    if bits<2 or not isinstance(value,int):raise ValueError("invalid signed value/width")
    value &= (1<<bits)-1
    return value-(1<<bits) if value&(1<<(bits-1)) else value

@dataclass(frozen=True)
class PEConfig:
    block_size:int=4
    data_width:int=8
    acc_width:int=32
    lanes:int=4
    def __post_init__(self):
        n=self.block_size
        if n<1 or self.data_width<2 or self.acc_width<2*self.data_width or self.lanes<1 or self.lanes>n*n or n*n%self.lanes:
            raise ValueError("invalid PE geometry")

def calculate(rows,vector,certified_nonzero:bool,cfg:PEConfig=PEConfig()):
    n=cfg.block_size
    if len(rows)!=n or len(vector)!=n or any(len(row)!=n for row in rows):raise ValueError("invalid shape")
    if not isinstance(certified_nonzero,bool):raise ValueError("invalid block certificate type")
    w=[[signed(x,cfg.data_width) for x in row] for row in rows]
    x=[signed(v,cfg.data_width) for v in vector]
    if not certified_nonzero and any(value for row in w for value in row):
        raise ValueError("invalid zero-block certificate: nonzero weights")
    sums=[signed(sum(a*b for a,b in zip(row,x)),cfg.acc_width) for row in w] if certified_nonzero else [0]*n
    mult=n*n if certified_nonzero else 0
    cyc=(mult+cfg.lanes-1)//cfg.lanes
    return {"sums":sums,"issued_multiplies":mult,"active_compute_cycles":cyc,
            "controller_cycles_including_start_done":cyc+2}
