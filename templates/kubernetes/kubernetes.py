
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
        for key in ['vdc', 'workersCount', 'sshKey']:
            value = self.data[key]
            if not value:
                raise ValueError('"%s" is required' % key)

        matches = self.api.services.find(template_uid=self.VDC_TEMPLATE, name=self.data['vdc'])
        if len(matches) != 1:
            raise RuntimeError('found %d vdcs with name "%s"' % (len(matches), self.data['vdc']))

    def _find_or_create(self, zrobot, template_uid, service_name, data):
        found = zrobot.services.find(
            template_uid=template_uid,
            name=service_name
        )

        if len(found) != 0:
            return found[0]

        return zrobot.services.create(
            template_uid=template_uid,
            service_name=service_name,
            data=data
        )

    def _ensure_nodes(self, zrobot):
        # create master node.
        nodes = []
        tasks = []
        for index in range(self.data['workersCount'] + 1):
            name = 'worker-%d' % index
            size_id = self.data['sizeId']
            disk_size = self.data['dataDiskSize']
            ports = []

            if index == 0:
                name = 'master'
                size_id = self.data['masterSizeId']
                ports = [{'source': '6443', 'destination': '6443'}]

            node = self._find_or_create(
                zrobot,
                template_uid=self.NODE_TEMPLATE,
                service_name=name,
                data={
                    'vdc': self.data['vdc'],
                    'sshKey': self.data['sshKey'],
                    'sizeId': size_id,
                    'dataDiskSize': disk_size,
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
        self._ensure_nodes(self.api)

        masters = [j.tools.nodemgr.get('%s_private' % name).prefab for name in self.data['masters']]
        workers = [j.tools.nodemgr.get('%s_private' % name).prefab for name in self.data['workers']]

        prefab = j.tools.prefab.local
        credentials = prefab.virtualization.kubernetes.multihost_install(
            masters=masters,
            nodes=workers,
            external_ips=[self.get_external_ip()],
        )

        self.state.set('actions', 'install', 'ok')
        return credentials
