from importlib.util import module_from_spec, spec_from_file_location
from os.path import join
from setuptools import setup


# noinspection PyUnresolvedReferences
def get_version_and_cmdclass(package_path):
    spec = spec_from_file_location("version", join(package_path, "version.py"))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.__version__, module.cmdclass


version, cmdclass = get_version_and_cmdclass("src/tpmmld")


setup(version=version, cmdclass=cmdclass)
