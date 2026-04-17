#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Shared test helpers for portieris lifecycle tests."""

from unittest import mock

from k8sapp_portieris.lifecycle import lifecycle_portieris as lc


def _create_lifecycle_operator():
    """Create a PortierisAppLifecycleOperator instance.

    Mocks the parent class __init__ to avoid
    dependency on the full sysinv environment.

    Returns:
        PortierisAppLifecycleOperator instance.
    """
    with mock.patch(
        'sysinv.helm.lifecycle_base'
        '.AppLifecycleOperator.__init__',
        return_value=None
    ):
        return lc.PortierisAppLifecycleOperator()


def _create_mock_app_operator(user_overrides=''):
    """Create a mocked app operator with dbapi.

    Args:
        user_overrides: Helm user override string.

    Returns:
        MagicMock app operator with configured dbapi.
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
    return app_operator
