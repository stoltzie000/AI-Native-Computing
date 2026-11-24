"""Read frozen Q8 fixtures and compare against unmodified pinned openTPU q8."""
import argparse,importlib.util,pathlib
import numpy as np

def verify(root,upstream):
    root=pathlib.Path(root);upstream=pathlib.Path(upstream)
    source=upstream/"opentpu"/"fp32.py"
    if not source.is_file():raise FileNotFoundError(source)
    spec=importlib.util.spec_from_file_location("pinned_fp32",source)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    words=np.asarray([int(x,16) for x in (root/"x.hex").read_text().splitlines()],dtype=np.uint32)
    expected=np.asarray([int(x,16) for x in (root/"expected.hex").read_text().splitlines()],dtype=np.uint8)
    if len(words)!=2049 or len(expected)!=2049:raise AssertionError("fixture count mismatch")
    got=module.q8(module.from_bits(words)).view(np.uint8)
    differences=np.flatnonzero(got!=expected)
    if len(differences):
        i=int(differences[0]);raise AssertionError(f"upstream mismatch i={i} word={words[i]:08x} expected={expected[i]:02x} got={got[i]:02x}")
    print(f"PASS_Q8_UPSTREAM cases={len(words)} matched={len(words)}")
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--fixtures",required=True);ap.add_argument("--upstream",required=True)
    args=ap.parse_args();verify(args.fixtures,args.upstream)
