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
from slugify import slugify
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.orm import validates
from sqlalchemy_mptt.mixins import BaseNestedSets


class Collection(db.Model):
    """Collection model."""

    __tablename__ = 'collection'

    def __repr__(self):
        """Return class representation."""
        return ('Collection <id: {0.id}, name: {0.name}, '
                'query: {0.query}>'.format(self))

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, index=True, nullable=False)
    query = db.Column(
        db.Text().with_variant(db.Text(20), 'mysql'), nullable=True)

    @validates('name')
    def validate_name(self, key, name):
        """Validate name, it should not contain '/'-character."""
        if '/' in name:
            raise ValueError("collection name shouldn't contain '/'-character")
        return slugify(name)

    @classmethod
    def get_root_collections(cls):
        """Get all the collections without a parent or not attached."""
        pass

    def attach_to_tree(self, parent_id, visible=True, virtual=False):
        pass

    def drilldown_tree(self, node_id=None, show_invisible=False, show_virtual=False):
        """Generate tree of current collection.

        :param show_invisible: If true invisible collections will be added to
            the tree.
        :param show_invisible: If true virtual collections will be added to
            the tree.
        :returns:

        """
        node = self._get_node_id(node_id=node_id)

        def query(nodes):
            filters = [node.__class__.tree_id.is_(node.tree_id), ]
            if not show_virtual:
                filters.append(node.__class__.virtual.is_(False))
            if not show_invisible:
                filters.append(node.__class__.visible.is_(True))
            return nodes.filter(*filters)

        return node.get_tree(session=db.session, query=query)

    def path_to_root(self, node_id=None, include_virtual=False):
        """Generate path from a leaf or intermediate node to the root."""
        node = self._get_node_id(node_id)
        return node.path_to_root().all()


    def _get_node_id(self, node_id=None):
        """Select the visible tree node with a "hard" link to its parent."""
        if node_id is None:
            return CollectionTreeNode.query.filter(
                CollectionTreeNode.collection_id == self.id,
                CollectionTreeNode.virtual.is_(False),
                CollectionTreeNode.visible.is_(True)).one()
        else:
            return CollectionTreeNode.query.get(node_id)


class CollectionTreeNode(db.Model, BaseNestedSets):
    """Collection Tree Node model."""

    __tablename__ = "collection_tree_node"

    def __repr__(self):
        """Return class representation."""
        return "Node <{0.id}: {0.collection_id}>".format(self)

    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer,
                              db.ForeignKey(Collection.id),
                              nullable=False)
    visible = db.Column(db.Boolean, default=True)
    virtual = db.Column(db.Boolean, default=False)

    collection = db.relationship('Collection')


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

__all__ = (
    'Collection',
    'CollectionTreeNode',
    'FacetCollection',
)
