# -*- coding: utf-8 -*-

from py2neo import Node, Relationship
from collections import namedtuple

# 使用neo4j数据库存储由owl/rdf构建的本体模型时，本质上是使用neo4j的数据模型“标签属性图”（LPG）存储所有信息
# 因此需要进行模型的转换，转换原则是：
# 1. 如果owl/rdf中的某元素和其他元素存在关系，那么该元素被转换为LPG中的节点：
#    例如，owl/rdf中的class对象，本身就对应概念，会和其他概念产生关系，需要被转换为节点；
#         datatypeProperty和objectProperty通过domain或者range和class产生关系，也需要被转换为节点，相当于将关系实体化了
# 2. 如果owl/rdf中的某元素单纯用于描述两个元素之间的关系，那么该元素被转换为LPG中的边：
#    例如，上面提到的domain/range，还有subclassof，subpropertyof等
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


class OwlOtpNode(Node):
    def __init__(self, name, sname, **properties):
        properties['name'] = name
        properties['sname'] = sname  # name shown on the edge, if this OTP node is instantiated to an edge
        Node.__init__(self, OwlObjLabel.otp, **properties)


def buildTopoOntology(g):

    ###############################################
    # Autonomous System(AS) 相关的本体
    # 创建Class节点
    autoSysCls = Node(OwlObjLabel.cls, name='AS')

    # AS的DataTypeProperty
    # DataTypeProperty的取值(range)是literal变量，没必要为字面量创建节点然后将range作为边，而是直接将range以key-value方式存储
    # range_type和rangeInterval合起来相当于range，rangeInterval可选
    autoSysNumber = Node(OwlObjLabel.dtp, name='ASN', rangeType=LiteralLabel.integer, rangeInterval=[1, 65535])
    # DataTypeProperty的domain
    r = Relationship(autoSysNumber, OwlRelLabel.domain, autoSysCls)
    g.create(r)

    # AS的ObjectProperty
    # AS Link
    AS_Link = OwlOtpNode(name='AS_Link', sname='connectedTo')
    rd = Relationship(AS_Link, OwlRelLabel.domain, autoSysCls)
    rr = Relationship(AS_Link, OwlRelLabel.range, autoSysCls)
    # AS Link的属性，如type属性peer/p2c
    AS_LinkType = Node(OwlObjLabel.dtp, name='type', range=('p2p', 'p2c', 'unknown'))
    r = Relationship(AS_LinkType, OwlRelLabel.domain, AS_Link)
    g.create(rd | rr | r)

    ipAddrCls = Node(OwlObjLabel.cls, name='IpAddr')
    ipAddrIsGlobal = Node(OwlObjLabel.dtp, name='isGolbalIpAddr', rangeType=LiteralLabel.boolean)
    r = Relationship(ipAddrIsGlobal, OwlRelLabel.domain, ipAddrCls)
    g.create(r)

    intNotation = Node(OwlObjLabel.dtp, name='intNotation')
    r = Relationship(intNotation, OwlRelLabel.domain, ipAddrCls)
    g.create(r)

    # ObjectProperty
    ipInAsRel = OwlOtpNode(name='ipInAS', sname='isInAS')
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
    isInRel = OwlOtpNode(name='isIn', sname='isIn')
    r = Relationship(ipInAsRel, OwlRelLabel.subProp, isInRel)
    g.create(r)

    ################################################################
    # 数据示例
    ################################################################
    autoSysInstance = Node(autoSysCls['name'], name='AS_1234')
    autoSysInstance[autoSysNumber['name']] = 1234
    r = Relationship(autoSysInstance, OwlRelLabel.isA, autoSysCls)
    g.create(r)

    autoSysInstance2 = Node(autoSysCls['name'], name='AS_5678')
    autoSysInstance2[autoSysNumber['name']] = 5678
    r = Relationship(autoSysInstance2, OwlRelLabel.isA, autoSysCls)
    g.create(r)

    r = Relationship(autoSysInstance, AS_Link['sname'], autoSysInstance2)
    r[AS_LinkType['name']] = 'p2p'
    g.create(r)

    ipV4AddrInstance = Node(ipV4AddrCls['name'], name='7.91.205.21')
    ipV4AddrInstance[intNotation['name']] = 1234567
    r = Relationship(ipV4AddrInstance, OwlRelLabel.isA, ipV4AddrCls)
    g.create(r)

    r = Relationship(ipV4AddrInstance, ipInAsRel['sname'], autoSysInstance)
    g.create(r)