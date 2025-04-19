#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import sys
sys.path.append('../..')
import config
import base
import os
import config

current_dir = os.path.join(base.get_script_dir(), "..", "..", "core", "Common", "3dParty", "socketrocket")

def buildIOS():
# Build for iphone
  base.cmd("xcodebuild", ["archive", "-project", os.path.join(current_dir, "SocketRocket.xcodeproj"), "-scheme",  "SocketRocket", "-archivePath", os.path.join(current_dir, "build", "SocketRocket-devices.xcarchive"), "-sdk", "iphoneos", "ENABLE_BITCODE=NO", "BUILD_LIBRARY_FOR_DISTRIBUTION=YES", "SKIP_INSTALL=NO"])
  base.cmd("xcodebuild", ["-sdk", "iphoneos", "BITCODE_GENERATION_MODE = bitcode", "ENABLE_BITCODE = YES", "OTHER_CFLAGS = -fembed-bitcode", "-configuration", "Release"])

# Build for simulator
  base.cmd("xcodebuild", ["archive", "-project", os.path.join(current_dir, "SocketRocket.xcodeproj"), "-scheme",  "SocketRocket", "-archivePath", os.path.join(current_dir, "build", "SocketRocket-simulators.xcarchive"), "-sdk", "iphonesimulator", "ENABLE_BITCODE=NO", "BUILD_LIBRARY_FOR_DISTRIBUTION=YES", "SKIP_INSTALL=NO"])
  base.cmd("xcodebuild", ["-sdk", "iphonesimulator", "BITCODE_GENERATION_MODE = bitcode", "ENABLE_BITCODE = YES", "OTHER_CFLAGS = -fembed-bitcode", "-configuration", "Release"])

# Package xcframework
  base.cmd("xcodebuild", ["-create-xcframework", "-library", os.path.join(current_dir, "build", "SocketRocket-devices.xcarchive", "Products", "usr", "local", "lib", "libSocketRocket.a"), "-library", os.path.join(current_dir, "build", "SocketRocket-simulators.xcarchive", "Products", "usr", "local", "lib", "libSocketRocket.a"), "-output", os.path.join(current_dir, "build", "SocketRocket.xcframework")])

# Remove arm64 for simulator for SDK 14
  base.cmd("lipo", ["-remove", "arm64", "-output", os.path.join("build", "Release-iphonesimulator", "libSocketRocket.a"), os.path.join("build", "Release-iphonesimulator", "libSocketRocket.a")])

  ios_lib_dir = os.path.join(current_dir, "build", "ios", "lib")
  base.create_dir(ios_lib_dir)

# Create fat lib
  base.cmd("lipo", [os.path.join(".", "build", "Release-iphonesimulator", "libSocketRocket.a"), os.path.join(".", "build", "Release-iphoneos", "libSocketRocket.a"), "-create", "-output", 
     os.path.join(ios_lib_dir, "libSoсketRocket.a")])

  return

def buildMacOS():

# Build for iphone
  base.cmd("xcodebuild", ["-sdk", "macosx", "BITCODE_GENERATION_MODE = bitcode", "ENABLE_BITCODE = YES", "OTHER_CFLAGS = -fembed-bitcode", "-configuration", "Release"])

  mac_64_lib_dir = os.path.join(current_dir, "build", "mac_64", "lib")
  mac_arm64_lib_dir = os.path.join(current_dir, "build", "mac_arm64", "lib")
  
  base.create_dir(mac_64_lib_dir)
  base.create_dir(mac_arm64_lib_dir)

  base.cmd("lipo", [os.path.join("build", "Release", "libSocketRocket.a"), "-thin", "x86_64", "-output", os.path.join(mac_64_lib_dir, "libSoсketRocket.a")])
  base.cmd("lipo", [os.path.join("build", "Release", "libSocketRocket.a"), "-thin", "arm64", "-output", os.path.join(mac_arm64_lib_dir, "libSoсketRocket.a")])

  base.delete_file(os.path.join("build", "Release", "libSocketRocket.a"))

  return

def make():
  if (-1 == config.option("platform").find("mac") and -1 == config.option("platform").find("ios")):
    return

  current_dir_old = os.getcwd()

  print("[build]: socketrocket")
  os.chdir(current_dir)

  if (-1 != config.option("platform").find("mac")):
    if not base.is_dir(os.path.join(current_dir, "build", "mac_64")) or not base.is_dir(os.path.join(current_dir, "build", "mac_arm_64")):
      buildMacOS()
  elif (-1 != config.option("platform").find("ios")):
    if not base.is_dir(os.path.join(current_dir, "build", "ios")):
      buildIOS()
  os.chdir(current_dir_old)
  return
