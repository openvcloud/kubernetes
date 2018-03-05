
from js9 import j
import itertools
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError


class Kubernetes(TemplateBase):

    version = '0.0.1'
    template_name = "kubernetes"

    NODE_TEMPLATE = 'github.com/openvcloud/0-templates/node/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

    def validate(self):
        if len(self.data['masters']) == 0:
            raise ValueError('master node(s) are required')

        for vm in itertools.chain(self.data['masters'], self.data['workers']):
            matches = self.api.services.find(template_uid=self.NODE_TEMPLATE, name=vm)
            if len(matches) != 1:
                raise RuntimeError('found %d nodes with name "%s"' % (len(matches), vm))

    def install(self):
        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass

        # this templates will only use the private prefab, it means that the ndoes
        # on this service must be installed with managedPrivate = true
        # that's exactly what the `setup` template will do.

        masters = [j.tools.nodemgr.get('%s_private' % name).prefab for name in self.data['masters']]
        workers = [j.tools.nodemgr.get('%s_private' % name).prefab for name in self.data['workers']]

        prefab = j.tools.prefab.local
        prefab.virtualization.kubernetes.multihost_install(
            masters=masters,
            nodes=workers
        )

        self.state.set('actions', 'install', 'ok')
