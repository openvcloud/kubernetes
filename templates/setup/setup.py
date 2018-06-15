
import time
from requests.exceptions import ConnectionError
from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError


class Setup(TemplateBase):

    version = '0.0.1'
    template_name = "setup"

    ZERO_TEMPLATES_REPO = 'https://github.com/openvcloud/0-templates.git'
    K8S_TEMPLATES_REPO = 'https://github.com/openvcloud/kubernetes.git'

    K8S_TEMPLATE = 'github.com/openvcloud/kubernetes/kubernetes/0.0.1'    
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
        self._k8s = None
        self._helper_node = None
        self._helper_bot = None

        # bind uninstall action to the delete method
        #self.add_delete_callback(self.uninstall)

    def validate(self):
        for key in ['vdc', 'workersCount', 'sshKey', 'zerotierToken', 'zerotierId', 'organization']:
            if not self.data[key]:
                raise ValueError('"%s" is required' % key)

    def get_info(self):
        """ Get kubernetes cluster credentials"""
        self.state.check('actions', 'install', 'ok')
        return {
            'credentials': self.data['credentials'],
        }

    @property
    def config(self):
        '''
        returns an object containing names of vdc, account, and ovc
        '''
        if self._config is not None:
            return self._config

        config = {}

        # fetch vdc name
        vdc_proxy = self.api.services.get(template_uid=self.VDC_TEMPLATE, name=self.data['vdc'])
        vdc_info = vdc_proxy.schedule_action('get_info').wait(die=True).result
        config['vdc'] = vdc_info['name']

        # fetch account name
        acc_proxy = self.api.services.get(template_uid=self.ACCOUNT_TEMPLATE, name=vdc_info['account'])
        acc_info = acc_proxy.schedule_action('get_info').wait(die=True).result
        config['account'] = acc_info['name']

        # fetch connection name
        ovc_proxy = self.api.services.get(template_uid=self.OVC_TEMPLATE, name=acc_info['openvcloud'])
        ovc_info = ovc_proxy.schedule_action('get_info').wait(die=True).result
        config['ovc'] = ovc_info['name']

        self._config = config
        return self._config

    def _ensure_helper_node(self):
        """ create helper zos machine, return zrobot object """

        # get ZeroTier client
        zerotier_instance = 'kubernetes_zerotier'
        j.clients.zerotier.get(zerotier_instance, {'token_': self.data['zerotierToken']})

        # add kubernetes service name to the machine name substituting spaces and underscores
        name = '%s-helper' % self.name.replace(' ','-').replace('_', '-')

        self._helper_node = self.api.services.find_or_create(
            template_uid=self.ZOS_NODE_TEMPLATE,
            service_name=name,
            data={
                'name': name,
                'vdc': self.data['vdc'],
                'zerotierId': self.data['zerotierId'],
                'organization': self.data['organization'],
                'zerotierClient': zerotier_instance,
                'branch': self.data['branch']['zos'] or 'master',
            }
        )
        
        self._helper_node.schedule_action('install').wait(die=True)

    @property
    def _bot(self):
        if self._helper_bot:
            return self._helper_bot

        self._ensure_helper_node()
        node_info = self._helper_node.schedule_action('get_info').wait(die=True).result
        # error if itsyou.online client instance is not configured
        iyo_client = j.clients.itsyouonline.get(instance='main', create=False)
        memberof_scope = "user:memberof:{}".format(self.data['organization'])
        jwt = iyo_client.jwt_get(scope=memberof_scope, refreshable=True)

        # connect to robot on helper machine
        bot_name = '%s-bot' % self.name
        def_robot_port = '6600'
        url = 'http://{}:{}'.format(node_info['zerotierPrivateIP'], def_robot_port)
        zrobot_data = {'jwt_': jwt, 'url': url}
        j.clients.zrobot.get(instance=bot_name, data=zrobot_data)
        bot = j.clients.zrobot.robots[bot_name]

        # ensure robot is up, if not wait robot for 5 min
        timeout = time.time() + 300
        while time.time() < timeout:
            try:
                bot.services.names
                break
            except ConnectionError:
                continue
        else:
            raise ConnectionError('robot {} does not respond'.format(url))

        self._helper_bot = bot
        return self._helper_bot

    def _load_helper_templates(self):
        """ load deployment templates """
        
        branch = self.data['branch']['zeroTemplates'] or 'master'
        if self.ACCOUNT_TEMPLATE in list(self._bot.templates.uids.keys()):
            self._bot.templates.checkout_repo(self.ZERO_TEMPLATES_REPO, branch)
        else:
            self._bot.templates.add_repo(self.ZERO_TEMPLATES_REPO, branch)

        branch = self.data['branch']['kubernetes'] or 'master'
        if self.K8S_TEMPLATE in list(self._bot.templates.uids.keys()):
            self._bot.templates.checkout_repo(self.K8S_TEMPLATES_REPO, branch)
        else:            
            self._bot.templates.add_repo(self.K8S_TEMPLATES_REPO, branch)

    def _deploy_k8s(self, zrobot):
        """ Schedule deployment of kubernetes cluster

            :param zrobot: 0-robot instance
            return value: credentials of kubernetes cluster.
        """

        ovc_client = j.clients.openvcloud.get(self.config['ovc'], create=False)
        self._k8s = zrobot.services.find_or_create(
            template_uid=self.K8S_TEMPLATE,
            service_name=self.name,
            data={
                'workersCount': self.data['workersCount'],
                'sizeId': self.data['sizeId'],
                'dataDiskSize': self.data['dataDiskSize'],
                'vdc': self.config['vdc'],
                'account': self.config['account'],
                'sshKey': self.data['sshKey'],
                'connection': {
                    'name': self.config['ovc'],
                    'location': ovc_client.config.data['location'],
                    'address': ovc_client.config.data['address'],
                    'port': ovc_client.config.data['port'],
                    'token': ovc_client.config.data['jwt_'],
                },
            }
        )

        self._k8s.schedule_action('install').wait(die=True)
        self.data['credentials'] = self._k8s.schedule_action('get_info').wait(die=True).result['credentials']

    def install(self):
        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass
        # get helper machine with robot
        self._bot

        # load deployment templates
        self._load_helper_templates()

        # deploy kubernetes cluster
        self._deploy_k8s(self._bot)

        # complete action install
        self.state.set('actions', 'install', 'ok')

    def uninstall(self):
        """ Uninstall kubernetes cluster """

        # delete created services
        if self._k8s:
            self._k8s.schedule_action('uninstall').wait(die=True)
            self._k8s.delete()
            self._k8s = None
            
        if self._helper_node:
            self._helper_node.schedule_action('uninstall').wait(die=True)
            self._helper_node.delete()
            self._helper_node = None

        self.data['credentials'] = None
        # unset state of action install
        self.state.delete('actions', 'install')