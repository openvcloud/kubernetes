import os
from unittest import mock
from unittest.mock import MagicMock, patch
from unittest import TestCase
from js9 import j


from zerorobot import config, template_collection
from zerorobot.template.state import StateCheckError


class TestSetup(TestCase):
    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/kebernates",
            os.path.dirname(__file__)
        )
        self.valid_data = {
            'vdc' : 'vdc-service-name',
            'workersCount': 2,
            'sshKey': {
                'name': 'k8s_id',
                'passphrase': 'testpassphrase',
            },
            'zerotierToken': '1234567qwerty435e24d345',
            'zerotierId': 'fydj364hs83hf6cj',
            'organization': 'test_organization',
        }
        self.ovc = {
            'service': 'test_ovc_service',
            'info': {'name': 'connection_instance_name'}
        }        
        self.acc = {'service': 'test_account-service',
                    'info': {'name': 'test_account_real_name',
                             'openvcloud': self.ovc['service']}
                    }
        self.vdc = {'service': 'test-vdc-service',
                    'info': {'name': 'test_vdc_real_name',
                             'account': self.acc['service']}
                    }
    def tearDown(self):
        mock.patch.stopall()

    def test_validate_success(self):
        instance = self.type('setup-service', None, self.valid_data)
        instance.validate()

    def test_validate_fail(self):
        invalid_data = self.valid_data.copy()
        invalid_data['vdc'] = ''
        instance = self.type('setup-service', None, invalid_data)
        
        with self.assertRaises(ValueError):
            instance.validate()

    def test_get_info_success(self):
        data = self.valid_data.copy()
        data['credentials'] = 'credentials'
        instance = self.type('setup-service', None, data)
        instance.state.set('actions', 'install', 'ok')
        assert instance.get_info() == {'credentials': 'credentials'}

    def test_get_info_fail_state_check(self):
        instance = self.type('setup-service', None, {})
        with self.assertRaises(StateCheckError):
            instance.get_info()

    @staticmethod
    def set_up_proxy_mock(result=None, name='service_name'):
        """ Setup a mock for a proxy of zrobot service  """
        proxy = MagicMock(schedule_action=MagicMock())
        proxy.schedule_action().wait = MagicMock()
        proxy.schedule_action().wait(die=True).result = result
        proxy.name = name
        return proxy

    def get_service(self, template_uid, name):
        if template_uid == self.type.OVC_TEMPLATE:
            proxy = self.set_up_proxy_mock(result=self.ovc['info'], name=name)
        elif template_uid == self.type.ACCOUNT_TEMPLATE:
            proxy = self.set_up_proxy_mock(result=self.acc['info'], name=name)
        elif template_uid == self.type.VDC_TEMPLATE:
            proxy = self.set_up_proxy_mock(result=self.vdc['info'], name=name)            
        else:
            proxy = None
        return proxy

    def find_or_create(self, template_uid, service_name, data):
        assert template_uid == self.type.ZOS_NODE_TEMPLATE
        proxy = self.set_up_proxy_mock(result={
            'zerotierPrivateIP': '192.168.100',
        })
        return proxy

    def test_ensure_helper_node(self):
        name = 'setup-service'
        instance = self.type(name, None, self.valid_data)
        helper_name = '{}-helper'.format(name)

        with patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service
            instance._ensure_helper_node()
            api.services.find_or_create.called_ones_with(
                template_uid=self.type.ZOS_NODE_TEMPLATE,
                service_name=helper_name,
                data={
                    'name': helper_name,
                    'vdc': self.vdc['info']['name'],
                    'zerotierId': self.valid_data['zerotierId'],
                    'organization': self.valid_data['organization'],
                    'zerotierClient': 'kubernetes_zerotier',
                    'branch': 'master',
                }
            )
            instance._helper_node.schedule_action.called_ones_with('install')

    @mock.patch.object(j.clients, '_openvcloud')            
    @mock.patch.object(j.clients, '_zrobot')
    def test_install(self, zrobot, ovc):
        name = 'test-setup-service'
        instance = self.type(name, None, self.valid_data)
        bot_name = '%s-bot' % name
        zrobot.robots = {bot_name:MagicMock()}
        ovc.get.side_effect = MagicMock()
        with patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service
            api.services.find_or_create.side_effect = self.find_or_create
            instance.install()
            assert api.services.find_or_create.call_count == 1
        instance.state.check('actions', 'install', 'ok')

    def test_uninstall(self):
        name = 'test-setup-service'
        data = self.valid_data.copy()
        data['credentials'] = 'credentials'
        instance = self.type(name, None, data)
        instance.state.set('actions', 'install', 'ok')

        service_mock = self.set_up_proxy_mock()
        instance._k8s = service_mock
        instance._helper_node = service_mock
        instance.uninstall()
        assert service_mock.delete.call_count == 2
        assert not instance._helper_node
        assert not instance._k8s
        assert not instance.data['credentials']
