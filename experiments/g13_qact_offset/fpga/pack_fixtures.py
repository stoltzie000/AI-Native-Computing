"""Pack the 24 existing ISA cases into one little-endian stream and board-test ROMs."""
import argparse
import hashlib
from pathlib import Path


def read_values(case, name, count):
    values = [int(v, 16) for v in (case / name).read_text().split()]
    if len(values) != count:
        raise ValueError(f"{case.name}/{name}: expected {count} entries, found {len(values)}")
    return values


def pack_bytes(values):
    data = bytes(values)
    return [int.from_bytes(data[i:i + 4], "little") for i in range(0, len(data), 4)]


def pack(source, output):
    output.mkdir(parents=True, exist_ok=True)
    cases = sorted(source.glob("case_*_activation_*"))
    if len(cases) != 24:
        raise ValueError(f"expected 24 ISA cases, found {len(cases)}")
    fields = {
        "frames": (8, []), "results": (8, []), "codes": (2, []),
        "offsets": (2, []), "scales": (8, []), "accumulators": (12, []), "drops": (4, [])
    }
    digest = hashlib.sha256()
    for case in cases:
        for name in ("x_raw.hex", "q.hex", "da.hex", "expected.hex", "expected_fp32.hex"):
            digest.update(name.encode() + b":" + (case / name).read_bytes())
        frame = pack_bytes(read_values(case, "w.hex", 320))
        frame += pack_bytes(read_values(case, "dw.hex", 10) + [0, 0])
        frame += read_values(case, "wscale.hex", 5) + read_values(case, "x_raw.hex", 64)
        fields["frames"][1].extend(frame)
        for target, name, count in [
            ("results", "expected_fp32.hex", 5), ("codes", "q.hex", 64),
            ("offsets", "da.hex", 8), ("scales", "ascale.hex", 1),
            ("accumulators", "expected.hex", 5), ("drops", "drops.hex", 1)
        ]:
            fields[target][1].extend(read_values(case, name, count))
    if digest.hexdigest() != "8a00dfbf8591ddb47af238780d2e8a48a93ac3e7c9c79881177e30826ff9a7e4":
        raise ValueError("ISA fixture digest changed")
    for name, (width, values) in fields.items():
        (output / f"{name}.hex").write_text("".join(f"{v:0{width}x}\n" for v in values))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    pack(args.source, args.output)
