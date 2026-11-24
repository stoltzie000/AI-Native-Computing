"""Regenerate all pinned QACT/MM ISA fixture rows, add original FP32 activations."""
import argparse,hashlib,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/"quantized_mxu_g12"),str(HERE.parent/"g13_fp32_epilogue")]
import adapter
import generate_cases

def generate(out):
 out=Path(out)
 adapter.verify_and_generate(out)
 generate_cases.generate(out,out/"arithmetic")
 count=0
 for name,x,w,sw,dw in adapter.generated_cases():
  for row in range(3):
   folder=out/f"{name}_activation_{row}"
   adapter.hexwrite(folder/"x_raw.hex",[int(v) for v in x[row].view("uint32")],32)
   if not (folder/"expected_fp32.hex").is_file():raise AssertionError("missing FP32 oracle")
   count+=1
 if count!=24:raise AssertionError("fixture rows mismatch")
 digest=hashlib.sha256()
 for folder in sorted(out.glob("case_*_activation_*")):
  for name in ("x_raw.hex","q.hex","da.hex","expected.hex","expected_fp32.hex"):
   digest.update(name.encode()+b":"+(folder/name).read_bytes())
 print(f"PASS_FULL_QACT_MXU_FIXTURES rows=24 fp32_outputs=120 sha256={digest.hexdigest()}")
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument("--out",required=True)
 generate(ap.parse_args().out)
