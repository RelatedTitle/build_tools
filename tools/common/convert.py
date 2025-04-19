#!/usr/bin/env python

import sys
import os
sys.path.append(os.path.join('..', '..', 'scripts'))
import base
import convert_common

# parse parameters
params = sys.argv[1:]
if (6 > len(params)):
  print("use: convert.py path_to_builder (1 or 0) path_to_output_dir path_to_data_dir server")
  exit(0)

base.set_script_dir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "scripts"))

path = params[0]
is_only_for_tests = True if "1" == params[1] else False
output_dir = params[2]
input_dir = params[3]
langs = params[5].split("\t")
server = params[4]
input_dir_absolute = os.path.join(os.getcwd(), input_dir)
output_dir_absolute = os.path.join(os.getcwd(), output_dir)
cache_dir = os.path.join(output_dir_absolute, "cache")

if not base.is_dir(path):
  base.create_dir(path)

base.create_dir(os.path.join(path, "HtmlFileInternal"))
base.copy_dir(os.path.join(input_dir_absolute, "js"), os.path.join(path, "HtmlFileInternal", "js"))
base.copy_dir(os.path.join(input_dir_absolute, "sdkjs"), os.path.join(path, "HtmlFileInternal", "sdkjs"))
base.copy_dir(os.path.join(input_dir_absolute, "web-apps"), os.path.join(path, "HtmlFileInternal", "web-apps"))

if not "windows" == base.host_platform():
  if ("linux" == base.host_platform()):
    env = os.environ
    env["LD_LIBRARY_PATH"] = os.path.abspath(os.path.join(path, "HtmlFileInternal", "sdkjs", "common", "HtmlFile", "ascshared", "lib"))
  elif ("mac" == base.host_platform()):
    env = os.environ
    env["DYLD_LIBRARY_PATH"] = os.path.dirname(os.path.abspath(os.path.join(path, "HtmlFileInternal", "sdkjs", "common", "HtmlFile", "ascshared", "lib")))

custom_public_key_file = os.path.join(input_dir_absolute, "onlyoffice.public.key")
if base.is_file(custom_public_key_file):
  base.copy_file(custom_public_key_file, os.path.join(path, "onlyoffice.public.key"))

base.create_dir(cache_dir)

params_from = []
params_to = []
for lang in langs:
  if is_only_for_tests:
    params_from.append("en-US")
    params_to.append(lang)
    convert_common.convert(path, params_from, params_to, output_dir_absolute, cache_dir, server)
    
    params_from.clear()
    params_to.clear()
  else:
    params_from.append(lang)
    params_to.append(lang)

if not is_only_for_tests:
  convert_common.convert(path, params_from, params_to, output_dir_absolute, cache_dir, server)
