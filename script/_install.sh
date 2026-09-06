echo "Installing the necessary packages ..."
pip install -r script/requirements.txt

echo "Installing pytorch3d ..."
# cd third_party/pytorch3d_simplified
# pip install -e .
# cd ../..
pip install "git+https://github.com/facebookresearch/pytorch3d.git@stable"

# Note on the former SAPIEN UTF-8 sed: the upstream RoboTwin install used to
# patch sapien/wrapper/urdf_loader.py to add ``encoding="utf-8"`` to the URDF/
# SRDF ``open(..., "r")`` calls. That workaround is a NO-OP under the RLinf
# install contract, which runs under a UTF-8 locale (the eval server is
# C.UTF-8, so the default open() encoding is already utf-8). The RPent
# ``[robotwin]`` install flow (``uv pip install -e ".[robotwin]"``) never ran
# this sed and the env resets/steps correctly, confirming it is not load-
# bearing. The sed is dropped to slim the install contract. (If you ever run
# RoboTwin under a non-UTF-8 locale, set PYTHONUTF8=1 or LC_ALL=C.UTF-8
# instead of patching sapien at install time.)

# Note on mplib: ``mplib==0.2.1`` remains a declared runtime dep of
# ``rlinf-robotwin-runtime``. The Phase 4 (Round 2) static reachability check
# found mplib is NOT removable:
#   * ``robotwin/envs/robot/planner.py`` does a top-level ``import mplib``,
#     so ``import robotwin.envs._base_task`` (which imports ``Robot`` ->
#     ``from .planner import MplibPlanner, MplibWrapperPlanner``) eagerly
#     imports mplib. Removing mplib breaks the env import entirely.
#   * ``MplibPlanner`` (the TOPP post-processor) IS instantiated on the
#     default task path: ``_base_task`` hardcodes ``self.need_topp = True``
#     and passes it to ``Robot(...)``, which constructs ``MplibPlanner``
#     when ``need_topp`` is true.
# Only ``MplibWrapperPlanner`` (the alternative motion planner, selected by
# ``planner_backend == "mplib"``) is never instantiated in production --
# ``robots/robotwin/env_server.py`` hardcodes ``planner_backend = "curobo"``.
# But that alone does not make mplib optional, because of the import-time and
# TOPP-planner reachability above. The mplib planner.py "drop collide bail"
# patch is therefore also not applied (no effect on the curobo eval path).

echo "Installing Curobo (pinned @ d64c4b, --no-build-isolation) ..."
# cuRobo is no longer vendored. Install the exact upstream commit (d64c4b)
# that was previously vendored, with --no-build-isolation so its CUDA
# extensions compile against the already-installed torch==2.8.0+cu128
# (curobo's [build-system] requires torch unpinned, which would pull a
# wrong torch under build isolation). See pyproject.toml note.
pip install --no-build-isolation "curobo @ git+https://github.com/NVlabs/curobo.git@d64c4b005459db10c5dd867d8b30a87d5bda9bdb"

echo "Installation basic environment complete!"
echo -e "You need to:"
echo -e "    1. \033[34m\033[1m(Important!)\033[0m Download asserts from huggingface."
echo -e "    2. Install requirements for running baselines. (Optional)"
echo "See INSTALLATION.md for more instructions."
