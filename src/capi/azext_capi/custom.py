# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64
import os
import platform
import re
import ssl
import stat
import subprocess
import sys

from ._params import _get_default_install_location
from azure.cli.core.util import in_cloud_console

from knack.log import get_logger
from knack.util import CLIError
from six.moves.urllib.request import urlopen  # pylint: disable=import-error


logger = get_logger(__name__)


def create_management_cluster(cmd):
    # TODO: add user confirmation
    check_preqreqs(cmd)
    cmd = ["clusterctl", "init", "--infrastructure", "azure"]
    try:
        output = subprocess.check_output(cmd, universal_newlines=True)
        logger.info("`{}` returned:\n{}".format(" ".join(cmd), output))
    except subprocess.CalledProcessError as err:
        raise CLIError(err)


def delete_management_cluster(cmd):
    # TODO: add user confirmation
    cmd = ["clusterctl", "delete", "--all", "--include-crd", "--include-namespace"]
    try:
        output = subprocess.check_output(cmd, universal_newlines=True)
        logger.info("`{}` returned:\n{}".format(" ".join(cmd), output))
    except subprocess.CalledProcessError as err:
        raise CLIError(err)
    namespaces = [
        "capi-kubeadm-bootstrap-system",
        "capi-kubeadm-control-plane-system",
        "capi-system",
        "capi-webhook-system",
        "capz-system",
        "cert-manager",
    ]
    cmd = ["kubectl", "delete", "namespace", "--ignore-not-found"] + namespaces
    try:
        output = subprocess.check_output(cmd, universal_newlines=True)
        logger.info("`{}` returned:\n{}".format(" ".join(cmd), output))
    except subprocess.CalledProcessError as err:
        raise CLIError(err)


def move_management_cluster(cmd):
    pass


def show_management_cluster(cmd):
    # TODO: echo details of the management cluster in all output formats
    pass


def update_management_cluster(cmd):
    # Check for local prerequisites
    check_preqreqs(cmd)
    cmd = [
        "clusterctl",
        "upgrade",
        "apply",
        "--management-group",
        "capi-system/cluster-api",
        "--contract",
        "v1alpha3",
    ]
    try:
        output = subprocess.check_output(cmd, universal_newlines=True)
        logger.info("`{}` returned:\n{}".format(" ".join(cmd), output))
    except subprocess.CalledProcessError as err:
        raise CLIError(err)


def create_workload_cluster(
    cmd,
    resource_group_name,
    capi_name,
    location=None,
    control_plane_machine_type="Standard_D2s_v3",
    control_plane_machine_count=3,
    node_machine_type="Standard_D2s_v3",
    node_machine_count=3,
    kubernetes_version="1.20.1",
    azure_cloud="AzurePublicCloud",
):
    # Check for local prerequisites
    check_preqreqs(cmd)
    # Identify a Kubernetes v1.16+ management cluster
    find_management_cluster()
    # Generate the cluster configuration
    cmd = [
        "clusterctl",
        "config",
        "cluster",
        capi_name,
        "--control-plane-machine-count={}".format(control_plane_machine_count),
        "--worker-machine-count={}".format(node_machine_count),
        "--kubernetes-version={}".format(kubernetes_version),
    ]
    # Some CAPZ options need to be set as env vars, not clusterctl arguments.
    os.environ.update(
        {
            "AZURE_CONTROL_PLANE_MACHINE_TYPE": control_plane_machine_type,
            "AZURE_NODE_MACHINE_TYPE": node_machine_type,
            "AZURE_LOCATION": location,
            "AZURE_ENVIRONMENT": azure_cloud,
        }
    )
    try:
        # TODO: save cluster configuration to .yaml file
        output = subprocess.check_output(cmd, universal_newlines=True)
        logger.info("`{}` returned:\n{}".format(" ".join(cmd), output))
    except subprocess.CalledProcessError as err:
        raise CLIError(err)
    # Apply the cluster configuration
    filename = "foo"
    cmd = ["kubectl", "apply", "-f", filename]
    try:
        output = subprocess.check_output(cmd, universal_newlines=True)
        logger.info("`{}` returned:\n{}".format(" ".join(cmd), output))
    except subprocess.CalledProcessError as err:
        raise CLIError(err)
    # AAD Pod identity we create RG and it's scoped to the RG


