"""Run the pinned numerical, protocol, self-test and XC7 mapping regressions."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys

from pack_fixtures import pack


FPGA = Path(__file__).resolve().parent
EXPERIMENT = FPGA.parent
ROOT = EXPERIMENT.parents[1]
RTL = EXPERIMENT / "rtl"
UPSTREAM = "d84db55712aba0d40811d7762cb052f05d55b7e5"
PIPELINE = (FPGA / "pipeline.f").read_text().splitlines()


def run(command, log, cwd=ROOT, env=None):
    with log.open("w") as stream:
        subprocess.run(command, cwd=cwd, env=env, stdout=stream,
                       stderr=subprocess.STDOUT, check=True)


def simulate(top, sources, build, arguments, defines=()):
    exe = build / f"{top}.vvp"
    run(["iverilog", "-g2012", "-Wall", *defines, "-s", top, "-o", exe, *sources],
        build / f"{top}-compile.log")
    for label, args in arguments.items():
        log = build / f"{label}.log"
        run(["vvp", exe, *args], log, cwd=build)
        for line in log.read_text().splitlines():
            if line.startswith("PASS_"):
                print(line, flush=True)


def synthesize(top, sources, build):
    # Flatten after technology mapping so both boundaries use identical options.
    netlist = build / f"{top}.json"
    commands = "read_verilog -sv -DSYNTHESIS " + " ".join(f'"{ROOT / path}"' for path in sources)
    commands += f"; synth_xilinx -family xc7 -top {top}; flatten; check -assert; write_json {netlist.name}"
    run(["yosys", "-Q", "-T", "-p", commands], build / f"{top}-yosys.log", cwd=build)
    cells = json.loads(netlist.read_bytes())["modules"][top]["cells"]
    counts = Counter(cell["type"] for cell in cells.values())
    blocks = [name for name, cell in cells.items() if cell["type"] in ("RAMB18E1","RAMB36E1")]
    return {"lut1_through_6": sum(counts[f"LUT{i}"] for i in range(1,7)),
            "flip_flops": sum(counts[k] for k in ("FDRE","FDSE","FDCE","FDPE")),
            "dsp48e1": counts["DSP48E1"], "block_ram_cells": blocks, "primitives": dict(sorted(counts.items()))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("upstream", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    upstream = args.upstream.resolve()
    if subprocess.check_output(["git","-C",upstream,"rev-parse","HEAD"],text=True).strip() != UPSTREAM:
        raise ValueError("wrong openTPU fixture generator revision")
    build = args.output.resolve()
    build.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONPATH": str(upstream), "PYTHONDONTWRITEBYTECODE":"1"}
    run([sys.executable, EXPERIMENT / "qact_full_reference.py", "--upstream", upstream,
         "--out", build / "stream"], build / "stream-oracle.log", env=env)
    run([sys.executable, EXPERIMENT / "full_qact_mxu_cases.py", "--out", build / "isa"],
        build / "isa-oracle.log", env=env)
    run([sys.executable, EXPERIMENT / "fp32_addsub_oracle.py", "--upstream", upstream,
         "--out", build / "addsub"], build / "addsub-oracle.log", env=env)
    pack(build / "isa", build)
    quant = PIPELINE[:5]
    baseline = quant[:4] + [str((RTL / name).relative_to(ROOT)) for name in
                ("qact_group_offset_hier.v","qact_row_scaled_serial.v","qact_row_clocked_original.v","qact_row_stream_original.v")]
    simulate("tb_fp32_addsub_ftz", [RTL / "fp32_addsub_ftz.v", RTL / "tb_fp32_addsub_ftz.sv"], build,
             {"addsub": [f"+folder={build / 'addsub'}"]}, ["-Ptb_fp32_addsub_ftz.BALANCED_NORMALIZE=1"])
    run(["yosys", "-Q", "-T", "-s", FPGA / "prove_addsub.ys"], build / "addsub-proof.log")
    print("PASS_BRAM_ADDSUB_EQUIVALENCE", flush=True)
    simulate("tb_qact_stream_original", quant + [RTL / "tb_qact_stream_original.sv"], build,
             {"stream": [f"+folder={build / 'stream'}"]}, ["-DQACT_BRAM"])
    simulate("tb_qact_mxu_stream_bram", PIPELINE + [RTL / "tb_qact_mxu_stream_bram.sv"], build,
             {"pipeline": [f"+folder={build}"]})
    simulate("tb_arty_bram_selftest", PIPELINE + [FPGA / "arty_bram_selftest.v",FPGA / "tb_arty_bram_selftest.sv"],
             build, {"board-pass": [], "board-fault": ["+corrupt"]})
    versions = subprocess.check_output(["yosys","-V"],text=True).strip()
    results = {"tool": versions, "baseline": synthesize("qact_row_stream_original", baseline, build),
               "candidate": synthesize("qact_row_stream_bram", quant, build)}
    (build / "resource_map.json").write_text(json.dumps(results,indent=2,sort_keys=True)+"\n")
    blocks = results["candidate"]["block_ram_cells"]
    if len(blocks) != 1 or "activation" not in blocks[0] or results["candidate"]["primitives"].get("RAMB18E1") != 1:
        raise RuntimeError(f"expected one RAMB18E1 backing activation; got {blocks}")
    print("PASS_BRAM_MAPPING", versions, blocks, flush=True)


if __name__ == "__main__":
    main()
