
py = import('python').find_installation()
dep_py = py.dependency()

compile_modules = [
    'AbstractSettings',
    'BetterThreadPoolExecutor',
    'CallableQThread',
    'DynamicTimer',
    'FileSystemTree',
    'QtClusterSettingsProvider',
    'TPCThread',
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
        subdir: 'WaNo/lib',
        dependencies : dep_py,
        install: true,
    )
endforeach
