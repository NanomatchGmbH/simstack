#!/usr/bin/env python3
from __future__ import print_function
from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext


import shutil,os
import glob

packagename = "WaNo"

ignore_files = []
#ignore_files.append(os.path.join(packagename, "notme.py"))


def mkdir_p(path):
    import errno

    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


#mod_compiler and the other two functions are required to remove -g from default compile options
def mod_compiler(compiler):
    try: 
        #Remove -g up to 10 times - exception, when not found
        for i in range(0,10):
            compiler.compiler_so.remove("-g")
    except:
        pass

class mod_build_ext(build_ext):
    def build_extension(self, ext):
        mod_compiler(self.compiler)
        return build_ext.build_extension(self,ext)

COMPILE_DIR="compile"
try:
    os.makedirs(COMPILE_DIR)
except OSError as e:
    print ("Directory %s already exists, Exception was: %s." %(COMPILE_DIR,e) )

compiler_directives = {
    "language_level": 3,
    "annotation_typing": False
}
extensions = []
for md,rd,files in os.walk(packagename):
    for mf in files:
        if not mf.endswith(".py"):
            continue
        fullpath = os.path.join(md,mf)
        if "__init__.py" in fullpath:
            ignore_files.append(fullpath)
        if fullpath in ignore_files:
            continue
        basename = os.path.basename(fullpath[:-3])
        modulename = fullpath[:-3].replace(os.sep,".")
        #modulename = fullpath[:-3].replace("/",".")
        pyxname = basename + ".pyx"
        outdir = os.path.join(COMPILE_DIR,md)
        mkdir_p(outdir)
        outfile = os.path.join(outdir,pyxname)
        shutil.copy(fullpath,outfile)
        ex = Extension(modulename, [outfile], extra_compile_args=["-O2"])
        extensions.append(ex)

onlycopy = []
for mf in ignore_files:
    onlycopy.append(mf[:-3].replace("/","."))

setup(
  name = "SimStack",
  ext_modules=cythonize(extensions, compiler_directives=compiler_directives),
  cmdclass = {'build_ext': mod_build_ext},
)

setup(
  name = packagename,
  package_dir = {"package" : "package" },
  py_modules = onlycopy 
)
