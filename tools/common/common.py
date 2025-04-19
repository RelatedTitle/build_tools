#!/usr/bin/env python

import sys
import os
import re
import shutil
import subprocess
import multiprocessing

def get_platform():
  platform = sys.platform
  if (platform == "win32"):
    return "win"
  elif (platform == "darwin"):
    return "mac"
  return "linux"

def get_system_libs(platform):
  if (platform == "mac"):
    return []
  if (platform != "linux"):
    return []
  
  # pacman
  ret = lib_from_command("pacman -Q | grep 'lib' | cut -d ' ' -f 1", "-devel")
  if (ret != []):
    return ret

  # apt-get
  ret = lib_from_command("apt list --installed | grep 'lib' | cut -d '/' -f 1", "-dev")
  if (ret != []):
    return ret

  # dnf
  ret = lib_from_command("dnf list installed | grep 'lib' | cut -d ' ' -f 1", "-devel")
  if (ret != []):
    return ret

  # yum
  ret = lib_from_command("yum list installed | grep 'lib' | cut -d ' ' -f 1", "-devel")
  if (ret != []):
    return ret

  # zypper
  ret = lib_from_command("zypper packages --installed-only | grep 'lib' | cut -d '|' -f 3 | sed -e 's/^[[:space:]]*//'", "-devel")
  if (ret != []):
    return ret

  return []

def lib_from_command(command, dev_suffix):
  ret = []
  search_libs = [
    "krb5", 
    "xslt", 
    "xml2", 
    "glib-2.0", 
    "cairo", 
    "gobject-2.0", 
    "pango-1.0", 
    "pangocairo-1.0", 
    "gtk-3", 
    "gdk-3"
  ]

  try:
    result = os.popen(command).read().strip()
    for line in result.split('\n'):
      for lib in search_libs:
        if lib in line:
          dev_package = line
          if (dev_package.find(dev_suffix) < 0 and dev_package.find("-dev") < 0):
            if not dev_package in ret:
              ret.append(dev_package)
          continue
  except:
    return []
  
  return ret

def run_command(sCommand):
  popen = subprocess.Popen(sCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
  result = {"stdout" : "", "stderr" : ""}
  try:
    stdout, stderr = popen.communicate()

    if (stdout is not None):
      if isinstance(stdout, bytes):
        stdout = stdout.decode('utf-8', errors='ignore')
      result["stdout"] = stdout

    if (stderr is not None):
      if isinstance(stderr, bytes):
        stderr = stderr.decode('utf-8', errors='ignore')
      result["stderr"] = stderr

    result["returncode"] = popen.returncode
  except subprocess.TimeoutExpired:
    pass

  return result

def run_process(args=[], is_no_errors=False, is_no_output=False):
  subprocess_args = {
    "args": args,
    "stderr": subprocess.PIPE,
    "stdout": subprocess.PIPE,
    "cwd": os.getcwd()
  }

  if sys.platform.startswith("win"):
    subprocess_args["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

  process = subprocess.Popen(**subprocess_args)

  stdout, stderr = process.communicate()
  
  if stdout:
    stdout = stdout.decode("utf-8", errors="ignore")
    if not is_no_output:
      print(stdout)

  if stderr:
    stderr = stderr.decode("utf-8", errors="ignore")
    if not is_no_errors:
      print(stderr)

  return process.returncode

def run_process_in_dir(directory, args=[], is_no_errors=False, is_no_output=False):
  cur_dir = os.getcwd()
  os.chdir(directory)
  ret = run_process(args, is_no_errors, is_no_output)
  os.chdir(cur_dir)
  return ret

# get count of processors
def get_proc_count():
  try:
    return multiprocessing.cpu_count()
  except:
    return 1
  
def get_script_dir(file=None):
  if file is None:
    file = __file__
  return os.path.dirname(os.path.realpath(file))

def is_file_exist(file_path):
  return os.path.exists(file_path)

def is_dir_exist(dir_path):
  return os.path.isdir(dir_path)

def get_path(path):
  if isfile_exist(path):
    return os.path.dirname(path)
  return ""

def copy_file(src, dst):
  if is_file_exist(dst):
    delete_file(dst)
  return shutil.copy2(src, dst)

def move_file(src, dst):
  if is_file_exist(dst):
    delete_file(dst)
  return shutil.move(src, dst)

def copy_dir(src, dst):
  if is_dir_exist(dst):
    delete_dir(dst)
  return shutil.copytree(src, dst)

def move_dir(src, dst):
  if is_dir_exist(dst):
    delete_dir(dst)
  return shutil.move(src, dst)

def delete_file(path):
  return os.remove(path)

def delete_dir(path):
  if not is_dir_exist(path):
    return
  shutil.rmtree(path)

def create_dir(path):
  if is_dir_exist(path):
    return
  os.makedirs(path)

def rename_file(src, dst):
  if is_file_exist(dst):
    delete_file(dst)
  return os.rename(src, dst)

def rename_dir(src, dst):
  if is_dir_exist(dst):
    delete_dir(dst)
  return os.rename(src, dst)

def read_file_unicode(file_path):
  try:
    with open(file_path, 'rb') as file:
      data = file.read()
      if (0xEF == data[0] and 0xBB == data[1] and 0xBF == data[2]):
        return data[3:].decode('utf-8')
      return data.decode('utf-8')
  except:
    return ""

def read_file_bytes(file_path):
  try:
    with open(file_path, 'rb') as file:
      return file.read()
  except:
    return bytes("")

def save_file(file_path, data, is_create_dirs=False):
  if (is_create_dirs):
    create_dirs_for_file(file_path)
  with open(file_path, 'wb') as file:
    file.write(data)
  return

def create_dirs_for_file(file_path):
  dir_path = os.path.dirname(file_path)
  if (dir_path):
    if not is_dir_exist(dir_path):
      os.makedirs(dir_path)

def join_path(path1, path2):
  if (path2.startswith("/")):
    return path2
  return os.path.join(path1, path2)

def get_file_name(path):
  return os.path.basename(path)

def get_dir_name(path):
  dir_name = os.path.dirname(path)
  if dir_name == path:
    return os.path.basename(dir_name)
  if dir_name[-1] == "/":
    dir_name = dir_name[:-1]
  return os.path.basename(dir_name)

def get_regex_pattern_list(regex, data):
  res = []
  regex_pattern = re.compile(regex)
  for line in data:
    matches = regex_pattern.findall(line)
    for match in matches:
      res.append(match)
  res = list(set(res))
  return res

def get_env(name):
  return os.getenv(name)

def set_env(name, value):
  os.environ[name] = value

def unset_env(name):
  try:
    del os.environ[name]
  except KeyError:
    pass 