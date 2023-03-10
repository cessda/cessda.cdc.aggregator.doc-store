# Copyright CESSDA ERIC 2021
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

from unittest import TestCase
from cdcagg_docstore import iter_collections
from cdcagg_docstore.mdb import studies_collection


class TestPackage(TestCase):

    def test_iter_collections_returns_collections(self):
        collections = list(iter_collections())
        self.assertEqual(collections, [studies_collection()])
