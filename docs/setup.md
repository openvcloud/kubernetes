# Deploying Kubernetes using the 0-templates for Kubernetes

First step is to create two private Git repositories:
- Zero-Robot data repository
- JumpScale configuration repository

Make sure to initialize them.

Copy the SSH address of all Git repositories in environment variables:
```bash
config_repo="ssh://git@docs.greenitglobe.com:10022/yves/jsconfig.git"
data_repo="ssh://git@docs.greenitglobe.com:10022/yves/robotdata.git"
template_repo_openvcloud="https://github.com/openvcloud/0-templates.git"
template_repo_kubernetes="https://github.com/openvcloud/kubernetes.git"
template_repos_all="https://github.com/openvcloud/0-templates.git,https://github.com/openvcloud/kubernetes.git"
```

If not already done, create a SSH key:
```bash
ssh-keygen -t rsa -f ~/.ssh/id_rsa -P ''
```

If not already done, start ssh-agent and load the SSH key:
```
eval `ssh-agent`
ssh-add ~/.ssh/id_rsa
```

Make sure that this SSH key is associated with your user account on the Git server where you created the 0-robot data and config repositories.

Get the internal IP address of your host into an environment variable:
```bash
internal_ip_address="$(ip route get 8.8.8.8 | awk '{print $NF; exit}')"
```

