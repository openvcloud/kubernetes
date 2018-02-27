# import time
# from js9 import j
from zerorobot.template.base import TemplateBase
# from zerorobot.template.state import StateCheckError


class Kubernetes(TemplateBase):

    version = '0.0.1'
    template_name = "kubernetes"

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)
