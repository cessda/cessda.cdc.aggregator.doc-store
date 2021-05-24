from unittest import TestCase
from cdcagg_docstore import iter_collections
from cdcagg_docstore.mdb import studies_collection


class TestPackage(TestCase):

    def test_iter_collections_returns_collections(self):
        collections = list(iter_collections())
        self.assertEqual(collections, [studies_collection()])
