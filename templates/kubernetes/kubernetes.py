
from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError


class Kubernetes(TemplateBase):

    version = '0.0.1'
    template_name = "kubernetes"

    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
    ACCOUNT_TEMPLATE = 'github.com/openvcloud/0-templates/account/0.0.1'
    VDC_TEMPLATE = 'github.com/openvcloud/0-templates/vdc/0.0.1'
    NODE_TEMPLATE = 'github.com/openvcloud/0-templates/node/0.0.1'
    VDC_TEMPLATE = 'github.com/openvcloud/0-templates/vdc/0.0.1'
    SSHKEY_TEMPLATE = 'github.com/openvcloud/0-templates/sshkey/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

    def validate(self):
        for key in ['vdc', 'account', 'workersCount', 'sshKey']:
            if not self.data[key]:
                raise ValueError('"%s" is required' % key)

        # validate ovc connection entries
        for key in self.data['connection'].keys():
            if not self.data['connection'][key]:
                raise ValueError('"%s" is required' % key)

    def get_info(self):
        """ Fetch data of kubernetes cluster """
        self.state.check('actions', 'install', 'ok')
        return {
            'credentials': self.data['credentials'],
        }


    @property
    def _services(self):
        # define names of services
        return {
            'sshKey': "{}-{}".format(self.name, self.data['sshKey']['name']),
            'ovc': "{}-{}".format(self.name, self.data['connection']['name']),
            'account': "{}-{}".format(self.name, self.data['account']),
            'vdc': "{}-{}".format(self.name, self.data['vdc']),
        }

    def _ensure_services(self, zrobot):
        """ Install services """

        data = self.data
        sshkey = zrobot.services.find_or_create(
            template_uid=self.SSHKEY_TEMPLATE,
            service_name=self._services['sshKey'],
            data=data['sshKey']
        )

        ovc = zrobot.services.find_or_create(
            template_uid=self.OVC_TEMPLATE,
            service_name=self._services['ovc'],
            data={
                'name': data['connection']['name'],
                'address': data['connection']['address'],
                'port': data['connection']['port'],
                'location': data['connection']['location'],
                'token': data['connection']['token'],
            }
        )

        account = zrobot.services.find_or_create(
            template_uid=self.ACCOUNT_TEMPLATE,
            service_name=self._services['account'],
            data={
                'name': data['account'],
                'openvcloud': self._services['ovc'],
                'create': False,
            }
        )

        vdc = zrobot.services.find_or_create(
            template_uid=self.VDC_TEMPLATE,
            service_name=self._services['vdc'],
            data={
                'name': data['vdc'],
                'account': self._services['account'],
                'create': False,
            }
        )

        # install services
        for service in [ovc, account, vdc, sshkey]:
            service.schedule_action('install').wait(die=True)


    def _ensure_nodes(self, zrobot):
        # create master node and worker nodes
        nodes = []
        tasks = []
        for index in range(self.data['workersCount'] + 1):
            name = '%s-worker-%d' % (self.name, index)
            size_id = self.data['workerSizeId']
            disk_size = self.data['dataDiskSize']

            if index == 0:
                name = '{}-master'.format(self.name)
                size_id = self.data['masterSizeId']

            node = zrobot.services.find_or_create(
                template_uid=self.NODE_TEMPLATE,
                service_name=name,
                data={
                    'name': name,
                    'vdc': self._services['vdc'],
                    'sshKey': self._services['sshKey'],
                    'sizeId': size_id,
                    'dataDiskSize': disk_size,
                    'managedPrivate': True,
                },
            )

            task = node.schedule_action('install')
            tasks.append(task)
            nodes.append(name)

        for task in tasks:
            task.wait(die=True)

        self.data['masters'] = [nodes[0]]
        self.data['workers'] = nodes[1:]

    @property
    def external_ip(self):
        vdc = self.api.services.get(template_uid=self.VDC_TEMPLATE, name=self._services['vdc'])
        return vdc.schedule_action('get_info').wait(die=True).result['public_ip']

    def install(self):
        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass

        # this templates will only use the private prefab, it means that the nodes
        # on this service must be installed with managedPrivate = true
        # that's exactly what the `setup` template will do.
        self._ensure_services(self.api)
        self._ensure_nodes(self.api)

        masters = [j.tools.nodemgr.get('%s_private' % name).prefab for name in self.data['masters']]
        workers = [j.tools.nodemgr.get('%s_private' % name).prefab for name in self.data['workers']]

        prefab = j.tools.prefab.local
        
        self.data['credentials'] = prefab.virtualization.kubernetes.multihost_install(
            masters=masters,
            nodes=workers,
            external_ips=[self.external_ip],
        )
        
        if not self.data['credentials']:
            raise RuntimeError('Something went wrong: kubernetes cluster credentials were not returned. Check if the cluster was not already installed previously')

        self.state.set('actions', 'install', 'ok')

    def uninstall(self):
        """ Uninstall kubernetes cluster """
        # delete nodes
        for nodes in ['masters', 'workers']:
            while self.data[nodes]:
                node = self.data[nodes].pop()
                service = self.api.services.get(name=node)
                service.schedule_action('uninstall').wait(die=True)
                service.delete()

        # uninstall created services
        for service_name in self._services:
            service = self.api.services.find(name=service_name)
            if service:
                service[0].delete()
        
        self.data['credentials'] = None
        self.state.delete('actions', 'install')




