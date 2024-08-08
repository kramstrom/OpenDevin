import modal
import subprocess

app = modal.App("open-devin")

image = (
    modal.Image.debian_slim(
        python_version="3.11",
    )
    .poetry_install_from_file("pyproject.toml")
    .apt_install("nodejs", "npm")
    .copy_local_dir("frontend", remote_path="/root/frontend")
    .run_commands(
        "cd /root/frontend && pwd && ls && npm install -g npm@10.5.1 && npm ci && npm run make-i18n && npm run build"
    )
    .run_commands(
        "pip install playwright && playwright install-deps && playwright install chromium"
    )
    .env(
        {
            "RUNTIME": "modal",
            "SANDBOX_BOX_TYPE": "modal",
            "WORKSPACE_MOUNT_PATH": "/workspace",
        }
    )
)


@app.function(
    allow_concurrent_inputs=100,
    image=image,
    mounts=[
        modal.Mount.from_local_dir("opendevin", remote_path="/root/opendevin"),
        modal.Mount.from_local_dir("agenthub", remote_path="/root/agenthub"),
    ],
    secrets=[
        modal.Secret.from_name("openai-secret", environment_name="main"),
    ],
)
@modal.web_server(3000, startup_timeout=60)
def run():
    cmd = "uvicorn opendevin.server.listen:app --host 0.0.0.0 --port 3000"
    subprocess.Popen(cmd, shell=True)
