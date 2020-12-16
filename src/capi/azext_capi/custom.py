# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def create_capi(cmd, resource_group_name, capi_name, location=None, tags=None):
    success, msgs = check_preqreqs()
    if not success:
        raise CLIError("\n".join(msgs))


def list_capi(cmd, resource_group_name=None):
    raise CLIError('TODO: Implement `capi list`')


def update_capi(cmd, instance, tags=None):
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags)
    return instance


def check_preqreqs(prompt=False):
    found, msgs = False, []

    # Identify a Kubernetes v1.16+ cluster
    if not find_management_cluster():
        msgs.append("Couldn't find management cluster")

    # Install clusterctl
    if not find_clusterctl():
        msgs.append("Couldn't find clusterctl")

    return found, msgs


def find_management_cluster():
    return False


def find_clusterctl():
    return False
