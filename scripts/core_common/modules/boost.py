#!/usr/bin/env python

import sys
sys.path.append('../..')
import config
import base
import os
import glob
import boost_qt
import shutil

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

def clean_boost_build_artifacts():
  """Clean build artifacts that might cause conflicts between builds"""
  paths_to_clean = [
    "bin.v2",
    "stage",
    "stage_win32",
    "stage_win64",
    os.path.join("boost", "bin.v2"),
    # Also clean project-config.jam which might have cached settings
    "project-config.jam"
  ]
  
  for path in paths_to_clean:
    if os.path.exists(path):
      print(f"Cleaning build artifact: {path}")
      try:
        if os.path.isdir(path):
          shutil.rmtree(path, ignore_errors=True)
        else:
          os.remove(path)
      except Exception as e:
        print(f"Warning: Could not remove {path}: {e}")
        
  # On Windows, clear cached b2 configurations that might contain conflicting settings
  if "windows" == base.host_platform():
    user_config = os.path.expanduser("~/user-config.jam")
    if os.path.exists(user_config):
      print(f"Removing user config: {user_config}")
      try:
        os.remove(user_config)
      except Exception as e:
        print(f"Warning: Could not remove {user_config}: {e}")
        
  # Verify the stage directory is completely gone
  if os.path.exists("stage"):
    print("WARNING: Stage directory still exists after cleanup!")
    try:
      # Try harder with os commands
      if "windows" == base.host_platform():
        os.system("rmdir /S /Q stage")
      else:
        os.system("rm -rf stage")
    except:
      pass

