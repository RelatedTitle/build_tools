#!/usr/bin/env python

import base
import os
import multiprocessing
import sys
import config_common

platforms = []
platforms_native = []
platforms_virtualbox_sdk = []
params = [
  {
    "name":"win_64",
    "os":"windows",
    "arch":"x86_64",
    "prefix":"amd64",
    "platform":"win64"
  },
  {
    "name":"win_32",
    "os":"windows",
    "arch":"x86",
    "prefix":"Win32",
    "platform":"win32"
  },
  {
    "name":"win_64_xp",
    "os":"windows",
    "arch":"x86_64",
    "prefix":"amd64",
    "platform":"win64_xp"
  },
  {
    "name":"win_32_xp",
    "os":"windows",
    "arch":"x86",
    "prefix":"Win32",
    "platform":"win32_xp"
  },
  {
    "name":"linux_64",
    "os":"linux",
    "arch":"x86_64",
    "prefix":"linux_64",
    "platform":"linux64"
  },
  {
    "name":"linux_32",
    "os":"linux",
    "arch":"x86",
    "prefix":"linux_32",
    "platform":"linux32"
  },
  {
    "name":"linux_arm64",
    "os":"linux",
    "arch":"aarch64",
    "prefix":"linux_arm64",
    "platform":"linux_arm64"
  },
  {
    "name":"mac_64",
    "os":"darwin",
    "arch":"x86_64",
    "prefix":"mac_64",
    "platform":"mac64"
  },
  {
    "name":"mac_arm64",
    "os":"darwin",
    "arch":"arm64",
    "prefix":"mac_arm64",
    "platform":"mac_arm64"
  },
  {
    "name":"ios",
    "os":"ios",
    "arch":"arm64",
    "prefix":"ios",
    "platform":"ios"
  },
  {
    "name":"android_arm64_v8a",
    "os":"android",
    "arch":"arm64-v8a",
    "prefix":"android_arm64",
    "platform":"android_arm64_v8a"
  },
  {
    "name":"android_armv7",
    "os":"android",
    "arch":"armv7",
    "prefix":"android_arm",
    "platform":"android_armv7"
  },
  {
    "name":"android_x86",
    "os":"android",
    "arch":"x86",
    "prefix":"android_x86",
    "platform":"android_x86"
  },
  {
    "name":"android_x86_64",
    "os":"android",
    "arch":"x86_64",
    "prefix":"android_x64",
    "platform":"android_x86_64"
  }
]

config = {}
config_platform = {}

# parse configuration
def parse():
  global platforms
  global platforms_native
  global config
  global config_platform
  global params

  path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config")
  if not base.is_file(path):
    return
  
  config, config_platform = config_common.parse_config(path)

  for item in config_platform:
    if not item in platforms:
      platforms.append(item)

  # add native platforms
  host = base.host_platform()
  
  # Add native platforms
  if host == "windows":
    if not "win_64" in platforms:
      platforms.append("win_64")
    if not "win_32" in platforms:
      platforms.append("win_32")
    platforms_native = ["win_32", "win_64"]
  elif host == "darwin":
    if not "mac_64" in platforms:
      platforms.append("mac_64")
    if not "mac_arm64" in platforms:
      platforms.append("mac_arm64")
    platforms_native = ["mac_64", "mac_arm64"]
  elif host == "linux":
    if not "linux_64" in platforms:
      platforms.append("linux_64")
    if not "linux_32" in platforms:
      platforms.append("linux_32")
    platforms_native = ["linux_32", "linux_64"]
    
  if (host == "windows"):
    if not "win_64_xp" in platforms:
      platforms.append("win_64_xp")
    if not "win_32_xp" in platforms:
      platforms.append("win_32_xp")
  
  # correction
  if "all" in platforms:
    if "android" in platforms:
      platforms.remove("android")
  if ("androidarm" in platforms) or ("_arm" in config.get("platform", "")):
    if not "android_arm64_v8a" in platforms:
      platforms.append("android_arm64_v8a")
    if not "android_armv7" in platforms:
      platforms.append("android_armv7")
    if not "android_x86" in platforms:
      platforms.append("android_x86")
    if not "android_x86_64" in platforms:
      platforms.append("android_x86_64")
    if "androidarm" in platforms:
      platforms.remove("androidarm")
  if "android" in platforms:
    if not "android_arm64_v8a" in platforms:
      platforms.append("android_arm64_v8a")
    if not "android_armv7" in platforms:
      platforms.append("android_armv7")
    if not "android_x86" in platforms:
      platforms.append("android_x86")
    if not "android_x86_64" in platforms:
      platforms.append("android_x86_64")
    platforms.remove("android")
  
  if "all" in platforms:
    if "windows" in platforms:
      platforms.remove("windows")
  if "windows" in platforms:
    if not "win_64" in platforms:
      platforms.append("win_64")
    if not "win_32" in platforms:
      platforms.append("win_32")
    platforms.remove("windows")
  
  if "all" in platforms:
    if "linux" in platforms:
      platforms.remove("linux")
  if "linux" in platforms:
    if not "linux_64" in platforms:
      platforms.append("linux_64")
    if not "linux_32" in platforms:
      platforms.append("linux_32")
    platforms.remove("linux")

  if "all" in platforms:
    if "darwin" in platforms:
      platforms.remove("darwin")
    if "mac" in platforms:
      platforms.remove("mac")
  if ("mac" in platforms) or ("darwin" in platforms):
    if not "mac_64" in platforms:
      platforms.append("mac_64")
    if not "mac_arm64" in platforms:
      platforms.append("mac_arm64")
    if "mac" in platforms:
      platforms.remove("mac")
    if "darwin" in platforms:
      platforms.remove("darwin")

  # platform
  if check_option("platform", "all"):
    platforms = []
    for item in params:
      platforms.append(item["name"])

  if check_option("platform", "native"):
    platforms = platforms_native
  
  if check_option("platform", "ios"):
    platforms = ["ios"]
    
  if check_option("platform", "native-win"):
    platforms = ["win_64", "win_32", "win_64_xp", "win_32_xp"]

  if check_option("platform", "native-linux"):
    platforms = ["linux_64", "linux_32"]

  if check_option("platform", "native-mac"):
    platforms = ["mac_64", "mac_arm64"]
  
  if check_option("platform", "freebsd"):
    platforms = ["freebsd"]

  # correction
  if "platform" in config:
    if "linux_arm64" in config["platform"]:
      if not "linux_arm64" in platforms:
        platforms.append("linux_arm64")

  return