Next you have two options:
- [Start the Zero-Robot on your host](#host)
- [Start the Zero-Robot in a Docker container](#docker)

Once done, you will have your Zero-Robot [execute the 0-blueprints](#blueprints).


<a id="host"></a>
## Start the Zero-Robot on your host

On your host machine make sure you have JumpScale installed using the [JumpScale Bash utilities](https://github.com/Jumpscale/bash):
```bash
export ZUTILSBRANCH="development"
export JS9BRANCH="development"
curl https://raw.githubusercontent.com/Jumpscale/bash/${ZUTILSBRANCH}/install.sh?$RANDOM > /tmp/install.sh
bash /tmp/install.sh
source ~/.bashrc
ZInstall_host_js9_full
```

Alternatively you can use the [Jumpscale installation script](https://github.com/Jumpscale/0-robot/blob/master/utils/scripts/jumpscale_install.sh) from the [Jumpscale/0-robot](https://github.com/Jumpscale/0-robot) repository, this script also creates a new SSH key and initializes your configuration manager.

Clone the 0-robot repository:
```bash
cd /opt/code/github/jumpscale
git clone git@github.com:Jumpscale/0-robot.git
```

Install Zero-Robot and all dependencies:
```bash
cd /opt/code/github/jumpscale/0-robot
export ZROBOTBRANCH="master"
git checkout $ZROBOTBRANCH
pip install -r requirements.txt
pip install .
```

Start Zero-Robot:
```bash
#zrobot server start --data-repo $data_repo --config-repo $config_repo --template-repo $template_repo_openvcloud -template-repo $template_repo_kubernetes --auto-push --auto-push-interval 30
zrobot server start -D $data_repo -C $config_repo -T $template_repo_openvcloud -T $template_repo_kubernetes --auto-push --auto-push-interval 30
```

Next, have your Zero-Robot execute the 0-blueprints, as documented [below](#blueprints).


<a id="docker"></a>
## Start the Zero-Robot in a Docker container

The Docker image for Zero-Robot is available from [Docker Hub]()https://hub.docker.com/: [jumpscale/0-robot](https://hub.docker.com/r/jumpscale/0-robot/).

The JumpScale script to create this image is available in the 0-robot repository: [dockerbuild.py](https://github.com/Jumpscale/0-robot/blob/master/utils/scripts/packages/dockerbuild.py)

First make sure you have Docker installed on your host. If you have JumpScale installed, installing Docker using the JumpScale interactive shell is easy:
Install Docker:
```python
j.tools.prefab.local.virtualization.docker.install()
```

Create a container:
```bash
port_forwarding="$internal_ip_address:8000:6600"

#docker run --name zrobot -e data_repo=$data_repo -e config_repo=$config_repo -e template_repo=$template_repo_all -p $port_forwarding -v /root/.ssh:/root/.ssh -e auto_push=1 -e auto_push_interval=30 jumpscale/0-robot
docker run --name zrobot -e data_repo=$data_repo -e config_repo=$config_repo -e template_repo=$template_repo_all -p $port_forwarding -v /root/.ssh:/root/.ssh jumpscale/0-robot
```

In the above approach we mount `/root/.ssh`, making your SSH keys available in the Docker container. When the container starts it will check for `id_rsa.pub`. If it finds `id_rsa.pub` 0-robot will use this key to push to your data and configuration repositories, so make sure that this key is registered on your Git server.

In case you don't mount `/root/.ssh`, the container will generate a new `ìd_rsa` key and exit with the value of `id_rsa.pub`. Register this public key in your Git server, so 0-robot can push changes to your data and configuration repositories. Once done so, start the container:
```bash
docker start zrobot
```

Next, have your Zero-Robot execute the 0-blueprints, as documented [below](#blueprints).


<a id="blueprints"></a>
## Execute the 0-blueprints


In order to use the `zdocker` command line tool from the host you first need to clone the 0-robot repository - already done when the 0-robot is running on the host:
```bash
cd /opt/code/github/jumpscale
git clone git@github.com:Jumpscale/0-robot.git
```

Then install 0-robot - all ready done when running the 0-robot directly on the host:
```bash
cd /opt/code/github/jumpscale/0-robot
pip install -e .
```

From the host, connect to the 0-robot - in case the 0-robot runs in the Docker container:
```bash
zrobot robot connect main http://$internal_ip_address:6600
```

Or in case the 0-robot runs in a Docker container:
```bash
zrobot robot connect main http://$internal_ip_address:8000
```

Check:
```bash
zrobot robot list
zrobot robot current
```

Create the blueprint `bp.yaml`:
```bash
mkdir /opt/var/blueprints
cd /opt/var/blueprints
vim bp.yaml
```

Here is the blueprint:
```yaml
services:
    - github.com/openvcloud/0-templates/openvcloud/0.0.1__be-gen-1:
        address: 'be-gen-1.demo.greenitglobe.com'
        location: 'be-gen-1'
        token: 'eyJhbGciOiJFUzM4NCIsInR5cCI6IkpXVCJ9.eyJhenAiOiJlMnpsTi03U0M2N3RhdjN0UlJuZG9VQUd4a1U1IiwiZXhwIjoxNTIxNzk4ODE1LCJpc3MiOiJpdHN5b3VvbmxpbmUiLCJzY29wZSI6WyJ1c2VyOmFkbWluIl0sInVzZXJuYW1lIjoieXZlcyJ9.3_WkvHcCvMDCRCwYy3tnqUnNQRE0OUACKkH57xUqQ5TNgPYF0FVigxFDNcPjrgOXU3ARoz6z1UN2PMaeSxHMRFH2AL8BPxwLVUz0WaP1YfYLzx2My_nYO8Q7obS83sw3'

    - github.com/openvcloud/0-templates/account/0.0.1__gigdevelopers:
        openvcloud: be-gen-1

    - github.com/openvcloud/0-templates/vdcuser/0.0.1__yves:
        openvcloud: be-gen-1
        provider: itsyouonline
        email: yves@gig.tech
        
    - github.com/openvcloud/0-templates/vdc/0.0.1__kuberyves:
        account: gigdevelopers
        location: be-gen-1
        users:
            - name: yves
              accesstype: CXDRAU
    
actions:
    actions: ['install']
```

Execute the blueprint:
```bash
zrobot blueprint execute bp.yaml
```

Check the result:
```bash
zrobot service list
```

Next let's deploy the Kubernetes cluster in the VDC, here's the `kuber.yaml` blueprint:
```yaml
services:
  - github.com/openvcloud/0-templates/sshkey/0.0.1__mykey:
      passphrase: 'helloworld'

  - github.com/openvcloud/kubernetes/setup/0.0.1__k8s:
      vdc: kuberyves
      sshKey: mykey
      workers: 1

actions:
   - template: github.com/openvcloud/kubernetes/setup/0.0.1
     actions: ['install']
```

Execute the blueprint:
```bash
zrobot blueprint execute kuber.yaml
```

List the services:
```bash
zrobot service list
github.com/openvcloud/0-templates/account/0.0.1 - 4e16bfb7-cc05-4469-a2fe-ba9fd687d157 - gigdevelopers
github.com/openvcloud/0-templates/disk/0.0.1 - 1ed597bf-1fcd-49e5-89da-13649ad76db9 - Disk5186
github.com/openvcloud/0-templates/disk/0.0.1 - 39ccf0e1-c0fc-4743-9d9c-13dfd0624a9d - Disk5185
github.com/openvcloud/0-templates/node/0.0.1 - dc80ee7e-51ab-4131-88e0-ec11db6e05ec - k8s-little-helper
github.com/openvcloud/0-templates/openvcloud/0.0.1 - 30d2d0da-dfb0-4dca-b9aa-f4c4655fb1f4 - be-gen-1
github.com/openvcloud/0-templates/sshkey/0.0.1 - 3edf611d-f447-4045-88c3-ea62d0cfaf6c - mykey
github.com/openvcloud/0-templates/vdc/0.0.1 - aa7c9689-1d26-4277-8d30-9ec20f9d5c8a - kuberyves
github.com/openvcloud/0-templates/vdcuser/0.0.1 - 94135d4c-1310-4225-880c-81e0a9f85871 - yves
github.com/openvcloud/0-templates/zrobot/0.0.1 - 446feaf0-7423-41b3-aab8-c43eb4cc250b - k8s-little-bot
github.com/openvcloud/kubernetes/setup/0.0.1 - 15b8c2fa-06fb-49e8-8102-b75fc02db5cb - k8s
```

This will create three virtual machines:
```
worker-1
master
k8s-little-helper
```



