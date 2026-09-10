# RoboTwin 2.0 Runtime for RLinf / RPent

[RoboTwin 2.0](https://github.com/RoboTwin-Platform/RoboTwin) is a
robot-manipulation simulation benchmark covering a wide range of single-arm
and dual-arm tasks.

`rlinf-robotwin-runtime` is the RLinf-maintained RoboTwin environment
distribution used by [RPent](https://github.com/RLinf/RPent).

This package focuses on the **simulation/runtime environment** required by
RPent. It is not intended to replace RoboTwin's full upstream development or
training setup.

## Installation

### Standalone runtime

```bash
pip install rlinf-robotwin-runtime==0.1.1
```

The PyPI wheel contains the RoboTwin runtime code and the small task/config
files required at runtime, but does not bundle the large simulation assets.

Download the required assets after installation:

```bash
robotwin-download-assets
```

### RPent

For RPent users, install RoboTwin through RPent's `robotwin` extra rather than
assembling the environment and VLA dependencies manually:

```bash
uv pip install -e ".[robotwin]"
```

The RPent RoboTwin stack consists of:

```text
RPent
├── rlinf-robotwin-runtime
├── rlinf-lingbotvla
└── NVIDIA cuRobo
```

## Package Contents

The wheel contains the runtime-facing RoboTwin Python package, including:

* RoboTwin environment and robot runtime code
* task configuration YAML files
* task instruction / object description metadata
* the `robotwin-download-assets` CLI

Repository-level development utilities such as tests and helper scripts are
not part of the runtime wheel.

Large simulator assets are also distributed separately.

## Runtime Contract

The `0.1.x` runtime is validated with:

| Component | Version        |
| --------- | -------------- |
| Python    | `>=3.10,<3.12` |
| PyTorch   | `2.7.1`        |
| SAPIEN    | `3.0.0b1`      |
| mplib     | `0.2.1`        |
| Gymnasium | `0.29.1`       |
| NumPy     | `1.26.4`       |

The package intentionally uses a relatively strict dependency contract because
these versions have been validated together for the RPent RoboTwin runtime.

## cuRobo

cuRobo is intentionally **not declared as a dependency of this PyPI package**.

RoboTwin treats cuRobo as an optional planner dependency. RPent owns the source
dependency for the complete integration and currently pins the official NVIDIA
release:

```text
NVlabs/curobo@v0.7.8
```

This keeps the public RoboTwin wheel free of direct Git dependencies while
keeping the full RPent installation reproducible.

## RLinf Compatibility

The RLinf-maintained source branch contains the environment/runtime integration
used by RPent:

* Source: [https://github.com/RLinf/RoboTwin](https://github.com/RLinf/RoboTwin)
* Upstream RoboTwin: [https://github.com/RoboTwin-Platform/RoboTwin](https://github.com/RoboTwin-Platform/RoboTwin)
* RPent: [https://github.com/RLinf/RPent](https://github.com/RLinf/RPent)

For the current list of tasks with RLinf-compatible reward support, see the
README in the RLinf RoboTwin repository.

## License

RoboTwin runtime code is distributed under the MIT License.

Please refer to the upstream RoboTwin project for additional dataset, asset,
and third-party licensing information.