def make():
  print("[fetch & build]: boost")

  base_dir = os.path.join(base.get_script_dir(), "..", "..", "core", "Common", "3dParty", "boost")
  old_cur = os.getcwd()
  os.chdir(base_dir)

  base.common_check_version("boost", "5", clean)

  if not base.is_dir("boost_1_72_0"):
    base.cmd("git", ["clone", "--recursive", "--depth=1", "https://github.com/boostorg/boost.git", "boost_1_72_0", "-b", "boost-1.72.0"])

  os.chdir("boost_1_72_0")

  # build
  if ("windows" == base.host_platform()):
    # Check for GitHub Actions environment variable for VS version
    github_vs_version = os.environ.get('ONLYOFFICE_BUILDSYSTEM_VS_VERSION', '')
    running_on_github = "GITHUB_ACTIONS" in os.environ and os.environ.get("GITHUB_ACTIONS") == "true"
    
    win_toolset = "msvc-14.0"
    win_boot_arg = "vc14"
    win_vs_version = "vc140"
    
    if github_vs_version == "2019" or (config.option("vs-version") == "2019"):
      print("Using Visual Studio 2019 toolset for Boost")
      win_toolset = "msvc-14.2"
      win_boot_arg = "vc142"
      win_vs_version = "vc142"

    # List of libraries to build - only the ones we actually need
    needed_libraries = ["filesystem", "system", "date_time", "regex"]
    
    # 64-bit build
    win64_lib_name = f"libboost_system-{win_vs_version}-mt-x64-1_72.lib"
    win64_lib_path = os.path.join("..", "build", "win_64", "lib", win64_lib_name)
    
    if (-1 != config.option("platform").find("win_64")) and not base.is_file(win64_lib_path):
      try:
        # Clean build artifacts to prevent conflicts
        clean_boost_build_artifacts()
        
        print(f"Running bootstrap.bat with {win_boot_arg}")
        base.cmd("bootstrap.bat", [win_boot_arg])
        
        # Ensure build directory exists
        win64_build_dir = os.path.join("..", "build", "win_64")
        os.makedirs(win64_build_dir, exist_ok=True)
        
        print("Generating headers")
        base.cmd("b2.exe", ["headers"])
        
        print("Cleaning previous build")
        base.cmd("b2.exe", ["--clean"])
        
        # Build with architecture-specific directories and limited libraries
        print("Building 64-bit Boost libraries")
        # First create a completely distinct temporary directory for installation
        temp_install_dir = os.path.join(os.getcwd(), "temp_install_win64")
        os.makedirs(temp_install_dir, exist_ok=True)
        
        # Build args without "install" to avoid the stage/prefix conflict
        build_args = [
          f"--prefix={temp_install_dir}",  # Install to a temporary directory
          "link=static", 
          f"--toolset={win_toolset}", 
          "address-model=64",
          "architecture=x86",
          "--layout=versioned",
          "--with-filesystem", 
          "--with-system", 
          "--with-date_time", 
          "--with-regex",
          "--without-context",     # Exclude problematic libraries
          "--without-coroutine",
          "--without-python",
          "--without-chrono",      # Explicitly exclude chrono which is causing the conflict
          "--without-atomic",      # Atomic depends on chrono
          "--without-thread",      # Thread depends on chrono
        ]
        
        # Build and install to temp directory
        print("Building Boost libraries...")
        base.cmd("b2.exe", build_args + ["install"])
        
        # Copy from temp location to final location
        temp_lib_dir = os.path.join(temp_install_dir, "lib")
        temp_include_dir = os.path.join(temp_install_dir, "include")
        final_lib_dir = os.path.join(win64_build_dir, "lib")
        final_include_dir = os.path.join(win64_build_dir, "include")
        
        # Create final directories
        os.makedirs(final_lib_dir, exist_ok=True)
        os.makedirs(final_include_dir, exist_ok=True)
        
        # Copy files
        print(f"Copying libraries from {temp_lib_dir} to {final_lib_dir}")
        if os.path.exists(temp_lib_dir):
          for file in os.listdir(temp_lib_dir):
            src_file = os.path.join(temp_lib_dir, file)
            if os.path.isfile(src_file):
              base.copy_file(src_file, os.path.join(final_lib_dir, file))
              
        print(f"Copying includes from {temp_include_dir} to {final_include_dir}")
        if os.path.exists(temp_include_dir):
          base.copy_dir(temp_include_dir, final_include_dir)
              
        # Remove temp dir after copying
        print(f"Cleaning up temporary directory: {temp_install_dir}")
        try:
          shutil.rmtree(temp_install_dir, ignore_errors=True)
        except Exception as e:
          print(f"Warning: Could not remove temp directory: {e}")
        
        # Verify the libs are installed properly
        if os.path.exists(final_lib_dir):
          print(f"Verifying libraries were installed to: {final_lib_dir}")
          libs = os.listdir(final_lib_dir)
          print(f"Built libraries: {', '.join(libs)}")
        else:
          print(f"WARNING: Library directory {final_lib_dir} not found after build!")
      
      except Exception as e:
        print(f"ERROR during Boost win_64 build: {str(e)}")
        # Continue execution even if there's an error
    
    # 32-bit build (only if not on GitHub)
    win32_lib_name = f"libboost_system-{win_vs_version}-mt-x32-1_72.lib"
    win32_lib_path = os.path.join("..", "build", "win_32", "lib", win32_lib_name)
    
    if (not running_on_github) and (-1 != config.option("platform").find("win_32")) and not base.is_file(win32_lib_path):
      try:
        # First make sure the 64-bit build is finished
        if (-1 != config.option("platform").find("win_64")):
          print("Ensuring 64-bit build is complete before starting 32-bit build")
          
        # Clean build artifacts to prevent conflicts
        clean_boost_build_artifacts()
        
        print(f"Running bootstrap.bat with {win_boot_arg} for 32-bit build")
        base.cmd("bootstrap.bat", [win_boot_arg])
        
        # Ensure build directory exists
        win32_build_dir = os.path.join("..", "build", "win_32")
        os.makedirs(win32_build_dir, exist_ok=True)
        
        print("Generating headers")
        base.cmd("b2.exe", ["headers"])
        
        print("Cleaning previous build")
        base.cmd("b2.exe", ["--clean"])
        
        # Build with architecture-specific directories and limited libraries
        print("Building 32-bit Boost libraries")
        # First create a completely distinct temporary directory for installation
        temp_install_dir = os.path.join(os.getcwd(), "temp_install_win32")
        os.makedirs(temp_install_dir, exist_ok=True)
        
        # Build args without "install" to avoid the stage/prefix conflict
        build_args = [
          f"--prefix={temp_install_dir}",  # Install to a temporary directory
          "link=static", 
          f"--toolset={win_toolset}", 
          "address-model=32",
          "architecture=x86",
          "--layout=versioned",
          "--with-filesystem", 
          "--with-system", 
          "--with-date_time", 
          "--with-regex",
          "--without-context",     # Exclude problematic libraries
          "--without-coroutine",
          "--without-python",
          "--without-chrono",      # Explicitly exclude chrono which is causing the conflict
          "--without-atomic",      # Atomic depends on chrono
          "--without-thread",      # Thread depends on chrono
        ]
        
        # Build and install to temp directory
        print("Building Boost libraries...")
        base.cmd("b2.exe", build_args + ["install"])
        
        # Copy from temp location to final location
        temp_lib_dir = os.path.join(temp_install_dir, "lib")
        temp_include_dir = os.path.join(temp_install_dir, "include")
        final_lib_dir = os.path.join(win32_build_dir, "lib")
        final_include_dir = os.path.join(win32_build_dir, "include")
        
        # Create final directories
        os.makedirs(final_lib_dir, exist_ok=True)
        os.makedirs(final_include_dir, exist_ok=True)
        
        # Copy files
        print(f"Copying libraries from {temp_lib_dir} to {final_lib_dir}")
        if os.path.exists(temp_lib_dir):
          for file in os.listdir(temp_lib_dir):
            src_file = os.path.join(temp_lib_dir, file)
            if os.path.isfile(src_file):
              base.copy_file(src_file, os.path.join(final_lib_dir, file))
              
        print(f"Copying includes from {temp_include_dir} to {final_include_dir}")
        if os.path.exists(temp_include_dir):
          base.copy_dir(temp_include_dir, final_include_dir)
              
        # Remove temp dir after copying
        print(f"Cleaning up temporary directory: {temp_install_dir}")
        try:
          shutil.rmtree(temp_install_dir, ignore_errors=True)
        except Exception as e:
          print(f"Warning: Could not remove temp directory: {e}")
        
        # Verify the libs are installed properly
        if os.path.exists(final_lib_dir):
          print(f"Verifying libraries were installed to: {final_lib_dir}")
          libs = os.listdir(final_lib_dir)
          print(f"Built libraries: {', '.join(libs)}")
        else:
          print(f"WARNING: Library directory {final_lib_dir} not found after build!")
      
      except Exception as e:
        print(f"ERROR during Boost win_32 build: {str(e)}")
        # Continue execution even if there's an error
    
    # Correct include installation
    if -1 != config.option("platform").find("win_64"):
      correct_install_includes_win(base_dir, "win_64")
    if not running_on_github and -1 != config.option("platform").find("win_32"):
      correct_install_includes_win(base_dir, "win_32")    

  # Non-Windows platform builds remain unchanged
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

