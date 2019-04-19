# -*- coding: utf-8 -*-

from py2neo import Node, Relationship
from collections import namedtuple


# 使用neo4j数据库存储本体模型时，本质上是使用neo4j

OwlObj = namedtuple('OwlObject',
                    ['cls', 'dtp', 'otp'])
OwlObjLabel = OwlObj(cls='owl_Class',
                     dtp='owl_DataTypeProperty',
                     otp='owl_ObjectProperty')

OwlRel = namedtuple('OwlObject',
                    ['domain', 'range', 'subCls', 'subProp', 'isA'])
OwlRelLabel = OwlRel(domain='owl_Domain',
                     range='owl_Range',
                     subCls='owl_SubClassOf',
                     subProp='owl_SubPropertyOf',
                     isA='owl_IsA')

LiteralType = namedtuple('LiteralType', ['integer', 'string', 'float', 'boolean'])
LiteralLabel = LiteralType(integer='literal_int',
                           string='literal_string',
                           float='literal_float',
                           boolean='literal_bool')


def buildTopoOntology(g):
    # 创建Class节点
    autoSysCls = Node(OwlObjLabel.cls, name='AS')

    # DataTypeProperty
    # DataTypeProperty的取值(range)是literal变量，没必要为字面量创建节点然后将range作为边，而是直接将range以key-value方式存储
    # range_type和rangeInterval合起来相当于range，rangeInterval可选
    autoSysNumber = Node(OwlObjLabel.dtp, name='ASN', rangeType=LiteralLabel.integer, rangeInterval=[1, 65535])
    # DataTypeProperty的domain
    r = Relationship(autoSysNumber, OwlRelLabel.domain, autoSysCls)
    g.create(r)

    ipAddrCls = Node(OwlObjLabel.cls, name='IpAddr')
    ipAddrIsGlobal = Node(OwlObjLabel.dtp, name='isGolbalIpAddr', rangeType=LiteralLabel.boolean)
    r = Relationship(ipAddrIsGlobal, OwlRelLabel.domain, ipAddrCls)
    g.create(r)

    intNotation = Node(OwlObjLabel.dtp, name='intNotation')
    r = Relationship(intNotation, OwlRelLabel.domain, ipAddrCls)
    g.create(r)

    # ObjectProperty
    ipInAsRel = Node(OwlObjLabel.otp, name='ipInAS')
    rd = Relationship(ipInAsRel, OwlRelLabel.domain, ipAddrCls)
    rr = Relationship(ipInAsRel, OwlRelLabel.range, autoSysCls)
    g.create(rd | rr)

    # SubClass
    ipV4AddrCls = Node(OwlObjLabel.cls, name='IpV4Addr')
    r = Relationship(ipV4AddrCls, OwlRelLabel.subCls, ipAddrCls)
    g.create(r)

    ipV6AddrCls = Node(OwlObjLabel.cls, name='IpV6Addr')
    r = Relationship(ipV6AddrCls, OwlRelLabel.subCls, ipAddrCls)
    g.create(r)

    # SubProperty
    isInRel = Node(OwlObjLabel.otp, name='isIn')
    r = Relationship(ipInAsRel, OwlRelLabel.subProp, isInRel)
    g.create(r)

    ################################################################
    # 数据示例
    ################################################################
    autoSysInstance = Node(autoSysCls['name'], name='AS_1234')
    autoSysInstance[autoSysNumber['name']] = 1234
    r = Relationship(autoSysInstance, OwlRelLabel.isA, autoSysCls)
    g.create(r)

    ipV4AddrInstance = Node(ipV4AddrCls['name'], name='7.91.205.21')
    ipV4AddrInstance[intNotation['name']] = 1234567
    r = Relationship(ipV4AddrInstance, OwlRelLabel.isA, ipV4AddrCls)
    g.create(r)

    r = Relationship(ipV4AddrInstance, ipInAsRel['name'], autoSysInstance)
    g.create(r)