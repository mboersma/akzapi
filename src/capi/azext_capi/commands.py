# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azext_capi._client_factory import cf_capi


def load_command_table(self, _):

    with self.command_group('capi', is_preview=True) as g:
        g.custom_command('create', 'create_workload_cluster')
        g.custom_command('delete', 'delete_workload_cluster')
        g.custom_command('update', 'update_workload_cluster')

    with self.command_group('capi management', is_preview=True) as g:
        g.custom_command('create', 'create_management_cluster')
        g.custom_command('delete', 'delete_management_cluster')
        g.custom_command('move', 'move_management_cluster')
        g.custom_command('show', 'show_management_cluster')
        g.custom_command('update', 'update_management_cluster')
