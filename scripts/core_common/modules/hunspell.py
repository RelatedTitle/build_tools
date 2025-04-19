import sys
sys.path.append('../../../scripts')
import base
import os

def clean():
  if base.is_dir("hunspell"):
    base.delete_dir_with_access_error("hunspell")
  return

def make(build_js = True):

  old_cur_dir = os.getcwd()
  #fetch libhunspell
  print("[fetch & build]: hunspell")
  core_common_dir = os.path.join(base.get_script_dir(), "../../core/Common")

  os.chdir(os.path.join(core_common_dir, "3dParty/hunspell"))

  base.common_check_version("hunspell", "1", clean)
  base.cmd("python", ["./before.py"])

  if (build_js):
    os.chdir(os.path.join(core_common_dir, "js"))
    base.cmd("python", ["./make.py", os.path.join(core_common_dir, "3dParty/hunspell/hunspell.json")])

  os.chdir(old_cur_dir)

if __name__ == '__main__':
  # manual compile
  make(True)
