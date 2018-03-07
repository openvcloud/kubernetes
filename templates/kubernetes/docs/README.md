### Deployment Flow

Installation of the kubernetes cluster is managed by a template [setup]().
Cluster is deployed in a given Virtual Data Center (VDC) and consists of `n+1` nodes: one `master` and `n` `workers`.
Two [`zrobots`]() are emloyed to manage the deployment. `zrobot 1` can be located remotely and assigned to set up a `helper` machine and install second `zrobot` on it. `zrobot 2` manages further kubernetes deployment locally.

Flow of deployment can be presented in the following steps:

1. `zrobot 1` deploys `helper` machine in given `vdc`.
2. `zrobot 1` installs `zrobot 2` in the `helper` with templates: [0-templates](https://github.com/openvcloud/0-templates), [kubernetes](https://github.com/openvcloud/kubernetes).
3. `zrobot 2` deploys `master` node and `worker-1`, ... `worker-n` nodes.
4. `zrobot 2` installs kubernetes on the cluster (`master`, `worker-1` ... `worker-n`)


# Install Kubernetes from Scratch

In order to deploy kubernetes in `vdc` of `openvcloud`:

## **zrobot**
* Make sure you have up-to-date version of [`zrobot`](https://github.com/Jumpscale/0-robot) installed. To learn more about [`zrobot`](https://github.com/Jumpscale/0-robot) see git [repository](https://github.com/Jumpscale/0-robot).
* Prior to starting `zrobot` create a config repository using [`configuration manager`](https://github.com/Jumpscale/) of [`jumpscale`](https://github.com/Jumpscale/core9/blob/dd9a6e29025eeba48c192f30e436828b864c8747/docs/config/configmanager.md) library. The repository will be used to store all private configuration data of `zrobot`.

* Run `zrobot` with [0-templates](https://github.com/openvcloud/0-templates) and [kubernetes](https://github.com/openvcloud/kubernetes)

``` bash
zrobot server start -D https://github.com/test/config_repo.git -L :6000 -T git@github.com:openvcloud/kubernetes.git -T git@github.com:openvcloud/0-templates.git
```

* Adjust blueprint for the deployment
``` yaml
services:
    - github.com/openvcloud/0-templates/sshkey/0.0.1__keyName:
        dir: '/root/.ssh/'          # directory where ssh-key is found/created
        passphrase: testpassphrase  # passphrase for ssh-key <keyName>
    - github.com/openvcloud/0-templates/openvcloud/0.0.1__ovcConnection: # creates insnance in config manager
        location: be-gen                        # environment where VDC is deployed
        address: 'be-gen.demo.greenitglobe.com' # address of OCV
        token: <token>                          # IYO token
    - github.com/openvcloud/0-templates/vdcuser/0.0.1__ekaterina_evdokimova_1:
        openvcloud: ovcConnection   # name of the ovcConnection (must agree with name of the service running)
        provider: itsyouonline      # provider
        email: address@gig.tech   # email registered in itsyouonline
    - github.com/openvcloud/0-templates/account/0.0.1__accountName:
        openvcloud: ovcConnection
        users:          # list of users required to have access to account
            - name: ekaterina_evdokimova_1
              accesstype: CXDRAU           
    - github.com/openvcloud/0-templates/vdc/0.0.1__vdcName:
        account: accountName
        openvcloud: ovcConnection
        users:          # list of users required to have access to vdc
          - name: user_name
            accesstype: CXDRAU                      
    - github.com/openvcloud/kubernetes/setup/0.0.1__k8s:
        vdc: vdcName   # name of the vdc (must agree with name of the service running)
        sshKey: keyName # name of the ssh-key to secure ssh-connection with `helper` node
        workers: 1          # number of nodes of type "worker-?"
actions: # list of actions to execute
    - template: github.com/openvcloud/kubernetes/setup/0.0.1 # name of the template
      actions: ['install']      # action
```
