#!/usr/bin/env python

import sys
sys.path.append('../..')
import base
import os
import config
from distutils.version import LooseVersion, StrictVersion

current_dir = os.path.join(base.get_script_dir(), "..", "..", "core", "Common", "3dParty", "ixwebsocket")

CMAKE = "cmake"

def find_last_version(arr_input, base_directory):
    arr = []
    for arr_rec in arr_input:
      if base.is_file(os.path.join(base_directory, arr_rec, "bin", "cmake")):
        arr.append(arr_rec)
    res = arr[0]
    for version in arr:
      if(LooseVersion(version) > LooseVersion(res)):
        res = version
    return res

def build_arch(platform, arch, params, is_debug=False):
  print("ixwebsocket build: " + platform + "....." + arch + " ----------------------------------------")

  build_dir = os.path.join(current_dir, "IXWebSocket", "build", platform, arch)
  if base.is_dir(build_dir):
    base.delete_dir(build_dir)
  base.create_dir(build_dir)
  cache_dir = os.path.join(current_dir, "IXWebSocket", "build", platform, "cache")
  base.create_dir(cache_dir)
  os.chdir(cache_dir)

  libext = "a" 
  prefix = "/"
  zlib = "1"
  if (0 == platform.find("windows")):
    zlib = "0"
    libext = "lib"
    prefix = os.path.join(cache_dir, "..", arch)

  path = platform
  if(platform == "ios" or platform == "android"):
    path += "/"
  else:
    path = ""

  openssl_base_path = os.path.join(cache_dir, "..", "..", "..", "..", "..", "openssl", "build")

  base.cmd(CMAKE, ["../../..",
    "-DUSE_WS=0", "-DUSE_ZLIB=" + zlib, "-DUSE_TLS=1", "-DUSE_OPEN_SSL=1", 
    "-DOPENSSL_ROOT_DIR=" + os.path.join(openssl_base_path, path, arch),
    "-DOPENSSL_INCLUDE_DIR=" + os.path.join(openssl_base_path, path, arch, "include"),
    "-DOPENSSL_CRYPTO_LIBRARY=" + os.path.join(openssl_base_path, path, arch, "lib", "libcrypto." + libext),
    "-DOPENSSL_SSL_LIBRARY=" + os.path.join(openssl_base_path, path, arch, "lib", "libssl." + libext),
    "-DCMAKE_INSTALL_PREFIX:PATH=" + prefix] + params)

  if(-1 != platform.find("ios") or -1 != platform.find("mac")):
    base.cmd(CMAKE, ["--build", ".", "--config", "Release"])
    base.cmd(CMAKE, ["--install", ".", "--config", "Release", "--prefix", os.path.join(cache_dir, "..", arch)])
  elif(-1 != platform.find("android") or -1 != platform.find("linux")):
    base.cmd("make", ["-j4"])
    base.cmd("make", ["DESTDIR=" + os.path.join(cache_dir, "..", arch), "install"])
  elif(-1 != platform.find("windows")):
    conf = "Debug" if is_debug else "Release"
    base.cmd(CMAKE, ["--build", ".", "--target", "install", "--config", conf])

  base.delete_dir(cache_dir)
  os.chdir(current_dir)

  return

def make():
  base_dir = os.path.join(base.get_script_dir(), "..", "..", "..", "core", "Common", "3dParty", "ixwebsocket")
  old_cur = os.getcwd()
  os.chdir(base_dir)

  if not base.is_dir("IXWebSocket"):
    base.cmd("git", ["clone", "--recursive", "-b", "11.4.3", "https://github.com/machinezone/IXWebSocket.git"])

  if ("windows" == base.host_platform()):
    # windows
    os.chdir("IXWebSocket")

    base.cmd("git", ["apply", "--ignore-whitespace", os.path.join("..", "patches", "ixwebsocket.patch")])

    # dont fetch openssl here because it leads to a third party dll
    base.replaceInFile("CMakeLists.txt", "if(USE_TLS AND NOT USE_MBED_TLS AND NOT USE_OPEN_SSL_LOCAL)", "if(false)")
    base.replaceInFile("CMakeLists.txt", "if(NOT USE_TLS)")
    base.replaceInFile("CMakeLists.txt", "else()")
    base.replaceInFile("CMakeLists.txt", "endif()")
    
    # dont try to set /EHs option. it's clang-only for some reason
    # base.replaceInFile("CMakeLists.txt", "target_compile_options(ixwebsocket PUBLIC /EHs)", "")
    
    if (-1 != config.option("platform").find("win_64")):
      base.cmd("cmake", ["-G", "Visual Studio 16 2019", "-A", "x64", "-DCMAKE_SYSTEM_VERSION=10.0.18362.0", "-DIX_OPENSSL=OFF", "."])
      
      base.cmd("cmake", ["--build", ".", "--config", "Release"])
    
    if (-1 != config.option("platform").find("win_32")):
      base.cmd("cmake", ["-G", "Visual Studio 16 2019", "-A", "Win32", "-DCMAKE_SYSTEM_VERSION=10.0.18362.0", "-DIX_OPENSSL=OFF", "."])
      
      base.cmd("cmake", ["--build", ".", "--config", "Release"])

  elif ("linux" == base.host_platform()):
    base.cmd("apt-get", ["-y", "install", "libssl-dev"])
    # linux
    os.chdir(os.path.join(base_dir, "IXWebSocket"))
    
    if (-1 != config.option("platform").find("linux_64")):
        base.cmd("cmake", ["-DIX_OPENSSL=ON", ".", "-DCMAKE_C_FLAGS=-m64", "-DCMAKE_CXX_FLAGS=-m64", "-DCMAKE_BUILD_TYPE=Release"])
    else:
        base.cmd("cmake", ["-DIX_OPENSSL=ON", ".", "-DCMAKE_C_FLAGS=-m32", "-DCMAKE_CXX_FLAGS=-m32", "-DCMAKE_BUILD_TYPE=Release"])

    base.cmd("cmake", ["--build", "."])

  elif ("mac" == base.host_platform()):
    # mac
    os.chdir(os.path.join(base_dir, "IXWebSocket"))
    
    base.cmd("cmake", ["-DIX_OPENSSL=OFF", "-DCMAKE_OSX_DEPLOYMENT_TARGET=10.11", ".", "-DCMAKE_BUILD_TYPE=Release"])
    base.cmd("cmake", ["--build", "."])

  os.chdir(old_cur)
  return