# github.com/openvcloud/kubernetes/zos_node/0.0.1

## Description

Template is responsible for installing and managing a Zero-os Virtual Machine (VM) in a Virtual Data Center (VDC) of the OpenvCloud environment. The VM is assigned to locally deploy and manage kubernetes cluster. To create service of this type, names of existent account and vdc have to be provided.

## Schema

* `name` - VM name. **Required**.
* `vdc` - VDC name. **Required**.
* `zerotierId` - ZeroTier network ID. **Required**.
* `organization` - [itsyou.online](itsyou.online) organization. **Required**.
* `zerotierClient` - ZeroTier clinet instance name. **Required**.
* `description` - description for the VM. **Optional**.
* `osImage` - OS image. Default to "IPXE Boot".
* `branch` - branch of Zero-os. Default to "master".
* `bootDiskSize` - memory available for the vm in GB. Default to 10.
* `sizeId` - type of VM: defines the number of CPU and memory available for the vm. Default to 2.
* `vCpus` - number of CPUs. **Autofilled**.
* `memSize` - memory in MB. **Autofilled**.
* `machineId` - ID of the VM. **Autofilled**.
* `devMode` - development mode, when set to true the node can be accessed directly. Default to `false`.
* `ipPublic` - public ip of the VM. **Autofilled**.
* `ipPrivate` - private ip of the VM. **Autofilled**.
* `zerotierPraivateIP` - ZeroTier node private IP. **Autofilled**.

## Actions

* `install` - create VM.
* `uninstall` - delete VM.

## Usage examples via the 0-robot DSL

``` py
from zerorobot.dsl import ZeroRobotAPI
api = ZeroRobotAPI.ZeroRobotAPI()
robot = api.robots['main']

# get zerotier client instance
zerotier_instance = 'main'
zerotier_token = '<token>'
j.clients.zerotier.get(zerotier_instance, data={'token_': zerotire_token})

self._helper_node = self.api.services.find_or_create(
    template_uid='github.com/openvcloud/kubernetes/zos_node/0.0.1',
    service_name='test-node',
    data={
        'name': name,
        'vdc': 'vdc-name',
        'zerotierId': '4h45j6k7j3k34j',
        'organization': 'test_organization',
        'zerotierClient': zerotier_instance,
        'branch': 'development',
    }
)
```

## Usage examples via the 0-robot CLI

``` yaml
services:
    - github.com/openvcloud/kubernetes/zos_node/0.0.1__node:
        name: node-test,
        vdc: vdc-name,
        zerotierId: 4h45j6k7j3k34j,
        organization: test_organization,
        zerotierClient: zerotier_instance,
        branch: development,
actions:
    - service: node
      actions: ['install']
```

``` yaml
actions:
    - service: node
      actions: ['uninstall']
```