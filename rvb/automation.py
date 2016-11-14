from troposphere import (
    Ref, Join, Base64
)
from troposphere.cloudformation import (
    Metadata, Init, InitConfigSets, InitConfig
)


def userdata_file_path(name):
    return name + '.sh'


def metadata(backup_bucket, mount_point, mount_cmd, **kwargs):
    config_sets = ['prepare', 'mount', 'start']
    return Metadata(
        Init(
            InitConfigSets(default=config_sets),
            prepare=InitConfig(
                packages={
                    'rpm': {
                        'go-server': 'https://download.go.cd/binaries/16.10.0-4131/rpm/go-server-16.10.0-4131.noarch.rpm',
                        'go-agent': 'https://download.go.cd/binaries/16.10.0-4131/rpm/go-agent-16.10.0-4131.noarch.rpm'
                    },
                    'yum': {
                        'go-server': [],
                        'go-agent': [],
                        'nfs-utils': [],
                        'git': []
                    }
                },


                commands={
                    'create_mount_point': {
                        'command': "mkdir -p {}".format(mount_point),
                        'env': {
                            "PATH": "/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:/opt/aws/bin:/root/bin"
                        }
                    },
                }
            ),

            mount=InitConfig(

                commands={
                    'chmod': {
                        'command': 'chmod 755 {0}'.format(mount_point),
                        'env': {
                            "PATH": "/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:/opt/aws/bin:/root/bin"
                        }
                    },
                    'mount': {
                        'command': mount_cmd,
                        'env': {
                            "PATH": "/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:/opt/aws/bin:/root/bin"
                        }
                    }
                }
            ),
            #restore=InitConfig(
            #
            #),
            start=InitConfig(
                services={
                    'sysvinit': {
                        "go-server": {
                            "enabled": "true",
                        },
                        "go-agent": {
                            "enabled": "true",
                        }

                    },
                }
            )
        )
    )


def userdata_from_file(userdata_file, parameters=None, references=None,
                       constants=None):
    """
    creates userdata for troposphere and cloudinit
    inserts `parameters` at the top of the script

    :type parameters: list
    :param parameters: list of troposphere.Parameters()

    :type references
    :param parameters: list of troposphere.Ref()

    :type constants
    :param constants: list of tuple(key, value)

    :rtype: troposphere.Base64()
    :return: troposphere ready to consume userdata
    """
    userdata = ['#!/bin/bash\n']
    if parameters is None:
        parameters = []

    if references is None:
        references = []

    if constants is None:
        constants = []

    for param in parameters:
        variable_name = param.title
        userdata = userdata + [variable_name] + ['='] + [Ref(param)] + ['\n']

    for ref in references:
        # Create variable name from Ref function
        # Example: {"Ref": "AWS::Region"} -> AWSRegion
        variable_name = ref.data['Ref'].replace('::', '')
        userdata = userdata + [variable_name] + ['='] + [ref.data] + ['\n']

    for constant in constants:
        userdata = userdata + [constant[0]] + ['='] + [constant[1]] + ['\n']

    # append the actial file
    with open(userdata_file, 'r') as f:
        userdata.extend(f.readlines())

    return Base64(Join('', userdata))
