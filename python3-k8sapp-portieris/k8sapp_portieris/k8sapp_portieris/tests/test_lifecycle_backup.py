#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for backup, restore, webhook, and helpers."""

import unittest
from unittest import mock

from k8sapp_portieris.tests.conftest import _create_lifecycle_operator
from k8sapp_portieris.tests.conftest import _create_mock_app_operator
from sysinv.common import exception


class TestGetWebhookConfig(unittest.TestCase):
    """Tests for _get_portieris_mutating_webhook."""

    def test_returns_webhook_when_one(self):
        """Verify single webhook returned."""
        operator = _create_lifecycle_operator()
        app_operator = mock.MagicMock()
        mock_webhook = mock.MagicMock()
        app_operator._kube \
            .kube_get_mutating_webhook_configurations_by_selector \
            .return_value = [mock_webhook]
        result = operator \
            ._get_portieris_mutating_webhook_configuration(
                app_operator
            )
        self.assertEqual(result, mock_webhook)

    def test_returns_none_when_empty(self):
        """Verify None returned when no webhooks."""
        operator = _create_lifecycle_operator()
        app_operator = mock.MagicMock()
        app_operator._kube \
            .kube_get_mutating_webhook_configurations_by_selector \
            .return_value = []
        result = operator \
            ._get_portieris_mutating_webhook_configuration(
                app_operator
            )
        self.assertIsNone(result)

    def test_raises_on_multiple(self):
        """Verify exception on multiple webhooks."""
        operator = _create_lifecycle_operator()
        app_operator = mock.MagicMock()
        app_operator._kube \
            .kube_get_mutating_webhook_configurations_by_selector \
            .return_value = [
                mock.MagicMock(), mock.MagicMock()
            ]
        self.assertRaises(
            exception.LifecycleSemanticCheckException,
            operator
            ._get_portieris_mutating_webhook_configuration,
            app_operator,
        )


class TestGetHelmUserOverrides(unittest.TestCase):
    """Tests for _get_helm_user_overrides."""

    def test_returns_existing_overrides(self):
        """Verify existing overrides returned."""
        operator = _create_lifecycle_operator()
        mock_dbapi = mock.MagicMock()
        override_obj = mock.MagicMock()
        override_obj.user_overrides = 'key: value'
        mock_dbapi.helm_override_get.return_value = (
            override_obj
        )
        result = operator._get_helm_user_overrides(
            mock_dbapi, 42
        )
        self.assertEqual(result, 'key: value')

    def test_returns_empty_when_none(self):
        """Verify empty string when overrides None."""
        operator = _create_lifecycle_operator()
        mock_dbapi = mock.MagicMock()
        override_obj = mock.MagicMock()
        override_obj.user_overrides = None
        mock_dbapi.helm_override_get.return_value = (
            override_obj
        )
        result = operator._get_helm_user_overrides(
            mock_dbapi, 42
        )
        self.assertEqual(result, '')

    def test_creates_override_when_not_found(self):
        """Verify override created when missing."""
        operator = _create_lifecycle_operator()
        mock_dbapi = mock.MagicMock()
        mock_dbapi.helm_override_get.side_effect = (
            exception.HelmOverrideNotFound(
                name='portieris',
                namespace='portieris'
            )
        )
        new_obj = mock.MagicMock()
        new_obj.user_overrides = None
        mock_dbapi.helm_override_create.return_value = (
            new_obj
        )
        result = operator._get_helm_user_overrides(
            mock_dbapi, 42
        )
        self.assertEqual(result, '')
        mock_dbapi.helm_override_create \
            .assert_called_once()


class TestUpdateHelmUserOverrides(unittest.TestCase):
    """Tests for _update_helm_user_overrides."""

    def test_updates_with_value(self):
        """Verify override updated with value."""
        operator = _create_lifecycle_operator()
        mock_dbapi = mock.MagicMock()
        operator._update_helm_user_overrides(
            mock_dbapi, 42, 'key: val'
        )
        mock_dbapi.helm_override_update \
            .assert_called_once()

    def test_empty_dict_becomes_none(self):
        """Verify empty dict becomes None."""
        operator = _create_lifecycle_operator()
        mock_dbapi = mock.MagicMock()
        operator._update_helm_user_overrides(
            mock_dbapi, 42, '{}'
        )
        call_kwargs = (
            mock_dbapi.helm_override_update.call_args
        )
        self.assertIsNone(
            call_kwargs[1]['values']['user_overrides']
        )

    def test_none_stays_none(self):
        """Verify None value stays None."""
        operator = _create_lifecycle_operator()
        mock_dbapi = mock.MagicMock()
        operator._update_helm_user_overrides(
            mock_dbapi, 42, None
        )
        call_kwargs = (
            mock_dbapi.helm_override_update.call_args
        )
        self.assertIsNone(
            call_kwargs[1]['values']['user_overrides']
        )


