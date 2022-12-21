#
# Copyright (c) 2020 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from k8sapp_portieris.common import constants
from sysinv.tests.db import base as dbbase
from sysinv.tests.helm.test_helm import HelmOperatorTestSuiteMixin


class K8SAppPortierisAppMixin(object):
    app_name = constants.HELM_APP_PORTIERIS
    path_name = app_name + '.tgz'

    def setUp(self):
        super(K8SAppPortierisAppMixin, self).setUp()


# Test Configuration:
# - Controller
# - IPv6
# - Ceph Storage
# - portieris app
class K8sAppPortierisControllerTestCase(K8SAppPortierisAppMixin,
                                        dbbase.BaseIPv6Mixin,
                                        dbbase.BaseCephStorageBackendMixin,
                                        HelmOperatorTestSuiteMixin,
                                        dbbase.ControllerHostTestCase):
    pass


# Test Configuration:
# - AIO
# - IPv4
# - Ceph Storage
# - portieris app
class K8SAppPortierisAIOTestCase(K8SAppPortierisAppMixin,
                                 dbbase.BaseCephStorageBackendMixin,
                                 HelmOperatorTestSuiteMixin,
                                 dbbase.AIOSimplexHostTestCase):
    pass
