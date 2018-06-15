# github.com/openvcloud/kubernetes/setup/0.0.1

## Description

Setup template triggers deployment of a kubernetes cluster in one of the Virtual Data Centers (VDC) on the OpenvCloud environment. The template is responsible for the following tasks:

* Create a helper virtual machine (VM) on the VDC with running [0-robot](https://github.com/zero-os/0-robot). The VM is assigned to create and manage cluster nodes locally.
* Ensure [0-robot](https://github.com/zero-os/0-robot) to have loaded and updated 0-[templates](https://github.com/openvcloud/0-templates) and [kubernetes](https://github.com/openvcloud/kubernetes) templates of the [openvcloud repo](https://github.com/openvcloud/).
* Create and install [service responsible for creating and loading ssh-key](https://github.com/openvcloud/0-templates/tree/master/templates/sshkey). Generated ssh-key will allow helper machine access to the kubernetes VMs.
* Trigger deployment of the kubernetes VMs by creating and installing a service of type [github.com/openvcloud/kubernetes/kubernetes/0.0.1](https://github.com/openvcloud/kubernetes/tree/master/templates/kubernetes). Credentials of the kubernetes cluster are returned as a result of action `install` scheduled on the [kubernetes](https://github.com/openvcloud/kubernetes/tree/master/templates/kubernetes) service.

## Schema

* `vdc` - name of VDC chosen for kubernetes cluster. **Required**.
* `zerotierId` - zerotier network ID. **Required**.
* `organization` - itsyou.online organization. **Required**.
* `zerotierToken` - ZeroTier authentification token. **Required**.
* `workersCount` - number of workers machines. **Required**.
* `sshKey` - sshkey name and passphrase to access workers from k8s cluster. **Required**.
* `description` - description of the kubernates cluster. **Optional**.
* `sizeId` - sizeId of the worker machines. Default to 6.
* `dataDiskSize` - disk size of the worker machine (per size). Default to 10.
* `branch` - branches of repo's required for the deployment (by default all branches are set to `master`):

  * `zos`: branch of [Zero-os](https://github.com/zero-os);
  * `zeroTemplates`: branch of [0-templates](https://github.com/openvcloud/0-templates) of OpenvCloud;
  * `kubernetes`: branch of [0-templates](https://github.com/openvcloud/kubernates) templates of OpenvCloud.
* `credentials` - cluster credentials returned. **Autofilled**.

## Actions

* `install` - deploy kubernetes cluster.
* `get_info` - get kubernetes cluster credentials.
* `uninstall` - uninstall kubernetes cluster, delete created VMs.

## Usage examples via the 0-robot DSL

``` py
from zerorobot.dsl import ZeroRobotAPI
api = ZeroRobotAPI.ZeroRobotAPI()
robot = api.robots['main']

# create required services
ovc = robot.services.create(
    template_uid="github.com/openvcloud/0-templates/openvcloud/0.0.1",
    service_name="ovc",
    data={'name': 'ovc_instance',
          'location':'be-gen-demo', 
          'address': 'ovc.demo.greenitglobe.com',
          'token': '<iyo jwt token>'}
)
ovc.schedule_action('install')

account = robot.services.create(
    template_uid="github.com/openvcloud/0-templates/account/0.0.1",
    service_name="account",
    data={'name': 'account_name',
          'openvcloud':'ovc_service'}
)
account.schedule_action('install')

vdc = robot.services.create(
    template_uid="github.com/openvcloud/0-templates/vdc/0.0.1",
    service_name="vdc",
    data={'name': 'vdc_name' ,
          'account':'account'}
)
vdc.schedule_action('install')

setup_kubernetes = robot.services.create(
    template_uid="github.com/openvcloud/kubernetes/setup/0.0.1",
    service_name="kubernetes",
    data={'name': 'k8s_cluster',
            'vdc': 'vdc',
            'workersCount': 1,
            'zerotierToken': '<token>',
            'zerotierId': 'c7c7c7c7c',
            'organization': 'test_organisation',
            'sshKey':{
                'name': 'k8s_id',
                'passphrase': 'testpass'
            }
)
# deploy cluster
setup_kubernetes.schedule_action('install')

# get credentials
credentials = setup_kubernetes.schedule_action('get_info').wait().result

# uninstall cluster
setup_kubernetes.schedule_action('uninstall')

```

## Usage examples via the 0-robot CLI

``` yaml
services:
    - github.com/openvcloud/0-templates/openvcloud/0.0.1__ovc:
        name: ovc_instance
        location: be-gen-demo
        address: ovc.demo.greenitglobe.com
        token: '<jwt_token>'
    - github.com/openvcloud/0-templates/account/0.0.1__account:
        name: account_name
        openvcloud: ovc
    - github.com/openvcloud/0-templates/vdc/0.0.1__vdc:
        name: vdc_name
        account: account
    - github.com/openvcloud/kubernetes/setup/0.0.1__setup:
        vdc: vdc
        workersCount: 1
        zerotierToken: '<token>'
        zerotierId: c7c7c7c7c
        organization: test_organisation
        sshKey:
            name: k8s_id
            passphrase: testpass
actions:
    - actions: ['install']
      service: ovc
    - actions: ['install']
      service: account
    - actions: ['install']
      service: vdc
    - actions: ['install']
      service: setup
```

``` yaml
actions:
    - service: setup
      actions: ['uninstall']
```
