#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for app_lifecycle_actions dispatch."""

import unittest
from unittest import mock

from k8sapp_portieris.tests.conftest import _create_lifecycle_operator
from sysinv.common import constants
from sysinv.helm.lifecycle_constants import LifecycleConstants
from sysinv.helm.lifecycle_hook import LifecycleHookInfo


def _create_lifecycle_hook(
    lifecycle_type, operation, timing, mode=None
):
    """Build a LifecycleHookInfo with given attributes.

    Args:
        lifecycle_type: Hook lifecycle type constant.
        operation: Hook operation constant.
        timing: Hook relative timing constant.
        mode: Optional hook mode constant.

    Returns:
        Configured LifecycleHookInfo instance.
    """
    hook_info = LifecycleHookInfo()
    hook_info.lifecycle_type = lifecycle_type
    hook_info.operation = operation
    hook_info.relative_timing = timing
    if mode is not None:
        hook_info.mode = mode
    return hook_info


class TestAppLifecyclePostApply(unittest.TestCase):
    """Test APP_APPLY_OP + POST dispatches post_apply."""

    def test_post_apply_called(self):
        """Verify post_apply dispatched."""
        operator = _create_lifecycle_operator()
        operator.post_apply = mock.MagicMock()
        app_operator = mock.MagicMock()
        mock_app = mock.MagicMock()
        hook_info = _create_lifecycle_hook(
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_OPERATION,
            constants.APP_APPLY_OP,
            LifecycleConstants
            .APP_LIFECYCLE_TIMING_POST,
        )
        operator.app_lifecycle_actions(
            None, None,
            app_operator, mock_app, hook_info
        )
        operator.post_apply.assert_called_once_with(
            app_operator, mock_app
        )


class TestAppLifecyclePreBackup(unittest.TestCase):
    """Test APP_BACKUP + PRE dispatches pre_backup."""

    def test_pre_backup_called(self):
        """Verify pre_backup dispatched."""
        operator = _create_lifecycle_operator()
        operator.pre_backup = mock.MagicMock()
        app_operator = mock.MagicMock()
        mock_app = mock.MagicMock()
        hook_info = _create_lifecycle_hook(
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_OPERATION,
            constants.APP_BACKUP,
            LifecycleConstants
            .APP_LIFECYCLE_TIMING_PRE,
        )
        operator.app_lifecycle_actions(
            None, None,
            app_operator, mock_app, hook_info
        )
        operator.pre_backup.assert_called_once_with(
            app_operator, mock_app
        )


class TestAppLifecyclePostBackup(unittest.TestCase):
    """Test APP_BACKUP + POST dispatches post_backup."""

    def test_post_backup_called(self):
        """Verify post_backup dispatched."""
        operator = _create_lifecycle_operator()
        operator.post_backup = mock.MagicMock()
        app_operator = mock.MagicMock()
        mock_app = mock.MagicMock()
        hook_info = _create_lifecycle_hook(
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_OPERATION,
            constants.APP_BACKUP,
            LifecycleConstants
            .APP_LIFECYCLE_TIMING_POST,
        )
        operator.app_lifecycle_actions(
            None, None,
            app_operator, mock_app, hook_info
        )
        operator.post_backup.assert_called_once_with(
            app_operator, mock_app
        )


class TestAppLifecyclePostRestore(unittest.TestCase):
    """Test APP_RESTORE + POST dispatches post_restore."""

    def test_post_restore_called(self):
        """Verify post_restore dispatched."""
        operator = _create_lifecycle_operator()
        operator.post_restore = mock.MagicMock()
        app_operator = mock.MagicMock()
        mock_app = mock.MagicMock()
        hook_info = _create_lifecycle_hook(
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_OPERATION,
            constants.APP_RESTORE,
            LifecycleConstants
            .APP_LIFECYCLE_TIMING_POST,
        )
        operator.app_lifecycle_actions(
            None, None,
            app_operator, mock_app, hook_info
        )
        operator.post_restore.assert_called_once_with(
            app_operator, mock_app
        )


class TestAppLifecyclePreUpdate(unittest.TestCase):
    """Test RESOURCE + UPDATE + PRE dispatches pre_update."""

    def test_pre_update_called(self):
        """Verify pre_update dispatched."""
        operator = _create_lifecycle_operator()
        operator.pre_update = mock.MagicMock()
        app_operator = mock.MagicMock()
        mock_app = mock.MagicMock()
        hook_info = _create_lifecycle_hook(
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_RESOURCE,
            constants.APP_UPDATE_OP,
            LifecycleConstants
            .APP_LIFECYCLE_TIMING_PRE,
        )
        operator.app_lifecycle_actions(
            None, None,
            app_operator, mock_app, hook_info
        )
        operator.pre_update.assert_called_once_with(
            app_operator, mock_app
        )


class TestAppLifecycleCleanUpdate(unittest.TestCase):
    """Test SEMANTIC_CHECK + AUTO + UPDATE + PRE."""

    def test_clean_update_called(self):
        """Verify clean_update dispatched."""
        operator = _create_lifecycle_operator()
        operator.clean_update = mock.MagicMock()
        app_operator = mock.MagicMock()
        mock_app = mock.MagicMock()
        hook_info = _create_lifecycle_hook(
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_SEMANTIC_CHECK,
            constants.APP_UPDATE_OP,
            LifecycleConstants
            .APP_LIFECYCLE_TIMING_PRE,
            mode=LifecycleConstants
            .APP_LIFECYCLE_MODE_AUTO,
        )
        operator.app_lifecycle_actions(
            None, None,
            app_operator, mock_app, hook_info
        )
        operator.clean_update.assert_called_once_with(
            app_operator, mock_app
        )


class TestAppLifecycleFallthrough(unittest.TestCase):
    """Test unmatched hook falls through to super."""

    @mock.patch(
        'sysinv.helm.lifecycle_base'
        '.AppLifecycleOperator'
        '.app_lifecycle_actions'
    )
    def test_super_called_for_unknown(
        self, mock_super
    ):
        """Verify super called for unknown hook."""
        operator = _create_lifecycle_operator()
        app_operator = mock.MagicMock()
        mock_app = mock.MagicMock()
        hook_info = _create_lifecycle_hook(
            'unknown_type',
            'unknown_op',
            'unknown_timing',
        )
        operator.app_lifecycle_actions(
            None, None,
            app_operator, mock_app, hook_info
        )
        mock_super.assert_called_once()
