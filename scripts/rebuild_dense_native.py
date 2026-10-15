"""Rebuild the villa-loadable checkpoint of Erwin Nieuwlaar's public dense_native ink model (step 16 000) from its
Hugging Face files: weights/dense_native_016000.safetensors + training/configs/train_dense_native.json.
Output: {'model': state_dict, 'config': <train json>, 'step': 16000}, the layout villa's ink inference loads.
usage: python rebuild_dense_native.py SAFETENSORS TRAIN_JSON OUT.pth"""
import json, sys
import torch
from safetensors.torch import load_file

st, cfg, out = sys.argv[1:4]
torch.save({'model': load_file(st), 'config': json.load(open(cfg)), 'step': 16000}, out)
print('wrote', out)
