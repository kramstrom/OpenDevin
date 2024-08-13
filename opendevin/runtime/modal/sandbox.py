import modal
import os
from pathlib import Path

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


class ModalSandBox(Sandbox):
    def __init__(
        self,
        config: SandboxConfig,
    ):
        self.config = config

        super().__init__(config)

        logger.info("creating sandbox")
        self.sandbox = modal.Sandbox.create(
            "sleep",
            "infinity",
            image=image,
            volumes={
                os.environ["WORKSPACE_MOUNT_PATH"]: workspace_volume,
            },
            mounts=[modal.Mount.from_local_dir("/root/opendevin", remote_path="/root/opendevin")],
            timeout=300,  # 5 minutes
        )
        logger.info("finished creating sandbox")



    def execute(
        self, cmd: str, stream: bool = False, timeout: int | None = None
    ) -> tuple[int, str | CancellableStream]:
        cmd = f"cd {os.environ['WORKSPACE_MOUNT_PATH']}; {cmd}"
        logger.info(f"`{cmd=}`")

        process = self.sandbox.exec("bash", "-c", cmd)

        stdout = process.stdout.read()
        logger.info(f"`{stdout=}`")

        # stderr = process.stderr.read()
        # logger.info(f"`{stderr=}`")

        return (0, stdout)

    def close(self):
        logger.info("closing sandbox")
        # self.sandbox.terminate()

    def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        logger.info(f"copying {host_src} to {sandbox_dest}, recursive={recursive}")
        sandbox_dest = Path(sandbox_dest) / Path(host_src).name
        cmd = f"cp -r {host_src} {sandbox_dest}" if recursive else f"cp {host_src} {sandbox_dest}"
        returncode, _ = self.execute(cmd)

        if returncode != 0:
            raise RuntimeError(f"Failed to copy {host_src} to {sandbox_dest} in sandbox")

    def get_working_directory(self):
        logger.info("getting working directory")
        raise NotImplementedError
