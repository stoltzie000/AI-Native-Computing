import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path
import numpy as np

FILE=Path(__file__).resolve().parents[1]/'tools'/'safetensors_sparsity.py'
spec=importlib.util.spec_from_file_location('sparsity_audit',FILE)
sparse=importlib.util.module_from_spec(spec);spec.loader.exec_module(sparse)


def build_file(dst, arrays):
    header={}; payload=b''
    for name,(dtype,shape,data) in arrays.items():
        start=len(payload);payload+=data
        header[name]={'dtype':dtype,'shape':list(shape),'data_offsets':[start,len(payload)]}
    h=json.dumps(header,separators=(',',':')).encode()
    dst.write_bytes(struct.pack('<Q',len(h))+h+payload)

class AuditTests(unittest.TestCase):
    def test_4x4_zero_blocks_and_negative_zero(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'toy.safetensors'
            a=np.zeros((8,8),dtype='<f4');a[0,0]=1;a[7,7]=-0.0
            build_file(f,{'layer':('F32',a.shape,a.tobytes())})
            x=sparse.audit(f,blocks=(4,8))['tensors']['layer']
            self.assertEqual(x['zero_elements'],63)
            self.assertEqual(x['blocks']['4']['eligible_blocks'],4)
            self.assertEqual(x['blocks']['4']['zero_blocks'],3)
            self.assertEqual(x['blocks']['8']['zero_blocks'],0)
    def test_half_bfloat_negative_zero(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'zeros.safetensors'
            a=np.zeros((4,4),dtype='<u2');a[0,0]=0x8000;a[3,3]=0x3c00
            build_file(f,{'bfloat':('BF16',a.shape,a.tobytes()),'half':('F16',a.shape,a.tobytes())})
            x=sparse.audit(f,blocks=(4,))['tensors']
            self.assertEqual(x['half']['zero_elements'],15)
            self.assertEqual(x['bfloat']['blocks']['4']['zero_blocks'],0)
    def test_partial_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'edge.safetensors'
            a=np.zeros((5,6),dtype=np.int8);a[4,5]=3
            build_file(f,{'w':('I8',a.shape,a.tobytes())})
            x=sparse.audit(f,blocks=(4,))['tensors']['w']
            self.assertEqual(x['zero_elements'],29)
            self.assertEqual(x['blocks']['4']['zero_blocks'],1)
            self.assertEqual(x['blocks']['4']['incomplete_edge_elements'],14)
    def test_bad_tensor_length(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'bad.safetensors'
            build_file(f,{'w':('I8',(4,4),b'\0'*15)})
            with self.assertRaises(ValueError):sparse.audit(f)
    def test_skips_nonmatrix(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'rank1.safetensors'
            build_file(f,{'bias':('F32',(4,),np.zeros((4,),dtype='<f4').tobytes())})
            self.assertEqual(sparse.audit(f)['tensors']['bias']['status'],'skipped_nonmatrix')
    def test_aggregate_is_weighted_by_blocks_not_tensor_mean(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'aggregate.safetensors'
            a=np.zeros((8,8),dtype=np.int8);a[0,0]=1
            b=np.zeros((4,4),dtype=np.int8)
            build_file(f,{'a':('I8',a.shape,a.tobytes()),'b':('I8',b.shape,b.tobytes())})
            x=sparse.audit(f,blocks=(4,))['aggregate']
            self.assertEqual(x['measured_matrix_tensors'],2)
            self.assertEqual(x['elements'],80)
            self.assertEqual(x['zero_elements'],79)
            self.assertEqual(x['blocks']['4']['eligible_blocks'],5)
            self.assertEqual(x['blocks']['4']['zero_blocks'],4)
            self.assertAlmostEqual(x['blocks']['4']['zero_block_fraction'],0.8)
    def test_reject_bad_block_shapes(self):
        for sizes in ((0,4),(3,4),(3,4,6),()):
            with self.subTest(sizes=sizes),self.assertRaises(ValueError):sparse.audit('absent',sizes)

if __name__=='__main__': unittest.main()
