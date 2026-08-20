#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for pre_update and clean_update methods."""

import unittest
from unittest import mock

from k8sapp_portieris.tests.conftest import _create_lifecycle_operator
from k8sapp_portieris.tests.conftest import _create_mock_app_operator


class TestPreUpdateNoExistingOverride(unittest.TestCase):
    """Test pre_update with no PostUpgradePolicy."""

    def test_sets_failure_policy_ignore(self):
        """Verify failure policy is set to Ignore."""
        operator = _create_lifecycle_operator()
        app_operator = _create_mock_app_operator(
            user_overrides=''
        )
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.pre_update(app_operator, mock_app)
        app_operator._dbapi.helm_override_update \
            .assert_called_once()
        call_kwargs = (
            app_operator._dbapi
            .helm_override_update.call_args
        )
        updated = (
            call_kwargs[1]['values']['user_overrides']
        )
        self.assertIn('Ignore', updated)


class TestPreUpdateExistingPolicy(unittest.TestCase):
    """Test pre_update when PostUpgradePolicy set."""

    def test_returns_early(self):
        """Verify no update when policy exists."""
        operator = _create_lifecycle_operator()
        app_operator = _create_mock_app_operator(
            user_overrides='PostUpgradePolicy: Fail\n'
        )
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.pre_update(app_operator, mock_app)
        app_operator._dbapi.helm_override_update \
            .assert_not_called()


class TestPreUpdateWithWebhooks(unittest.TestCase):
    """Test pre_update with existing failurePolicy."""

    def test_preserves_original_policy(self):
        """Verify original webhook policy preserved."""
        operator = _create_lifecycle_operator()
        overrides = (
            'webHooks:\n  failurePolicy: Fail\n'
        )
        app_operator = _create_mock_app_operator(
            user_overrides=overrides
        )
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.pre_update(app_operator, mock_app)
        call_kwargs = (
            app_operator._dbapi
            .helm_override_update.call_args
        )
        updated = (
            call_kwargs[1]['values']['user_overrides']
        )
        self.assertIn('PostUpgradePolicy', updated)
        self.assertIn('Ignore', updated)


class TestCleanUpdateUpgradeInProgress(unittest.TestCase):
    """Test clean_update during upgrade."""

    @mock.patch('os.path.exists', return_value=True)
    def test_returns_early_during_upgrade(
        self, _mock_exists
    ):
        """Verify no update during active upgrade."""
        operator = _create_lifecycle_operator()
        app_operator = _create_mock_app_operator(
            user_overrides='PostUpgradePolicy: Fail\n'
        )
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.clean_update(app_operator, mock_app)
        app_operator._dbapi.helm_override_update \
            .assert_not_called()


class TestCleanUpdateNoPolicy(unittest.TestCase):
    """Test clean_update with no PostUpgradePolicy."""

    @mock.patch('os.path.exists', return_value=False)
    def test_returns_early_no_policy(
        self, _mock_exists
    ):
        """Verify no update when policy absent."""
        operator = _create_lifecycle_operator()
        app_operator = _create_mock_app_operator(
            user_overrides=''
        )
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.clean_update(app_operator, mock_app)
        app_operator._dbapi.helm_override_update \
            .assert_not_called()


class TestCleanUpdateNullValue(unittest.TestCase):
    """Test clean_update with null value policy."""

    @mock.patch('os.path.exists', return_value=False)
    def test_removes_webhook_override(
        self, _mock_exists
    ):
        """Verify webhook override removed."""
        operator = _create_lifecycle_operator()
        overrides = (
            'PostUpgradePolicy: "~"\n'
            'webHooks:\n  failurePolicy: Ignore\n'
        )
        app_operator = _create_mock_app_operator(
            user_overrides=overrides
        )
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.clean_update(app_operator, mock_app)
        app_operator._dbapi.helm_override_update \
            .assert_called()
        app_operator.perform_app_apply \
            .assert_called_once()


class TestCleanUpdateRestoresPolicy(unittest.TestCase):
    """Test clean_update restores failurePolicy."""

    @mock.patch('os.path.exists', return_value=False)
    def test_restores_failure_policy(
        self, _mock_exists
    ):
        """Verify original failure policy restored."""
        operator = _create_lifecycle_operator()
        overrides = (
            'PostUpgradePolicy: Fail\n'
            'webHooks:\n  failurePolicy: Ignore\n'
        )
        app_operator = _create_mock_app_operator(
            user_overrides=overrides
        )
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.clean_update(app_operator, mock_app)
        call_kwargs = (
            app_operator._dbapi
            .helm_override_update.call_args
        )
        updated = (
            call_kwargs[1]['values']['user_overrides']
        )
        self.assertIn('Fail', updated)


class TestCleanUpdateNullOnlyWebhook(unittest.TestCase):
    """Test clean_update null with only failurePolicy."""

    @mock.patch('os.path.exists', return_value=False)
    def test_removes_webhooks_key(
        self, _mock_exists
    ):
        """Verify webhooks key removed."""
        operator = _create_lifecycle_operator()
        overrides = (
            'PostUpgradePolicy: "~"\n'
            'webHooks:\n  failurePolicy: Ignore\n'
        )
        app_operator = _create_mock_app_operator(
            user_overrides=overrides
        )
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.clean_update(app_operator, mock_app)
        app_operator._dbapi.helm_override_update \
            .assert_called()


class TestCleanUpdateNullMultipleWebhooks(unittest.TestCase):
    """Test clean_update null with multiple webhooks."""

    @mock.patch('os.path.exists', return_value=False)
    def test_keeps_other_webhook_keys(
        self, _mock_exists
    ):
        """Verify other webhook keys preserved."""
        operator = _create_lifecycle_operator()
        overrides = (
            'PostUpgradePolicy: "~"\n'
            'webHooks:\n  failurePolicy: Ignore\n'
            '  otherKey: value\n'
        )
        app_operator = _create_mock_app_operator(
            user_overrides=overrides
        )
        mock_app = mock.MagicMock()
        mock_app.name = 'portieris'
        operator.clean_update(app_operator, mock_app)
        call_kwargs = (
            app_operator._dbapi
            .helm_override_update.call_args
        )
        updated = (
            call_kwargs[1]['values']['user_overrides']
        )
        self.assertNotIn('PostUpgradePolicy', updated)
