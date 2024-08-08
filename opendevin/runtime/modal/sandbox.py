import modal
import atexit
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from opendevin.core.config import SandboxConfig
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import CancellableStream
from opendevin.runtime.sandbox import Sandbox


image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "curl",
        "wget",
        "git",
        "vim",
        "nano",
        "unzip",
        "zip",
        "build-essential",
        "openssh-server",
        "sudo",
        "gcc",
        "jq",
        "g++",
        "make",
        "iproute2",
    )
    .run_commands(
        """wget --progress=bar:force -O Miniforge3.sh \
            "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" && \
            bash Miniforge3.sh -b -p /opendevin/miniforge3 
            """
    )
    .run_commands("/opendevin/miniforge3/bin/pip install --upgrade pip")
    .run_commands(
        "/opendevin/miniforge3/bin/pip install jupyterlab notebook jupyter_kernel_gateway flake8"
    )
    .run_commands(
        "/opendevin/miniforge3/bin/pip install python-docx PyPDF2 python-pptx pylatexenc openai"
    )
    .run_commands(
        "/opendevin/miniforge3/bin/pip install python-dotenv toml termcolor pydantic python-docx pyyaml docker pexpect tenacity e2b browsergym minio"
    )
    .run_commands("echo '' > /opendevin/bash.bashrc && mkdir -p /opendevin/logs")
)

workspace_volume = modal.Volume.from_name(
    "opendevin-workspace-volume", create_if_missing=True
)
workdir_volume = modal.Volume.from_name(
    "opendevin-workdir-volume", create_if_missing=True
)

# mounts = [
#     modal.Mount.from_local_dir(
#         "/root/opendevin/runtime/plugins",
#         remote_path="/opendevin/plugins",
#     )
# ]


class ModalSandBox(Sandbox):
    def __init__(
        self,
        config: SandboxConfig,
        # workspace_base: str,
    ):
        self.config = config
        # self.sandbox = None # create modal sandbox here
        # os.makedirs(workspace_base, exist_ok=True)
        # self.workspace_base = workspace_base
        # atexit.register(self.cleanup)

        self.mounts = []

        super().__init__(config)

    def execute(
        self, cmd: str, stream: bool = False, timeout: int | None = None
    ) -> tuple[int, str | CancellableStream]:
        # local_dir = Path(TemporaryDirectory().name)

        logger.info(f"executing command: `{cmd}`")
        logger.info(f"mounts: {self.mounts}")

        sb = modal.Sandbox.create(
            "bash",
            "-c",
            cmd,
            image=image,
            volumes={
                os.environ["WORKSPACE_MOUNT_PATH"]: workspace_volume,
                "/app": workdir_volume,
            },
            mounts=self.mounts,
            timeout=120,  # 1 minute
            workdir="/app",
        )

        sb.wait()

        returncode = sb.returncode
        stdout = sb.stdout.read()
        stderr = sb.stderr.read()

        logger.info(f"returncode: {returncode}")
        logger.info(f"stdout: {stdout}")
        logger.info(f"stderr: {stderr}")

        # return (sb.returncode, sb.stdout.read(), sb.stderr.read())
        return (returncode, stdout)

    def close(self):
        logger.info("closing sandbox")

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        logger.info(f"copying {host_src} to {sandbox_dest}, recursive={recursive}")

        sandbox_dest = Path(sandbox_dest) / Path(host_src).name

        if recursive:
            self.mounts.append(
                modal.Mount.from_local_dir(host_src, remote_path=sandbox_dest)
            )
        else:
            self.mounts.append(
                modal.Mount.from_local_file(host_src, remote_path=sandbox_dest)
            )

        # raise NotImplementedError

    def get_working_directory(self):
        logger.info("getting working directory")
        # raise NotImplementedError
