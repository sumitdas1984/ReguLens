"""
Test that project structure is correctly set up.
Validates acceptance criteria from spec.
"""

import importlib
import pytest
from pathlib import Path


def test_backend_app_directory_exists():
    """Test that backend/app directory exists."""
    app_dir = Path("backend/app")
    assert app_dir.exists()
    assert app_dir.is_dir()


def test_all_required_directories_exist():
    """Test that all required subdirectories exist."""
    required_dirs = [
        "backend/app/models",
        "backend/app/schemas",
        "backend/app/api",
        "backend/app/routes",
        "backend/app/scrapers",
        "backend/app/ai",
        "backend/app/jobs",
        "backend/app/utils",
        "backend/templates",
        "backend/static",
        "scripts",
    ]

    for dir_path in required_dirs:
        path = Path(dir_path)
        assert path.exists(), f"Directory {dir_path} does not exist"
        assert path.is_dir(), f"{dir_path} is not a directory"


def test_main_module_can_be_imported():
    """Test that backend.app.main can be imported successfully."""
    try:
        from backend.app import main
        assert hasattr(main, "app")
        assert main.app is not None
    except ImportError as e:
        pytest.fail(f"Failed to import backend.app.main: {e}")


def test_fastapi_app_instance_exists():
    """Test that FastAPI app instance can be accessed."""
    from backend.app.main import app
    from fastapi import FastAPI

    assert isinstance(app, FastAPI)
    assert app.title == "ReguLens"


def test_all_submodules_can_be_imported():
    """Test that all created modules can be imported."""
    modules = [
        "backend.app",
        "backend.app.config",
        "backend.app.database",
        "backend.app.dependencies",
        "backend.app.models",
        "backend.app.schemas",
        "backend.app.api",
        "backend.app.routes",
        "backend.app.scrapers",
        "backend.app.ai",
        "backend.app.jobs",
        "backend.app.utils",
    ]

    for module_name in modules:
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")


def test_config_loads_from_env():
    """Test that config can be loaded from settings."""
    from backend.app.config import settings

    assert settings.APP_NAME == "ReguLens"
    assert settings.APP_VERSION == "0.1.0"
