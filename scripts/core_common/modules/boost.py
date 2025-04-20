#!/usr/bin/env python

import sys
sys.path.append('../..')
import config
import base
import os
import glob
import boost_qt

def move_debug_libs_windows(dir):
  debug_dir = os.path.join(dir, "debug")
  base.create_dir(debug_dir)
  for file in glob.glob(os.path.join(dir, "*")):
    file_name = os.path.basename(file)
    if not base.is_file(file):
      continue
    if (0 != file_name.find("libboost_")):
      continue
    base.copy_file(file, os.path.join(debug_dir, file_name))
    base.delete_file(file)
  return

def clean():
  if base.is_dir("boost_1_58_0"):
    base.delete_dir_with_access_error("boost_1_58_0")
    base.delete_dir("boost_1_58_0")
  if base.is_dir("boost_1_72_0"):
    base.delete_dir_with_access_error("boost_1_72_0")
    base.delete_dir("boost_1_72_0")
  if base.is_dir("build"):
    base.delete_dir("build")
  return

def correct_install_includes_win(base_dir, platform):
  build_dir = os.path.join(base_dir, "build", platform, "include")
  boost_1_72_dir = os.path.join(build_dir, "boost-1_72")
  boost_1_72_boost_dir = os.path.join(boost_1_72_dir, "boost")
  boost_dir = os.path.join(build_dir, "boost")
  if base.is_dir(boost_1_72_dir) and base.is_dir(boost_1_72_boost_dir):
    base.copy_dir(boost_1_72_boost_dir, boost_dir)
    base.delete_dir(boost_1_72_dir)
  return

def clang_correct():
  base.replaceInFile(os.path.join(".", "tools", "build", "src", "tools", "darwin.jam"), 
                    "flags darwin.compile.c++ OPTIONS $(condition) : -fcoalesce-templates ;", 
                    "#flags darwin.compile.c++ OPTIONS $(condition) : -fcoalesce-templates ;")
  base.replaceInFile(os.path.join(".", "tools", "build", "src", "tools", "darwin.py"), 
                    "toolset.flags ('darwin.compile.c++', 'OPTIONS', None, ['-fcoalesce-templates'])", 
                    "#toolset.flags ('darwin.compile.c++', 'OPTIONS', None, ['-fcoalesce-templates'])")
  return

