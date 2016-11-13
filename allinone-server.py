from troposphere import (
    Template, GetAZs, Select, Ref, Parameter, Base64,
    Join, GetAtt, Output, Not, Equals, If, ec2, iam, ImportValue, Sub
)
from awacs.aws import (Allow, Policy, Principal, Statement)
from awacs.sts import (AssumeRole)

from rvb.automation import userdata_file_path, userdata_from_file

t = Template()

t.add_description("CF All in one server")
t.add_version("2010-09-09")

instance_key = t.add_parameter(Parameter(
    "InstanceKey",
    Type="AWS::EC2::KeyPair::KeyName",
    Description="pick keypair to use"
))

ami = t.add_parameter(Parameter(
    "Ami",
    Type="AWS::EC2::Image::Id",
    Description="Ami id for the all in one server"
))

instance_type = t.add_parameter(Parameter(
    "InstanceType",
    Type="String",
    AllowedValues=["t2.micro"]
))

network_stack = t.add_parameter(Parameter(
    "NetworkStack",
    Type="String",
    Description="Network stack name"
))

db_stack = t.add_parameter(Parameter(
    "DbStack",
    Type="String",
    Description="Db stack name"
))

security_group_web = t.add_resource(ec2.SecurityGroup(
    "SecurityGroupWeb",
    GroupDescription=Sub("${AWS::StackName} port 80 to the world"),
     SecurityGroupIngress=[
        ec2.SecurityGroupRule(
            FromPort=80,
            ToPort=80,
            IpProtocol="tcp",
            CidrIp="0.0.0.0/0"
        )
    ],
    VpcId=ImportValue(
        Sub("${NetworkStack}-Vpc")
    ),
))

role = t.add_resource(iam.Role(
    "Role",
    AssumeRolePolicyDocument=Policy(
        Version="2012-10-17",
        Statement=[
            Statement(
                Effect=Allow,
                Action=[AssumeRole],
                Principal=Principal("Service", ["ec2.amazonaws.com"])
            )
        ]
    ),
    Policies=[
    ],
    ManagedPolicyArns=[
        "arn:aws:iam::aws:policy/AWSCodePipelineCustomActionAccess"
    ]
))

profile = t.add_resource(iam.InstanceProfile(
    "Profile",
    Roles=[Ref(role)]
))
userdata_template = userdata_file_path('discoverdb')
userdata_references = [Ref('AWS::Region'), Ref('AWS::StackName')]
userdata = userdata_from_file(
    userdata_template,
    references=userdata_references,
    constants=[
        ('DbHost', ImportValue(Sub("${DbStack}-DbHost"))),
        ('DbPort', ImportValue(Sub("${DbStack}-DbPort")))

    ]
)

instance = t.add_resource(ec2.Instance(
    "Instance",
    InstanceType=Ref(instance_type),
    KeyName=Ref(instance_key),
    ImageId=Ref(ami),  # Amazon Linux AMI
    IamInstanceProfile=Ref(profile),
    SecurityGroupIds=[
        ImportValue(
            Sub("${NetworkStack}-SecurityGroupPublic")
        ),
        ImportValue(
            Sub("${DbStack}-ClientSG")
        )
    ],
    SubnetId=ImportValue(
        Sub("${NetworkStack}" + "-PublicSubnet{}".format(0))
    ),
    UserData=userdata

))

ip = t.add_resource(ec2.EIP(
    "ip",
    Domain="vpc",
    InstanceId=Ref(instance)
))

print t.to_json()
