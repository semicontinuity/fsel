import sys
from setuptools import setup, find_packages


if sys.version_info < (3, 0):
    sys.stderr.write("Sorry, Python < 3.0 is not supported\n")
    sys.exit(1)


setup(name='fsel',
      version='0.1',
      description="""A text user interface (TUI) program to navigate folders""",
      long_description=open('README.md').read(),
      url='https://github.com/semicontinuity/fsel',
      author='Semicontinuity',
      license='MIT',
      install_requires=['picotui'],
      packages=['fsel', 'fsel.lib'],
)
