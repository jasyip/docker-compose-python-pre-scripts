#!/usr/bin/env python

import os
from configparser import ConfigParser
from pathlib import Path
from shutil import copyfile
from subprocess import run as sp_run

SCRIPT_DIR = Path(__file__).parent

env_path = SCRIPT_DIR / ".env.ini"


def xdg_config_home() -> Path:
    if "XDG_CONFIG_HOME" in os.environ:
        return Path(os.environ["XDG_CONFIG_HOME"])
    return Path.home() / ".config"


config: ConfigParser = ConfigParser()
# default values if not provided by config file
config.read_dict(
    {
        "general": {
            "executable": "/usr/bin/docker",
            "container_run_flags": " ".join(
                (
                    "-it --rm",
                    "--security-opt",
                    "label=disable",
                    "--device",
                    "/dev/fuse",
                )
            ),
            "host_pudb_conf_dir": str(xdg_config_home() / "pudb"),
        },
    }
)
required_keys = {
        "general" : {"python_versions", "image_name", "executable", "container_run_flags",
                     "host_pudb_conf_dir"},
        }
config.read(env_path)

for section, required_keys_for_section in required_keys.items():
    for required_key in required_keys_for_section:
        if required_key not in config[section]:
            raise ValueError(f"key '{required_key}' missing in configuration section [{section}]")


for python_version in config["general"]["python_versions"].split():
    image_name: str = f"""{config["general"]["image_name"]}:{python_version}"""

    if config["container_only"].get("pudb_on_error") == "1":
        pudb_cfg = Path(config["general"]["host_pudb_conf_dir"]) / "pudb.cfg"
        dest_pudb_cfg = SCRIPT_DIR / ".pudb.cfg"
        if pudb_cfg.is_file():
            copyfile(pudb_cfg, dest_pudb_cfg)
        elif not dest_pudb_cfg.is_file():
            # e044 is hardcoded magic value according to
            # https://github.com/inducer/pudb/blob/cd27015ae203307cec09adf336cfe237d03cc076/pudb/debugger.py#L2503
            dest_pudb_cfg.write_text("[pudb]\nseen_welcome = e044")

    sp_run(
        (
            config["general"]["executable"],
            "build",
            "--build-arg",
            f"PYTHON_VERSION={python_version}",
            "-t",
            image_name,
            str(SCRIPT_DIR),
        ),
        check=True,
    )

    container_run_flags: str = config["general"]["container_run_flags"].split()

    for k, v in config["container_only"].items():
        container_run_flags.extend(("-e", f"""{k.upper()}={v}"""))

    if "container_name" in config["general"]:
        container_run_flags.extend(("--name", config["general"]["container_name"]))

    sp_run(
        (
            config["general"]["executable"],
            "run",
            *container_run_flags,
            image_name,
        ),
        check=True,
    )
