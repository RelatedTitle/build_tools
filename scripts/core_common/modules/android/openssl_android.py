#!/usr/bin/env python

import sys
sys.path.append('../../../scripts')
import base
import os
import android_ndk

current_dir = os.path.abspath(os.path.join(base.get_script_dir(), "../../core/Common/3dParty/openssl"))
# Ensure directory ends with separator for all platforms
current_dir = os.path.join(current_dir, "")

lib_name = "openssl-1.1.1t"

options = [
  "no-shared",
  "no-tests",
  "enable-ssl3",
  "enable-ssl3-method",
  "enable-md2",
  "no-asm"
]

def fetch():
  if not base.is_dir(os.path.join(current_dir, lib_name)):
    base.cmd("curl", ["-L", "-s", "-o", os.path.join(current_dir, lib_name + ".tar.gz"), 
      "https://www.openssl.org/source/" + lib_name + ".tar.gz"])
    base.cmd("tar", ["xfz", os.path.join(current_dir, lib_name + ".tar.gz"), "-C", current_dir])
  return

def build_host():
  # not needed, just create directories
  build_dir = os.path.join(current_dir, "build")
  if not base.is_dir(build_dir):
    base.create_dir(build_dir)
  
  android_dir = os.path.join(build_dir, "android")
  if not base.is_dir(android_dir):
    base.create_dir(android_dir)
  return

def build_arch(arch):
  dst_dir = os.path.join(current_dir, "build", "android", android_ndk.platforms[arch]["dst"])
  if base.is_dir(dst_dir):
    return

  android_ndk.prepare_platform(arch)

  ndk_dir = android_ndk.ndk_dir()
  toolchain = android_ndk.toolchain_dir()

  base.set_env("ANDROID_NDK_HOME", ndk_dir)
  base.set_env("ANDROID_NDK", ndk_dir)

  arch_build_dir = os.path.abspath(os.path.join(current_dir, "build", "android", "tmp"))
  base.create_dir(arch_build_dir)

  old_cur = os.getcwd()
  os.chdir(os.path.join(current_dir, lib_name))

  base.cmd("./Configure", ["android-" + arch, "--prefix=" + arch_build_dir, "-D__ANDROID_API__=" + android_ndk.platforms[arch]["api"]] + options)

  base.replaceInFile("./Makefile", "LIB_CFLAGS=", "LIB_CFLAGS=-fvisibility=hidden ")
  base.replaceInFile("./Makefile", "LIB_CXXFLAGS=", "LIB_CXXFLAGS=-fvisibility=hidden ")

  base.cmd("make", ["clean"])
  base.cmd("make", ["-j4"])
  base.cmd("make", ["install"])

  os.chdir(old_cur)

  base.create_dir(dst_dir)
  lib_dir = os.path.join(dst_dir, "lib")
  base.create_dir(lib_dir)
  base.copy_file(os.path.join(arch_build_dir, "lib", "libcrypto.a"), lib_dir)
  base.copy_file(os.path.join(arch_build_dir, "lib", "libssl.a"), lib_dir)
  base.copy_dir(os.path.join(arch_build_dir, "include"), os.path.join(dst_dir, "include"))

  base.delete_dir(arch_build_dir)
  return

def make():
  old_env = dict(os.environ)

  fetch()

  build_host()

  for arch in android_ndk.archs:
    build_arch(arch)

  os.environ.clear()
  os.environ.update(old_env)
  return

if __name__ == "__main__":
  make()
