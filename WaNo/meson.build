
py = import('python').find_installation()
dep_py = py.dependency()

compile_modules = [
   'SimStackEntryPoint',
   'SSHConnector',
   'UnicoreState',
   'WaNoGitRevision',
   'WaNoSettingsProvider',
   'Constants',
   'SimStackPaths',
   'WFELicense',
   'WFEditorApplication',
]
copy_src_files = [
   '__init__.py',
]
foreach compile_module : compile_modules
    _compile_src_cython=configure_file(input: compile_module + '.py',
               output: compile_module + '.pyx',
               configuration: configuration_data())

    py.extension_module(
        compile_module,
        _compile_src_cython,
        subdir: 'WaNo',
        dependencies : dep_py,
        install: true,
    )
endforeach
instdir = py.get_install_dir()
install_subdir('ctrl_img', install_dir: instdir + 'WaNo/')
install_subdir('Media', install_dir: instdir + 'WaNo/')
subdir('lib')
subdir('view')
