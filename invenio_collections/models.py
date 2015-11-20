# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014, 2015 CERN.
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

"""Database models for collections."""

from invenio_db import db
from sqlalchemy.orm import foreign, remote, reconstructor
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy_mptt.mixins import BaseNestedSets


class Collection(db.Model, BaseNestedSets):
    """Collection model, defined as a tree node."""

    __tablename__ = 'collection'

    def __repr__(self):
        """Return class representation."""
        return ('Collection <id: {0.id}, name: {0.name}, '
                'query: {0.query}>'.format(self))

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, index=True, nullable=False)

    query = db.Column(
        db.Text().with_variant(db.Text(20), 'mysql'), nullable=True)

    virtual = db.Column(db.Boolean, default=False)

    reference = db.Column(db.Integer, db.ForeignKey('collection.id'))
    referenced_collection = db.relationship(
        'Collection',
        primaryjoin=remote(id) == foreign(reference))

    def path_to_root(self, follow_virtual=False):
        """Generate path from a leaf or intermediate node to the root.

        :param follow_virtual: If set to False it stops when a virtual
            collection is found, if not it continues.
        """
        path = super(Collection, self).path_to_root(session=db.session).all()
        for collection in path:
            yield collection
            if collection.virtual and not follow_virtual:
                raise StopIteration()

    def _drilldown_query(self, nodes=None):
        """Generate the filter to create a branch dereferencing collections."""
        dereferenced_self = self if not self.reference else self.referenced_collection
        return super(Collection, dereferenced_self)._drilldown_query(nodes)


class FacetCollection(db.Model):
    """Facet configuration for collection."""

    __tablename__ = 'collection_facets'

    id = db.Column(db.Integer, primary_key=True)
    id_collection = db.Column(db.Integer,
                              db.ForeignKey(Collection.id))
    order = db.Column(db.Integer)
    facet_name = db.Column(db.String(80))

    collection = db.relationship(Collection, backref='facets')

    def __repr__(self):
        """Return class representation."""
        return ('FacetCollection <id: {0.id}, id_collection: '
                '{0.id_collection}, order: {0.order}, '
                'facet_name: {0.facet_name}>'.format(self))

    @classmethod
    def is_place_taken(cls, id_collection, order):
        """Check if there is already a facet on the given position.

        .. note:: This works well as a pre-check, however saving can still fail
            if somebody else creates the same record in other session
            (phantom reads).
        """
        return bool(cls.query.filter(
            cls.id_collection == id_collection,
            cls.order == order).count())

    @classmethod
    def is_duplicated(cls, id_collection, facet_name):
        """Check if the given facet is already assigned to this collection.

        .. note:: This works well as a pre-check, however saving can still fail
            if somebody else creates the same record in other session
            (phantom reads).
        """
        return bool(cls.query.filter(
            cls.id_collection == id_collection,
            cls.facet_name == facet_name).count())
