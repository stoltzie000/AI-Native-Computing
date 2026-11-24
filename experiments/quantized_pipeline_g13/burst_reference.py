"""G1.3 experimental tagged-burst read/reorder model, NOT hardware timing.

Models one request issue port and one response port per modeled cycle,
bounded outstanding credits, fixed+jittered response latency, independent
request/response stalls, aligned masked head/tail, and out-of-order responses.
Assumed cycles are not DRAM/FPGA measurements. Source buffers are read-only.
"""
from dataclasses import dataclass
from random import Random


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class Burst:
    tag: int
    address: int
    width: int
    byte_mask: int


def bursts(base: int, length: int, width: int) -> list[Burst]:
    if base < 0 or length <= 0 or width <= 0 or width & (width - 1):
        raise ValueError("base, length or power-of-two width invalid")
    start = base // width * width
    stop = base + length
    result = []
    for addr in range(start, stop, width):
        lo, hi = max(addr, base), min(addr + width, stop)
        mask = ((1 << (hi - lo)) - 1) << (lo - addr)
        result.append(Burst(len(result), addr, width, mask))
    assert sum(b.byte_mask.bit_count() for b in result) == length
    return result


def place_response(assembled: bytearray, written: bytearray,
                   base: int, request: Burst, data: bytes) -> None:
    """Independent tag/byte-enable checker; duplicate writes are failures."""
    if len(data) != request.width or request.byte_mask <= 0:
        raise ProtocolError("invalid response width/mask")
    if request.byte_mask >> request.width:
        raise ProtocolError("response mask outside bus")
    for lane in range(request.width):
        if request.byte_mask & (1 << lane):
            out = request.address + lane - base
            if not 0 <= out < len(assembled) or written[out]:
                raise ProtocolError("duplicate or out-of-range response byte")
            assembled[out] = data[lane]
            written[out] = 1


def simulate(memory: bytes, base: int, length: int, *, width: int = 64,
             depth: int = 4, latency: int = 8, jitter: int = 7,
             seed: int = 20261124, req_stall_every: int = 5,
             rsp_stall_every: int = 7) -> tuple[bytes, dict]:
    """Read real bytes; deterministic scheduling does not claim physical latency."""
    if depth <= 0 or latency <= 0 or jitter < 0:
        raise ValueError("invalid credit/latency configuration")
    if req_stall_every < 0 or rsp_stall_every < 0:
        raise ValueError("invalid stall configuration")
    bs = bursts(base, length, width)
    if base + length > len(memory) or bs[-1].address + width > len(memory):
        raise ValueError("storage does not cover full aligned response")
    rng = Random(seed)
    outstanding = {}
    complete = set()
    assembled = bytearray(length)
    written = bytearray(length)
    cycle = next_issue = peak = blocked = reorders = 0
    last_response_tag = -1
    trace = []
    # Model one read-request acceptance and at most one response per cycle.
    while len(complete) < len(bs):
        if cycle > max(50000, len(bs) * (latency + jitter + 5) * 10):
            raise TimeoutError("memory scheduler deadlock")
        candidates = [tag for tag, item in outstanding.items() if item[0] <= cycle]
        if candidates and not (rsp_stall_every and cycle % rsp_stall_every == 0):
            # Earliest available completion; independent per-tag jitter may reorder.
            tag = min(candidates, key=lambda t: (outstanding[t][0], t))
            ready_at, request = outstanding.pop(tag)
            if tag in complete:
                raise ProtocolError("duplicate response tag")
            place_response(assembled, written, base, request,
                           memory[request.address:request.address + width])
            complete.add(tag)
            if tag < last_response_tag:
                reorders += 1
            last_response_tag = tag
            trace.append((cycle, "response", tag))
        if next_issue < len(bs):
            if len(outstanding) >= depth or (req_stall_every and
                                               cycle % req_stall_every == 0):
                blocked += 1
            else:
                request = bs[next_issue]
                outstanding[request.tag] = (cycle + latency + rng.randrange(jitter + 1),
                                            request)
                trace.append((cycle, "issue", request.tag))
                next_issue += 1
                peak = max(peak, len(outstanding))
        cycle += 1
    if not all(written) or next_issue != len(bs) or outstanding:
        raise ProtocolError("missing request/response or useful bytes")
    return bytes(assembled), dict(cycles=cycle, requests=len(bs),
                                  responses=len(complete),
                                  useful=length, transferred=len(bs) * width,
                                  padding=len(bs) * width - length,
                                  peak=peak, blocked_issue_cycles=blocked,
                                  reordered_responses=reorders,
                                  first_events=trace[:16])
