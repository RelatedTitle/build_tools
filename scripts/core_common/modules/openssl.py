#!/usr/bin/env python

import sys
sys.path.append('../..')
import config
import base
import os
import platform
import openssl_mobile

def clean():
  if base.is_dir("openssl"):
    base.delete_dir("openssl")
  if base.is_dir("build"):
    base.delete_dir("build")
  return

def make():

  print("[fetch & build]: openssl")

  base_dir = os.path.join(base.get_script_dir(), "..", "..", "core", "Common", "3dParty", "openssl")
  old_cur = os.getcwd()
  os.chdir(base_dir)

  base.common_check_version("openssl", "4", clean)

  if (-1 != config.option("platform").find("android") or -1 != config.option("platform").find("ios")):
    os.chdir(old_cur)
    openssl_mobile.make()
    return

  if not base.is_dir("openssl"):
    base.cmd("git", ["clone", "--depth=1", "--branch", "OpenSSL_1_1_1f", "https://github.com/openssl/openssl.git"])
    if ("mac" == base.host_platform()):
      base.cmd_in_dir("openssl", "sed", ["-i", "", "s/\\(define CRYPTOGAMS\\)/\\1 1/g", "./crypto/modes/asm/aesni-gcm-x86_64.pl"])
      base.cmd_in_dir("openssl", "sed", ["-i", "", "s/\\(define CRYPTOGAMS\\)/\\1 1/g", "./crypto/poly1305/asm/poly1305-x86_64.pl"])
  
  os_prefix = ""
  if base.is_dir(os.path.join("openssl", ".git")):
    base.delete_dir_with_access_error(os.path.join("openssl", ".git"))

  os.chdir(os.path.join(old_cur, "openssl"))

  if ("win_32" == base.host_platform_()):
    if (-1 != config.option("platform").find("win_32")):
      prefix_path = os.path.join("..", "build", "win_32", "openssl")
      base.cmd("perl", ["Configure", "VC-WIN32", "no-shared", "no-asm", f"--prefix={prefix_path}", f"--openssldir={prefix_path}"])
      base.cmd("nmake", ["clean"])
      base.cmd("nmake", ["build_libs"])
      base.cmd("nmake", ["install_dev"])
      # make error to not build twice (note: true result: no errors)
      return

  if ("win_64" == base.host_platform_()):
    if (-1 != config.option("platform").find("win_64")):
      prefix_path = os.path.join("..", "build", "win_64", "openssl")
      base.cmd("perl", ["Configure", "VC-WIN64A", "no-shared", "no-asm", f"--prefix={prefix_path}", f"--openssldir={prefix_path}"])
      base.cmd("nmake", ["clean"])
      base.cmd("nmake", ["build_libs"])
      base.cmd("nmake", ["install_dev"])
      # make error to not build twice (note: true result: no errors)
      return

  if ("linux_64" == base.host_platform_()) and (-1 != config.option("platform").find("linux_64")):
    prefix_path = os.path.join("..", "build", "linux_64", "openssl")
    base.cmd("./config", ["no-shared", f"--prefix={prefix_path}", f"--openssldir={prefix_path}"])
    base.cmd("make", ["clean"])
    base.cmd("make", ["build_libs"])
    base.cmd("make", ["install_dev"])
    # make error to not build twice (note: true result: no errors)
    return

  if ("linux" == base.host_platform()) and (-1 != config.option("platform").find("linux_arm64")):
    prefix_path = os.path.join("..", "build", "linux_arm64", "openssl")
    base.cmd("./Configure", ["linux-aarch64", "no-shared", f"--prefix={prefix_path}", f"--openssldir={prefix_path}"])
    base.cmd("make", ["clean"])
    base.cmd("make", ["build_libs"])
    base.cmd("make", ["install_dev"])
    # make error to not build twice (note: true result: no errors)
    return

  if (-1 != config.option("platform").find("linux_32")):
    prefix_path = os.path.join("..", "build", "linux_32", "openssl")
    base.cmd("./config", ["no-shared", "-m32", f"--prefix={prefix_path}", f"--openssldir={prefix_path}"])
    base.cmd("make", ["clean"])
    base.cmd("make", ["build_libs"])
    base.cmd("make", ["install_dev"])
    # make error to not build twice (note: true result: no errors)
    return
  
  if ("mac" == base.host_platform()):
    if (-1 != config.option("platform").find("mac")):
      prefix_path = os.path.join("..", "build", "mac_64", "openssl")
      base.cmd("./Configure", ["no-shared", "darwin64-x86_64-cc", f"--prefix={prefix_path}", f"--openssldir={prefix_path}", "-mmacosx-version-min=10.11"])
      base.cmd("make", ["clean"])
      base.cmd("make", ["build_libs"])
      base.cmd("make", ["install_dev"])
      return

  if (-1 != config.option("platform").find("ios")):
    if not config.check_option("platform", "ios_simulator"):
      prefix_path = os.path.join("..", "build", "ios", "openssl")
      base.cmd("./Configure", ["no-shared", "iphoneos-cross", "no-asm", f"--prefix={prefix_path}", f"--openssldir={prefix_path}"])
    else:
      prefix_path = os.path.join("..", "build", "ios_simulator", "openssl")
      base.cmd("./Configure", ["no-shared", "iphonesimulator-x86_64", "no-asm", f"--prefix={prefix_path}", f"--openssldir={prefix_path}"])
    
    old_env = os.environ.copy()
    
    os.environ["CROSS_TOP"] = base.get_env("CROSS_TOP")
    os.environ["CROSS_SDK"] = base.get_env("CROSS_SDK")
    
    if (base.get_env("CCACHE") != ""):
      os.environ["CC"] = "{0} clang -fembed-bitcode".format(base.get_env("CCACHE"))
    else:
      os.environ["CC"] = "clang -fembed-bitcode"
    base.cmd_and_return_cwd(base.cmd, ["make", "clean"])
    base.cmd_and_return_cwd(base.cmd, ["make", "build_libs"])
    base.cmd_and_return_cwd(base.cmd, ["make", "install_dev"])
    
    os.environ.clear()
    os.environ.update(old_env)
  
  if ("android" == config.option("platform")):
    if not base.is_dir(os.path.join(old_cur, "android_openssl")):
      android_openssl_dir = os.path.join(old_cur, "android_openssl")
      base.create_dir(android_openssl_dir)
      os.chdir(android_openssl_dir)
      base.cmd("git", ["clone", "--depth=1", "--branch", "master", "https://github.com/ONLYOFFICE/android_openssl.git", "."])
      os.chdir(os.path.join(old_cur, "openssl"))

    os.environ["ANDROID_NDK_HOME"] = os.environ["ANDROID_NDK_ROOT"]
    target_dir = os.path.join(old_cur, "build", "android")
    
    # Build for each architecture
    for arch in ["arm64", "arm", "x86", "x86_64"]:
      build_script = os.path.join(old_cur, "android_openssl", "build.py")
      base.cmd(build_script, [
        f"--openssl=./", 
        f"--ndk-root={os.environ['ANDROID_NDK_ROOT']}", 
        f"--target-dir={target_dir}", 
        f"--arch={arch}"
      ])
  
  os.chdir(old_cur)
  return
