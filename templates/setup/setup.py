
from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError


class Setup(TemplateBase):

    version = '0.0.1'
    template_name = "setup"

    ZERO_TEMPLATES = 'https://github.com/openvcloud/0-templates.git'
    K8S_TEMPLATES = 'https://github.com/openvcloud/kubernetes.git'

    SSHKEY_TEMPLATE = 'github.com/openvcloud/0-templates/sshkey/0.0.1'
    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
    ACCOUNT_TEMPLATE = 'github.com/openvcloud/0-templates/account/0.0.1'
    VDC_TEMPLATE = 'github.com/openvcloud/0-templates/vdc/0.0.1'
    NODE_TEMPLATE = 'github.com/openvcloud/0-templates/node/0.0.1'
    ZROBOT_TEMPLATE = 'github.com/openvcloud/0-templates/zrobot/0.0.1'

    ZOS_NODE_TEMPLATE = 'github.com/openvcloud/kubernetes/zos_node/0.0.1'
    K8S_TEMPLATE = 'github.com/openvcloud/kubernetes/kubernetes/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        self._config = None

    def validate(self):
        for key in ['vdc', 'workers', 'sshKey', 'zerotierToken', 'zerotierId']:
            if not self.data[key]:
                raise ValueError('"%s" is required' % key)

    @property
    def config(self):
        '''
        returns an object with names of vdc, account, and ovc
        '''
        if self._config is not None:
            return self._config

        config = {}
        # traverse the tree up words so we have all info we need to return, connection and
        # account
        vdc_proxy = self.api.services.get(template_uid=self.VDC_TEMPLATE, name=self.data['vdc'])
        vdc_info = vdc_proxy.schedule_action('get_info').wait(die=True).result
        config['vdc'] = vdc_info['name']

        acc_proxy = self.api.services.get(template_uid=self.ACCOUNT_TEMPLATE, name=vdc_info['account'])
        acc_info = acc_proxy.schedule_action('get_info').wait(die=True).result
        config['account'] = acc_info['name']

        ovc_proxy = self.api.services.get(template_uid=self.OVC_TEMPLATE, name=acc_info['openvcloud'])
        ovc_info = ovc_proxy.schedule_action('get_info').wait(die=True).result
        config['ovc'] = ovc_info['name']

        self._config = config
        return self._config

    def _ensure_helper(self):
        """ create helper zos machine, return zrobot object """

        # get ZeroTier client
        zerotier_instance = 'kubernetes_zerotier'
        j.clients.zerotier.get(zerotier_instance, {'token_': self.data['zerotierToken']})

        name = '%s-helper' % self.name
        #name = 'zosnodeDev'
        node = self.api.services.find_or_create(
            template_uid=self.ZOS_NODE_TEMPLATE,
            service_name=name,
            data={
                'name': name,
                'vdc': self.data['vdc'],
                'zerotierId': self.data['zerotierId'],
                'organization': self.data['organization'],
                'zerotierClient': zerotier_instance,
            }
        )

        node.schedule_action('install').wait(die=True)
        node_info = node.schedule_action('get_info').wait(die=True).result

        # error if itsyou.online client instance is not configured
        iyo_client = j.clients.itsyouonline.get(instance='main', create=False)
        memberof_scope = "user:memberof:{}".format(self.data['organization'])
        jwt = iyo_client.jwt_get(scope=memberof_scope, refreshable=True)

        # connect to robot on helper machine
        bot_name = '%s-bot' % self.name
        def_robot_port = '6600'
        url = '{}:{}'.format(node_info['zerotierPublicIP'], def_robot_port)
        zrobot_data = {'jwt_': jwt, 'url': url}
        j.clients.zrobot.get(instance=bot_name, data=zrobot_data)
        bot = j.clients.zrobot.robots[bot_name]

        # load templates to the k8s robot
        bot.templates.add_repo(self.ZERO_TEMPLATES)

        # TESTING: branch = update
        bot.templates.add_repo(self.K8S_TEMPLATES, branch='update')
        import ipdb; ipdb.set_trace()

        return bot

    def _deploy_k8s(self, zrobot):
        """ Schedule deployment of kubernetes cluster

            :param zrobot: 0-robot instance
            return value: credentials of kubernetes cluster.
        """

        ovc_client = j.clients.openvcloud.get(self.config['ovc'], create=False)
        k8s = zrobot.services.find_or_create(
            template_uid=self.K8S_TEMPLATE,
            service_name=self.name,
            data={
                'workersCount': self.data['workers'],
                'sizeId': self.data['sizeId'],
                'dataDiskSize': self.data['dataDiskSize'],
                'vdc': self.config['vdc'],
                'account': self.config['account'],
                'ovcConnect': {
                    'location': ovc_client.config.data['location'],
                    'address': ovc_client.config.data['address'],
                    'port': ovc_client.config.data['port'],
                    'token': ovc_client.config.data['jwt_']
                }
            }
        )

        credentials = k8s.schedule_action('install').wait(die=True).result

        return credentials

    def install(self):
        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass

        import ipdb; ipdb.set_trace()
        zrobot = self._ensure_helper()
        #bot = self._ensure_zrobot(helper)
        #zrobot = self.api.robots[bot.name]

        import ipdb; ipdb.set_trace()
        #self._mirror_services(zrobot)
        self.data['credentials'] = self._deploy_k8s(zrobot)

        # next step, make a deployment
        self.state.set('actions', 'install', 'ok')