def delete_workload_cluster(cmd):
    # Check for local prerequisites
    check_preqreqs(cmd)


def update_workload_cluster(cmd):
    # Check for local prerequisites
    check_preqreqs(cmd)


# def list_capi(cmd, resource_group_name=None):
#     raise CLIError('TODO: Implement `capi list`')


# def update_capi(cmd, instance, tags=None):
#     with cmd.update_context(instance) as c:
#         c.set_param('tags', tags)
#     return instance


def check_preqreqs(cmd):
    # Install kubectl
    if not which("kubectl"):
        install_kubectl(cmd)

    # Install clusterctl
    if not which("clusterctl"):
        install_clusterctl(cmd)

    # Check for required environment variables
    for var in [
        "AZURE_CLIENT_ID",
        "AZURE_CLIENT_SECRET",
        "AZURE_SUBSCRIPTION_ID",
        "AZURE_TENANT_ID",
    ]:
        check_environment_var(var)


def check_environment_var(var):
    var_b64 = var + "_B64"
    val = os.environ.get(var_b64)
    if val:
        logger.info("Found environment variable {}".format(var_b64))
    else:
        try:
            val = os.environ[var]
        except KeyError as err:
            raise CLIError(
                "Required environment variable {} was not found.".format(err)
            )
        # Set the base64-encoded variable as a convenience
        val = base64.b64encode(val.encode("utf-8")).decode("ascii")
        os.environ[var_b64] = val
        logger.info("Set environment variable {} from {}".format(var_b64, var))


def find_management_cluster():
    cmd = ["kubectl", "cluster-info"]
    output = subprocess.check_output(cmd, universal_newlines=True)
    logger.info("`{}` returned:\n{}".format(" ".join(cmd), output))
    match = re.search(r"Kubernetes control plane.*?is running", output)
    if match is None:
        raise CLIError("No accessible Kubernetes cluster found")
    cmd = ["kubectl", "get", "pods", "--namespace", "capz-system"]
    try:
        output = subprocess.check_output(cmd, universal_newlines=True)
        logger.info("`{}` returned:\n{}".format(" ".join(cmd), output))
        match = re.search(r"capz-controller-manager-.+?Running", output)
        if match is None:
            raise CLIError("No CAPZ installation found")
    except subprocess.CalledProcessError as err:
        logger.error(err)

    # cmd = ["clusterctl", "config", "provider", "--infrastructure", "azure"]
    # output = subprocess.check_output(cmd).decode("utf-8")
    # logger.info("`{}` returned:\n{}".format(" ".join(cmd), output))
    # match = re.search(r"Version:\s+(\S+)", output)
    # if match is None:
    #     raise CLIError("No CAPI installation found")
    # capi_version = match.group(1)
    # logger.warn("Cluster API Provider for Azure version is {}".format(capi_version))


def which(binary):
    path_var = os.getenv("PATH")

    if platform.system() == "Windows":
        binary += ".exe"
        parts = path_var.split(";")
    else:
        parts = path_var.split(":")

    for part in parts:
        bin_path = os.path.join(part, binary)
        if os.path.isfile(bin_path) and os.access(bin_path, os.X_OK):
            return bin_path

    return None


def install_clusterctl(
    cmd, client_version="latest", install_location=None, source_url=None
):
    """
    Install clusterctl, a command-line interface for Cluster API Kubernetes clusters.
    """

    if not source_url:
        source_url = "https://github.com/kubernetes-sigs/cluster-api/releases/"
        # TODO: mirror clusterctl binary to Azure China cloud--see install_kubectl().

    if client_version != "latest":
        source_url += "tags/"
    source_url += "{}/download/clusterctl-{}-amd64"

    file_url = ""
    system = platform.system()
    if system in ("Darwin", "Linux"):
        file_url = source_url.format(client_version, system.lower())
    else:  # TODO: support Windows someday?
        raise CLIError('The clusterctl binary is not available for "{}"'.format(system))

    # ensure installation directory exists
    if install_location is None:
        install_location = _get_default_install_location("clusterctl")
    install_dir, cli = os.path.dirname(install_location), os.path.basename(
        install_location
    )
    if not os.path.exists(install_dir):
        os.makedirs(install_dir)

    logger.warning('Downloading client to "%s" from "%s"', install_location, file_url)
    try:
        _urlretrieve(file_url, install_location)
        perms = (
            os.stat(install_location).st_mode
            | stat.S_IXUSR
            | stat.S_IXGRP
            | stat.S_IXOTH
        )
        os.chmod(install_location, perms)
    except IOError as ex:
        raise CLIError(
            "Connection error while attempting to download client ({})".format(ex)
        )

    logger.warning(
        "Please ensure that %s is in your search PATH, so the `%s` command can be found.",
        install_dir,
        cli,
    )


