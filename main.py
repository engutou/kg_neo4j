#! python
# -*- coding: utf-8 -*-

from ontology import *
from py2neo import Graph, Node, Relationship

if __name__ == '__main__':
    g = Graph("bolt://localhost:7687", user='neo4j', password='123')
    g.delete_all()
    buildTopoOntology(g)
