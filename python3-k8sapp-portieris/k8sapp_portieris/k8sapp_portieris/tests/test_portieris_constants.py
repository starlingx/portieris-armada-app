#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Unit tests for common.constants module."""

import unittest

from k8sapp_portieris.common import constants


class TestPortierisConstants(unittest.TestCase):
    """Tests for constants module values."""

    def test_helm_app_portieris(self):
        """Verify HELM_APP_PORTIERIS constant."""
        self.assertEqual(
            constants.HELM_APP_PORTIERIS,
            'portieris'
        )

    def test_helm_chart_portieris(self):
        """Verify HELM_CHART_PORTIERIS constant."""
        self.assertEqual(
            constants.HELM_CHART_PORTIERIS,
            'portieris'
        )

    def test_helm_ns_portieris(self):
        """Verify HELM_NS_PORTIERIS constant."""
        self.assertEqual(
            constants.HELM_NS_PORTIERIS,
            'portieris'
        )

    def test_helm_component_label(self):
        """Verify HELM_COMPONENT_LABEL_PORTIERIS."""
        self.assertEqual(
            constants.HELM_COMPONENT_LABEL_PORTIERIS,
            'app.starlingx.io/component'
        )

    def test_constants_are_strings(self):
        """Verify all constants are string type."""
        self.assertIsInstance(
            constants.HELM_APP_PORTIERIS, str
        )
        self.assertIsInstance(
            constants.HELM_CHART_PORTIERIS, str
        )
        self.assertIsInstance(
            constants.HELM_NS_PORTIERIS, str
        )
        self.assertIsInstance(
            constants.HELM_COMPONENT_LABEL_PORTIERIS,
            str
        )

    def test_constants_not_empty(self):
        """Verify no constants are empty strings."""
        self.assertTrue(
            constants.HELM_APP_PORTIERIS
        )
        self.assertTrue(
            constants.HELM_CHART_PORTIERIS
        )
        self.assertTrue(
            constants.HELM_NS_PORTIERIS
        )
        self.assertTrue(
            constants.HELM_COMPONENT_LABEL_PORTIERIS
        )
