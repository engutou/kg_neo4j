# -*- coding: utf-8 -*-

from py2neo import Node, Relationship
from collections import namedtuple

"""
使用neo4j数据库存储由owl/rdf构建的本体模型时，本质上是使用neo4j的数据模型“标签属性图”（lpg）存储所有信息
因此需要进行模型的转换，转换原则是：
1. 如果owl/rdf中的某元素和其他元素存在关系，那么该元素被转换为lpg中的节点：
   例如，owl/rdf中的class对象，本身就对应概念，会和其他概念产生关系，需要被转换为节点；
        datatypeProperty和objectProperty通过domain或者range和class产生关系，也需要被转换为节点，相当于将关系实体化了
2. 如果owl/rdf中的某元素单纯用于描述两个元素之间的关系，那么该元素被转换为lpg中的边：
   例如，上面提到的domain/range，还有subClassOf，subPropertyOf等
   
********

命名规则：
实体/概念——驼峰表示，首字母大写，如Organization，University
关系——驼峰表示，首字母小写，如isIn，isA
属性——所有字母小写，单词间用_连接，如type，is_boundary
缩写——所有字母大写，但后面增加下划线，如AS，IP，AS_Link，IP_Link
"""

OwlObjType = namedtuple('OwlObject',
                        ['cls', 'dtp', 'otp'])
OwlObjLabel = OwlObjType(cls='owl_Class',
                         dtp='owl_DataTypeProperty',
                         otp='owl_ObjectProperty')

OwlRelType = namedtuple('OwlObject',
                        ['domain', 'range', 'subCls', 'subProp', 'isA'])
OwlRelLabel = OwlRelType(domain='owl_domain',
                         range='owl_range',
                         subCls='owl_subClassOf',
                         subProp='owl_subPropertyOf',
                         isA='owl_isA')

LiteralType = namedtuple('LiteralType', ['integer', 'string', 'float', 'boolean', 'date'])
LiteralLabel = LiteralType(integer='literal_int',
                           string='literal_string',
                           float='literal_float',
                           boolean='literal_bool',
                           date='literal_date')


class OwlClsNode(Node):
    # lpg中的节点，对应owl/rdf中的class
    def __init__(self, name, **properties):
        # name to be shown on the node
        properties['name'] = name
        Node.__init__(self, OwlObjLabel.cls, **properties)


class OwlOtpNode(Node):
    # lpg中的节点，对应owl/rdf中的objectProperty
    def __init__(self, name, ename, **properties):
        # name to be shown on the node
        properties['name'] = name
        # name to be shown on the edge, if the ObjectProperty node is instantiated to an edge
        # 如果这个关系在数据层面没有被实体化，仍是用边表示，那么ename就作为边的标识
        properties['ename'] = ename
        Node.__init__(self, OwlObjLabel.otp, **properties)


class OwlDtpNode(Node):
    # lpg中的节点，对应owl/rdf中的datatypeProperty
    def __init__(self, name, **properties):
        # name to be shown on the node
        properties['name'] = name
        Node.__init__(self, OwlObjLabel.dtp, **properties)