class TestCreatePortierisOverride(unittest.TestCase):
    """Tests for _create_portieris_override."""

    def test_creates_override_string(self):
        """Verify override string created."""
        operator = _create_lifecycle_operator()
        mock_dbapi = mock.MagicMock()
        operator._create_portieris_override(
            mock_dbapi, 42, ['other: val'], 'false'
        )
        mock_dbapi.helm_override_update \
            .assert_called_once()
        call_kwargs = (
            mock_dbapi.helm_override_update.call_args
        )
        updated = (
            call_kwargs[1]['values']['user_overrides']
        )
        self.assertIn(
            'ReapplyAdmissionWebhook: false', updated
        )
        self.assertIn('other: val', updated)


class TestPreBackupWithWebhook(unittest.TestCase):
    """Tests for pre_backup method."""

    def test_deletes_webhook_and_creates_override(self):
        """Verify webhook deleted and override set."""
        operator = _create_lifecycle_operator()
        app_operator = _create_mock_app_operator(
            user_overrides='existing: val'
        )
        mock_webhook = mock.MagicMock()
        mock_webhook.metadata.name = (
            'portieris-webhook'
        )
        app_operator._kube \
            .kube_get_mutating_webhook_configurations_by_selector \
            .return_value = [mock_webhook]
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.pre_backup(app_operator, mock_app)
        app_operator._kube \
            .kube_delete_mutating_webhook_configuration \
            .assert_called_once_with(
                'portieris-webhook'
            )
        app_operator._dbapi.helm_override_update \
            .assert_called()


class TestPreBackupNoWebhook(unittest.TestCase):
    """Tests for pre_backup when no webhook exists."""

    def test_returns_early(self):
        """Verify early return without webhook."""
        operator = _create_lifecycle_operator()
        app_operator = _create_mock_app_operator()
        app_operator._kube \
            .kube_get_mutating_webhook_configurations_by_selector \
            .return_value = []
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.pre_backup(app_operator, mock_app)
        app_operator._kube \
            .kube_delete_mutating_webhook_configuration \
            .assert_not_called()


class TestPostBackup(unittest.TestCase):
    """Tests for post_backup method."""

    def test_calls_recreate(self):
        """Verify recreate webhook called."""
        operator = _create_lifecycle_operator()
        recreate_method = (
            '_recreate_portieris'
            '_mutating_webhook_configuration'
        )
        setattr(
            operator,
            recreate_method,
            mock.MagicMock()
        )
        app_operator = mock.MagicMock()
        mock_app = mock.MagicMock()
        operator.post_backup(app_operator, mock_app)
        getattr(
            operator, recreate_method
        ).assert_called_once_with(
            app_operator, mock_app
        )


class TestPostRestore(unittest.TestCase):
    """Tests for post_restore method."""

    def test_calls_recreate(self):
        """Verify recreate webhook called."""
        operator = _create_lifecycle_operator()
        recreate_method = (
            '_recreate_portieris'
            '_mutating_webhook_configuration'
        )
        setattr(
            operator,
            recreate_method,
            mock.MagicMock()
        )
        app_operator = mock.MagicMock()
        mock_app = mock.MagicMock()
        operator.post_restore(app_operator, mock_app)
        getattr(
            operator, recreate_method
        ).assert_called_once_with(
            app_operator, mock_app
        )


class TestDeletePortierisPods(unittest.TestCase):
    """Tests for _delete_portieris_pods."""

    def test_deletes_all_pods(self):
        """Verify all pods deleted."""
        operator = _create_lifecycle_operator()
        app_operator = mock.MagicMock()
        core_client = mock.MagicMock()
        mock_pod_one = mock.MagicMock()
        mock_pod_one.metadata.name = 'pod-1'
        mock_pod_two = mock.MagicMock()
        mock_pod_two.metadata.name = 'pod-2'
        pods_list = mock.MagicMock()
        pods_list.items = [mock_pod_one, mock_pod_two]
        core_client.list_namespaced_pod.return_value = (
            pods_list
        )
        operator._delete_portieris_pods(
            app_operator, core_client
        )
        self.assertEqual(
            app_operator._kube
            .kube_delete_pod.call_count,
            2
        )

    def test_no_pods_no_deletion(self):
        """Verify no deletion when no pods."""
        operator = _create_lifecycle_operator()
        app_operator = mock.MagicMock()
        core_client = mock.MagicMock()
        pods_list = mock.MagicMock()
        pods_list.items = []
        core_client.list_namespaced_pod.return_value = (
            pods_list
        )
        operator._delete_portieris_pods(
            app_operator, core_client
        )
        app_operator._kube.kube_delete_pod \
            .assert_not_called()
