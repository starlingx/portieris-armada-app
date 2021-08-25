#
# Copyright (c) 2021 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
# All Rights Reserved.
#

""" System inventory App lifecycle operator."""

from time import time

from k8sapp_portieris.common import constants as app_constants
from oslo_log import log as logging
from sysinv.common import constants
from sysinv.common import exception
from sysinv.helm import lifecycle_base as base
from sysinv.helm.lifecycle_hook import LifecycleHookInfo

LOG = logging.getLogger(__name__)

REAPPLY_PORTIERIS_WEBHOOK_OVERRIDE = "ReapplyAdmissionWebhook"


class PortierisAppLifecycleOperator(base.AppLifecycleOperator):
    def app_lifecycle_actions(self, context, conductor_obj, app_op, app, hook_info):
        """Perform lifecycle actions for an operation

        :param context: request context, can be None
        :param conductor_obj: conductor object, can be None
        :param app_op: AppOperator object
        :param app: AppOperator.Application object
        :param hook_info: LifecycleHookInfo object

        """
        if hook_info.lifecycle_type == constants.APP_LIFECYCLE_TYPE_OPERATION:
            if hook_info.operation == constants.APP_BACKUP:
                if hook_info.relative_timing == constants.APP_LIFECYCLE_TIMING_PRE:
                    return self.pre_backup(app_op, app)

        if hook_info.lifecycle_type == constants.APP_LIFECYCLE_TYPE_OPERATION:
            if hook_info.operation == constants.APP_BACKUP:
                if hook_info.relative_timing == constants.APP_LIFECYCLE_TIMING_POST:
                    return self.post_backup(app_op, app)

        if hook_info.lifecycle_type == constants.APP_LIFECYCLE_TYPE_OPERATION:
            if hook_info.operation == constants.APP_RESTORE:
                if hook_info.relative_timing == constants.APP_LIFECYCLE_TIMING_POST:
                    return self.post_restore(app_op, app)

        super(PortierisAppLifecycleOperator, self).app_lifecycle_actions(
            context, conductor_obj, app_op, app, hook_info
        )

    def pre_backup(self, app_op, app):
        LOG.debug(
            "Executing pre_backup for {} app".format(constants.HELM_APP_PORTIERIS)
        )
        webhook = self._get_portieris_mutating_webhook_configuration(app_op)

        if not webhook:
            LOG.info("Mutating webhook not present on system. Nothing to be done.")
            return

        webhook_name = webhook.metadata.name
        app_op._kube.kube_delete_mutating_webhook_configuration(webhook_name)

        dbapi_instance = app_op._dbapi
        db_app_id = dbapi_instance.kube_app_get(app.name).id

        user_overrides = self._get_helm_user_overrides(dbapi_instance, db_app_id)

        other_overrides = [
            override
            for override in user_overrides.split("\n")
            if REAPPLY_PORTIERIS_WEBHOOK_OVERRIDE not in override
        ]
        self._create_portieris_override(
            dbapi_instance, db_app_id, other_overrides, "false"
        )

    def post_backup(self, app_op, app):
        LOG.debug(
            "Executing post_backup for {} app".format(constants.HELM_APP_PORTIERIS)
        )
        self._recreate_portieries_mutating_webhook_configuration(app_op, app)

    def post_restore(self, app_op, app):
        LOG.debug(
            "Executing post_restore for {} app".format(constants.HELM_APP_PORTIERIS)
        )
        self._recreate_portieries_mutating_webhook_configuration(app_op, app)

    def _get_portieris_mutating_webhook_configuration(self, app_op):
        webhooks = app_op._kube.kube_get_mutating_webhook_configurations_by_selector(
            "app={}".format(constants.HELM_APP_PORTIERIS), ""
        )
        if len(webhooks) > 1:
            raise exception.LifecycleSemanticCheckException(
                "Multiple Mutating Webhook Configurations found for portieris"
            )
        if webhooks:
            return webhooks[0]

    def _recreate_portieries_mutating_webhook_configuration(self, app_op, app):
        webhook = self._get_portieris_mutating_webhook_configuration(app_op)
        if webhook:
            LOG.info("Mutating webhook found. Nothing to be done.")
            return

        dbapi_instance = app_op._dbapi
        db_app_id = dbapi_instance.kube_app_get(app.name).id

        user_overrides = self._get_helm_user_overrides(dbapi_instance, db_app_id)

        if REAPPLY_PORTIERIS_WEBHOOK_OVERRIDE not in user_overrides:
            LOG.info("Override for portieris webhook not found.")
            return

        LOG.info("Recreating portieris mutating webhook configuration.")

        other_overrides = [
            override
            for override in user_overrides.split("\n")
            if REAPPLY_PORTIERIS_WEBHOOK_OVERRIDE not in override
        ]

        # The timestamp is a unique value ensuring helm will 'upgrade' the
        # create-admission-webhooks job
        self._create_portieris_override(
            dbapi_instance, db_app_id, other_overrides, time()
        )

        # Reapply portieris
        lifecycle_hook_info = LifecycleHookInfo()
        lifecycle_hook_info.operation = constants.APP_APPLY_OP
        app_op.perform_app_apply(
            app._kube_app, constants.APP_LIFECYCLE_MODE_AUTO, lifecycle_hook_info
        )

        # Clean portieris override
        self._update_helm_user_overrides(
            dbapi_instance,
            db_app_id,
            "\n".join(other_overrides) or None,
        )

    def _get_helm_user_overrides(self, dbapi_instance, db_app_id):
        try:
            overrides = dbapi_instance.helm_override_get(
                app_id=db_app_id,
                name=app_constants.HELM_CHART_PORTIERIS,
                namespace=app_constants.HELM_NS_PORTIERIS,
            )
        except exception.HelmOverrideNotFound:
            values = {
                "name": app_constants.HELM_CHART_PORTIERIS,
                "namespace": app_constants.HELM_NS_PORTIERIS,
                "db_app_id": db_app_id,
            }
            overrides = dbapi_instance.helm_override_create(values=values)
        return overrides.user_overrides or ""

    def _update_helm_user_overrides(self, dbapi_instance, db_app_id, updated_overrides):
        dbapi_instance.helm_override_update(
            app_id=db_app_id,
            name=app_constants.HELM_CHART_PORTIERIS,
            namespace=app_constants.HELM_NS_PORTIERIS,
            values={"user_overrides": updated_overrides},
        )

    def _create_portieris_override(
        self, dbapi_instance, db_app_id, other_overrides, override_value
    ):
        portieris_override = "%s: %s" % (
            REAPPLY_PORTIERIS_WEBHOOK_OVERRIDE,
            override_value,
        )
        self._update_helm_user_overrides(
            dbapi_instance, db_app_id, "\n".join([portieris_override] + other_overrides)
        )
