# Copyright CESSDA ERIC 2021-2025
#
# Licensed under the EUPL, Version 1.2 (the "License"); you may not
# use this file except in compliance with the License.
# You may obtain a copy of the License at
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import (
    setup,
    find_packages
)


with open('VERSION', 'r') as file_obj:
    version = file_obj.readline().strip()


requires = [
    'tornado',
    'motor',
    'pymongo',
    'cerberus',
    'kuha_common>=2.4.0',
    'kuha_document_store>=1.3.0',
    'cdcagg_common>=0.7.0'
]


setup(name='cdcagg_docstore',
      version=version,
      url='https://github.com/cessda/cessda.cdc.aggregator.doc-store',
      description='',
      license='EUPL v1.2',
      author='Toni Sissala',
      author_email='toni.sissala@tuni.fi',
      packages=find_packages(exclude=['tests']),
      include_package_data=True,
      install_requires=requires,
      classifiers=(
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: European Union Public Licence 1.2 (EUPL 1.2)',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
          'Programming Language :: Python :: 3.12',
          'Topic :: Internet :: WWW/HTTP :: HTTP Servers'))
