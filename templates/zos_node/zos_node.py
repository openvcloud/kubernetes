from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError
from zerorobot.template.decorator import retry


class ZosNode(TemplateBase):

    version = '0.0.1'
    template_name = "zos_node"

    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
    ACCOUNT_TEMPLATE = 'github.com/openvcloud/0-templates/account/0.0.1'
    VDC_TEMPLATE = 'github.com/openvcloud/0-templates/vdc/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        self._config = None
        self._ovc = None
        self._space = None
        self._machine = None
        self._zerotier_node_id = None

    def validate(self):
        """
        Validate service data received during creation
        """
        for key in ['name', 'vdc', 'zerotierId', 'organization', 'zerotierClient']:
            if not self.data[key]:
                raise ValueError('"%s" is required' % key)

    def get_info(self):
        """ Get VM info """
        self.state.check('actions', 'install', 'ok')
        return {
            'name': self.data['name'],
            'id': self.data['machineId'],
            'vdc': self.data['vdc'],
            'zerotierId': self.data['zerotierId'],
            'zerotierPublicIP': self.data['zerotierPublicIP'],
            'organization': self.data['organization']
        }

    @property
    def config(self):
        """
        returns an object with names of vdc, account, and ovc
        """
        if self._config is not None:
            return self._config

        config = {}
        # traverse the tree up words so we have all info we need to return, connection and

        # get vdc proxy
        proxy = self.api.services.get(template_uid=self.VDC_TEMPLATE, name=self.data['vdc'])

        # get vdc info
        vdc_info = proxy.schedule_action(action='get_info').wait(die=True).result
        config['vdc'] = vdc_info['name']

        # get account name
        proxy = self.api.services.get(template_uid=self.ACCOUNT_TEMPLATE,  name=vdc_info['account'])
        account_info = proxy.schedule_action(action='get_info').wait(die=True).result
        config['account'] = account_info['name']

        # get connection instance name
        proxy = self.api.services.get(
            template_uid=self.OVC_TEMPLATE, name=account_info['openvcloud'])
        ovc_info = proxy.schedule_action(action='get_info').wait(die=True).result
        config['ovc'] = ovc_info['name']

        self._config = config
        return self._config

    @property
    def ovc(self):
        """
        An ovc connection instance
        """
        if self._ovc is not None:
            return self._ovc

        self._ovc = j.clients.openvcloud.get(instance=self.config['ovc'])

        return self._ovc

    @property
    def space(self):
        """ Return space object """
        if not self._space:
            account = self.config['account']
            vdc = self.config['vdc']
            self._space = self.ovc.space_get(
                accountName=account,
                spaceName=vdc
            )
        return self._space

    @property
    def machine(self):
        """ Return VM object """
        if not self._machine:
            if self.data['name'] in self.space.machines:
                self._machine = self.space.machine_get(name=self.data['name'])

        return self._machine

    @retry((BaseException),
           tries=5, delay=3, backoff=2, logger=None)
    def install(self):
        """ Install VM """

        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass

        # get new vm
        vm = self.space.create_and_connect_zos_machine(
            name=self.data['name'],
            zerotier_id=self.data['zerotierId'],
            organization=self.data['organization'],
            zerotier_client=self.data['zerotierClient'],
            sizeId=self.data['sizeId'],
            branch=self.data['branch']
        )
        self._machine = vm['openvcloud']

        # fetch vm IP in ZeroTier network
        self.data['zerotierPublicIP'] = 'http://{}'.format(vm['zerotier'].private_ip)

        # Get data from the vm
        self.data['ipPrivate'] = self.machine.ipaddr_priv
        self.data['ipPublic'] = self.machine.ipaddr_public
        self.data['machineId'] = self.machine.id

        self.state.set('actions', 'install', 'ok')
