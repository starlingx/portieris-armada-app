#
# Copyright (c) 2021,2025 Wind River Systems, Inc.
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
from sysinv.helm.lifecycle_constants import LifecycleConstants
from sysinv.helm.lifecycle_hook import LifecycleHookInfo
import os
import yaml

LOG = logging.getLogger(__name__)

REAPPLY_PORTIERIS_WEBHOOK_OVERRIDE = "ReapplyAdmissionWebhook"
POST_UPGRADE_POLICY_OVERRIDE = 'PostUpgradePolicy'
NULL_VALUE = '~'


class PortierisAppLifecycleOperator(base.AppLifecycleOperator):
    def app_lifecycle_actions(self, context, conductor_obj, app_op, app, hook_info):
        """Perform lifecycle actions for an operation

        :param context: request context, can be None
        :param conductor_obj: conductor object, can be None
        :param app_op: AppOperator object
        :param app: AppOperator.Application object
        :param hook_info: LifecycleHookInfo object

        """
        if hook_info.lifecycle_type == LifecycleConstants.APP_LIFECYCLE_TYPE_OPERATION:
            # Apply
            if hook_info.operation == constants.APP_APPLY_OP:
                if hook_info.relative_timing == LifecycleConstants.APP_LIFECYCLE_TIMING_POST:
                    return self.post_apply(app_op, app)

            # B&R
            if hook_info.operation == constants.APP_BACKUP:
                if hook_info.relative_timing == LifecycleConstants.APP_LIFECYCLE_TIMING_PRE:
                    return self.pre_backup(app_op, app)

                if hook_info.relative_timing == LifecycleConstants.APP_LIFECYCLE_TIMING_POST:
                    return self.post_backup(app_op, app)

            if hook_info.operation == constants.APP_RESTORE:
                if hook_info.relative_timing == LifecycleConstants.APP_LIFECYCLE_TIMING_POST:
                    return self.post_restore(app_op, app)

        # Update
        if hook_info.lifecycle_type == LifecycleConstants.APP_LIFECYCLE_TYPE_RESOURCE:
            # Prepare
            if hook_info.operation == constants.APP_UPDATE_OP:
                if hook_info.relative_timing == LifecycleConstants.APP_LIFECYCLE_TIMING_PRE:
                    return self.pre_update(app_op, app)

        if hook_info.lifecycle_type == LifecycleConstants.APP_LIFECYCLE_TYPE_SEMANTIC_CHECK:
            # Cleanup
            if hook_info.mode == LifecycleConstants.APP_LIFECYCLE_MODE_AUTO:
                if hook_info.operation == constants.APP_UPDATE_OP:
                    if hook_info.relative_timing == LifecycleConstants.APP_LIFECYCLE_TIMING_PRE:
                        return self.clean_update(app_op, app)

        super(PortierisAppLifecycleOperator, self).app_lifecycle_actions(
            context, conductor_obj, app_op, app, hook_info
        )

    def pre_update(self, app_op, app):
        """Post update actions

        Change the MutatingWebhookConfiguration 'failurePolicy' to Ignore. The default
        value 'Fail' can cause issues during upgrades.

        :param app_op: AppOperator object
        :param app: AppOperator.Application object
        """
        LOG.debug(
            "Executing pre_update for {} app".format(constants.HELM_APP_PORTIERIS)
        )
        dbapi_instance = app_op._dbapi
        db_app_id = dbapi_instance.kube_app_get(app.name).id
        user_overrides = yaml.safe_load(
            self._get_helm_user_overrides(dbapi_instance, db_app_id)) or {}

        if user_overrides.get(POST_UPGRADE_POLICY_OVERRIDE, None) is not None:
            LOG.info("Post-upgrade policy override already filled. Ignoring.")
            return

        postUpgradePolicy = user_overrides.get('webHooks', {}).get('failurePolicy', None)
        if postUpgradePolicy is None:
            postUpgradePolicy = NULL_VALUE
        else:
            LOG.debug("failurePolicy original value is %s" % postUpgradePolicy)

        user_overrides.update({POST_UPGRADE_POLICY_OVERRIDE: postUpgradePolicy})
        webhook_overrides = user_overrides.get('webHooks', {})
        webhook_overrides.update({'failurePolicy': 'Ignore'})
        user_overrides['webHooks'] = webhook_overrides

        self._update_helm_user_overrides(
            dbapi_instance, db_app_id, yaml.dump(user_overrides, default_flow_style=False))

    def clean_update(self, app_op, app):
        """Clean update changes

        Reapply the values changed in the MutatingWebhookConfiguration during pre update.

        :param app_op: AppOperator object
        :param app: AppOperator.Application object
        """
        dbapi_instance = app_op._dbapi
        db_app_id = dbapi_instance.kube_app_get(app.name).id
        user_overrides = yaml.safe_load(
            self._get_helm_user_overrides(dbapi_instance, db_app_id)) or {}

        if os.path.exists(constants.USM_UPGRADE_IN_PROGRESS):
            LOG.info("Upgrade is in progress. Avoiding cleaning portieris update flag.")
            return

        postUpgradePolicy = user_overrides.pop(POST_UPGRADE_POLICY_OVERRIDE, None)
        if postUpgradePolicy is None:
            return

        LOG.info(
            "Executing post_update clean for {} app".format(constants.HELM_APP_PORTIERIS)
        )

        if postUpgradePolicy == NULL_VALUE:
            LOG.info("Removing webhook temporary override for failurePolicy.")
            if len(user_overrides.get('webHooks', {})) <= 1:
                user_overrides.pop('webHooks', None)
            else:
                user_overrides['webHooks'].pop('failurePolicy', None)
        else:
            LOG.info("Restoring webhook override failurePolicy: %s" % postUpgradePolicy)
            webhook_overrides = user_overrides.get('webHooks', {})
            webhook_overrides.update({'failurePolicy': postUpgradePolicy})
            user_overrides['webHooks'] = webhook_overrides

        self._update_helm_user_overrides(
            dbapi_instance, db_app_id, yaml.dump(user_overrides, default_flow_style=False))

        # Reapply portieris
        LOG.info("Cleaned update overrides. Reapplying portieris.")
        lifecycle_hook_info = LifecycleHookInfo()
        lifecycle_hook_info.operation = constants.APP_APPLY_OP
        app_op.perform_app_apply(
            app._kube_app, LifecycleConstants.APP_LIFECYCLE_MODE_AUTO, lifecycle_hook_info
        )

    def post_apply(self, app_op, app):
        """Post Apply actions

        Creates the local registry secret and migrates helm user overrides
        from one chart name to another

        :param app_op: AppOperator object
        :param app: AppOperator.Application object
        """
        LOG.info(
            "Executing post_apply for {} app".format(constants.HELM_APP_PORTIERIS)
        )

        dbapi_instance = app_op._dbapi
        db_app_id = dbapi_instance.kube_app_get(app.name).id

        client_core = app_op._kube._get_kubernetesclient_core()
        component_constant = app_constants.HELM_COMPONENT_LABEL_PORTIERIS

        # chart overrides
        chart_overrides = self._get_helm_user_overrides(
            dbapi_instance,
            db_app_id)

        override_label = {}

        # Namespaces variables
        namespace = client_core.read_namespace(app_constants.HELM_APP_PORTIERIS)

        # Old namespace variable
        old_namespace_label = (namespace.metadata.labels.get(component_constant)
                               if component_constant in namespace.metadata.labels
                               else None)

        if component_constant in chart_overrides:
            # User Override variables
            dict_chart_overrides = yaml.safe_load(chart_overrides)
            override_label = dict_chart_overrides.get(component_constant)

        if override_label == 'application':
            namespace.metadata.labels.update({component_constant: 'application'})
            app_op._kube.kube_patch_namespace(app_constants.HELM_APP_PORTIERIS, namespace)
        elif override_label == 'platform':
            namespace.metadata.labels.update({component_constant: 'platform'})
            app_op._kube.kube_patch_namespace(app_constants.HELM_APP_PORTIERIS, namespace)
        elif not override_label:
            namespace.metadata.labels.update({component_constant: 'platform'})
            app_op._kube.kube_patch_namespace(app_constants.HELM_APP_PORTIERIS, namespace)
        else:
            LOG.info(f'WARNING: Namespace label {override_label} not supported')

        namespace_label = namespace.metadata.labels.get(component_constant)
        if old_namespace_label != namespace_label:
            self._delete_portieris_pods(app_op, client_core)

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
            app._kube_app, LifecycleConstants.APP_LIFECYCLE_MODE_AUTO, lifecycle_hook_info
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
        if updated_overrides is not None and updated_overrides.rstrip('\n') == '{}':
            updated_overrides = None
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

    def _delete_portieris_pods(self, app_op, client_core):
        # pod list
        pods = client_core.list_namespaced_pod(app_constants.HELM_NS_PORTIERIS)

        # Delete pods to force restart when it have any change in namespace_label
        for pod in pods.items:
            app_op._kube.kube_delete_pod(
                name=pod.metadata.name,
                namespace=app_constants.HELM_NS_PORTIERIS,
                grace_periods_seconds=0
            )