def make():
  print("[fetch & build]: boost")

  base_dir = os.path.join(base.get_script_dir(), "..", "..", "core", "Common", "3dParty", "boost")
  old_cur = os.getcwd()
  os.chdir(base_dir)

  # download
  #url = "https://downloads.sourceforge.net/project/boost/boost/1.58.0/boost_1_58_0.7z"  
  #if not base.is_file("boost_1_58_0.7z"):
  #  base.download("https://downloads.sourceforge.net/project/boost/boost/1.58.0/boost_1_58_0.7z", "boost_1_58_0.7z")
  #if not base.is_dir("boost_1_58_0"):
  #  base.extract("boost_1_58_0.7z", "./")

  base.common_check_version("boost", "5", clean)

  if not base.is_dir("boost_1_72_0"):
    base.cmd("git", ["clone", "--recursive", "--depth=1", "https://github.com/boostorg/boost.git", "boost_1_72_0", "-b", "boost-1.72.0"])

  os.chdir("boost_1_72_0")

  # build
  if ("windows" == base.host_platform()):
    # Check for GitHub Actions environment variable for VS version
    github_vs_version = os.environ.get('ONLYOFFICE_BUILDSYSTEM_VS_VERSION', '')
    
    win_toolset = "msvc-14.0"
    win_boot_arg = "vc14"
    win_vs_version = "vc140"
    
    if github_vs_version == "2019" or (config.option("vs-version") == "2019"):
      print("Using Visual Studio 2019 toolset for Boost")
      win_toolset = "msvc-14.2"
      win_boot_arg = "vc142"
      win_vs_version = "vc142"

    # Detect if we're on GitHub Actions
    running_on_actions = "GITHUB_ACTIONS" in os.environ and os.environ.get("GITHUB_ACTIONS") == "true"
    
    # add "define=_ITERATOR_DEBUG_LEVEL=0" to b2 args before install for disable _ITERATOR_DEBUG_LEVEL
    win64_lib_name = f"libboost_system-{win_vs_version}-mt-x64-1_72.lib"
    win64_lib_path = os.path.join("..", "build", "win_64", "lib", win64_lib_name)
    
    # Only build Win64 libs on GitHub Actions or if platform contains win_64
    if (running_on_actions or (-1 != config.option("platform").find("win_64"))) and not base.is_file(win64_lib_path):
      print(f"Running bootstrap.bat with {win_boot_arg}")
      base.cmd("bootstrap.bat", [win_boot_arg])
      print(f"Running b2.exe with toolset={win_toolset}")
      
      # For GitHub Actions, add more explicit architecture flags to avoid conflicts
      if running_on_actions:
        print("Setting explicit architecture flags for GitHub Actions build")
        base.cmd("b2.exe", ["headers"])
        base.cmd("b2.exe", ["--clean"])
        base.cmd("b2.exe", ["--prefix=./../build/win_64", 
                            "link=static", 
                            "--with-filesystem", 
                            "--with-system", 
                            "--with-date_time", 
                            "--with-regex", 
                            f"--toolset={win_toolset}", 
                            "address-model=64", 
                            "architecture=x86", 
                            "-j4", 
                            "--disable-context",  # Disable context library that's causing asm issues
                            "--build-type=complete", 
                            "install"])
      else:
        base.cmd("b2.exe", ["headers"])
        base.cmd("b2.exe", ["--clean"])
        base.cmd("b2.exe", ["--prefix=./../build/win_64", 
                            "link=static", 
                            "--with-filesystem", 
                            "--with-system", 
                            "--with-date_time", 
                            "--with-regex", 
                            f"--toolset={win_toolset}", 
                            "address-model=64", 
                            "install"])
    
    # Only build Win32 libs if not on GitHub Actions and if platform contains win_32
    win32_lib_name = f"libboost_system-{win_vs_version}-mt-x32-1_72.lib"
    win32_lib_path = os.path.join("..", "build", "win_32", "lib", win32_lib_name)
    
    if (not running_on_actions) and (-1 != config.option("platform").find("win_32")) and not base.is_file(win32_lib_path):
      print(f"Running bootstrap.bat with {win_boot_arg}")
      base.cmd("bootstrap.bat", [win_boot_arg])
      print(f"Running b2.exe with toolset={win_toolset}")
      base.cmd("b2.exe", ["headers"])
      base.cmd("b2.exe", ["--clean"])
      base.cmd("b2.exe", ["--prefix=./../build/win_32", "link=static", "--with-filesystem", "--with-system", "--with-date_time", "--with-regex", f"--toolset={win_toolset}", "address-model=32", "install"])
    
    correct_install_includes_win(base_dir, "win_64")
    if not running_on_actions:
      correct_install_includes_win(base_dir, "win_32")

  linux_64_build_dir = os.path.join("..", "build", "linux_64")
  if config.check_option("platform", "linux_64") and not base.is_dir(linux_64_build_dir):
    base.cmd("./bootstrap.sh", ["--with-libraries=filesystem,system,date_time,regex"])
    base.cmd("./b2", ["headers"])
    base.cmd("./b2", ["--clean"])
    base.cmd("./b2", ["--prefix=./../build/linux_64", "link=static", "cxxflags=-fPIC", "install"])    
    # TODO: support x86

  linux_arm64_build_dir = os.path.join("..", "build", "linux_arm64")
  if config.check_option("platform", "linux_arm64") and not base.is_dir(linux_arm64_build_dir):
    boost_qt.make(os.getcwd(), ["filesystem", "system", "date_time", "regex"], "linux_arm64")
    directory_build = os.path.join(base_dir, "build", "linux_arm64", "lib")
    base.delete_file(os.path.join(directory_build, "libboost_system.a"))
    base.delete_file(os.path.join(directory_build, "libboost_system.so"))
    base.copy_files(os.path.join(directory_build, "linux_arm64", "*.a"), directory_build)

  ios_build_dir = os.path.join("..", "build", "ios")
  if (-1 != config.option("platform").find("ios")) and not base.is_dir(ios_build_dir):
    old_cur2 = os.getcwd()
    clang_correct()
    os.chdir("../")
    base.bash("./boost_ios")
    os.chdir(old_cur2)

  ios_xcframework_dir = os.path.join("..", "build", "ios_xcframework")
  if (-1 != config.option("platform").find("ios")) and not base.is_dir(ios_xcframework_dir):
    boost_qt.make(os.getcwd(), ["filesystem", "system", "date_time", "regex"], "ios_xcframework/ios_simulator", "xcframework_platform_ios_simulator")
    boost_qt.make(os.getcwd(), ["filesystem", "system", "date_time", "regex"], "ios_xcframework/ios")

  android_build_dir = os.path.join("..", "build", "android")
  if (-1 != config.option("platform").find("android")) and not base.is_dir(android_build_dir):
    boost_qt.make(os.getcwd(), ["filesystem", "system", "date_time", "regex"])

  mac_64_build_dir = os.path.join("..", "build", "mac_64")
  if (-1 != config.option("platform").find("mac")) and not base.is_dir(mac_64_build_dir):
    boost_qt.make(os.getcwd(), ["filesystem", "system", "date_time", "regex"], "mac_64")
    directory_build = os.path.join(base_dir, "build", "mac_64", "lib")
    base.delete_file(os.path.join(directory_build, "libboost_system.a"))
    base.delete_file(os.path.join(directory_build, "libboost_system.dylib"))
    base.copy_files(os.path.join(directory_build, "mac_64", "*.a"), directory_build)

  mac_arm64_build_dir = os.path.join("..", "build", "mac_arm64")
  if (-1 != config.option("platform").find("mac_arm64")) and not base.is_dir(mac_arm64_build_dir):
    boost_qt.make(os.getcwd(), ["filesystem", "system", "date_time", "regex"], "mac_arm64")
    directory_build = os.path.join(base_dir, "build", "mac_arm64", "lib")
    base.delete_file(os.path.join(directory_build, "libboost_system.a"))
    base.delete_file(os.path.join(directory_build, "libboost_system.dylib"))
    base.copy_files(os.path.join(directory_build, "mac_arm64", "*.a"), directory_build)

  os.chdir(old_cur)
  return

