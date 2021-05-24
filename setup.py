from setuptools import (
    setup,
    find_packages
)


with open('VERSION', 'r') as file_obj:
    version = file_obj.readline().strip()


setup(name='cdcagg_docstore',
      version=version,
      url='https://bitbucket.org/cessda/cessda.cdc.aggregator.doc-store',
      description='',
      license='EUPL v1.2',
      author='Toni Sissala',
      author_email='toni.sissala@tuni.fi',
      packages=find_packages(exclude=['tests']),
      include_package_data=True,
      classifiers=(
          'Development Status :: 1 - Planning',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: European Union Public Licence 1.2 (EUPL 1.2)',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Topic :: Internet :: WWW/HTTP :: HTTP Servers'))
