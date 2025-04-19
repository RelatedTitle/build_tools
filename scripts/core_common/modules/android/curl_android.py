#!/usr/bin/env python

import sys
sys.path.append('../../../scripts')
import base
import os
import android_ndk

current_dir = os.path.abspath(os.path.join(base.get_script_dir(), "../../core/Common/3dParty/curl"))
# Ensure directory ends with separator for all platforms
current_dir = os.path.join(current_dir, "")

lib_version = "curl-7_68_0"
lib_name = "curl-7.68.0"

def fetch():
  if not base.is_dir(os.path.join(current_dir, lib_name)):
    base.cmd("curl", ["-L", "-s", "-o", os.path.join(current_dir, lib_name + ".tar.gz"), 
      "https://github.com/curl/curl/releases/download/" + lib_version + "/" + lib_name + ".tar.gz"])
    base.cmd("tar", ["xfz", os.path.join(current_dir, lib_name + ".tar.gz"), "-C", current_dir])
  return

def build_host():
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

  params = []
  if ("arm64" == arch):
    params.append("--host=aarch64-linux-android")
  elif ("arm" == arch):
    params.append("--host=arm-linux-androideabi")
  elif ("x86_64" == arch):
    params.append("--host=x86_64-linux-android")
  elif ("x86" == arch):
    params.append("--host=i686-linux-android")

  openssl_dir = os.path.abspath(os.path.join(current_dir, "../openssl/build/android", android_ndk.platforms[arch]["dst"]))

  params.append("--enable-ipv6")
  params.append("--enable-static")
  params.append("--disable-shared")
  params.append("--prefix=" + arch_build_dir)
  params.append("--with-ssl=" + openssl_dir)

  base.cmd("./configure", params)

  base.cmd("make", ["clean"])
  base.cmd("make", ["-j4"])
  base.cmd("make", ["install"])

  os.chdir(old_cur)

  base.create_dir(dst_dir)
  base.copy_file(os.path.join(arch_build_dir, "lib", "libcurl.a"), dst_dir)
  base.copy_dir(os.path.join(arch_build_dir, "include"), os.path.join(current_dir, "build", "android", "include"))

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
