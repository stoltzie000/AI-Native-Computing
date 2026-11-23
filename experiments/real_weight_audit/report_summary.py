"""Print provenance-rich aggregate numbers from JSON reports; no model code executed."""
import json
import sys
from pathlib import Path

def summarize(path):
    report=json.loads(Path(path).read_text(encoding="utf-8"))
    a=report["aggregate"]
    if a["measured_matrix_tensors"] <= 0 or a["elements"]<=0:
        raise ValueError("no eligible 2D weight tensors")
    result={
        "model_report":Path(path).name,
        "sha256":report["file_sha256"],
        "model_file_bytes":report["file_size_bytes"],
        "matrix_count":a["measured_matrix_tensors"],
        "matrix_elements":a["elements"],
        "zero_elements":a["zero_elements"],
        "zero_element_fraction":a["zero_element_fraction"],
        "blocks":{
          key:{"eligible":value["eligible_blocks"],"zeros":value["zero_blocks"],
               "zero_fraction":value["zero_block_fraction"]}
          for key,value in a["blocks"].items()
        }
    }
    print("MEASURED_WEIGHT_AUDIT "+json.dumps(result,sort_keys=True))
    return result

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: report_summary.py mixer.json transformer.json")
    for filename in sys.argv[1:]:
        summarize(filename)
