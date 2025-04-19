#!/usr/bin/env python

import config
import base
import os

def exclude_arch(directory, frameworks):
  for lib in frameworks:
    base.cmd("lipo", ["-remove", "arm64", os.path.join(directory, lib + ".framework", lib), "-o", os.path.join(directory, lib + ".framework", lib)])
  return

def deploy_fonts(git_dir, root_dir, platform=""):
  base.create_dir(os.path.join(root_dir, "fonts"))
  base.copy_file(os.path.join(git_dir, "core-fonts", "ASC.ttf"), os.path.join(root_dir, "fonts", "ASC.ttf"))
  base.copy_dir(os.path.join(git_dir, "core-fonts", "asana"), os.path.join(root_dir, "fonts", "asana"))
  base.copy_dir(os.path.join(git_dir, "core-fonts", "caladea"), os.path.join(root_dir, "fonts", "caladea"))
  base.copy_dir(os.path.join(git_dir, "core-fonts", "crosextra"), os.path.join(root_dir, "fonts", "crosextra"))
  base.copy_dir(os.path.join(git_dir, "core-fonts", "openoffice"), os.path.join(root_dir, "fonts", "openoffice"))
  if (platform == "android"):
    base.copy_dir(os.path.join(git_dir, "core-fonts", "dejavu"), os.path.join(root_dir, "fonts", "dejavu"))
    base.copy_dir(os.path.join(git_dir, "core-fonts", "liberation"), os.path.join(root_dir, "fonts", "liberation"))
  return 

