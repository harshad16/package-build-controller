from setuptools import setup

setup(name='package-build-controller',
      version='0.1',
      description='package-build-controller',
      url='https://github.com/thoth-station/package-build-controller',
      author='sub-mod',
      author_email='subin@apache.org',
      license='MIT',
      packages=['package-build-controller'],
      install_requires=[
            'pybloom-mirror',
      ],
      zip_safe=False)