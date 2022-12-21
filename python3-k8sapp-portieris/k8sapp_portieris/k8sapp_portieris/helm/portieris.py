#
# Copyright (c) 2020 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from k8sapp_portieris.common import constants

from sysinv.common import exception

from sysinv.helm import base


class PortierisHelm(base.BaseHelm):
    """Class to encapsulate helm operations for the psp rolebinding chart"""

    SUPPORTED_NAMESPACES = base.BaseHelm.SUPPORTED_NAMESPACES + \
        [constants.HELM_NS_PORTIERIS]
    SUPPORTED_APP_NAMESPACES = {
        constants.HELM_APP_PORTIERIS:
            base.BaseHelm.SUPPORTED_NAMESPACES + [constants.HELM_NS_PORTIERIS],
    }

    CHART = constants.HELM_CHART_PORTIERIS
    SERVICE_NAME = 'portieris'

    def get_namespaces(self):
        return self.SUPPORTED_NAMESPACES

    def get_overrides(self, namespace=None):
        overrides = {
            constants.HELM_NS_PORTIERIS: {}
        }

        if namespace in self.SUPPORTED_NAMESPACES:
            return overrides[namespace]
        elif namespace:
            raise exception.InvalidHelmNamespace(chart=self.CHART,
                                                 namespace=namespace)
        else:
            return overrides
