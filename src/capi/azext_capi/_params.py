# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

import os
import os.path
import platform

from knack.arguments import CLIArgumentType


def load_arguments(self, _):

    from azure.cli.core.commands.parameters import tags_type
    from azure.cli.core.commands.validators import get_default_location_from_resource_group

    capi_name_type = CLIArgumentType(options_list='--capi-name-name', help='Name of the Capi.', id_part='name')

    with self.argument_context('capi') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('capi_name', capi_name_type, options_list=['--name', '-n'])

    with self.argument_context('capi list') as c:
        c.argument('capi_name', capi_name_type, id_part=None)

    # with self.argument_context('capi init') as c:
    #     c.argument('install_location', type=file_type, completer=FilesCompleter(),
    #                default=_get_default_install_location('kubectl'))


def _get_default_install_location(exe_name):
    system = platform.system()
    if system == 'Windows':
        home_dir = os.environ.get('USERPROFILE')
        if not home_dir:
            return None
        install_location = os.path.join(home_dir, r'.azure-{0}\{0}.exe'.format(exe_name))
    elif system in ('Linux', 'Darwin'):
        install_location = '/usr/local/bin/{}'.format(exe_name)
    else:
        install_location = None
    return install_location
