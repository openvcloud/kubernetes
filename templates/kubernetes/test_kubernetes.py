import os
from unittest import mock
from unittest.mock import MagicMock, patch
from unittest import TestCase
from js9 import j


from zerorobot import config, template_collection
from zerorobot.template.state import StateCheckError


class TestKubernetes(TestCase):
    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/kebernates",
            os.path.dirname(__file__)
        )
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
                     'account': self.acc['service'],
                     'public_ip': '0.0.0.0'}
            }
        self.ssh = {'service': 'test-ssh-service',
            'info': {
                'name': 'k8s_id',
                'passphrase': 'test_passphrase',
                }
        }                    
        self.valid_data = {
            'workersCount': 2,
            'sizeId': 6,
            'dataDiskSize': 10,
            'vdc': self.vdc['info']['name'],
            'account': self.acc['info']['name'],
            'sshKey': self.ssh['info'],
            'connection': {
                'name': self.ovc['info']['name'],
                'location': 'ovc_location',
                'address': 'addres.com',
                'port': 443,
                'token': '<token>',
            }
        }
    def tearDown(self):
        mock.patch.stopall()

    def test_validate_success(self):
        instance = self.type('kubernetes-service', None, self.valid_data)
        instance.validate()

    def test_validate_fail(self):
        invalid_data = self.valid_data.copy()
        invalid_data['vdc'] = ''
        instance = self.type('kubernetes-service', None, invalid_data)
        
        with self.assertRaises(ValueError):
            instance.validate()

    def test_get_info_success(self):
        data = self.valid_data.copy()
        data['credentials'] = 'credentials'
        instance = self.type('kubernetes-service', None, data)
        instance.state.set('actions', 'install', 'ok')
        assert instance.get_info() == {'credentials': 'credentials'}

    def test_get_info_fail_state_check(self):
        instance = self.type('kubernetes-service', None, {})
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

    def find_or_create(self, template_uid='', service_name='', data={}):
        if template_uid == self.type.OVC_TEMPLATE:
            proxy = self.set_up_proxy_mock(result=self.ovc['info'], name=service_name)
        elif template_uid == self.type.ACCOUNT_TEMPLATE:
            proxy = self.set_up_proxy_mock(result=self.acc['info'], name=service_name)
        elif template_uid == self.type.VDC_TEMPLATE:
            proxy = self.set_up_proxy_mock(result=self.vdc['info'], name=service_name)
        elif template_uid == self.type.SSHKEY_TEMPLATE:
            proxy = self.set_up_proxy_mock(result=self.ssh['info'], name=service_name)
        elif template_uid == self.type.NODE_TEMPLATE:
            proxy = self.set_up_proxy_mock(name=service_name)                   
        else:
            proxy = None
        return proxy

    def find(self,name=''):
        return [self.set_up_proxy_mock()]

    def service_get(self, name):
        proxy = self.set_up_proxy_mock()
        return proxy

    @mock.patch.object(j.clients, '_openvcloud')            
    @mock.patch.object(j.tools, '_prefab')
    def test_install(self, prefab, ovc):
        name = 'test-kubernetes-service'
        instance = self.type(name, None, self.valid_data)
        ovc.get.side_effect = MagicMock()
        with patch.object(instance, 'api') as api:
            api.services.find_or_create.side_effect = self.find_or_create
            instance.install()
            assert prefab.local.virtualization.kubernetes.multihost_install.called_ones_with(
                masters=instance.data['masters'],
                workers=instance.data['workers'],
                external_ips=[self.vdc['info']['public_ip']],
            )
            assert api.services.find_or_create.call_count == 7
        instance.state.check('actions', 'install', 'ok')

    def test_uninstall(self):
        name = 'test-kubernetes-service'
        instance = self.type(name, None, self.valid_data)

        with patch.object(instance, 'api') as api:
            api.services.get = self.service_get('name')
            api.services.find.side_effect = self.find
            instance.data['masters'] = [api.services.get]
            instance.data['workers'] = [api.services.get, api.services.get]
            instance.uninstall()
            assert api.services.get.return_value.schedule_action.call_count == 3
            assert api.services.get.return_value.delete.call_count == 3
            assert api.services.find.call_count == 4

        with self.assertRaises(StateCheckError):
            instance.state.check('actions', 'install', 'ok')