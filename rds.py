from troposphere import (
    Template, GetAZs, Select, Ref, Parameter, Base64, Export,
    Join, GetAtt, Output, Not, Equals, If, ec2, iam, ImportValue, Sub, rds
)

t = Template()

t.add_description("RDS")
t.add_version("2010-09-09")

existing_db_snapshot = t.add_parameter(Parameter(
    "ExistingDbSnapshot",
    Type="String",
    Description="Existing Db snapshot to restore, leave blank to create a new",
    Default=""
))
db_master_password = t.add_parameter(Parameter(
    "DbMasterPassword",
    Type="String",
    NoEcho=True,
    Default="",
    Description="Password for the database, if you are restoring a snapshot leave this blank"
))
network_stack = t.add_parameter(Parameter(
    "NetworkStack",
    Type="String",
    Description="Network stack name"
))
restore_snapshot = "RestoreSnapshot"

t.add_condition(
    restore_snapshot,
    Not(Equals(Ref(existing_db_snapshot), existing_db_snapshot.Default))
)

security_group_client = t.add_resource(ec2.SecurityGroup(
    "SecurityGroupClient",
    GroupDescription=Sub("Security group for client created by ${AWS::StackName}"),
    VpcId=ImportValue(
        Sub("${NetworkStack}-Vpc")
    ),
))

security_group_db = t.add_resource(
ec2.SecurityGroup(
    "SecurityGroupDb",
    GroupDescription=Sub("Security group for DB created by ${AWS::StackName}"),
    SecurityGroupIngress=[
        ec2.SecurityGroupRule(
            FromPort=3306,
            ToPort=3306,
            IpProtocol="tcp",
            SourceSecurityGroupId=Ref(security_group_client),
        )
    ],
    VpcId=ImportValue(
        Sub("${NetworkStack}-Vpc")
    ),
))

db = t.add_resource(rds.DBInstance(
    "db",
    DeletionPolicy="Snapshot",
    DBSubnetGroupName=ImportValue(
        Sub("${NetworkStack}-DBSubnetGroup")
    ),
    AllocatedStorage=If(
        restore_snapshot,
        Ref("AWS::NoValue"),
        "5"
    ),
    AllowMajorVersionUpgrade=False,
    AutoMinorVersionUpgrade=True,
    BackupRetentionPeriod="3",
    DBInstanceClass="db.t2.micro",
    DBSnapshotIdentifier=If(
        restore_snapshot,
        Ref(existing_db_snapshot),
        Ref("AWS::NoValue")
    ),
    Engine=If(
        restore_snapshot,
        Ref("AWS::NoValue"),
        "mysql"
    ),
    MasterUsername=If(
        restore_snapshot,
        Ref("AWS::NoValue"),
        "master"
    ),
    MasterUserPassword=If(
        restore_snapshot,
        Ref("AWS::NoValue"),
        Ref(db_master_password),
    ),
    MonitoringInterval=0,
    MultiAZ=False,
    VPCSecurityGroups=[
        Ref(security_group_client),
        Ref(security_group_db)
    ]

))

t.add_output(Output(
    "Db",
    Value=Ref(db),
    Export=Export(
        Sub("${AWS::StackName}-Db")
    )
))

t.add_output(Output(
    "DbHost",
    Value=GetAtt(db,"Endpoint.Address"),
    Export=Export(
        Sub("${AWS::StackName}-DbHost")
    )
))

t.add_output(Output(
    "DbPort",
    Value=GetAtt(db,"Endpoint.Port"),
    Export=Export(
        Sub("${AWS::StackName}-DbPort")
    )
))

t.add_output(Output(
    "ClientSG",
    Value=Ref(security_group_client),
    Export=Export(
        Sub("${AWS::StackName}-ClientSG")
    )
))
print t.to_json()