def buildTopoOntology(g):

    ###############################################
    # Autonomous System(AS) 相关的本体
    ###############################################

    # 创建class对应的节点
    AS_Cls = OwlClsNode(name='AS')

    # AS的datatypeProperty
    # datatypeProperty的range是literal变量，没必要为字面量创建节点然后将range作为边，而是直接将range以key-value方式存储
    # range_type和range_interval合起来相当于range，rangeInterval可选
    AS_Number = OwlDtpNode(name='ASN', range_type=LiteralLabel.integer, range_interval=[1, 65535])
    # DataTypeProperty的domain
    g.create(Relationship(AS_Number, OwlRelLabel.domain, AS_Cls))

    AS_Type = OwlDtpNode(name='type', range_type=LiteralLabel.string, range=('Transit/Access', 'Content', 'Enterprise'))
    g.create(Relationship(AS_Type, OwlRelLabel.domain, AS_Cls))

    # AS的ObjectProperty
    # AS Link
    AS_Link = OwlOtpNode(name='AS_Link', ename='connectedTo')
    rd = Relationship(AS_Link, OwlRelLabel.domain, AS_Cls)
    rr = Relationship(AS_Link, OwlRelLabel.range, AS_Cls)

    # AS Link的属性，如type属性peer/p2c
    AS_LinkType = OwlDtpNode(name='type', range_type=LiteralLabel.string, range=('peer', 'p2c', 'unknown'))
    r = Relationship(AS_LinkType, OwlRelLabel.domain, AS_Link)
    g.create(rd | rr | r)

    # 组织机构
    OrgCls = OwlClsNode(name='Organization')
    AS_Owner = OwlOtpNode(name='AS_Owner', ename='ownedBy')
    g.create(Relationship(AS_Owner, OwlRelLabel.domain, AS_Cls))
    g.create(Relationship(AS_Owner, OwlRelLabel.range, OrgCls))

    # 所属国家/城市
    CountryCls = OwlClsNode(name='Country/Region')
    CityCls = OwlClsNode(name='City')
    cityInCountry = OwlOtpNode(name='cityInCountry', ename='isIn')
    g.create(Relationship(cityInCountry, OwlRelLabel.domain, CityCls))
    g.create(Relationship(cityInCountry, OwlRelLabel.range, CountryCls))

    ASInCountry = OwlOtpNode(name='ASInCountry', ename='isIn')
    g.create(Relationship(ASInCountry, OwlRelLabel.domain, CountryCls))
    g.create(Relationship(cityInCountry, OwlRelLabel.range, CountryCls))

    # AS注册机构
    RIR_Cls = OwlClsNode(name='RIR', full_name='Regional Internet Registry')
    AS_Reg = OwlOtpNode(name='registerEvent', ename='registeredAt')
    g.create(Relationship(AS_Reg, OwlRelLabel.domain, AS_Cls))
    g.create(Relationship(AS_Reg, OwlRelLabel.range, RIR_Cls))

    AS_RegDate = OwlDtpNode(name='register_date', range_type=LiteralLabel.date, range=('1950-01-01', 'Now'))
    g.create(Relationship(AS_RegDate, OwlRelLabel.domain, AS_Reg))

    IpAddrCls = OwlClsNode(name='IpAddr')
    isIpGlobal = OwlDtpNode(name='is_global', rangeType=LiteralLabel.boolean)
    r = Relationship(isIpGlobal, OwlRelLabel.domain, IpAddrCls)
    g.create(r)

    intNotation = OwlDtpNode(name='int_note')
    r = Relationship(intNotation, OwlRelLabel.domain, IpAddrCls)
    g.create(r)

    # ObjectProperty
    ipInAsRel = OwlOtpNode(name='ipInAS', ename='isInAS')
    rd = Relationship(ipInAsRel, OwlRelLabel.domain, IpAddrCls)
    rr = Relationship(ipInAsRel, OwlRelLabel.range, AS_Cls)
    g.create(rd | rr)

    # SubClass
    IPv4AddrCls = OwlClsNode(name='IPv4Addr')
    r = Relationship(IPv4AddrCls, OwlRelLabel.subCls, IpAddrCls)
    g.create(r)

    IPv6AddrCls = OwlClsNode(name='IPv6Addr')
    r = Relationship(IPv6AddrCls, OwlRelLabel.subCls, IpAddrCls)
    g.create(r)

    # SubProperty
    isInRel = OwlOtpNode(name='isIn', ename='isIn')
    r = Relationship(ipInAsRel, OwlRelLabel.subProp, isInRel)
    g.create(r)

    ################################################################
    # 数据示例
    ################################################################
    AS_1 = Node(AS_Cls['name'], name='AS_1234')
    AS_1[AS_Number['name']] = 1234
    AS_1[AS_Type['name']] = AS_Type['range'][1]
    r = Relationship(AS_1, OwlRelLabel.isA, AS_Cls)
    g.create(r)

    AS_2 = Node(AS_Cls['name'], name='AS_5678')
    AS_2[AS_Number['name']] = 5678
    AS_1[AS_Type['name']] = AS_Type['range'][0]
    r = Relationship(AS_2, OwlRelLabel.isA, AS_Cls)
    g.create(r)

    r = Relationship(AS_1, AS_Link['ename'], AS_2)
    r[AS_LinkType['name']] = AS_LinkType['range'][1]
    g.create(r)

    ip = Node(IPv4AddrCls['name'], name='7.91.205.21')
    ip[intNotation['name']] = 1234567
    r = Relationship(ip, OwlRelLabel.isA, IPv4AddrCls)
    g.create(r)

    r = Relationship(ip, ipInAsRel['ename'], AS_1)
    g.create(r)