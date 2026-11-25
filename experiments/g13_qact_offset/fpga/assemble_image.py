"""Assemble an accepted bring-up route and compare every set configuration bit."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def compare_frames(frame_file, decoded_file):
    frames = {}
    with frame_file.open() as stream:
        for line in stream:
            raw_address, payload = line.split()
            address = int(raw_address, 16)
            words = [int(word, 16) for word in payload.split(",")]
            if address in frames or len(words) != 101:
                raise ValueError(f"invalid Series-7 frame at {raw_address}")
            frames[address] = words
    expected_count = sum(word.bit_count() for words in frames.values() for word in words)
    if not expected_count:
        raise ValueError("empty configuration")
    count = 0
    with decoded_file.open() as stream:
        for line in stream:
            prefix, raw_address, word, bit = line.strip().split("_")
            address, word, bit = int(raw_address,16), int(word), int(bit)
            if prefix != "bit" or not (0 <= word < 101 and 0 <= bit < 32):
                raise ValueError(f"invalid decoded bit: {line}")
            mask = 1 << bit
            if address not in frames or not (frames[address][word] & mask):
                raise ValueError(f"unexpected or repeated decoded bit: {line}")
            frames[address][word] ^= mask
            count += 1
    if count != expected_count:
        raise ValueError(f"{expected_count-count} set configuration bits missing from image")
    return len(frames), count


def assemble(build):
    part = "xc7a100tcsg324-1"
    package = Path(shutil.which("nextpnr-xilinx")).resolve().parents[1]
    database = Path(os.environ.get("PRJXRAY_DB_DIR", package / "share/nextpnr/external/prjxray-db")) / "artix7"
    part_file = database / part / "part.yaml"
    partial = build / "image.partial.bit"
    with (build / "image-assembly.log").open("w") as log:
        for cmd in [
            ["fasm2frames","--db-root",database,"--part",part,"board.fasm","board.frames"],
            ["xc7frames2bit","--part_file",part_file,"--part_name",part,"--frm_file","board.frames","--output_file",partial],
            ["bitread","--part_file",part_file,"-y","-z","-o","decoded.bits",partial]
        ]:
            subprocess.run(cmd, cwd=build, stdout=log, stderr=subprocess.STDOUT, check=True)
    frame_count, bit_count = compare_frames(build / "board.frames", build / "decoded.bits")
    image = build / "arty-bram-6m25.bit"
    partial.replace(image)
    info = {"file": image.name, "part": part, "clock_mhz": 6.25, "bytes": image.stat().st_size,
            "sha256": hashlib.sha256(image.read_bytes()).hexdigest(), "source_frames": frame_count,
            "verified_set_bits": bit_count}
    (build / "image-manifest.json").write_text(json.dumps(info,indent=2)+"\n")
    print("PASS_CONFIGURATION_READBACK", json.dumps(info,sort_keys=True), flush=True)
