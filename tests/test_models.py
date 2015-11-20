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

    from invenio_collections.models import Collection

    with app.app_context():
        create_database(db.engine.url)
        db.create_all()
        assert 'collection' in db.metadata.tables
        assert 'collection_facets' in db.metadata.tables

        coll1 = Collection(name='coll1')
        db.session.add(coll1)
        db.session.commit()

        coll2 = Collection(name='coll2', parent_id=coll1.id)
        db.session.add(coll2)
        coll3 = Collection(name='coll3', virtual=True, parent_id=coll1.id)
        db.session.add(coll3)
        db.session.commit()

        coll4 = Collection(name='coll4', parent_id=coll2.id)
        db.session.add(coll4)
        coll5 = Collection(name='coll5', parent_id=coll2.id)
        db.session.add(coll5)
        coll6 = Collection(name='coll6', parent_id=coll3.id)
        db.session.add(coll6)
        db.session.commit()

        coll4_ref = Collection(
            name='coll4_ref', parent_id=coll3.id, reference=coll4.id)
        db.session.add(coll4_ref)
        coll7 = Collection(name='coll7', parent_id=coll4.id)
        db.session.add(coll7)
        coll8 = Collection(name='coll8', parent_id=coll4.id)
        db.session.add(coll8)
        db.session.commit()

        assert coll4_ref.referenced_collection.name == coll4.name
        assert coll4.drilldown_tree() == coll4_ref.drilldown_tree()

        tree = coll1.drilldown_tree()
        assert tree == [
            {'node': coll1,
             'children': [{'node': coll2,
                           'children': [{'node': coll4,
                                         'children': [{'node': coll7},
                                                      {'node': coll8}
                                                      ]
                                         },
                                        {'node': coll5}]},
                          {'node': coll3,
                           'children': [{'node': coll6},
                                        {'node': coll4_ref}]}
                          ]
             }
        ]
        assert tree == coll8.get_tree(session=db.session)

        path_to_root_7 = list(coll7.path_to_root())
        assert path_to_root_7 == [coll7, coll4, coll2, coll1]

        path_to_root_6 = list(coll6.path_to_root())
        assert path_to_root_6 == [coll6, coll3]

    with app.app_context():
        db.drop_all()
        drop_database(db.engine.url)
