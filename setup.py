import sys
import setuptools
from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext


__version__ = "0.0.2"


#==========================================================
# Helpers  to compile with Pybind11
# See: https://github.com/pybind/python_example

class get_pybind_include(object):
    """
    Helper class to determine the pybind11 include path
    The purpose of this class is to postpone importing pybind11
    until it is actually installed, so that the ``get_include()``
    method can be invoked.
    """

    def __init__(self, user=False):
        self.user = user

    def __str__(self):
        import pybind11
        return pybind11.get_include(self.user)


def has_flag(compiler, flagname):
    """
    Return a boolean indicating whether a flag name is supported on
    the specified compiler.
    """
    import tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.cpp') as f:
        f.write('int main (int argc, char **argv) { return 0; }')
        try:
            compiler.compile([f.name], extra_postargs=[flagname])
        except setuptools.distutils.errors.CompileError:
            return False
    return True


def cpp_flag(compiler):
    """
    Return the -std=c++[11/14] compiler flag.
    The c++14 is prefered over c++11 (when it is available).
    """
    if has_flag(compiler, '-std=c++14'):
        return '-std=c++14'
    elif has_flag(compiler, '-std=c++11'):
        return '-std=c++11'
    else:
        raise RuntimeError('Unsupported compiler -- at least C++11 support '
                           'is needed!')


class BuildExt(build_ext):
    """ A custom build extension for adding compiler-specific options. """
    c_opts = {
        'msvc': ['/EHsc'],
        'unix': [],
    }

    if sys.platform == 'darwin':
        c_opts['unix'] += ['-stdlib=libc++', '-mmacosx-version-min=10.7']

    def build_extensions(self):
        ct = self.compiler.compiler_type
        opts = self.c_opts.get(ct, [])
        if ct == 'unix':
            opts.append('-DVERSION_INFO="%s"' % self.distribution.get_version())
            opts.append(cpp_flag(self.compiler))
            if has_flag(self.compiler, '-fvisibility=hidden'):
                opts.append('-fvisibility=hidden')
        elif ct == 'msvc':
            opts.append('/DVERSION_INFO=\\"%s\\"' % self.distribution.get_version())
        for ext in self.extensions:
            ext.extra_compile_args = opts
        build_ext.build_extensions(self)

#==========================================================


ext_modules = [
    Extension("synaptor.seg_utils._seg_utils",
              ["synaptor/seg_utils/_seg_utils.cpp"],
              include_dirs=[get_pybind_include(),
                            get_pybind_include(user=True)],
              language='c++'),
    Extension("synaptor.seg_utils._relabel",
              ["synaptor/seg_utils/_relabel.cpp"],
              include_dirs=[get_pybind_include(),
                            get_pybind_include(user=True)],
              language='c++'),
    Extension("synaptor.seg_utils._describe",
              ["synaptor/seg_utils/_describe.cpp"],
              include_dirs=[get_pybind_include(),
                            get_pybind_include(user=True)],
              language='c++')
]


setup(
    name='synaptor',
    version=__version__,
    description='Processing voxelwise descriptors for Connectomics.',
    author='Nicholas Turner',
    author_email='nturner@cs.princeton.edu',
    url='https://github.com/nicholasturner1/Synaptor',
    packages=setuptools.find_packages(),
    ext_modules=ext_modules,
    install_requires=['numpy', 'scipy', 'python-igraph', 'pandas', 'h5py',
                      'cloud-volume', 'task-queue', 'torch==1.0.1',
                      'torchvision', 'future', 'pybind11>=2.2',
                      'psycopg2-binary', 'sqlalchemy', 'pytest'],
    cmdclass={'build_ext': BuildExt},
    zip_safe=False
)
