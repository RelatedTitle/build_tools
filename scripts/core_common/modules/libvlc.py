#!/usr/bin/env python

import sys
sys.path.append('../..')
import config
import base
import os

def docker_build(image_name, dockerfile_dir, base_dir):
  base.cmd("docker", ["build", "-t", image_name, dockerfile_dir])
  vlc_dir = os.path.join(base_dir, "vlc")
  base.cmd("docker", ["run", "--rm", "-v", vlc_dir + ":/vlc", image_name])
  base.cmd("docker", ["image", "rm", image_name])
  return

def form_build_win(src_dir, dest_dir):
  if not base.is_dir(dest_dir):
    base.create_dir(dest_dir)
  # copy include dir
  base.copy_dir(os.path.join(src_dir, "sdk", "include"), os.path.join(dest_dir, "include"))
  # form lib dir
  base.create_dir(os.path.join(dest_dir, "lib"))
  base.copy_file(os.path.join(src_dir, "sdk", "lib", "libvlc.lib"), os.path.join(dest_dir, "lib", "vlc.lib"))
  base.copy_file(os.path.join(src_dir, "sdk", "lib", "libvlccore.lib"), os.path.join(dest_dir, "lib", "vlccore.lib"))
  base.copy_dir(os.path.join(src_dir, "plugins"), os.path.join(dest_dir, "lib", "plugins"))
  base.copy_file(os.path.join(src_dir, "libvlc.dll"), os.path.join(dest_dir, "lib", "libvlc.dll"))
  base.copy_file(os.path.join(src_dir, "libvlccore.dll"), os.path.join(dest_dir, "lib", "libvlccore.dll"))
  base.copy_file(os.path.join(src_dir, "vlc-cache-gen.exe"), os.path.join(dest_dir, "lib", "vlc-cache-gen.exe"))
  # generate cache file 'plugins.dat' for plugins loading
  base.cmd_exe(os.path.join(dest_dir, "lib", "vlc-cache-gen"), [os.path.join(dest_dir, "lib", "plugins")])
  return

def form_build_linux(src_dir, dest_dir):
  if not base.is_dir(dest_dir):
    base.create_dir(dest_dir)
  # copy include dir
  base.copy_dir(os.path.join(src_dir, "include"), os.path.join(dest_dir, "include"))
  # copy and form lib dir
  base.copy_dir(os.path.join(src_dir, "lib"), os.path.join(dest_dir, "lib"))
  base.delete_dir(os.path.join(dest_dir, "lib", "pkgconfig"))
  base.delete_file(os.path.join(dest_dir, "lib", "vlc", "libcompat.a"))
  return

def form_build_mac(src_dir, dest_dir):
  if not base.is_dir(dest_dir):
    base.create_dir(dest_dir)
  # copy include dir
  base.copy_dir(os.path.join(src_dir, "include"), os.path.join(dest_dir, "include"))
  # copy and form lib dir
  base.copy_dir(os.path.join(src_dir, "lib"), os.path.join(dest_dir, "lib"))
  base.cmd("find", [os.path.join(dest_dir, "lib"), "-name", "\"*.la\"", "-type", "f", "-delete"])
  base.delete_dir(os.path.join(dest_dir, "lib", "pkgconfig"))
  base.delete_file(os.path.join(dest_dir, "lib", "vlc", "libcompat.a"))
  # generate cache file 'plugins.dat' for plugins loading
  plugins_dir = os.path.join(dest_dir, "lib", "vlc", "plugins")
  vlc_cache_gen = os.path.join(dest_dir, "lib", "vlc", "vlc-cache-gen")
  lib_path = os.path.join(dest_dir, "lib")
  base.run_command("DYLD_LIBRARY_PATH=" + lib_path + " " + vlc_cache_gen + " " + plugins_dir)
  return

