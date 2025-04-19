#!/usr/bin/env python
import sys
sys.path.append('../..')
sys.path.append('android')
import base
import config
import os
import subprocess
import openssl_android

def clean():
  if base.is_dir("openssl"):
    base.delete_dir("openssl")
  return

def make():
  if not base.is_dir("openssl"):
    base.cmd("git", ["clone", "--depth=1", "--branch", "OpenSSL_1_1_1t", "https://github.com/openssl/openssl.git"])
  
  old_cur = os.getcwd()
  
  if base.is_dir(os.path.join("openssl", ".git")):
    base.delete_dir_with_access_error(os.path.join("openssl", ".git"))
  
  if (-1 != config.option("platform").find("ios")):
    os.chdir(os.path.join(old_cur, "openssl"))
    if not config.check_option("platform", "ios_simulator"):
      ios_prefix = os.path.join(old_cur, "build", "ios", "openssl")
      base.cmd("./Configure", ["no-shared", "no-asm", "no-hw", f"--prefix={ios_prefix}", f"--openssldir={ios_prefix}", "iphoneos-cross"])
    else:
      ios_sim_prefix = os.path.join(old_cur, "build", "ios_simulator", "openssl")
      base.cmd("./Configure", ["no-shared", "no-asm", "no-hw", f"--prefix={ios_sim_prefix}", f"--openssldir={ios_sim_prefix}", "iphonesimulator-x86_64"])
    
    old_env = os.environ.copy()
    
    os.environ["CROSS_TOP"] = base.get_env("CROSS_TOP")
    os.environ["CROSS_SDK"] = base.get_env("CROSS_SDK")
    
    if (base.get_env("CCACHE") != ""):
      os.environ["CC"] = "{0} clang -fembed-bitcode".format(base.get_env("CCACHE"))
    else:
      os.environ["CC"] = "clang -fembed-bitcode"
    base.cmd("make", ["clean"])
    base.cmd("make", ["build_libs"])
    base.cmd("make", ["install_dev"])
    
    os.environ.clear()
    os.environ.update(old_env)
    os.chdir(old_cur)
  
  if ("android" == config.option("platform")):
    os.chdir(old_cur)
    android_openssl_dir = os.path.join(old_cur, "android_openssl")
    if not base.is_dir(android_openssl_dir):
      base.create_dir(android_openssl_dir)
      os.chdir(android_openssl_dir)
      base.cmd("git", ["clone", "--depth=1", "--branch", "master", "https://github.com/ONLYOFFICE/android_openssl.git", "."])
    
    os.chdir(old_cur)
    os.environ["ANDROID_NDK_HOME"] = os.environ["ANDROID_NDK_ROOT"]
    
    openssl_path = os.path.join(old_cur, "openssl")
    target_dir = os.path.join(old_cur, "build", "android")
    
    # Build for each architecture
    for arch in ["arm64", "arm", "x86", "x86_64"]:
      build_script = os.path.join(old_cur, "android_openssl", "build.py")
      base.cmd(build_script, [
        f"--openssl={openssl_path}",
        f"--ndk-root={os.environ['ANDROID_NDK_ROOT']}",
        f"--target-dir={target_dir}",
        f"--arch={arch}"
      ])
  
  return