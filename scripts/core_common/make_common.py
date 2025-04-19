#!/usr/bin/env python

import sys
sys.path.append('modules')
sys.path.append('..')

import config
import base
import glob
import os

import boost
import cef
import icu
import openssl
import curl
import websocket_all
import v8
import html2
import iwork
import hunspell
import glew
import harfbuzz
import hyphen
import googletest
import libvlc

def check_android_ndk_macos_arm(dir):
  darwin_x86_64 = os.path.join(dir, "darwin-x86_64")
  darwin_arm64 = os.path.join(dir, "darwin-arm64")
  if base.is_dir(darwin_x86_64) and not base.is_dir(darwin_arm64):
    print("copy toolchain... [" + dir + "]")
    base.copy_dir(darwin_x86_64, darwin_arm64)
  return


def make():
  if (config.check_option("platform", "android")) and (base.host_platform() == "mac") and (base.is_os_arm()):
    for toolchain in glob.glob(os.path.join(base.get_env("ANDROID_NDK_ROOT"), "toolchains", "*")):
      if base.is_dir(toolchain):
        check_android_ndk_macos_arm(os.path.join(toolchain, "prebuilt"))

  boost.make()
  cef.make()
  icu.make()
  openssl.make()
  v8.make()
  html2.make()
  iwork.make(False)
  hunspell.make(False)
  harfbuzz.make()
  glew.make()
  hyphen.make()
  googletest.make()

  if config.check_option("build-libvlc", "1"):
    libvlc.make()
  
  if config.check_option("module", "mobile"):
    if (config.check_option("platform", "android")):
      curl.make()
    websocket_all.make()
  return