def make():
  print("[fetch & build]: libvlc")

  base_dir = os.path.join(base.get_script_dir(), "..", "..", "core", "Common", "3dParty", "libvlc")
  vlc_dir = os.path.join(base_dir, "vlc")
  vlc_version = "3.0.18"

  tools_dir = os.path.join(base.get_script_dir(), "..", "tools")
  old_cur = os.getcwd()
  os.chdir(base_dir)

  if not base.is_dir(vlc_dir):
    # temporary disable auto CRLF for Windows
    if "windows" == base.host_platform():
      autocrlf_old = base.run_command("git config --global core.autocrlf")['stdout']
      base.cmd("git", ["config", "--global", "core.autocrlf", "false"])
    base.cmd("git", ["clone", "https://code.videolan.org/videolan/vlc.git", "--branch", vlc_version])
    if "windows" == base.host_platform():
      base.cmd("git", ["config", "--global", "core.autocrlf", autocrlf_old])

  base.create_dir("build")
  base.copy_file(os.path.join("tools", "ignore-cache-time.patch"), "vlc")

  # windows
  if "windows" == base.host_platform():
    if config.check_option("platform", "win_64"):
      base.copy_file(os.path.join("tools", "win_64", "build.patch"), "vlc")
      docker_build("libvlc-win64", os.path.join(base_dir, "tools", "win_64"), base_dir)
      win64_build_path = os.path.join(vlc_dir, "build", "win64", "vlc-" + vlc_version)
      win64_dest_path = os.path.join(base_dir, "build", "win_64")
      form_build_win(win64_build_path, win64_dest_path)

    if config.check_option("platform", "win_32"):
      base.copy_file(os.path.join("tools", "win_32", "build.patch"), "vlc")
      docker_build("libvlc-win32", os.path.join(base_dir, "tools", "win_32"), base_dir)
      win32_build_path = os.path.join(vlc_dir, "build", "win32", "vlc-" + vlc_version)
      win32_dest_path = os.path.join(base_dir, "build", "win_32")
      form_build_win(win32_build_path, win32_dest_path)

  # linux
  if config.check_option("platform", "linux_64"):
    base.copy_file(os.path.join(tools_dir, "linux", "elf", "patchelf"), "vlc")
    base.copy_file(os.path.join("tools", "linux_64", "change-rpaths.sh"), "vlc")
    docker_build("libvlc-linux64", os.path.join(base_dir, "tools", "linux_64"), base_dir)
    linux64_build_path = os.path.join(vlc_dir, "build", "linux_64")
    linux64_dest_path = os.path.join(base_dir, "build", "linux_64")
    form_build_linux(linux64_build_path, linux64_dest_path)

  # mac
  if "mac" == base.host_platform():
    os.chdir(vlc_dir)

    base.cmd("git", ["restore", "src/modules/bank.c"])
    base.cmd("patch", ["-p1", "src/modules/bank.c", os.path.join("..", "tools", "ignore-cache-time.patch")])

    if config.check_option("platform", "mac_64"):
      base.cmd("git", ["restore", "extras/package/macosx/build.sh"])
      base.cmd("patch", ["-p1", "extras/package/macosx/build.sh", os.path.join("..", "tools", "mac_64", "build.patch")])
      mac64_build_dir = os.path.join("build", "mac_64")
      base.create_dir(mac64_build_dir)
      os.chdir(mac64_build_dir)
      base.cmd("../../extras/package/macosx/build.sh", ["-c"])
      mac64_install_dir = os.path.join(vlc_dir, "build", "mac_64", "vlc_install_dir")
      mac64_dest_dir = os.path.join(base_dir, "build", "mac_64")
      form_build_mac(mac64_install_dir, mac64_dest_dir)

    if config.check_option("platform", "mac_arm64"):
      base.cmd("git", ["restore", "extras/package/macosx/build.sh"])
      base.cmd("patch", ["-p1", "extras/package/macosx/build.sh", os.path.join("..", "tools", "mac_arm64", "build.patch")])
      mac_arm64_build_dir = os.path.join("build", "mac_arm64")
      base.create_dir(mac_arm64_build_dir)
      os.chdir(mac_arm64_build_dir)
      base.cmd("../../extras/package/macosx/build.sh", ["-c"])
      mac_arm64_install_dir = os.path.join(vlc_dir, "build", "mac_arm64", "vlc_install_dir")
      mac_arm64_dest_dir = os.path.join(base_dir, "build", "mac_arm64")
      form_build_mac(mac_arm64_install_dir, mac_arm64_dest_dir)

  os.chdir(old_cur)
  return
