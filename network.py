from troposphere import (
    Template, GetAZs, Select, Ref, Parameter, Base64,
    Join, GetAtt, Output, Not, Equals, If, ec2, Export, Sub, rds
)
from rvb.networking import *

t = Template()

t.add_description("Networking")
t.add_version("2010-09-09")

white_list_ip = t.add_parameter(Parameter(
    "WhiteListIp",
    Type="String",
    Description="White listed ip"
))

vpc = t.add_resource(ec2.VPC(
    "Vpc",
    CidrBlock="10.0.0.0/16",
    EnableDnsSupport=True,
    EnableDnsHostnames=True
))

security_group_public = t.add_resource(ec2.SecurityGroup(
    "SecurityGroupPublic",
    VpcId=Ref(vpc),
    GroupDescription="Everything from whitelisted ip",
    SecurityGroupIngress=[
        ec2.SecurityGroupRule(
            IpProtocol="-1",
            FromPort="-1",
            ToPort="-1",
            CidrIp=Ref(white_list_ip),
        )
    ]
))

public_zone = PublicZone()
db_zone = DbZone()

for k, v in [('a', 0), ('b', 1), ('c', 2)]:
    public_zone.subnets.append(t.add_resource(ec2.Subnet(
        "PublicSubnet{}".format(k.capitalize()),
        AvailabilityZone=Select(v, GetAZs()),
        CidrBlock="10.0.{}.0/24".format(v),
        MapPublicIpOnLaunch=public_zone.public,
        VpcId=Ref(vpc),
    )))
    t.add_output(Output(
        "PublicSubnet{}".format(v),
        Value=Ref(public_zone.subnets[v]),
        Export=Export(
            Sub("${AWS::StackName}-PublicSubnet" + str(v))
        )
    ))
    db_zone.subnets.append(t.add_resource(ec2.Subnet(
        "PrivateSubnet{}".format(k.capitalize()),
        AvailabilityZone=Select(v, GetAZs()),
        CidrBlock="10.0.{}.0/24".format(v + 3),
        MapPublicIpOnLaunch=db_zone.public,
        VpcId=Ref(vpc),
    )))
    t.add_output(Output(
        "DBSubnet{}".format(v),
        Value=Ref(db_zone.subnets[v]),
        Export=Export(
            Sub("${AWS::StackName}-DBSubnetId" + str(v))
        )
    ))

db_subnet_group = t.add_resource(
    db_zone.get_db_subnet_group()
)

igw = t.add_resource(ec2.InternetGateway(
    "Igw",
))

igw_attachment = t.add_resource(ec2.VPCGatewayAttachment(
    "IgwAttachment",
    VpcId=Ref(vpc),
    InternetGatewayId=Ref(igw),
))

route_table = t.add_resource(ec2.RouteTable(
    "RouteTable",
    VpcId=Ref(vpc),
))

public_route = t.add_resource(ec2.Route(
    "PublicRoute",
    DependsOn=[igw_attachment.title],
    DestinationCidrBlock="0.0.0.0/0",
    GatewayId=Ref(igw),
    RouteTableId=Ref(route_table),
))

for s in public_zone.subnets:
    t.add_resource(ec2.SubnetRouteTableAssociation(
        "Assoc{}".format(s.title),
        RouteTableId=Ref(route_table),
        SubnetId=Ref(s)
    ))

t.add_output(Output(
    "Vpc",
    Value=Ref(vpc),
    Export=Export(
        Sub("${AWS::StackName}-Vpc")
    )
))

t.add_output(Output(
    "SecurityGroupPublic",
    Value=Ref(security_group_public),
    Export=Export(
        Sub("${AWS::StackName}-SecurityGroupPublic")
    )

))
t.add_output(Output(
    "DbSubnetGroup",
    Value=Ref(db_subnet_group),
    Export=Export(
        Sub("${AWS::StackName}-DBSubnetGroup")
    )
))
print t.to_json()
