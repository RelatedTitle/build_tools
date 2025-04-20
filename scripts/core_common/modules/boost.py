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

def write_boost_user_config(toolset="msvc-14.2"):
  """Create a user-config.jam file that explicitly configures the toolset"""
  user_config_content = f"""
# Boost user configuration for ONLYOFFICE builds
# Explicitly disable problematic libraries and configure toolset
using {toolset} ;
"""
  user_config_path = os.path.expanduser("~/user-config.jam")
  with open(user_config_path, "w") as f:
    f.write(user_config_content)
  print(f"Created Boost user config at {user_config_path} with toolset {toolset}")
  return user_config_path

def clean_boost_dirs():
  """Do a complete cleanup of Boost directories that might cause conflicts"""
  dirs_to_clean = [
    "bin.v2",
    "stage",
    os.path.join("..", "build")
  ]
  
  for dir_path in dirs_to_clean:
    if os.path.exists(dir_path):
      print(f"Removing potential conflict directory: {dir_path}")
      try:
        if os.path.isdir(dir_path):
          shutil.rmtree(dir_path, ignore_errors=True)
        else:
          os.remove(dir_path)
      except Exception as e:
        print(f"Warning: Could not fully remove {dir_path}: {e}")
        # Try using base delete functions as fallback
        try:
          base.delete_dir_with_access_error(dir_path)
          base.delete_dir(dir_path)
        except:
          pass
  
  # Also remove b2 config cache
  config_cache = os.path.join("tools", "build", "src", "engine", "config.log")
  if os.path.exists(config_cache):
    try:
      os.remove(config_cache)
      print(f"Removed build config cache: {config_cache}")
    except:
      pass
      
  # Additionally clean temporary files
  for temp_file in glob.glob("*.pdb") + glob.glob("*.idb") + glob.glob("*.obj") + glob.glob("*.exe"):
    try:
      os.remove(temp_file)
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
  if "windows" == base.host_platform():
    # Determine Visual Studio version from environment or config
    github_vs_version = os.environ.get('ONLYOFFICE_BUILDSYSTEM_VS_VERSION', '')
    running_on_github = "GITHUB_ACTIONS" in os.environ and os.environ.get("GITHUB_ACTIONS") == "true"
    
    # Default to VS 2015 (14.0)
    win_toolset = "msvc-14.0"
    win_boot_arg = "vc14"
    win_vs_version = "vc140"
    
    # Override for VS 2019 if specified
    if github_vs_version == "2019" or (config.option("vs-version") == "2019"):
      print("Using Visual Studio 2019 toolset for Boost")
      win_toolset = "msvc-14.2"
      win_boot_arg = "vc142" 
      win_vs_version = "vc142"

    # Define strictly which libraries we need - minimal set
    needed_libraries = ["filesystem", "system", "date_time", "regex"]
    
    # Set up platform-specific paths and settings
    if -1 != config.option("platform").find("win_64"):
      platform = "win_64"
      address_model = "64"
      
      # Main build target file to check if already built
      lib_name = f"libboost_system-{win_vs_version}-mt-x64-1_72.lib"
      lib_path = os.path.join("..", "build", platform, "lib", lib_name)
      
      # Only proceed if not already built
      if not base.is_file(lib_path):
        try:
          # Complete cleanup
          clean_boost_dirs()
          
          # Write user config with correct toolset
          write_boost_user_config(win_toolset)
          
          print(f"Building Boost for {platform} with {win_toolset}")
          print(f"Running bootstrap.bat with {win_boot_arg}")
          base.cmd("bootstrap.bat", [win_boot_arg])
          
          # Create build directory structure
          build_dir = os.path.join("..", "build", platform)
          os.makedirs(build_dir, exist_ok=True)
          
          # Create a dedicated path for this specific build to avoid any cross-contamination
          unique_build_dir = os.path.join(build_dir, "boost_build")
          stage_dir = os.path.join("stage", f"{platform}_only")
          
          os.makedirs(unique_build_dir, exist_ok=True)
          os.makedirs(stage_dir, exist_ok=True)
          
          # Build command with explicit paths for everything
          b2_args = [
            f"--prefix={unique_build_dir}",
            f"--stagedir={stage_dir}",
            f"--build-dir=bin.v2_{platform}",
            f"--toolset={win_toolset}",
            f"address-model={address_model}",
            "architecture=x86",
            "link=static",
            "threading=multi",
            "runtime-link=shared",
            "variant=release,debug",
            "--layout=versioned",
            "-j4",
          ]
          
          # Exclude all libraries we don't need
          exclude_libs = [
            "context", "coroutine", "python", "mpi", "wave", "graph", "test",
            "chrono", "atomic", "thread", "serialization", "iostreams", "log",
            "math", "contract", "exception", "fiber", "graph_parallel", "json",
            "locale", "random", "stacktrace", "timer", "type_erasure", "wave"
          ]
          
          for lib in exclude_libs:
            b2_args.append(f"--without-{lib}")
            
          # Include only libraries we need
          for lib in needed_libraries:
            b2_args.append(f"--with-{lib}")
          
          # Clean previous build
          print("Cleaning any previous build artifacts")
          base.cmd("b2.exe", ["--clean"])
          
          # First generate headers
          print("Generating Boost headers")
          base.cmd("b2.exe", ["headers"])
          
          # Build and install
          print(f"Building with arguments: {' '.join(b2_args)}")
          base.cmd("b2.exe", b2_args + ["install"])
          
          # Copy from unique build directory to expected location
          lib_src_dir = os.path.join(unique_build_dir, "lib")
          lib_dst_dir = os.path.join("..", "build", platform, "lib")
          include_src_dir = os.path.join(unique_build_dir, "include")
          include_dst_dir = os.path.join("..", "build", platform, "include")
          
          os.makedirs(lib_dst_dir, exist_ok=True)
          os.makedirs(include_dst_dir, exist_ok=True)
          
          # Copy files
          print(f"Copying libraries from {lib_src_dir} to {lib_dst_dir}")
          if os.path.exists(lib_src_dir):
            for file in os.listdir(lib_src_dir):
              base.copy_file(os.path.join(lib_src_dir, file), os.path.join(lib_dst_dir, file))
          
          print(f"Copying includes from {include_src_dir} to {include_dst_dir}")
          if os.path.exists(include_src_dir):
            base.copy_dir(include_src_dir, include_dst_dir)
            
          # Verify success
          print("Verifying build results")
          if os.path.exists(lib_dst_dir):
            libs = os.listdir(lib_dst_dir)
            print(f"Built libraries: {', '.join(libs)}")
          else:
            print(f"WARNING: Library directory {lib_dst_dir} not found after build!")
        
        except Exception as e:
          print(f"ERROR during Boost {platform} build: {str(e)}")
          # Continue execution even if there's an error
          
    # Only build Win32 if specifically requested and not on GitHub
    if not running_on_github and -1 != config.option("platform").find("win_32"):
      platform = "win_32"
      address_model = "32"
      
      # Main build target file to check if already built
      lib_name = f"libboost_system-{win_vs_version}-mt-x32-1_72.lib"
      lib_path = os.path.join("..", "build", platform, "lib", lib_name)
      
      # Only proceed if not already built
      if not base.is_file(lib_path):
        try:
          # Complete cleanup
          clean_boost_dirs()
          
          # Write user config with correct toolset
          write_boost_user_config(win_toolset)
          
          print(f"Building Boost for {platform} with {win_toolset}")
          print(f"Running bootstrap.bat with {win_boot_arg}")
          base.cmd("bootstrap.bat", [win_boot_arg])
          
          # Create build directory structure
          build_dir = os.path.join("..", "build", platform)
          os.makedirs(build_dir, exist_ok=True)
          
          # Create a dedicated path for this specific build to avoid any cross-contamination
          unique_build_dir = os.path.join(build_dir, "boost_build")
          stage_dir = os.path.join("stage", f"{platform}_only")
          
          os.makedirs(unique_build_dir, exist_ok=True)
          os.makedirs(stage_dir, exist_ok=True)
          
          # Build command with explicit paths for everything
          b2_args = [
            f"--prefix={unique_build_dir}",
            f"--stagedir={stage_dir}",
            f"--build-dir=bin.v2_{platform}",
            f"--toolset={win_toolset}",
            f"address-model={address_model}",
            "architecture=x86",
            "link=static",
            "threading=multi",
            "runtime-link=shared",
            "variant=release,debug",
            "--layout=versioned",
            "-j4",
          ]
          
          # Exclude all libraries we don't need
          exclude_libs = [
            "context", "coroutine", "python", "mpi", "wave", "graph", "test",
            "chrono", "atomic", "thread", "serialization", "iostreams", "log",
            "math", "contract", "exception", "fiber", "graph_parallel", "json",
            "locale", "random", "stacktrace", "timer", "type_erasure", "wave"
          ]
          
          for lib in exclude_libs:
            b2_args.append(f"--without-{lib}")
            
          # Include only libraries we need
          for lib in needed_libraries:
            b2_args.append(f"--with-{lib}")
          
          # Clean previous build
          print("Cleaning any previous build artifacts")
          base.cmd("b2.exe", ["--clean"])
          
          # First generate headers
          print("Generating Boost headers")
          base.cmd("b2.exe", ["headers"])
          
          # Build and install
          print(f"Building with arguments: {' '.join(b2_args)}")
          base.cmd("b2.exe", b2_args + ["install"])
          
          # Copy from unique build directory to expected location
          lib_src_dir = os.path.join(unique_build_dir, "lib")
          lib_dst_dir = os.path.join("..", "build", platform, "lib")
          include_src_dir = os.path.join(unique_build_dir, "include")
          include_dst_dir = os.path.join("..", "build", platform, "include")
          
          os.makedirs(lib_dst_dir, exist_ok=True)
          os.makedirs(include_dst_dir, exist_ok=True)
          
          # Copy files
          print(f"Copying libraries from {lib_src_dir} to {lib_dst_dir}")
          if os.path.exists(lib_src_dir):
            for file in os.listdir(lib_src_dir):
              base.copy_file(os.path.join(lib_src_dir, file), os.path.join(lib_dst_dir, file))
          
          print(f"Copying includes from {include_src_dir} to {include_dst_dir}")
          if os.path.exists(include_src_dir):
            base.copy_dir(include_src_dir, include_dst_dir)
            
          # Verify success
          print("Verifying build results")
          if os.path.exists(lib_dst_dir):
            libs = os.listdir(lib_dst_dir)
            print(f"Built libraries: {', '.join(libs)}")
          else:
            print(f"WARNING: Library directory {lib_dst_dir} not found after build!")
        
        except Exception as e:
          print(f"ERROR during Boost {platform} build: {str(e)}")
          # Continue execution even if there's an error
    
    # Correct includes structure
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

