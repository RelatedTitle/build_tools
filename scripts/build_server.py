#!/usr/bin/env python

import config
import base
import datetime
import os

def make():
  #check server module to build
  if(not config.check_option("module", "server")):
    return

  git_dir = os.path.join(base.get_script_dir(), "..", "..")
  server_dir = os.path.join(base.get_script_dir(), "..", "..", "server")
  branding_dir = os.path.join(server_dir, "branding")

  if("" != config.option("branding")):
    branding_dir = os.path.join(git_dir, config.option("branding"), 'server')

  build_server_with_addons()

    #env variables
  product_version = base.get_env('PRODUCT_VERSION')
  if(not product_version):
    product_version = "0.0.0"

  build_number = base.get_env('BUILD_NUMBER')
  if(not build_number):
    build_number = "0"

  cur_date = datetime.date.today().strftime("%m/%d/%Y")

  base.replaceInFileRE(os.path.join(server_dir, "Common", "sources", "commondefines.js"), "const buildNumber = [0-9]*", "const buildNumber = " + build_number)
  base.replaceInFileRE(os.path.join(server_dir, "Common", "sources", "license.js"), "const buildDate = '[0-9-/]*'", "const buildDate = '" + cur_date + "'")
  base.replaceInFileRE(os.path.join(server_dir, "Common", "sources", "commondefines.js"), "const buildVersion = '[0-9.]*'", "const buildVersion = '" + product_version + "'")

  custom_public_key = os.path.join(branding_dir, 'debug.js')

  if(base.is_exist(custom_public_key)):
      base.copy_file(custom_public_key, os.path.join(server_dir, 'Common', 'sources'))

  pkg_target = "node16"

  if ("linux" == base.host_platform()):
    pkg_target += "-linux"
    if (-1 != config.option("platform").find("linux_arm64")):
      pkg_target += "-arm64"

  if ("windows" == base.host_platform()):
    pkg_target += "-win"

  base.cmd_in_dir(os.path.join(server_dir, "DocService"), "pkg", [".", "-t", pkg_target, "--options", "max_old_space_size=4096", "-o", "docservice"])
  base.cmd_in_dir(os.path.join(server_dir, "FileConverter"), "pkg", [".", "-t", pkg_target, "-o", "converter"])
  base.cmd_in_dir(os.path.join(server_dir, "Metrics"), "pkg", [".", "-t", pkg_target, "-o", "metrics"])

  example_dir = os.path.join(base.get_script_dir(), "..", "..", "document-server-integration", "web", "documentserver-example", "nodejs")
  base.delete_dir(os.path.join(example_dir, "node_modules"))
  base.cmd_in_dir(example_dir, "npm", ["ci"])
  base.cmd_in_dir(example_dir, "pkg", [".", "-t", pkg_target, "-o", "example"])

def build_server_with_addons():
  addons = {}
  addons["server"] = [True, False]
  addons.update(base.get_server_addons())
  for addon in addons:
    if (addon):
      addon_dir = os.path.join(base.get_script_dir(), "..", "..", addon)
      base.cmd_in_dir(addon_dir, "npm", ["ci"])
      base.cmd_in_dir(addon_dir, "npm", ["run", "build"])

def build_server_develop():
  server_dir = os.path.join(base.get_script_dir(), "..", "..", "server")
  base.cmd_in_dir(server_dir, "npm", ["ci"])
  base.cmd_in_dir(server_dir, "grunt", ["develop", "-v"] + base.server_addons_param())
