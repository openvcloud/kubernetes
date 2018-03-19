import unittest
from framework.utils.utils import OVC_BaseTest
from collections import OrderedDict
from random import randint


class kubernetes(OVC_BaseTest):
    def setUp(self):
        super().setUp()
        self.account_service = self.random_string()
        self.account_service_parameter = {self.account_service: {'openvcloud': self.openvcloud}}

        self.cloudspace_service = self.random_string()
        self.cloudspace_service_parameter = {self.cs1: {'account': self.acc1,
                                                        'openvcloud': self.openvcloud}}
        self.kubernetes_service = self.random_string()
        self.temp_actions = {'account': {'actions': ['install']},
                             'vdc': {'actions': ['install']},
                             'kubernetes': {'action': ['install']}}

    def test002_construct_kybernetes_cluster_on_OVC(self):
        """ ZRT-OVC-000
        Test case for constructing kybernetes cluster on OVC*

        **Test Scenario:**

        """
        self.log('%s STARTED' % self._testID)
        self.kubernetes_service_parameter = {self.kubernetes_service: {'vdc': self.cloudspace_service,
                                                                       'sshKey': self.key,
                                                                       'workers': randint(1, 20)}}
        response = self.create_kubernetes(self.kubernetes_service_parameter)
        self.assertTrue(type(response), type(dict()))

        # self.wait_for_service_action_status(self.vm1, response[self.vm1])
        # self.cs1_id = self.get_cloudspace(self.cs1)['id']
        #
        # self.log("Check if the 1st vm's parameters are reflected correctly on OVC")
        # vm = self.get_vm(cloudspaceId=self.cs1_id, vmname=self.vm1)
        # self.assertEqual(self.cs1_id, vm['cloudspaceid'])
        #
        # self.log('%s ENDED' % self._testID)

    def tearDown(self):
        for accountname in self.accounts.keys():
            if self.check_if_service_exist(accountname):
                self.temp_actions = {'account': {'actions': ['uninstall']}}
                self.create_account(openvcloud=self.openvcloud, vdcusers=self.vdcusers,
                                    accounts=self.accounts, temp_actions=self.temp_actions)
        self.delete_services()

