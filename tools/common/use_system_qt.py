#!/usr/bin/env python

import sys
import os
import re
import glob

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import base

def read_file_configurable():
  global configurable
  path_config = os.path.join(base.get_script_dir(), "..", "..", "configure.txt")
  if not os.path.exists(path_config):
    return
  with open(path_config, "r") as file:
    content = file.read()
    configurable = content.split("\n")

def is_file_exist(file):
  file_path = os.path.join(get_qmake_binary_dir(), file)
  if os.path.exists(file_path):
    return True
  return False

def get_qmake_binary_dir():
  # linux and mac
  if ("linux" == base.host_platform() or "darwin" == base.host_platform()):
    qt_dir = glob_find("/usr/bin/*", "qmake")
    if ("" == qt_dir):
      qt_dir = glob_find("/usr/bin/*", "qmake-qt5")
    if ("" == qt_dir):
      qt_dir = glob_find("/usr/bin/*", "qmake-qt4")
    return qt_dir

  # windows
  res = os.getenv("PROGRAMFILES(X86)")
  if res is None:
    res = os.getenv("PROGRAMFILES")
  return res

def glob_find(path, pattern):
  dir = ""
  for dir in glob.glob(path):
    if -1 != dir.find(pattern):
      return os.path.dirname(dir)
  return ""

def get_path_to_used_system_qt(dir):
  global qmake_path
  global mxe_dir
  global configurable
  global enable_system_qt

  configurable = []
  read_file_configurable()
  
  if (sys.argv[1] == "check-system-qt"):
    enable_system_qt = "true" in configurable
    return ""

  # linux and mac
  if ("linux" == base.host_platform() or "darwin" == base.host_platform()):
    if (not "true" in configurable):
      return dir
    qt_dir = get_qmake_binary_dir()
    if ("" == qt_dir):
      return dir
    env_file_path = os.path.join(dir, "env", "qt.env")
    with open(env_file_path, "w") as file:
      file.write("export QT_DEPLOY=" + qt_dir + "\n")
    qmake_path = os.path.join(qt_dir, "qmake")
    if not os.path.exists(qmake_path):
      qmake_path = os.path.join(qt_dir, "qmake-qt5")
    if not os.path.exists(qmake_path):
      qmake_path = os.path.join(qt_dir, "qmake-qt4")
    return dir

  if ("windows" == base.host_platform()):
    if ("1" == sys.argv[1]):
      mxe_dir = os.path.join(dir, "qt_build")
      if ("true" in configurable):
        if (0 == base.run_command("qmake -query QT_INSTALL_BINS")["returncode"]):
          mxe_dir = base.get_stdout_command("qmake -query QT_INSTALL_BINS")
          mxe_dir = mxe_dir.replace("\r\n", "").replace("\n", "")
          mxe_dir = os.path.dirname(mxe_dir)
          env_file_path = os.path.join(dir, "env", "qt.env")
          with open(env_file_path, "w") as file:
            file.write("set QT_DEPLOY=" + mxe_dir + "\n")
          return ""
      
      res = get_qmake_binary_dir()
      
      if res is None:
        return dir

      last_folder_version = ""
      qt_dir_max_version = ""
      qt_max_version = [0, 0, 0, 0]
      qt_dir = ""

      for path in glob.glob(os.path.join(res, "Qt*")):
        if not os.path.isdir(path):
          continue
        last_folder = os.path.basename(path)
        folder_version = last_folder.replace("Qt", "")
        
        if not is_version(folder_version):
          continue

        qmake_file = os.path.join(path, "5.1.0", "mingw48_32", "bin", "qmake.exe")
        
        if not os.path.exists(qmake_file):
          folder_versions = get_sub_dirs(path)
          if (0 == len(folder_versions)):
            continue
          
          best_folder_version = get_best_version(folder_versions)
          platforms = get_sub_dirs(os.path.join(path, best_folder_version))
          
          if 0 == len(platforms):
            continue
          
          Qt_platforms = []
          for platform in platforms:
            # search binary qmake
            qmake_file = os.path.join(path, best_folder_version, platform, "bin", "qmake.exe")
            if os.path.exists(qmake_file):
              Qt_platforms.append(platform)

          if 0 == len(Qt_platforms):
            continue

          sorted_platforms = sorted(Qt_platforms)
          n = len(sorted_platforms)
          best_index = -1
          for i in range(n):
            if -1 != sorted_platforms[i].find("mingw"):
              best_index = i

          if -1 == best_index:
            best_index = n - 1

          best_platform = sorted_platforms[best_index]
          tmp = best_folder_version.split(".")
          tmp_array_version = [0, 0, 0, 0]
          
          if 1 < len(tmp):
            if is_version(tmp[0]):
              tmp_array_version[0] = int(tmp[0])
            if is_version(tmp[1]):
              tmp_array_version[1] = int(tmp[1])
          if 2 < len(tmp):
            if is_version(tmp[2]):
              tmp_array_version[2] = int(tmp[2])
          if 3 < len(tmp):
            if is_version(tmp[3]):
              tmp_array_version[3] = int(tmp[3])
              
          if array_compare(qt_max_version, tmp_array_version) <= 0:
            qt_max_version = tmp_array_version
            qt_dir = os.path.join(path, best_folder_version, best_platform)
            qt_dir_max_version = best_folder_version
            last_folder_version = last_folder

      if ("" == qt_dir):
        return dir

      qmake_path = os.path.join(qt_dir, "bin", "qmake.exe")
      
      get_environ_paths = os.environ["PATH"].split(os.pathsep)
      qt_bins_path = os.path.join(qt_dir, "bin")
      qt_libs_path = os.path.join(qt_dir, "lib")
      
      environment_path = []
      for i in range(0, len(get_environ_paths)):
        if (-1 == get_environ_paths[i].find(last_folder_version)):
          environment_path.append(get_environ_paths[i])

      environment_path.append(qt_bins_path)
      environment_path.append(qt_libs_path)
      
      os.environ["PATH"] = os.pathsep.join(environment_path)
      return dir

  return dir

