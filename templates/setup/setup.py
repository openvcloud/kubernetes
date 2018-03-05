
from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError
from JumpScale9Lib.clients.zerorobot.client import Client


class Setup(TemplateBase):

    version = '0.0.1'
    template_name = "setup"

    OVC_TEMPLATE = 'github.com/openvcloud/0-templates/openvcloud/0.0.1'
    ACCOUNT_TEMPLATE = 'github.com/openvcloud/0-templates/account/0.0.1'
    VDC_TEMPLATE = 'github.com/openvcloud/0-templates/vdc/0.0.1'
    NODE_TEMPLATE = 'github.com/openvcloud/0-templates/node/0.0.1'
    ZROBOT_TEMPLATE = 'github.com/openvcloud/0-templates/zrobot/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        self._config = None

    def validate(self):
        for key in ['vdc', 'workers', 'sshKey']:
            value = self.data[key]
            if not value:
                raise ValueError('"%s" is required' % key)

    @property
    def config(self):
        '''
        returns an object with names of vdc, account, and ovc
        '''
        if self._config is not None:
            return self._config

        config = {
            'vdc': self.data['vdc'],
        }
        # traverse the tree up words so we have all info we need to return, connection and
        # account
        matches = self.api.services.find(template_uid=self.VDC_TEMPLATE, name=config['vdc'])
        if len(matches) != 1:
            raise RuntimeError('found %d vdcs with name "%s"' % (len(matches), config['vdc']))

        vdc = matches[0]
        self._vdc = vdc
        task = vdc.schedule_action('get_account')
        task.wait()

        config['account'] = task.result

        matches = self.api.services.find(template_uid=self.ACCOUNT_TEMPLATE, name=config['account'])
        if len(matches) != 1:
            raise ValueError('found %s accounts with name "%s"' % (len(matches), config['account']))

        account = matches[0]
        # get connection
        task = account.schedule_action('get_openvcloud')
        task.wait()

        config['ovc'] = task.result

        self._config = config
        return self._config

    def _ensure_helper(self):
        name = '%s-little-helper' % self.name
        nodes = self.api.services.find(template_uid=self.NODE_TEMPLATE, name=name)
        if len(nodes) != 0:
            return nodes[0]

        # create the node instead
        # create a disk service
        node = self.api.services.create(
            template_uid=self.NODE_TEMPLATE,
            service_name=name,
            data={
                'vdc': self.data['vdc'],
                'sshKey': self.data['sshKey'],
                'sizeId': 2,
            },
        )

        # update data in the disk service
        task = node.schedule_action('install')
        task.wait()
        if task.state == 'error':
            raise task.eco

        return node

    def _ensure_zrobot(self, helper):
        name = '%s-little-bot' % self.name
        bots = self.api.services.find(template_uid=self.ZROBOT_TEMPLATE, name=name)
        if len(bots) != 0:
            return bots[0]

        # create the node instead
        # create a disk service
        bot = self.api.services.create(
            template_uid=self.ZROBOT_TEMPLATE,
            service_name=name,
            data={
                'node': helper.name,
                'port': 6600,
                'templates': [
                    'https://github.com/openvcloud/0-templates.git',
                    'https://github.com/openvcloud/kubernetes.git',
                ],
            },
        )

        # update data in the disk service
        task = bot.schedule_action('install')
        task.wait()
        if task.state == 'error':
            raise task.eco

        return bot

    def _mirror_services(self, zrobot):
        config = self.config
        ovc = j.clients.openvcloud.get(config['ovc'])

        zrobot.services.create(
            template_uid=self.OVC_TEMPLATE,
            service_name=config['ovc'],
            data={
                'address': ovc.config.data['address'],
                'port': ovc.config.data['port'],
                'location': ovc.config.data['location'],
                'token': ovc.config.data['jwt_'],
            }
        )

        account = zrobot.services.create(
            template_uid=self.ACCOUNT_TEMPLATE,
            service_name=config['account'],
            data={
                'openvcloud': config['ovc'],
                'create': False,
            }
        )

        vdc = zrobot.services.create(
            template_uid=self.VDC_TEMPLATE,
            service_name=config['vdc'],
            data={
                'account': config['account'],
                'create': False,
            }
        )

        # make sure they are installed
        for instance in [account, vdc]:
            task = instance.schedule_action('install')
            task.wait()
            if task.state == 'error':
                raise task.eco

    def install(self):
        # try:
        #     self.state.check('actions', 'install', 'ok')
        #     return
        # except StateCheckError:
        #     pass

        helper = self._ensure_helper()
        bot = self._ensure_zrobot(helper)

        zrobot = self.api.robots[bot.name]

        self._mirror_services(zrobot)

        self.state.set('actions', 'install', 'ok')
