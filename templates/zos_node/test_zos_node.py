from unittest import TestCase
from unittest import mock
from unittest.mock import MagicMock, patch
from unittest import skip
import tempfile
import shutil
import os

from js9 import j
from zerorobot.template.base import TemplateBase
from zerorobot import config, template_collection
from zerorobot.template_uid import TemplateUID
from zerorobot.template.state import StateCheckError
from zerorobot.service_collection import ServiceNotFoundError


class TestZosNode(TestCase):

    def setUp(self):
        config.DATA_DIR = '/tmp'
        self.type = template_collection._load_template(
            "https://github.com/openvcloud/0-templates",
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
                             'account': self.acc['service']}
                    }
        self.sshkey = {
            'service': 'test_node_service',
            'info': {
                    'name': 'test_sshkey_name',
                }
        }                 
        self.node = {
            'service': 'test_node_service',
            'info': {
                    'name': 'test_helper',
                    'vdc': self.vdc['service'],
                    'sshKey': self.sshkey['service']
                }
        }
        self.valid_data = {
            'name': self.node['info']['name'],
            'vdc': self.vdc['service'],
            'zerotierId': 'g6h7j9906dsd',
            'organization': 'test_organization',
            'zerotierClient': 'zt_instance_name',
        } 


    def tearDown(self):
        patch.stopall()

    def ovc_mock(self, instance):
        machine_mock = MagicMock()
        space_mock = MagicMock(machines=[self.node['info']['name']],
                               machine_create=MagicMock(return_value=machine_mock))
        return MagicMock(space_get=MagicMock(return_value=space_mock))

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
        elif template_uid == self.type.SSH_TEMPLATE:
            proxy = self.set_up_proxy_mock(result=self.sshkey['info'], name=name)            
        else:
            proxy = None
        return proxy

    def test_validate_success(self):
        """
        Test successfull validation
        """
        name = 'test'
        instance = self.type(name=name, guid=None, data=self.valid_data)
        instance.validate()

    def test_validate_fail(self):
        """
        Test successfull validation
        """
        name = 'test'
        invalid_data = self.valid_data.copy()
        invalid_data['vdc'] = ''
        instance = self.type(name=name, guid=None, data=invalid_data)
        
        with self.assertRaises(ValueError):
            instance.validate()

    def test_config(self):
        """
        Test fetching config from vdc, account, and ovc services
        """
        instance = self.type(name='test', data=self.valid_data)

        with patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service
            instance.config
            
        self.assertEqual(
            instance.config['ovc'], self.ovc['info']['name'])
        self.assertEqual(
            instance.config['account'], self.acc['info']['name'])
        self.assertEqual(
            instance.config['vdc'], self.vdc['info']['name'])

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install_when_already_installed(self, ovc):
        """
        Test successfull install VM action
        """
        # if installed, do nothing
        instance = self.type(name='test', data=self.valid_data)
        instance.state.set('actions', 'install', 'ok')
        instance.install()
        ovc.get.return_value.space_get.return_value.create_and_connect_zos_machine.assert_not_called()

    @mock.patch.object(j.clients, '_openvcloud')
    def test_install(self, ovc):
        """
        Test successfull install VM action
        """
        instance = self.type(name='test', data=self.node['info'])

        ovc.get.return_value = self.ovc_mock(self.ovc['info']['name'])

        with patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service
            instance.install()

            # check call to get/create machine
            instance.space.create_and_connect_zos_machine.assert_called_once_with(
                name=instance.data['name'],
                zerotier_id=instance.data['zerotierId'],
                organization=instance.data['organization'],
                zerotier_client=instance.data['zerotierClient'],
                sizeId=instance.data['sizeId'],
                branch=instance.data['branch'],
                dev_mode=instance.data['devMode'],
            )

    @mock.patch.object(j.clients, '_zerotier')
    @mock.patch.object(j.clients, '_openvcloud')
    def test_uninstall(self, ovc, zt):
        """
        Test uninstall VM action
        """
        instance = self.type(name='test', data=self.valid_data)
        zt.get = MagicMock()
        ovc.get.side_effect = self.ovc_mock

        with patch.object(instance, 'api') as api:
            api.services.get.side_effect = self.get_service
            instance.uninstall()
        assert not instance._machine_
        assert not instance._zerotier_node_

        