def make():
  base_dir = os.path.join(base.get_script_dir(), "..", "out")
  git_dir = os.path.join(base.get_script_dir(), "..", "..")
  core_dir = os.path.join(git_dir, "core")
  branding = config.branding()

  platforms = config.option("platform").split()
  for native_platform in platforms:
    if not native_platform in config.platforms:
      continue

    root_dir = os.path.join(base_dir, native_platform, branding, "mobile")

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
    base.copy_lib(os.path.join(core_build_dir, "lib", platform_postfix), root_dir, "kernel")
    base.copy_lib(os.path.join(core_build_dir, "lib", platform_postfix), root_dir, "kernel_network")
    base.copy_lib(os.path.join(core_build_dir, "lib", platform_postfix), root_dir, "UnicodeConverter")
    base.copy_lib(os.path.join(core_build_dir, "lib", platform_postfix), root_dir, "graphics")
    base.copy_lib(os.path.join(core_build_dir, "lib", platform_postfix), root_dir, "PdfFile")
    base.copy_lib(os.path.join(core_build_dir, "lib", platform_postfix), root_dir, "DjVuFile")
    base.copy_lib(os.path.join(core_build_dir, "lib", platform_postfix), root_dir, "XpsFile")
    base.copy_lib(os.path.join(core_build_dir, "lib", platform_postfix), root_dir, "HtmlFile2")
    base.copy_lib(os.path.join(core_build_dir, "lib", platform_postfix), root_dir, "doctrenderer")
    base.copy_lib(os.path.join(core_build_dir, "lib", platform_postfix), root_dir, "Fb2File")
    base.copy_lib(os.path.join(core_build_dir, "lib", platform_postfix), root_dir, "EpubFile")
    base.copy_lib(os.path.join(core_build_dir, "lib", platform_postfix), root_dir, "IWorkFile")
    base.copy_lib(os.path.join(core_build_dir, "lib", platform_postfix), root_dir, "HWPFile")
    base.copy_lib(os.path.join(core_build_dir, "lib", platform_postfix), root_dir, "DocxRenderer")
    base.copy_file(os.path.join(git_dir, "sdkjs", "pdf", "src", "engine", "cmap.bin"), os.path.join(root_dir, "cmap.bin"))

    if (0 == platform.find("win") or 0 == platform.find("linux") or 0 == platform.find("mac")):
      base.copy_exe(os.path.join(core_build_dir, "bin", platform_postfix), root_dir, "x2t")
    else:
      base.copy_lib(os.path.join(core_build_dir, "lib", platform_postfix), root_dir, "x2t")

    # icu
    if (0 == platform.find("win")):
      base.copy_file(os.path.join(core_dir, "Common", "3dParty", "icu", platform, "build", "icudt58.dll"), os.path.join(root_dir, "icudt58.dll"))
      base.copy_file(os.path.join(core_dir, "Common", "3dParty", "icu", platform, "build", "icuuc58.dll"), os.path.join(root_dir, "icuuc58.dll"))

    if (0 == platform.find("linux")):
      base.copy_file(os.path.join(core_dir, "Common", "3dParty", "icu", platform, "build", "libicudata.so.58"), os.path.join(root_dir, "libicudata.so.58"))
      base.copy_file(os.path.join(core_dir, "Common", "3dParty", "icu", platform, "build", "libicuuc.so.58"), os.path.join(root_dir, "libicuuc.so.58"))

    if (0 == platform.find("mac")):
      base.copy_file(os.path.join(core_dir, "Common", "3dParty", "icu", platform, "build", "libicudata.58.dylib"), os.path.join(root_dir, "libicudata.58.dylib"))
      base.copy_file(os.path.join(core_dir, "Common", "3dParty", "icu", platform, "build", "libicuuc.58.dylib"), os.path.join(root_dir, "libicuuc.58.dylib"))
    
    if (0 == platform.find("android")):
      #base.copy_file(core_dir + "/Common/3dParty/icu/android/build/" + platform[8:] + "/libicudata.so", root_dir + "/libicudata.so")
      #base.copy_file(core_dir + "/Common/3dParty/icu/android/build/" + platform[8:] + "/libicuuc.so", root_dir + "/libicuuc.so")
      base.copy_file(os.path.join(core_dir, "Common", "3dParty", "icu", "android", "build", platform[8:], "icudt58l.dat"), os.path.join(root_dir, "icudt58l.dat"))

    # js
    base.copy_dir(os.path.join(base_dir, "js", branding, "mobile", "sdkjs"), os.path.join(root_dir, "sdkjs"))

    # correct ios frameworks
    if ("ios" == platform):
      base.generate_plist(root_dir)
      deploy_fonts(git_dir, root_dir)
      base.copy_dictionaries(os.path.join(git_dir, "dictionaries"), os.path.join(root_dir, "dictionaries"), True, False)

    if (0 == platform.find("mac")):
      base.mac_correct_rpath_x2t(root_dir)

  for native_platform in platforms:
    if native_platform == "android":
      # make full version
      root_dir = os.path.join(base_dir, "android", branding, "mobile")
      if (base.is_dir(root_dir)):
        base.delete_dir(root_dir)
      base.create_dir(root_dir)
      # js
      base.copy_dir(os.path.join(base_dir, "js", branding, "mobile", "sdkjs"), os.path.join(root_dir, "sdkjs"))
      # fonts
      deploy_fonts(git_dir, root_dir, "android")
      base.copy_dictionaries(os.path.join(git_dir, "dictionaries"), os.path.join(root_dir, "dictionaries"), True, False)
      # app
      base.generate_doctrenderer_config(os.path.join(root_dir, "DoctRenderer.config"), "./", "builder", "", "./dictionaries")      
      libs_dir = os.path.join(root_dir, "lib")
      base.create_dir(os.path.join(libs_dir, "arm64-v8a"))
      base.copy_files(os.path.join(base_dir, "android_arm64_v8a", branding, "mobile", "*.so"), os.path.join(libs_dir, "arm64-v8a"))
      base.copy_files(os.path.join(base_dir, "android_arm64_v8a", branding, "mobile", "*.so.*"), os.path.join(libs_dir, "arm64-v8a"))
      base.copy_files(os.path.join(base_dir, "android_arm64_v8a", branding, "mobile", "*.dat"), os.path.join(libs_dir, "arm64-v8a"))
      base.create_dir(os.path.join(libs_dir, "armeabi-v7a"))
      base.copy_files(os.path.join(base_dir, "android_armv7", branding, "mobile", "*.so"), os.path.join(libs_dir, "armeabi-v7a"))
      base.copy_files(os.path.join(base_dir, "android_armv7", branding, "mobile", "*.so.*"), os.path.join(libs_dir, "armeabi-v7a"))
      base.copy_files(os.path.join(base_dir, "android_armv7", branding, "mobile", "*.dat"), os.path.join(libs_dir, "armeabi-v7a"))
      base.create_dir(os.path.join(libs_dir, "x86"))
      base.copy_files(os.path.join(base_dir, "android_x86", branding, "mobile", "*.so"), os.path.join(libs_dir, "x86"))
      base.copy_files(os.path.join(base_dir, "android_x86", branding, "mobile", "*.so.*"), os.path.join(libs_dir, "x86"))
      base.copy_files(os.path.join(base_dir, "android_x86", branding, "mobile", "*.dat"), os.path.join(libs_dir, "x86"))
      base.create_dir(os.path.join(libs_dir, "x86_64"))
      base.copy_files(os.path.join(base_dir, "android_x86_64", branding, "mobile", "*.so"), os.path.join(libs_dir, "x86_64"))
      base.copy_files(os.path.join(base_dir, "android_x86_64", branding, "mobile", "*.so.*"), os.path.join(libs_dir, "x86_64"))
      base.copy_files(os.path.join(base_dir, "android_x86_64", branding, "mobile", "*.dat"), os.path.join(libs_dir, "x86_64"))
      break

  return
