import os
import sysconfig
import tempfile
import pytest
from pathlib import Path

from oracletrace.tracer import Tracer


@pytest.fixture
def tracer():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Tracer(tmpdir)


@pytest.fixture
def stdlib_path():
    return os.path.realpath(sysconfig.get_path("stdlib"))


@pytest.fixture
def site_paths():
    import site
    paths = site.getsitepackages() + [site.getusersitepackages()]
    return [os.path.realpath(p) for p in paths]


def test_user_code_under_root(tracer):
    user_file = os.path.join(tracer._root_path, "my_module.py")
    Path(user_file).touch()
    assert tracer._is_user_code(user_file)


def test_user_code_nested_under_root(tracer):
    nested_dir = os.path.join(tracer._root_path, "subdir", "deep")
    os.makedirs(nested_dir, exist_ok=True)
    user_file = os.path.join(nested_dir, "my_module.py")
    Path(user_file).touch()
    assert tracer._is_user_code(user_file)


def test_external_code_outside_root(tracer):
    with tempfile.TemporaryDirectory() as tmpdir:
        external_file = os.path.join(tmpdir, "external.py")
        Path(external_file).touch()
        assert not tracer._is_user_code(external_file)


def test_stdlib_excluded(tracer, stdlib_path):
    stdlib_file = os.path.join(stdlib_path, "os.py")
    assert not tracer._is_user_code(stdlib_file)


def test_site_packages_excluded(tracer, site_paths):
    for sp in site_paths:
        if os.path.exists(sp):
            site_file = os.path.join(sp, "requests", "__init__.py")
            assert not tracer._is_user_code(site_file)


def test_venv_site_packages_excluded(tracer):
    venv_path = os.path.join(tracer._root_path, "venv", "lib", "python", "site-packages", "numpy", "__init__.py")
    assert not tracer._is_user_code(venv_path)


def test_prefix_false_positive(tracer):
    similar_path = tracer._root_path + "_backup"
    os.makedirs(similar_path, exist_ok=True)
    similar_file = os.path.join(similar_path, "module.py")
    Path(similar_file).touch()
    assert not tracer._is_user_code(similar_file)


def test_symlinked_user_code(tracer):
    real_file = os.path.join(tracer._root_path, "real_module.py")
    Path(real_file).touch()

    symlink_dir = tempfile.mkdtemp()
    symlink_file = os.path.join(symlink_dir, "linked_module.py")
    os.symlink(real_file, symlink_file)

    try:
        assert tracer._is_user_code(symlink_file)
    finally:
        os.unlink(symlink_file)
        os.rmdir(symlink_dir)


def test_dist_packages_excluded(tracer):
    dist_pkg_path = "/usr/lib/python3/dist-packages/numpy/__init__.py"
    assert not tracer._is_user_code(dist_pkg_path)


def test_dot_venv_excluded(tracer):
    venv_path = os.path.join(tracer._root_path, ".venv", "lib", "python", "site-packages", "flask", "__init__.py")
    assert not tracer._is_user_code(venv_path)


def test_env_excluded(tracer):
    env_path = os.path.join(tracer._root_path, "env", "lib", "python", "site-packages", "django", "__init__.py")
    assert not tracer._is_user_code(env_path)


def test_dot_env_excluded(tracer):
    env_path = os.path.join(tracer._root_path, ".env", "lib", "python", "site-packages", "pandas", "__init__.py")
    assert not tracer._is_user_code(env_path)


def test_root_path_with_trailing_slash(tracer):
    user_file = os.path.join(tracer._root_path, "module.py")
    Path(user_file).touch()
    assert tracer._is_user_code(user_file)
