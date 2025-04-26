#!/usr/bin/env python

import sys
sys.path.append('../..')
sys.path.append('android')
import config
import base
import os
import glob
import icu_android

def fetch_icu(major, minor):
  if (base.is_dir("./icu2")):
    base.delete_dir_with_access_error("icu2")  
  base.cmd("git", ["clone", "--depth", "1", "--branch", "maint/maint-" + major, "https://github.com/unicode-org/icu.git", "./icu2"])
  base.copy_dir("./icu2/icu4c", "./icu")
  base.delete_dir_with_access_error("icu2")
  #base.cmd("svn", ["export", "https://github.com/unicode-org/icu/tags/release-" + icu_major + "-" + icu_minor + "/icu4c", "./icu", "--non-interactive", "--trust-server-cert"])
  return

def clear_module():
  if base.is_dir("icu"):
    base.delete_dir_with_access_error("icu")

  # remove build
  for child in glob.glob("./*"):
    if base.is_dir(child):
      base.delete_dir(child)

  return

def make():
  print("[fetch & build]: icu")

  base_dir = os.path.join(base.get_script_dir(), "../../core/Common/3dParty/icu")
  old_cur = os.getcwd()
  os.chdir(base_dir)

  base.check_module_version("3", clear_module)

  if (-1 != config.option("platform").find("android")):
    icu_android.make()

  os.chdir(base_dir)

  icu_major = "58"
  icu_minor = "3"
  
  if not base.is_dir("icu"):
    fetch_icu(icu_major, icu_minor)  

  if ("windows" == base.host_platform()):
    platformToolset = "v140"
    if (config.option("vs-version") == "2019"):
      platformToolset = "v142"
    need_platforms = []
    if (-1 != config.option("platform").find("win_64")):
      need_platforms.append("win_64")
    if (-1 != config.option("platform").find("win_32")):
      need_platforms.append("win_32")
    for platform in need_platforms:
      if not config.check_option("platform", platform) and not config.check_option("platform", platform + "_xp"):
        continue
      platform_build_dir = os.path.join(platform, "build")
      if not base.is_dir(platform_build_dir):
        base.create_dir(platform)
        compile_bat = []
        compile_bat.append("setlocal")
        compile_bat.append("call \"" + config.option("vs-path") + "/vcvarsall.bat\" " + ("x86" if base.platform_is_32(platform) else "x64"))
        compile_bat.append("call MSBuild.exe icu/source/allinone/allinone.sln /p:Configuration=Release /p:PlatformToolset=" + platformToolset + " /p:Platform=" + ("Win32" if base.platform_is_32(platform) else "X64"))
        compile_bat.append("endlocal")
        base.run_as_bat(compile_bat)
        bin_dir = "icu/bin64/" if ("win_64" == platform) else "icu/bin/"
        lib_dir = "icu/lib64/" if ("win_64" == platform) else "icu/lib/"
        base.create_dir(platform_build_dir)
        base.copy_file(os.path.join(bin_dir, "icudt" + icu_major + ".dll"), os.path.join(platform_build_dir, "icudt" + icu_major + ".dll"))
        base.copy_file(os.path.join(bin_dir, "icuuc" + icu_major + ".dll"), os.path.join(platform_build_dir, "icuuc" + icu_major + ".dll"))
        base.copy_file(os.path.join(lib_dir, "icudt.lib"), os.path.join(platform_build_dir, "icudt.lib"))
        base.copy_file(os.path.join(lib_dir, "icuuc.lib"), os.path.join(platform_build_dir, "icuuc.lib"))
    os.chdir(old_cur)
    return

  if ("linux" == base.host_platform()):
    icu_source_digitlst = os.path.join("./icu/source/i18n/digitlst.cpp")
    icu_source_digitlst_bak = os.path.join("./icu/source/i18n/digitlst.cpp.bak")
    if not base.is_file(icu_source_digitlst_bak):
      base.copy_file(icu_source_digitlst, icu_source_digitlst_bak)
      base.replaceInFile(icu_source_digitlst, "xlocale", "locale")
      linux_64_dir = os.path.join(base_dir, "linux_64")
      if base.is_dir(linux_64_dir):
        base.delete_dir(linux_64_dir)
      linux_arm64_dir = os.path.join(base_dir, "linux_arm64")
      if base.is_dir(linux_arm64_dir):
        base.delete_dir(linux_arm64_dir)

    linux_64_dir = os.path.join(base_dir, "linux_64")
    if not base.is_dir(linux_64_dir):
      icu_cross_build_dir = os.path.join(base_dir, "icu/cross_build")
      base.create_dir(icu_cross_build_dir)
      os.chdir("icu/cross_build")
      icu_cross_build_install = os.path.join(base_dir, "icu/cross_build_install")
      base.cmd("./../source/runConfigureICU", ["Linux", "--prefix=" + icu_cross_build_install])
      base.replaceInFile("./../source/icudefs.mk.in", "LDFLAGS = @LDFLAGS@ $(RPATHLDFLAGS)", "LDFLAGS = @LDFLAGS@ $(RPATHLDFLAGS) -static-libstdc++ -static-libgcc")
      base.cmd("make", ["-j4"])
      base.cmd("make", ["install"], True)
      base.create_dir(linux_64_dir)
      linux_64_build_dir = os.path.join(linux_64_dir, "build")
      base.create_dir(linux_64_build_dir)
      libicudata_so = os.path.join(icu_cross_build_install, "lib", "libicudata.so." + icu_major + "." + icu_minor)
      libicudata_so_dest = os.path.join(linux_64_build_dir, "libicudata.so." + icu_major)
      base.copy_file(libicudata_so, libicudata_so_dest)
      libicuuc_so = os.path.join(icu_cross_build_install, "lib", "libicuuc.so." + icu_major + "." + icu_minor)
      libicuuc_so_dest = os.path.join(linux_64_build_dir, "libicuuc.so." + icu_major)
      base.copy_file(libicuuc_so, libicuuc_so_dest)
      base.copy_dir(os.path.join(icu_cross_build_install, "include"), os.path.join(linux_64_build_dir, "include"))
      
    linux_arm64_dir = os.path.join(base_dir, "linux_arm64")
    if config.check_option("platform", "linux_arm64") and not base.is_dir(linux_arm64_dir) and not base.is_os_arm():
      icu_linux_arm64_dir = os.path.join(base_dir, "icu/linux_arm64")
      base.create_dir(icu_linux_arm64_dir)
      os.chdir(icu_linux_arm64_dir)
      base_arm_tool_dir = base.get_prefix_cross_compiler_arm64()
      icu_linux_arm64_install = os.path.join(base_dir, "icu/linux_arm64_install")
      icu_cross_build = os.path.join(base_dir, "icu/cross_build")
      base.cmd("./../source/configure", ["--host=arm-linux", "--prefix=" + icu_linux_arm64_install, "--with-cross-build=" + icu_cross_build,
        "CC=" + base_arm_tool_dir + "gcc", "CXX=" + base_arm_tool_dir + "g++", "AR=" + base_arm_tool_dir + "ar", "RANLIB=" + base_arm_tool_dir + "ranlib"])
      base.cmd("make", ["-j4"])
      base.cmd("make", ["install"], True)
      base.create_dir(linux_arm64_dir)
      linux_arm64_build_dir = os.path.join(linux_arm64_dir, "build")
      base.create_dir(linux_arm64_build_dir)
      base.copy_file(os.path.join(icu_linux_arm64_install, "lib", "libicudata.so." + icu_major + "." + icu_minor), 
                    os.path.join(linux_arm64_build_dir, "libicudata.so." + icu_major))
      base.copy_file(os.path.join(icu_linux_arm64_install, "lib", "libicuuc.so." + icu_major + "." + icu_minor), 
                    os.path.join(linux_arm64_build_dir, "libicuuc.so." + icu_major))
      base.copy_dir(os.path.join(icu_linux_arm64_install, "include"), os.path.join(linux_arm64_build_dir, "include"))

      os.chdir("../..")

  if ("mac" == base.host_platform()):
    icu_pkgdata_path = os.path.join("./icu/source/tools/pkgdata/pkgdata.cpp")
    icu_pkgdata_bak = os.path.join("./icu/source/tools/pkgdata/pkgdata.cpp.bak")
    if not base.is_file(icu_pkgdata_bak):
      base.copy_file(icu_pkgdata_path, icu_pkgdata_bak)
      base.replaceInFile(icu_pkgdata_path, "cmd, \"%s %s -o %s%s %s %s%s %s %s\",", "cmd, \"%s %s -o %s%s %s %s %s %s %s\",")

    # mac
    mac_64_build_dir = os.path.join("mac_64", "build")
    if (-1 != config.option("platform").find("mac_")) and not base.is_dir(mac_64_build_dir):
      modules_dir = os.path.join(base_dir, "../../../../build_tools/scripts/core_common/modules")
      base.cmd_in_dir(modules_dir, "python", ["icu_mac.py"])

    # ios
    if (-1 != config.option("platform").find("ios")):
      if not base.is_dir("build"):
        base.bash("./icu_ios")
      
  os.chdir(old_cur)
  return
