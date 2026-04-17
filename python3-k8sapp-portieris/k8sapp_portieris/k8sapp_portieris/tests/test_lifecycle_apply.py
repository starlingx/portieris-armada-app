#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for PortierisAppLifecycleOperator.post_apply."""

import unittest
from unittest import mock

from k8sapp_portieris.common import constants as app_constants
from k8sapp_portieris.tests.conftest import _create_lifecycle_operator


def _create_mock_app_operator(user_overrides=''):
    """Create mocked app operator with dbapi and kube.

    Args:
        user_overrides: Helm user override string.

    Returns:
        Tuple of (app_operator, namespace, core_client).
    """
    app_operator = mock.MagicMock()
    mock_db_app = mock.MagicMock()
    mock_db_app.id = 42
    app_operator._dbapi.kube_app_get.return_value = (
        mock_db_app
    )
    override_obj = mock.MagicMock()
    override_obj.user_overrides = user_overrides
    app_operator._dbapi.helm_override_get.return_value = (
        override_obj
    )
    namespace = mock.MagicMock()
    namespace.metadata.labels = {}
    core_client = mock.MagicMock()
    core_client.read_namespace.return_value = namespace
    app_operator._kube._get_kubernetesclient_core \
        .return_value = core_client
    return app_operator, namespace, core_client


class TestPostApplyNoOverrideLabel(unittest.TestCase):
    """Test post_apply with no component label."""

    def test_sets_platform_label(self):
        """Verify platform label is set."""
        operator = _create_lifecycle_operator()
        app_operator, namespace, _core_client = (
            _create_mock_app_operator(user_overrides='')
        )
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.post_apply(app_operator, mock_app)
        label_key = (
            app_constants.HELM_COMPONENT_LABEL_PORTIERIS
        )
        self.assertEqual(
            namespace.metadata.labels[label_key],
            'platform'
        )
        app_operator._kube.kube_patch_namespace \
            .assert_called_once()


class TestPostApplyApplicationLabel(unittest.TestCase):
    """Test post_apply with application label."""

    def test_sets_application_label(self):
        """Verify application label is set."""
        operator = _create_lifecycle_operator()
        label_key = (
            app_constants.HELM_COMPONENT_LABEL_PORTIERIS
        )
        overrides = '%s: application\n' % label_key
        app_operator, namespace, _core_client = (
            _create_mock_app_operator(
                user_overrides=overrides
            )
        )
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.post_apply(app_operator, mock_app)
        self.assertEqual(
            namespace.metadata.labels[label_key],
            'application'
        )


class TestPostApplyPlatformLabel(unittest.TestCase):
    """Test post_apply with platform label."""

    def test_sets_platform_label(self):
        """Verify platform label is set."""
        operator = _create_lifecycle_operator()
        label_key = (
            app_constants.HELM_COMPONENT_LABEL_PORTIERIS
        )
        overrides = '%s: platform\n' % label_key
        app_operator, namespace, _core_client = (
            _create_mock_app_operator(
                user_overrides=overrides
            )
        )
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.post_apply(app_operator, mock_app)
        self.assertEqual(
            namespace.metadata.labels[label_key],
            'platform'
        )


class TestPostApplyUnsupportedLabel(unittest.TestCase):
    """Test post_apply with unsupported label value."""

    def test_unsupported_label_no_patch(self):
        """Verify no patch for unsupported label."""
        operator = _create_lifecycle_operator()
        label_key = (
            app_constants.HELM_COMPONENT_LABEL_PORTIERIS
        )
        overrides = '%s: unsupported\n' % label_key
        app_operator, namespace, _core_client = (
            _create_mock_app_operator(
                user_overrides=overrides
            )
        )
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.post_apply(app_operator, mock_app)
        app_operator._kube.kube_patch_namespace \
            .assert_not_called()


class TestPostApplyLabelChanged(unittest.TestCase):
    """Test post_apply deletes pods on label change."""

    def test_pods_deleted_on_label_change(self):
        """Verify pods deleted when label changes."""
        operator = _create_lifecycle_operator()
        label_key = (
            app_constants.HELM_COMPONENT_LABEL_PORTIERIS
        )
        app_operator, namespace, core_client = (
            _create_mock_app_operator(user_overrides='')
        )
        namespace.metadata.labels = {
            label_key: 'application'
        }
        mock_pod = mock.MagicMock()
        mock_pod.metadata.name = 'portieris-pod-1'
        pods_list = mock.MagicMock()
        pods_list.items = [mock_pod]
        core_client.list_namespaced_pod.return_value = (
            pods_list
        )
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.post_apply(app_operator, mock_app)
        app_operator._kube.kube_delete_pod \
            .assert_called_once()


class TestPostApplyLabelUnchanged(unittest.TestCase):
    """Test post_apply skips pod deletion."""

    def test_no_pod_deletion(self):
        """Verify no pod deletion when unchanged."""
        operator = _create_lifecycle_operator()
        label_key = (
            app_constants.HELM_COMPONENT_LABEL_PORTIERIS
        )
        app_operator, namespace, _core_client = (
            _create_mock_app_operator(user_overrides='')
        )
        namespace.metadata.labels = {
            label_key: 'platform'
        }
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.post_apply(app_operator, mock_app)
        app_operator._kube.kube_delete_pod \
            .assert_not_called()
