#!/usr/bin/env python

import sys
sys.path.append('../..')
import config
import base
import os
import qmake

def make(src_dir, modules, build_platform="android", qmake_addon=""):
  old_cur = os.getcwd()

  print("boost-headers...")
  base.cmd("./bootstrap.sh", ["--with-libraries=system"])
  base.cmd("./b2", ["--prefix=./../build/" + build_platform, "headers", "install"])

  for module in modules:
    print("boost-module: " + module + " ...")
    module_dir = os.path.join(src_dir, "libs", module)
    os.chdir(module_dir)
    pro_file_content = []
    pro_file_content.append("QT -= core gui")
    pro_file_content.append("TARGET = boost_" + module)
    pro_file_content.append("TEMPLATE = lib")
    pro_file_content.append("CONFIG += staticlib")
    if (build_platform == "android"):
      pro_file_content.append("DEFINES += \"_HAS_AUTO_PTR_ETC=0\"")
    pro_file_content.append("")
    pro_file_content.append("CORE_ROOT_DIR = $$PWD/../../../../../..")
    pro_file_content.append("PWD_ROOT_DIR = $$PWD")
    pro_file_content.append("include($$PWD/../../../../../base.pri)")
    pro_file_content.append("")
    pro_file_content.append("BOOST_SOURCES=$$PWD/../..")
    pro_file_content.append("INCLUDEPATH += $$BOOST_SOURCES")
    pro_file_content.append("INCLUDEPATH += $$PWD/include")
    pro_file_content.append("")
    pro_file_content.append("SOURCES += $$files($$PWD/src/*.cpp, true)")
    pro_file_content.append("")
    
    # Ensure forward slashes in paths for Qt .pro files, which is what Qt expects even on Windows
    dest_path = "$$BOOST_SOURCES/../build/" + build_platform + "/lib/$$CORE_BUILDS_PLATFORM_PREFIX"
    pro_file_content.append("DESTDIR = " + dest_path)
    
    pro_file_path = os.path.join(module_dir, module + ".pro")
    base.save_as_script(pro_file_path, pro_file_content)
    os.chdir(module_dir)
    qmake.make_all_platforms(pro_file_path, qmake_addon)
  
  os.chdir(old_cur)
  return