def install_kubectl(
    cmd, client_version="latest", install_location=None, source_url=None
):
    """
    Install kubectl, a command-line interface for Kubernetes clusters.
    """

    if not source_url:
        source_url = "https://storage.googleapis.com/kubernetes-release/release"
        cloud_name = cmd.cli_ctx.cloud.name
        if cloud_name.lower() == "azurechinacloud":
            source_url = "https://mirror.azure.cn/kubernetes/kubectl"

    if client_version == "latest":
        context = _ssl_context()
        version = urlopen(source_url + "/stable.txt", context=context).read()
        client_version = version.decode("UTF-8").strip()
    else:
        client_version = "v%s" % client_version

    file_url = ""
    system = platform.system()
    base_url = source_url + "/{}/bin/{}/amd64/{}"

    # ensure installation directory exists
    if install_location is None:
        install_location = _get_default_install_location("kubectl")
    install_dir, cli = os.path.dirname(install_location), os.path.basename(
        install_location
    )
    if not os.path.exists(install_dir):
        os.makedirs(install_dir)

    if system == "Windows":
        file_url = base_url.format(client_version, "windows", "kubectl.exe")
    elif system == "Linux":
        # TODO: Support ARM CPU here
        file_url = base_url.format(client_version, "linux", "kubectl")
    elif system == "Darwin":
        file_url = base_url.format(client_version, "darwin", "kubectl")
    else:
        raise CLIError(
            "Proxy server ({}) does not exist on the cluster.".format(system)
        )

    logger.warning('Downloading client to "%s" from "%s"', install_location, file_url)
    try:
        _urlretrieve(file_url, install_location)
        os.chmod(
            install_location,
            os.stat(install_location).st_mode
            | stat.S_IXUSR
            | stat.S_IXGRP
            | stat.S_IXOTH,
        )
    except IOError as ex:
        raise CLIError(
            "Connection error while attempting to download client ({})".format(ex)
        )

    if (
        system == "Windows"
    ):  # be verbose, as the install_location likely not in Windows's search PATHs
        env_paths = os.environ["PATH"].split(";")
        found = next(
            (x for x in env_paths if x.lower().rstrip("\\") == install_dir.lower()),
            None,
        )
        if not found:
            # pylint: disable=logging-format-interpolation
            logger.warning(
                'Please add "{0}" to your search PATH so the `{1}` can be found. 2 options: \n'
                '    1. Run "set PATH=%PATH%;{0}" or "$env:path += \'{0}\'" for PowerShell. '
                "This is good for the current command session.\n"
                "    2. Update system PATH environment variable by following "
                '"Control Panel->System->Advanced->Environment Variables", and re-open the command window. '
                "You only need to do it once".format(install_dir, cli)
            )
    else:
        logger.warning(
            "Please ensure that %s is in your search PATH, so the `%s` command can be found.",
            install_dir,
            cli,
        )


def _ssl_context():
    if sys.version_info < (3, 4) or (
        in_cloud_console() and platform.system() == "Windows"
    ):
        try:
            return ssl.SSLContext(ssl.PROTOCOL_TLS)  # added in python 2.7.13 and 3.6
        except AttributeError:
            return ssl.SSLContext(ssl.PROTOCOL_TLSv1)

    return ssl.create_default_context()


def _urlretrieve(url, filename):
    req = urlopen(url, context=_ssl_context())
    with open(filename, "wb") as f:
        f.write(req.read())