def check_compiler(platform):
  compiler = {}
  compiler["compiler"] = option("compiler")
  compiler["compiler_64"] = compiler["compiler"] + "_64"

  if (compiler["compiler"] != ""):
    if ("linux" == base.host_platform()) and (platform.startswith("linux")):
      compiler_version = "-" + compiler["compiler"]
      if platform.endswith("64") and not platform.startswith("linux_arm"):
        compiler_version = "-" + compiler["compiler_64"]
      if ("gcc" == compiler["compiler"]) and not base.is_dir("/usr/lib" + compiler_version):
        print("compiler not found (" + compiler_version + ")")
        exit(0)
    if ("mac" == base.host_platform()) and (platform.startswith("mac")):
      compiler_dir = "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain"
      if base.is_dir(compiler_dir):
        print("compiler find: " + compiler_dir)
      else:
        print("compiler not found (" + compiler_dir + ")")
        exit(0)
    if ("windows" == base.host_platform()) and (platform.startswith("win")):
      compiler_dir = base.get_env("ProgramFiles") + "\\Microsoft Visual Studio 14.0";
      if base.is_dir(compiler_dir):
        print("compiler find: " + compiler_dir)
      else:
        print("compiler not found (" + compiler_dir + ")")
        exit(0)
  return

def check_option(name, value):
  if not name in config:
    return False
  if config[name] == value:
    return True
  return False

def option(name):
  if name in config:
    return config[name]
  return ""

def extend_option(name, value):
  if name in config:
    config[name] = config[name] + " " + value
  else:
    config[name] = value

def set_option(name, value):
  config[name] = value

def branding():
  branding = option("branding-name")
  if ("" == branding):
    branding = "onlyoffice"
  return branding

def is_mobile_platform():
  all_platforms = [
    "android_arm64_v8a", 
    "android_armv7",
    "android_x86",
    "android_x86_64",
    "ios"
  ]
  for _platform in all_platforms:
    if (_platform in platforms):
      return True
  return False

def parse_defaults():
  if is_mobile_platform():
    config["module"] = "mobile"
    return

  # core
  modules = []

  # add core module
  if ("core" in config):
    modules.append("core")
  
  if ("modulestrunks" in config):
    modules.extend(config["modulestrunks"].split(" "))
  if ("modules" in config):
    modules.extend(config["modules"].split(" "))
    
  if ("server" in modules):
    modules.append("server")
  
  if ("server" in modules):
    if ("desktop" in modules):
      if not "builder" in modules:
        modules.append("builder")

  if not "core" in modules:
    modules.append("core")
  config["modules"] = " ".join(modules)
  
  if "desktop" in modules or "builder" in modules or "server" in modules:
    if "" == config.get("qt_dir", ""):
      for _platform in platforms:
        if (_platform.startswith("linux")):
          config["qt_dir"] = "/usr/local/Qt5.15.3/5.15.3/gcc_64"
          break
        if (_platform.startswith("win")):
          config["qt_dir"] = "C:/Qt/5.15.3/msvc2019_64"
          break
  
  if "desktop" in modules:
    if ("1" == config.get("clean", "1")):
      if " " != config.get("config",""):
        config["config"] = config["config"] + " "
      config["config"] = config["config"] + "clean"

  if "desktop" in modules:
    if not base.is_windows():
      if not "platform" in config:
        config["platform"] = "native"
        
  # check vs-version
  if ("2019" == config.get("vs-version", "")):
    config["vs-path"] = "C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\Community\\VC\\Auxiliary\\Build"
  elif ("2022" == config.get("vs-version", "")):
    config["vs-path"] = "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Auxiliary\\Build"
  if ("" == config.get("vs-path", "")):
    config["vs-path"] = "C:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC"
  
  # check sdkjs-plugins
  if not "sdkjs-plugin" in config and "sdkjs-plugin-server" in config:
    config["sdkjs-plugin"] = config["sdkjs-plugin-server"]
    
  # check qmake addon
  if not "multiprocess" in config:
    config["multiprocess"] = "0"
  
  return

def is_cef_107():
  return (not check_option("config", "no_107_cef"))
  
def is_v8_60():
  return check_option("config", "v8_60")
