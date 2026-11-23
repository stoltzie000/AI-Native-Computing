"""Explicit, uncalibrated burst-memory transaction and row tiling experiment.

This estimates traffic and serialized service cycles only. It is not a model of
real HBM signaling, command queues, banks, power, or actual GPU performance.
"""
from dataclasses import dataclass
from math import ceil, isfinite

@dataclass(frozen=True)
class Tiling:
    total_rows:int=64
    columns:int=4
    active_columns:int=2
    row_tile:int=4
    multiplier_lanes:int=4
    bytes_per_weight:int=1
    minimum_burst_bytes:int=64
    memory_first_byte_cycles:int=200
    transfer_bytes_per_cycle:int=32
    pipelined:bool=True

    def __post_init__(self):
        integer_fields=(self.total_rows,self.columns,self.active_columns,self.row_tile,
                        self.multiplier_lanes,self.bytes_per_weight,self.minimum_burst_bytes,
                        self.memory_first_byte_cycles,self.transfer_bytes_per_cycle)
        if any(not isinstance(v,int) or isinstance(v,bool) for v in integer_fields):
            raise ValueError("input parameters must be integers")
        if any(v<=0 for v in integer_fields[:2]+integer_fields[3:]):
            raise ValueError("positive parameters required")
        if self.active_columns<0 or self.active_columns>self.columns:
            raise ValueError("invalid nonzero column count")
        if self.total_rows % self.row_tile:
            raise ValueError("total rows must be divisible by tile rows")
        if self.multiplier_lanes>self.row_tile:
            raise ValueError("cannot have more active row lanes than rows")

def estimate(cfg:Tiling):
    tiles=cfg.total_rows//cfg.row_tile
    column_bytes=cfg.row_tile*cfg.bytes_per_weight
    burst_bytes=ceil(column_bytes/cfg.minimum_burst_bytes)*cfg.minimum_burst_bytes
    useful=cfg.total_rows*cfg.active_columns*cfg.bytes_per_weight
    transferred=cfg.active_columns*tiles*burst_bytes
    requests=cfg.active_columns*tiles
    memory_cycles=cfg.memory_first_byte_cycles+ceil(burst_bytes/cfg.transfer_bytes_per_cycle)
    compute_cycles=ceil(cfg.row_tile/cfg.multiplier_lanes)
    if cfg.active_columns==0:
        tile_cycles=2+cfg.columns
    elif cfg.pipelined:
        tile_cycles=(2+cfg.columns+memory_cycles+compute_cycles+
                     (cfg.active_columns-1)*max(memory_cycles,compute_cycles))
    else:
        tile_cycles=2+cfg.columns+cfg.active_columns*(memory_cycles+compute_cycles)
    return {
        "row_tile":cfg.row_tile,"tiles":tiles,"requests":requests,
        "useful_bytes":useful,"transferred_bytes":transferred,
        "burst_utilization":1 if transferred==0 else useful/transferred,
        "memory_cycles_per_request":memory_cycles,
        "compute_cycles_per_active_column":compute_cycles,
        "idealized_total_cycles":tile_cycles*tiles,
        "assumptions":"one independent physical burst per active column per row-tile; idealized optional double-buffer pipeline"
    }
