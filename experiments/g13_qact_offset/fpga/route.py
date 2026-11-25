"""Place, route and check the 100 MHz board self-test with openXC7."""
import argparse
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="directory containing frames.hex and results.hex")
    args = parser.parse_args()
    build = args.output.resolve()
    fpga = Path(__file__).resolve().parent
    root = fpga.parents[2]
    if not all((build / f).is_file() for f in ("frames.hex","results.hex")):
        parser.error("run validate.py first or provide its two board-test ROMs")
    sources = [root / f for f in (fpga / "pipeline.f").read_text().splitlines()]
    sources.append(fpga / "arty_bram_selftest.v")
    commands = "read_verilog -sv -DSYNTHESIS " + " ".join(f'"{p}"' for p in sources)
    commands += "; synth_xilinx -family xc7 -flatten -top arty_bram_selftest; check -assert; write_json board.json; stat"
    with (build / "board-yosys.log").open("w") as log:
        subprocess.run(["yosys","-Q","-T","-p",commands], cwd=build, stdout=log,
                       stderr=subprocess.STDOUT, check=True)
    report = build / "board-route.json"
    report.unlink(missing_ok=True)  # a failed retry must never inherit a prior timing report
    with (build / "board-route.log").open("w") as log:
        subprocess.run(["nextpnr-xilinx","--device","xc7a100tcsg324-1","--json","board.json",
                        "-o",f"xdc={fpga / 'arty_a7_100t.xdc'}","--freq","100","--seed","1",
                        "--timing-allow-fail","--detailed-timing-report","--report",report.name],
                       cwd=build, stdout=log, stderr=subprocess.STDOUT, check=True)
    clocks = json.loads(report.read_text())["fmax"]
    if len(clocks) != 1:
        raise RuntimeError(f"expected one timed core clock: {clocks}")
    clock, timing = next(iter(clocks.items()))
    if abs(timing["constraint"] - 100) > 0.001 or timing["achieved"] <= 0:
        raise RuntimeError(f"invalid clock constraint or timing result: {clocks}")
    print(f"ROUTED xc7a100tcsg324-1 seed=1 clock={clock} target_mhz=100 estimated_mhz={timing['achieved']:.3f}", flush=True)
    if timing["achieved"] < 100:
        raise SystemExit("NOT_MET: 100 MHz routed setup estimate")


if __name__ == "__main__":
    main()
