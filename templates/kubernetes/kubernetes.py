import json
from js9 import j
import itertools
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError


class Kubernetes(TemplateBase):

    version = '0.0.1'
    template_name = "kubernetes"

    NODE_TEMPLATE = 'github.com/openvcloud/0-templates/node/0.0.1'
    SSHKEY_TEMPLATE = 'github.com/openvcloud/0-templates/sshkey/0.0.1'
    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
    ACCOUNT_TEMPLATE = 'github.com/openvcloud/0-templates/account/0.0.1'
    VDC_TEMPLATE = 'github.com/openvcloud/0-templates/vdc/0.0.1'
    NODE_TEMPLATE = 'github.com/openvcloud/0-templates/node/0.0.1'
    SSHKEY = 'k8s_sshkey'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)
        self._master = None
        self._workers = []

    def validate(self):
        for key in ['vdc', 'workers']:
            value = self.data[key]
            if not value:
                raise ValueError('"%s" is required' % key)

    def _find_or_create(self, template_uid, service_name, data):
        found = self.api.services.find(
            template_uid=template_uid,
            name=service_name
        )

        if len(found) != 0:
            return found[0]

        return self.api.services.create(
            template_uid=template_uid,
            service_name=service_name,
            data=data
        )

    def _ensure_nodes(self):
        """
        Find or create master node and workers
        """
        nodes = []
        tasks = []
        for index in range(self.data['workers'] + 1):
            name = 'worker-%d' % index
            if index == 0:
                name = 'master'                
                # portforward for k8s on master vm
                ports = [{'443' : '443'}]
                size_id = self.data['masterSizeId'],
                dataDiskSize = 20
            else:
                ports = []
                size_id = self.data['workerSizeId'],
                dataDiskSize = self.data['workerDataDiskSize']

            node = self._find_or_create(
                template_uid=self.NODE_TEMPLATE,
                service_name=name,
                data={
                    'vdc': self.data['vdc'],
                    'sshKey': self.SSHKEY,
                    'sizeId': size_id,
                    'dataDiskSize': dataDiskSize,
                    'managedPrivate': True,
                    'ports': ports,
                },
            )
            task = node.schedule_action('install')
            tasks.append(task)
            nodes.append(node)

        for task in tasks:
            task.wait()
            if task.state == 'error':
                raise task.eco

        self.data['masters'] = [nodes[0].name]
        self.data['workers'] = [n.name for n in nodes[1:]]
        self.save()
        
        return nodes[0], nodes[1:]

    def _install_k8s_sshkey(self):
        ssh = self._find_or_create(
            template_uid=self.SSHKEY_TEMPLATE,
            service_name=self.SSHKEY,
            data={
                'passphrase': j.data.idgenerator.generatePasswd(20, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
            }
        )
        task = ssh.schedule_action('install')
        task.wait()
        if task.state == 'error':
            raise task.eco

    def install(self):
        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass
        # this templates will only use the private prefab, it means that the nodes
        # on this service must be installed with managedPrivate = true
        # that's exactly what the `setup` template will do.
        
        self._install_k8s_sshkey()
        self._ensure_nodes()

        masters = [j.tools.nodemgr.get('%s_private' % name).prefab for name in self.data['masters']]
        workers = [j.tools.nodemgr.get('%s_private' % name).prefab for name in self.data['workers']]

        prefab = j.tools.prefab.local
        self.data['connectionInfo'] = json.dumps(list(prefab.virtualization.kubernetes.multihost_install(
            masters=masters,
            nodes=workers
        )))
        self.logger.info("connection info %s" % self.data['connectionInfo'])
        
        self.save()
        self.state.set('actions', 'install', 'ok')

    def get_connection_info(self):
        """ Return connection info for k8s cluster """
        return self.data['connectionInfo']        


