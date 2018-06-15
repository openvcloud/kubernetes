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
        self._machine_ = None
        self._zerotier_node_ = None
        self._zerotier_network_ = None

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
            'zerotierPrivateIP': self.data['zerotierPrivateIP'],
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
    def _machine(self):
        """ Return VM object """
        if not self._machine_:
            if self.data['name'] in self.space.machines:
                self._machine_ = self.space.machine_get(name=self.data['name'])

        return self._machine_


    @property
    def _zerotier_network(self):
        if self._zerotier_network_:
            return self._zerotier_network_
        client = j.clients.zerotier.get(self.data['zerotierClient'], create=False)
        self._zerotier_network_ = client.network_get(network_id=self.data['zerotierId'])

        return self._zerotier_network_  


    @property
    def _zerotier_node(self):
        """ Return ZeroTier member object """
        if self._zerotier_node_:
            return self._zerotier_node_

        if self.data['zerotierPraivateIP']:
            # if zerotierPraivateIP is not set in data, node was not added to the network
            return None

        self._zerotier_node_ = self._zerotier_network.member_get(private_ip=self.data['zerotierPraivateIP'])

        return self._zerotier_node_

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
            branch=self.data['branch'],
            dev_mode=self.data['devMode'],
        )
        self._machine_ = vm['openvcloud']
        self._zerotier_node_ = vm['zerotier']

        # fetch vm IP in ZeroTier network
        self.data['zerotierPrivateIP'] = self._zerotier_node.private_ip

        # Get data from the vm
        self.data['ipPrivate'] = self._machine.ipaddr_priv
        self.data['ipPublic'] = self._machine.ipaddr_public
        self.data['machineId'] = self._machine.id

        self.state.set('actions', 'install', 'ok')

    def uninstall(self):
        """ Delete node """

        # delete machine from openvcloud
        if self._machine:
            self._machine.delete()
            self._machine_ = None

        # delete member of zerotier
        if self._zerotier_node:
            self._zerotier_network.member_delete(self._zerotier_node.address)
            self._zerotier_node_ = None
