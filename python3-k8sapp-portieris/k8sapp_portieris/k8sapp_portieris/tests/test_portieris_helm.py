#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Unit tests for helm.portieris module."""

import unittest
from unittest import mock

from k8sapp_portieris.common import constants
from k8sapp_portieris.helm.portieris import PortierisHelm
from sysinv.common import exception


class TestPortierisHelmAttributes(unittest.TestCase):
    """Tests for PortierisHelm class attributes."""

    def test_chart_constant(self):
        """Verify CHART matches constant."""
        self.assertEqual(
            PortierisHelm.CHART,
            constants.HELM_CHART_PORTIERIS
        )

    def test_service_name(self):
        """Verify SERVICE_NAME attribute."""
        self.assertEqual(
            PortierisHelm.SERVICE_NAME,
            'portieris'
        )

    def test_supported_namespaces_contains_portieris(self):
        """Verify portieris in SUPPORTED_NAMESPACES."""
        self.assertIn(
            constants.HELM_NS_PORTIERIS,
            PortierisHelm.SUPPORTED_NAMESPACES
        )

    def test_supported_app_namespaces_key(self):
        """Verify SUPPORTED_APP_NAMESPACES key."""
        self.assertIn(
            constants.HELM_APP_PORTIERIS,
            PortierisHelm.SUPPORTED_APP_NAMESPACES
        )

    def test_supported_app_namespaces_value(self):
        """Verify app namespace list content."""
        namespace_list = (
            PortierisHelm.SUPPORTED_APP_NAMESPACES[
                constants.HELM_APP_PORTIERIS
            ]
        )
        self.assertIn(
            constants.HELM_NS_PORTIERIS,
            namespace_list
        )


class TestPortierisHelmGetNamespaces(unittest.TestCase):
    """Tests for get_namespaces method."""

    def setUp(self):
        """Set up test fixtures."""
        with mock.patch(
            'sysinv.helm.base.BaseHelm.__init__',
            return_value=None
        ):
            self.helm = PortierisHelm(
                mock.MagicMock()
            )

    def test_get_namespaces_returns_list(self):
        """Verify get_namespaces returns a list."""
        result = self.helm.get_namespaces()
        self.assertIsInstance(result, list)

    def test_get_namespaces_contains_portieris(self):
        """Verify portieris in returned list."""
        result = self.helm.get_namespaces()
        self.assertIn(
            constants.HELM_NS_PORTIERIS, result
        )

    def test_get_namespaces_matches_supported(self):
        """Verify matches SUPPORTED_NAMESPACES."""
        result = self.helm.get_namespaces()
        self.assertEqual(
            result,
            self.helm.SUPPORTED_NAMESPACES
        )


class TestPortierisHelmGetOverrides(unittest.TestCase):
    """Tests for get_overrides method."""

    def setUp(self):
        """Set up test fixtures."""
        with mock.patch(
            'sysinv.helm.base.BaseHelm.__init__',
            return_value=None
        ):
            self.helm = PortierisHelm(
                mock.MagicMock()
            )

    def test_get_overrides_no_namespace(self):
        """Verify get_overrides with no namespace."""
        result = self.helm.get_overrides(
            namespace=None
        )
        self.assertIsInstance(result, dict)
        self.assertIn(
            constants.HELM_NS_PORTIERIS, result
        )

    def test_get_overrides_valid_namespace(self):
        """Verify get_overrides with valid namespace."""
        result = self.helm.get_overrides(
            namespace=constants.HELM_NS_PORTIERIS
        )
        self.assertIsInstance(result, dict)

    def test_get_overrides_portieris_ns_returns_empty(self):
        """Verify portieris ns returns empty dict."""
        result = self.helm.get_overrides(
            namespace=constants.HELM_NS_PORTIERIS
        )
        self.assertEqual(result, {})

    def test_get_overrides_invalid_namespace(self):
        """Verify invalid namespace raises error."""
        self.assertRaises(
            exception.InvalidHelmNamespace,
            self.helm.get_overrides,
            namespace='invalid-ns'
        )

    def test_get_overrides_none_returns_all(self):
        """Verify None namespace returns all."""
        result = self.helm.get_overrides(
            namespace=None
        )
        self.assertEqual(
            result,
            {constants.HELM_NS_PORTIERIS: {}}
        )
