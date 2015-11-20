# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
# -*- coding: utf-8 -*-
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""Model test cases."""

import os

from flask import Flask
from flask_cli import FlaskCLI
from invenio_db import InvenioDB, db
from sqlalchemy_utils.functions import create_database, drop_database

from invenio_collections import InvenioCollections


def test_db():
    """Test database backend."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'
    )
    FlaskCLI(app)
    InvenioDB(app)
    InvenioCollections(app)

    with app.app_context():
        create_database(db.engine.url)
        db.create_all()
        assert 'collection' in db.metadata.tables
        assert 'collection_tree_node' in db.metadata.tables
        assert 'collection_facets' in db.metadata.tables

    from invenio_collections.models import (
        Collection, CollectionTreeNode, FacetCollection)

    with app.app_context():
        assert db.session.query(Collection).count() == 0
        assert db.session.query(CollectionTreeNode).count() == 0

        coll1 = Collection(name='coll1', query='doct_type:article')
        db.session.add(coll1)
        db.session.commit()
        node_coll1 = CollectionTreeNode(collection_id=coll1.id)
        db.session.add(node_coll1)
        db.session.commit()

        assert db.session.query(Collection).count() == 1
        assert db.session.query(CollectionTreeNode).count() == 1

        coll2 = Collection(name='coll2')
        db.session.add(coll2)
        db.session.commit()
        node_coll2 = CollectionTreeNode(
            collection_id=coll2.id, parent_id=node_coll1.id)
        db.session.add(node_coll2)
        db.session.commit()

        tree = coll1.drilldown_tree()
        assert tree == [
            {'children': [{'node': node_coll2}], 'node': node_coll1}]

        coll3 = Collection(name='coll3')
        db.session.add(coll3)
        db.session.commit()
        node_coll3 = CollectionTreeNode(
            collection_id=coll3.id, parent_id=node_coll1.id, virtual=True)
        db.session.add(node_coll3)
        db.session.commit()

        tree = coll1.drilldown_tree()
        assert tree == [
            {'children': [{'node': node_coll2}], 'node': node_coll1}]

        tree = coll1.drilldown_tree(show_virtual=True)
        assert tree == [
                {'children': [{'node': node_coll2}, {'node': node_coll3}],
                 'node': node_coll1}]

        coll4 = Collection(name='coll4')
        db.session.add(coll4)
        db.session.commit()
        node_coll4 = CollectionTreeNode(
            collection_id=coll4.id, parent_id=node_coll2.id)
        db.session.add(node_coll4)
        node_coll4_coll3 = CollectionTreeNode(
            collection_id=coll4.id, parent_id=node_coll3.id)
        db.session.add(node_coll4_coll3)
        db.session.commit()

        coll5 = Collection(name='coll5')
        db.session.add(coll5)
        db.session.commit()
        node_coll5 = CollectionTreeNode(
            collection_id=coll5.id, parent_id=node_coll2.id)
        db.session.add(node_coll5)
        db.session.commit()

        path_to_root = coll4.path_to_root()
        assert path_to_root == [node_coll4, node_coll2, node_coll1]
        path_to_root = coll4.path_to_root(node_id=node_coll4_coll3.id)
        assert path_to_root == [node_coll4_coll3, node_coll3]

    with app.app_context():
        db.drop_all()
        drop_database(db.engine.url)

#
# from invenio_base.wrappers import lazy_import
#
# from invenio_testing import InvenioTestCase
#
# Collection = lazy_import('invenio_collections.models:Collection')
# cfg = lazy_import('invenio_base.globals:cfg')
#
#
# class ModelsTestCase(InvenioTestCase):
#
#     """Test model classes."""
#
#     def test_collection_name_validation(self):
#         """Test Collection class' name validation."""
#         c = Collection()
#         test_name = cfg['CFG_SITE_NAME'] + ' - not site name'
#
#         # Name can't contain '/' characters
#         with self.assertRaises(ValueError):
#             c.name = 'should/error'
#
#         # Name should equal the site name if the collection is a root
#         c.id = 1
#         self.assertTrue(c.is_root)
#         with self.assertWarns(UserWarning):
#             c.name = test_name
#         # Root node's name can equal site name
#         try:
#             with self.assertWarns(UserWarning):
#                 c.name = cfg['CFG_SITE_NAME']
#         except AssertionError:
#             pass
#
#         # Name can't equal the site name if not root collection
#         c.id = 2
#         self.assertFalse(c.is_root)
#         with self.assertRaises(ValueError):
#             c.name = cfg['CFG_SITE_NAME']
#
#         # Assigning should work in other cases
#         c.name = test_name
#         self.assertEquals(c.name, test_name)
