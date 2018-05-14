
from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError


class Kubernetes(TemplateBase):

    version = '0.0.1'
    template_name = "kubernetes"

    NODE_TEMPLATE = 'github.com/openvcloud/0-templates/node/0.0.1'
    VDC_TEMPLATE = 'github.com/openvcloud/0-templates/vdc/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

    def validate(self):
        import ipdb; ipdb.set_trace()
        for key in ['vdc', 'account', 'workersCount', 'sshKey']:
            if not self.data[key]:
                raise ValueError('"%s" is required' % key)

        # validate ovc connection entries
        for key in self.data['ovcConnect'].keys():
            if not self.data['ovcConnect']['key']:
                raise ValueError('"%s" is required' % key)
                
    def _ensure_services(self, zrobot):
        """ Install services """

        data = self.data

        # define names of services
        service_names = {
            'sshkey': "{}-{}".format(self.name, data['sshKey']),
            'ovc': "{}-{}".format(self.name, data['ovcConnect']['name']),
            'account': "{}-{}".format(self.name, data['account']),
            'vdc': "{}-{}".format(self.name, data['vdc']),
        }

        sshkey = zrobot.services.find_or_create(
            template_uid=self.SSHKEY_TEMPLATE,
            service_name=service_names['sshkey'],
            data={
                'name': data['sshkey'],
                'passphrase': j.data.idgenerator.generatePasswd(20, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
            }
        )

        ovc = zrobot.services.find_or_create(
            template_uid=self.OVC_TEMPLATE,
            service_name=service_names['ovc'],
            data={
                'name': data['ovcConnect']['name'],
                'address': data['ovcConnect']['address'],
                'port': data['ovcConnect']['port'],
                'location': data['ovcConnect']['location'],
                'token': data['ovcConnect']['token'],
            }
        )
        account = zrobot.services.find_or_create(
            template_uid=self.ACCOUNT_TEMPLATE,
            service_name=service_names['account'],
            data={
                'name': data['account'],
                'openvcloud': service_names['ovc'],
                'create': False,
            }
        )

        vdc = zrobot.services.find_or_create(
            template_uid=self.VDC_TEMPLATE,
            service_name=service_names['vdc'],
            data={
                'name': data['vdc'],
                'account': service_names['account'],
                'create': False,
            }
        )

        # install services
        for service in [ovc, account, vdc, sshkey]:
            service.schedule_action('install').wait(die=True)

    def _ensure_nodes(self, zrobot):
        # create master node.
        nodes = []
        tasks = []
        for index in range(self.data['workersCount'] + 1):
            name = '%s_worker-%d' % (self.name, index)
            size_id = self.data['workerSizeId']
            disk_size = self.data['dataDiskSize']

            if index == 0:
                name = '{}_master'.format(self.name)
                size_id = self.data['masterSizeId']
                #ports = [{'source': '6443', 'destination': '6443'}]

            node = zrobot.find_or_create(
                template_uid=self.NODE_TEMPLATE,
                service_name=name,
                data={
                    'name': name,
                    'vdc': self.data['vdc'],
                    'sshKey': self.data['sshKey'],
                    'sizeId': size_id,
                    'dataDiskSize': disk_size,
                    'managedPrivate': True,
                },
            )

            task = node.schedule_action('install')
            tasks.append(task)
            nodes.append(node)

        for task in tasks:
            task.wait(die=True)

        self.data['masters'] = [nodes[0].name]
        self.data['workers'] = [node.name for node in nodes[1:]]

    def get_external_ip(self):
        matches = self.api.services.find(template_uid=self.VDC_TEMPLATE, name=self.data['vdc'])
        if len(matches) != 1:
            raise RuntimeError('found %d vdcs with name "%s"' % (len(matches), self.data['vdc']))
        vdc = matches[0]
        task = vdc.schedule_action('get_public_ip')
        task.wait()

        return task.result

    def install(self):
        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass

        # this templates will only use the private prefab, it means that the ndoes
        # on this service must be installed with managedPrivate = true
        # that's exactly what the `setup` template will do.

        import ipdb; ipdb.set_trace()        
        self._ensure_services(self.api)
        self._ensure_nodes(self.api)

        masters = [j.tools.nodemgr.get('%s_private' % name).prefab for name in self.data['masters']]
        workers = [j.tools.nodemgr.get('%s_private' % name).prefab for name in self.data['workers']]

        prefab = j.tools.prefab.local
        credentials = prefab.virtualization.kubernetes.multihost_install(
            masters=masters,
            nodes=workers,
            external_ips=[self.get_external_ip()],
        )

        self.data['credentials'] = credentials
        self.state.set('actions', 'install', 'ok')
        return credentials
