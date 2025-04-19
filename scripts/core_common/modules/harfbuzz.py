#!/usr/bin/env python

import sys
sys.path.append('../..')
import base
import os

def make():
  print("[fetch & build]: harfbuzz")
  harfbuzz_dir = os.path.join(base.get_script_dir(), "../../core/Common/3dParty/harfbuzz")
  base.cmd_in_dir(harfbuzz_dir, "./make.py")
  return

if __name__ == '__main__':
  # manual compile
  make()
