#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for webhook recreate and module constants."""

import unittest
from unittest import mock

from k8sapp_portieris.lifecycle import lifecycle_portieris as lc
from k8sapp_portieris.tests.conftest import _create_lifecycle_operator
from k8sapp_portieris.tests.conftest import _create_mock_app_operator


class TestRecreateWebhookAlreadyExists(unittest.TestCase):
    """Test recreate when webhook already exists."""

    def test_returns_early(self):
        """Verify early return when webhook found."""
        operator = _create_lifecycle_operator()
        app_operator = _create_mock_app_operator()
        mock_webhook = mock.MagicMock()
        app_operator._kube \
            .kube_get_mutating_webhook_configurations_by_selector \
            .return_value = [mock_webhook]
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        method = getattr(
            operator,
            '_recreate_portieris'
            '_mutating_webhook_configuration'
        )
        method(app_operator, mock_app)
        app_operator.perform_app_apply \
            .assert_not_called()


class TestRecreateNoOverride(unittest.TestCase):
    """Test recreate with no ReapplyAdmissionWebhook."""

    def test_returns_early(self):
        """Verify early return without override."""
        operator = _create_lifecycle_operator()
        app_operator = _create_mock_app_operator(
            user_overrides='other: val'
        )
        app_operator._kube \
            .kube_get_mutating_webhook_configurations_by_selector \
            .return_value = []
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        method = getattr(
            operator,
            '_recreate_portieris'
            '_mutating_webhook_configuration'
        )
        method(app_operator, mock_app)
        app_operator.perform_app_apply \
            .assert_not_called()


class TestRecreateWithOverride(unittest.TestCase):
    """Test recreate with override and no webhook."""

    def test_reapplies_and_cleans(self):
        """Verify reapply and cleanup performed."""
        operator = _create_lifecycle_operator()
        overrides = (
            'ReapplyAdmissionWebhook: false\n'
            'other: val'
        )
        app_operator = _create_mock_app_operator(
            user_overrides=overrides
        )
        app_operator._kube \
            .kube_get_mutating_webhook_configurations_by_selector \
            .return_value = []
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        method = getattr(
            operator,
            '_recreate_portieris'
            '_mutating_webhook_configuration'
        )
        method(app_operator, mock_app)
        app_operator.perform_app_apply \
            .assert_called_once()
        self.assertEqual(
            app_operator._dbapi
            .helm_override_update.call_count,
            2
        )


class TestPreBackupFiltersOverrides(unittest.TestCase):
    """Test pre_backup filters ReapplyAdmissionWebhook."""

    def test_filters_existing_reapply_override(self):
        """Verify existing reapply override filtered."""
        operator = _create_lifecycle_operator()
        overrides = (
            'ReapplyAdmissionWebhook: old\n'
            'other: val'
        )
        app_operator = _create_mock_app_operator(
            user_overrides=overrides
        )
        mock_webhook = mock.MagicMock()
        mock_webhook.metadata.name = 'test-webhook'
        app_operator._kube \
            .kube_get_mutating_webhook_configurations_by_selector \
            .return_value = [mock_webhook]
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.pre_backup(app_operator, mock_app)
        call_kwargs = (
            app_operator._dbapi
            .helm_override_update.call_args
        )
        updated = (
            call_kwargs[1]['values']['user_overrides']
        )
        self.assertIn(
            'ReapplyAdmissionWebhook: false', updated
        )
        self.assertIn('other: val', updated)


class TestModuleConstants(unittest.TestCase):
    """Test module-level constants."""

    def test_reapply_webhook_override(self):
        """Verify REAPPLY_PORTIERIS_WEBHOOK_OVERRIDE."""
        self.assertEqual(
            lc.REAPPLY_PORTIERIS_WEBHOOK_OVERRIDE,
            'ReapplyAdmissionWebhook'
        )

    def test_post_upgrade_policy(self):
        """Verify POST_UPGRADE_POLICY_OVERRIDE."""
        self.assertEqual(
            lc.POST_UPGRADE_POLICY_OVERRIDE,
            'PostUpgradePolicy'
        )

    def test_null_value(self):
        """Verify NULL_VALUE constant."""
        self.assertEqual(lc.NULL_VALUE, '~')
