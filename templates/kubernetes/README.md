# github.com/openvcloud/kubernetes/kubernetes/0.0.1

## Description
Template is responsible to manage kubernetes cluster locally. Since nodes of the k8s cluster are managed privatly, Kubernetes service has to run on a helper machine at the same VDC where k8s cluster is being deployed.

## Schema

* `vdc` - VDC name. **Required**.
* `account` - Account name. **Required**.
* `connection` - OpnevCloud connection data. **Required**.
    Fields of the struct of type `Connection`:
        * `name` - instance name
        * `address` - OVC address (URL)
        * `token` - IYO Token
        * `location` - Location
        * `port` - OpenvCloud port
* `sshKey` - ssh-key that will be uploaded to the kubernetes VMs. **Required**.
    Fields of the struct of type `SshKey`:
        * `name` - name of the ssh-key
        * `passphrase` - passhrase at least 5 characters long
* `description` - Claster description. **Optional**.
* `masterSizeId` - Size ID of a master machine. Default to 2.
* `workerSizeId` -  Size ID of a worker machine. Default to 2.
* `dataDiskSize` - Size of data disk in GB. Default to 10.
* `workersCount` - Number of worker machines. Default to 1.
* `masters` - List of master machines. **Autofilled**.
* `workers` - List of worker machines.  **Autofilled**.
* `credentials` - Kubernetes credentials.  **Autofilled**.

## Actions

* `install` - action installs kubernetes cluster and save credentials in schema. The following steps:

  * create and install services required to access [openvcloud](https://github.com/openvcloud/0-templates/tree/master/templates/openvcloud) environment, [account](https://github.com/openvcloud/0-templates/tree/master/templates/openvcloud), and [VDC](https://github.com/openvcloud/0-templates/tree/master/templates/account)
  * Create master and worker nodes and install cluster.
  * Return credentials of the kubernetes cluster as a result of the action.
* `get_info` - get kubernetes cluster credentials.
* `uninstall` - uninstall kubernetes cluster, delete master and workers machines.

## Usage examples via the 0-robot DSL

``` python
from zerorobot.dsl import ZeroRobotAPI
api = ZeroRobotAPI.ZeroRobotAPI()
robot = api.robots['main']

# create services
kubernetes = robot.services.create(
    template_uid="github.com/openvcloud/kubernetes/kubernetes/0.0.1",
    service_name="k8s",
    data={
        'workersCount': 1,
        'sizeId': 2,
        'dataDiskSize': 10,
        'vdc': 'vdc_name',
        'account': 'account_name',
        'sshKey': {
            'name': 'k8s_id',
            'passphrase': '12345'
        },
        'connection': {
            'name': 'ovc',
            'location':  'be-gen-demo',
            'address': 'be-gen-demo.greenitglobe.com',
            'port': 443,
            'token': '<token>',
    }
)
kubernetes.schedule_action('install')
# get credentials
credentials = kubernetes.schedule_action('get_info').wait().result

# uninstall cluster
kubernetes.schedule_action('uninstall')
```

## Usage examples via the 0-robot CLI

``` yaml
services:
    - github.com/openvcloud/kubernetes/kubernetes/0.0.1_k8s:
        workersCount: 1
        sizeId: 2
        dataDiskSize: 10,
        vdc: vdc_name
        account: account_name
        sshKey:
            name: k8s_id
            passphrase: hard-to-guess-passphrase
        connection:
            name: ovc
            location:  be-gen-demo
            address: be-gen-demo.greenitglobe.com
            port: 443
            token: <token>
actions:
    - actions: ['install']
```

``` yaml
actions:
    - service: k8s
      actions: ['uninstall']
```
