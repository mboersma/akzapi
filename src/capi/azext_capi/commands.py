# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azext_capi._client_factory import cf_capi


def load_command_table(self, _):

    # TODO: Add command type here
    # capi_sdk = CliCommandType(
    #    operations_tmpl='<PATH>.operations#None.{}',
    #    client_factory=cf_capi)


    with self.command_group('capi') as g:
        g.custom_command('create', 'create_capi')
        # g.command('delete', 'delete')
        g.custom_command('list', 'list_capi')
        # g.show_command('show', 'get')
        # g.generic_update_command('update', setter_name='update', custom_func_name='update_capi')


    with self.command_group('capi', is_preview=True):
        pass

