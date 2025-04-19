#!/usr/bin/env python

import sys
import os
import subprocess
import codecs

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import base

def make():
  base_dir = base.get_script_dir() + "/.."
  old_cur = os.getcwd()
  os.chdir(base_dir)
  base_dir = os.getcwd()
  os.chdir(old_cur)
  if ("windows" == base.host_platform()):
    if not base.is_os_64bit():
      programFilesDir = os.environ["ProgramFiles"]
    else:
      programFilesDir = os.environ["ProgramFiles(x86)"]
    
    sdkDir = programFilesDir + "\\Windows Kits\\10\\bin\\"
    
    config = "xp"
    platform = "x86"
    
    if (base.is_os_64bit()):
      platform = "x64"
      
    compiler_platform = "x86"
    if (base.is_os_64bit()):
      compiler_platform = "amd64"
    
    os.chdir(os.path.join(base_dir, "build_tools", "tools", "win"))
    
    subdirs = []
    for file in os.listdir(sdkDir):
      if os.path.isdir(os.path.join(sdkDir, file)):
        subdirs.append(file)
   
    version_max = "0"
    for subdir in subdirs:
      if (-1 != subdir.find(".")):
        if (version_max < subdir):
          version_max = subdir
    
    # для 10-й версии SDK
    if ("0" != version_max):
      binDir = os.path.join(sdkDir, version_max, platform)
      if not os.path.exists(binDir):
        binDir = os.path.join(sdkDir, version_max, "x86")
      
      if not os.path.exists(binDir + "\\mt.exe"):
        print("Error: in SDK bin dir mt.exe not found!")
        return
      
      argv = ["call", "vcvarsall.bat", compiler_platform + "_xp", "&&", "python", "make.py", config]
      
      print("ms build tools with xp: " + " ".join(argv))
      
      osEnv = os.environ.copy()
      osEnv["PATH"] = binDir + ";" + osEnv["PATH"]
      
      popen = subprocess.Popen(argv, env=osEnv, shell=True)
      popen.communicate()
      return

    # check 8.1 SDK
    if (os.path.exists(programFilesDir + "\\Windows Kits\\8.1\\")):
      osEnv = os.environ.copy()
      
      kernel32file = programFilesDir + "\\Windows Kits\\8.1\\Lib\\winv6.3\\um\\" + platform + "\\kernel32.lib"
      
      if base.is_file(kernel32file):
        sdk_dir = programFilesDir + "\\Windows Kits\\8.1\\"
        path_append = sdk_dir + "\\bin\\" + platform + ";" + sdk_dir + "\\bin\\x86" + ";" + programFilesDir + "\\Microsoft Visual Studio 14.0\\VC\\bin"
        osEnv["PATH"] = path_append + ";" + osEnv["PATH"]
        
        include_append = sdk_dir + "\\Include\\um;" + sdk_dir + "\\Include\\shared"
        osEnv["INCLUDE"] = include_append + ";" + osEnv["INCLUDE"]
        
        libpath_append = sdk_dir + "\\Lib\\winv6.3\\um\\" + platform
        osEnv["LIB"] = libpath_append + ";" + osEnv["LIB"]
      elif os.path.exists(programFilesDir + "\\Windows Kits\\8.1\\Lib\\winv6.3\\um\\" + platform):
        sdk_dir = programFilesDir + "\\Windows Kits\\8.1\\"
        path_append = sdk_dir + "\\bin\\" + platform + ";" + sdk_dir + "\\bin\\x86" + ";" + programFilesDir + "\\Microsoft Visual Studio 14.0\\VC\\bin"
        osEnv["PATH"] = path_append + ";" + osEnv["PATH"]
        
        include_append = sdk_dir + "\\Include\\um;" + sdk_dir + "\\Include\\shared"
        osEnv["INCLUDE"] = include_append + ";" + osEnv["INCLUDE"]
        
        libpath_append = sdk_dir + "\\Lib\\winv6.3\\um\\" + platform
        osEnv["LIB"] = libpath_append + ";" + osEnv["LIB"]
      else:
        print("Error: Windows SDK 8.1 not found!")
        return
        
      argv = ["call", "vcvarsall.bat", compiler_platform, "&&", "python", "make.py", config]
      
      print("ms build tools with 8.1 SDK: " + " ".join(argv))
      
      popen = subprocess.Popen(argv, env=osEnv, shell=True)
      popen.communicate()
      return
      
    print("Error: Windows SDK 8.1 not found!")
    return

  if ("linux" == base.host_platform()):
    # check icu
    result_check_icu = base.run_command("icuinfo -v")["stdout"]
    
    isFoundIcu = False
    
    if (result_check_icu.find("ICU") != -1):
      isFoundIcu = True
      
      checks = ["unicode/ubrk.h", "unicode/utypes.h", "unicode/ustring.h", "unicode/ucnv.h", "unicode/uchar.h", "unicode/coll.h"]
      path_usr_include = "/usr/include/"
      
      isFoundIcuInclude = True
      for check in checks:
        if not base.is_file(path_usr_include + check):
          isFoundIcuInclude = False
          break
      
      if not isFoundIcuInclude:
        print("[WARNING] -----------------------------------------------------------")
        print("[WARNING] Please install icu development package to build fetch.")
        print("[WARNING] -----------------------------------------------------------")
        isFoundIcu = False
        
    if not isFoundIcu:
      print("  dependencies.py fetch")
      base.cmd_in_dir(base_dir + "/build_tools", "python", ["dependencies.py", "fetch", "icu"])
      
    os.chdir(os.path.join(base_dir, "build_tools", "tools", "linux"))
    base.cmd("python", ["make.py", "all", "clean"])
    base.cmd("python", ["make.py", "xp"])
    return

  if ("darwin" == base.host_platform()):
    os.chdir(os.path.join(base_dir, "build_tools", "tools", "mac"))
    base.cmd("python", ["make.py", "clean"])
    base.cmd("python", ["make.py", "xp"])
    return

if __name__ == "__main__":
  make() 