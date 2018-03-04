
from js9 import j
import itertools
from zerorobot.template.base import TemplateBase
from zerorobot.template.state import StateCheckError


class Setup(TemplateBase):

    version = '0.0.1'
    template_name = "setup"

    VDC_TEMPLATE = 'github.com/openvcloud/0-templates/vdc/0.0.1'
    NODE_TEMPLATE = 'github.com/openvcloud/0-templates/node/0.0.1'
    ZROBOT_TEMPLATE = 'github.com/openvcloud/0-templates/zrobot/0.0.1'

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

    def validate(self):
        if self.data['vdc'] == '':
            raise ValueError('vdc is required')

        if self.data['workers'] == 0:
            raise ValueError('require at least 1 worker node')

    def _ensure_helper(self):
        name = '%s-little-helper'
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

    def install(self):
        try:
            self.state.check('actions', 'install', 'ok')
            return
        except StateCheckError:
            pass

        helper = self._ensure_helper()
        self._ensure_zrobot(helper)

        self.state.set('actions', 'install', 'ok')