def array_compare(arr1, arr2):
  if arr1[0] > arr2[0]:
    return 1
  if arr1[0] < arr2[0]:
    return -1
  if arr1[1] > arr2[1]:
    return 1
  if arr1[1] < arr2[1]:
    return -1
  if arr1[2] > arr2[2]:
    return 1
  if arr1[2] < arr2[2]:
    return -1
  if arr1[3] > arr2[3]:
    return 1
  if arr1[3] < arr2[3]:
    return -1
  return 0

def is_version(text):
  if None == text:
    return False
  return re.match(r'^ *\d+(\.\d+)? *$', text)

def get_sub_dirs(dir):
  if not os.path.isdir(dir):
    return []
  res = []
  for item in os.listdir(dir):
    if os.path.isdir(os.path.join(dir, item)):
      res.append(item)
  return res

def get_best_version(versions):
  if 0 == len(versions):
    return ""
  best_version = ""
  max_array = [0, 0, 0, 0]
  for version in versions:
    arr_version = [0, 0, 0, 0]
    items = version.split(".")
    if 1 < len(items):
      if is_version(items[0]):
        arr_version[0] = int(items[0])
      if is_version(items[1]):
        arr_version[1] = int(items[1])
    if 2 < len(items):
      if is_version(items[2]):
        arr_version[2] = int(items[2])
    if 3 < len(items):
      if is_version(items[3]):
        arr_version[3] = int(items[3])
    
    if array_compare(max_array, arr_version) <= 0:
      max_array = arr_version
      best_version = version
  return best_version

def configure_params(params):
  global qmake_path
  global mxe_dir
  global enable_system_qt

  if not "linux" == base.host_platform() and not "darwin" == base.host_platform():
    return params

  if not ("true" in configurable):
    return params

  # important order!!! options for qmake!!
  params[params.index("--qt-dir=../../../../build_tools/qt_build")] = "--qt-dir=" + get_qmake_binary_dir()
  return params

qmake_path = ""
mxe_dir = ""
configurable = []
enable_system_qt = False

if __name__ == "__main__":
  dir = get_path_to_used_system_qt(sys.argv[2])
  
  if "" != dir:
    print(dir, end='')
  elif "" != mxe_dir:
    print(mxe_dir, end='') 