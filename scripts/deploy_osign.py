#!/usr/bin/env python

import config
import base
import os

def make():
  base_dir = os.path.join(base.get_script_dir(), "..", "out")
  git_dir = os.path.join(base.get_script_dir(), "..", "..")
  core_dir = os.path.join(git_dir, "core")
  branding = config.branding()

  platforms = config.option("platform").split()
  for native_platform in platforms:
    if not native_platform in config.platforms:
      continue

    root_dir = os.path.join(base_dir, native_platform, branding, "osign")

    if base.get_env("DESTDIR_BUILD_OVERRIDE") != "":
      return
      
    if (base.is_dir(root_dir)):
      base.delete_dir(root_dir)
    base.create_dir(root_dir)

    qt_dir = base.qt_setup(native_platform)
    platform = native_platform

    core_build_dir = os.path.join(core_dir, "build")
    if ("" != config.option("branding")):
      core_build_dir = os.path.join(core_build_dir, config.option("branding"))

    platform_postfix = platform + base.qt_dst_postfix()

    # x2t
    base.copy_lib(os.path.join(core_build_dir, "lib", platform_postfix), root_dir, "osign")

    # correct ios frameworks
    if ("ios" == platform):
      base.generate_plist(root_dir)

  for native_platform in platforms:
    if native_platform == "android":
      # make full version
      root_dir = os.path.join(base_dir, "android", branding, "osign")
      if (base.is_dir(root_dir)):
        base.delete_dir(root_dir)
      base.create_dir(root_dir)
      libs_dir = os.path.join(root_dir, "lib")
      base.create_dir(os.path.join(libs_dir, "arm64-v8a"))
      base.copy_files(os.path.join(base_dir, "android_arm64_v8a", branding, "osign", "*.so"), os.path.join(libs_dir, "arm64-v8a"))
      base.create_dir(os.path.join(libs_dir, "armeabi-v7a"))
      base.copy_files(os.path.join(base_dir, "android_armv7", branding, "osign", "*.so"), os.path.join(libs_dir, "armeabi-v7a"))
      base.create_dir(os.path.join(libs_dir, "x86"))
      base.copy_files(os.path.join(base_dir, "android_x86", branding, "osign", "*.so"), os.path.join(libs_dir, "x86"))
      base.create_dir(os.path.join(libs_dir, "x86_64"))
      base.copy_files(os.path.join(base_dir, "android_x86_64", branding, "osign", "*.so"), os.path.join(libs_dir, "x86_64"))
      break

  return
