from testconfig import config
from framework.constructor import constructor
from js9 import j


class OVC_BaseTest(constructor):

    env = config['main']['environment']

    def __init__(self, *args, **kwargs):
        super(OVC_BaseTest, self).__init__(*args, **kwargs)
        self.ovc_client = self.ovc_client()

    def setUp(self):
        super(OVC_BaseTest, self).setUp()
        self.key = self.random_string()
        self.openvcloud = self.random_string()
        self.vdcusers = {'gig_qa_1': {'openvcloud': self.openvcloud,
                                      'provider': 'itsyouonline',
                                      'email': 'dina.magdy.mohammed+123@gmail.com'}}

    def iyo_jwt(self):
        ito_client = j.clients.itsyouonline.get(instance="main")
        return ito_client.jwt

    def ovc_client(self):
        data = {'address': OVC_BaseTest.env,
                'port': 443
                }
        return j.clients.openvcloud.get(instance='main', data=data)

    def handle_blueprint(self, yaml, **kwargs):
        kwargs['token'] = self.iyo_jwt()
        blueprint = self.create_blueprint(yaml, **kwargs)
        return self.execute_blueprint(blueprint)

    def create_kubernetes(self, **kwargs):
        return self.handle_blueprint('kubernetes.yaml', **kwargs)
