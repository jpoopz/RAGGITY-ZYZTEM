"""
Unit tests for unified settings system.

Tests precedence order, validation, and persistence.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

import pytest

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.settings_schema import Settings
from core.settings import load_settings, save_yaml, save_json


@pytest.fixture
def temp_root(tmp_path):
    """Create temporary project root for testing"""
    # Create directory structure
    (tmp_path / "ui").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "vectorstore").mkdir()
    
    # Temporarily patch ROOT in settings module
    import core.settings as settings_module
    original_root = settings_module.ROOT
    settings_module.ROOT = tmp_path
    
    yield tmp_path
    
    # Restore original
    settings_module.ROOT = original_root


def test_defaults_when_no_config(temp_root, monkeypatch):
    """Test that load_settings returns defaults when no config files exist"""
    # Clear any environment variables
    env_vars = [
        "MODEL_NAME", "LLM_MODEL", "LLM_PROVIDER", "VECTOR_STORE",
        "TEMP", "LLM_TEMPERATURE", "HYBRID_MODE", "DATA_DIR"
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)
    
    settings = load_settings()
    
    # Check defaults
    assert settings.provider == "ollama"
    assert settings.model_name == "llama3.2"
    assert settings.vector_store == "faiss"
    assert settings.temperature == 0.3
    assert settings.hybrid_mode is True
    assert settings.batch_size == 64


def test_yaml_overrides_defaults(temp_root, monkeypatch):
    """Test that config.yaml overrides defaults"""
    # Clear env vars
    monkeypatch.delenv("VECTOR_STORE", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)
    
    # Create config.yaml
    yaml_path = temp_root / "config.yaml"
    yaml_content = """
vector_store: chroma
model_name: llama3.1
temperature: 0.5
hybrid_mode: false
"""
    yaml_path.write_text(yaml_content)
    
    settings = load_settings()
    
    assert settings.vector_store == "chroma"
    assert settings.model_name == "llama3.1"
    assert settings.temperature == 0.5
    assert settings.hybrid_mode is False


def test_json_overrides_yaml(temp_root, monkeypatch):
    """Test that ui/config.json overrides config.yaml"""
    monkeypatch.delenv("VECTOR_STORE", raising=False)
    
    # Create config.yaml
    yaml_path = temp_root / "config.yaml"
    yaml_path.write_text("vector_store: faiss\nmax_k: 5")
    
    # Create ui/config.json
    json_path = temp_root / "ui" / "config.json"
    json_path.write_text(json.dumps({
        "vector_store": "chroma",
        "max_k": 10
    }))
    
    settings = load_settings()
    
    # JSON should win over YAML
    assert settings.vector_store == "chroma"
    assert settings.max_k == 10


def test_env_overrides_all(temp_root, monkeypatch):
    """Test that environment variables override everything"""
    # Create config.yaml
    yaml_path = temp_root / "config.yaml"
    yaml_path.write_text("vector_store: faiss\nmodel_name: llama3.2")
    
    # Create ui/config.json
    json_path = temp_root / "ui" / "config.json"
    json_path.write_text(json.dumps({"vector_store": "chroma"}))
    
    # Set environment variable (should win)
    monkeypatch.setenv("VECTOR_STORE", "faiss")
    monkeypatch.setenv("MODEL_NAME", "custom-model")
    monkeypatch.setenv("TEMP", "0.7")
    
    settings = load_settings()
    
    # ENV should win
    assert settings.vector_store == "faiss"
    assert settings.model_name == "custom-model"
    assert settings.temperature == 0.7


def test_save_yaml_excludes_secrets(temp_root):
    """Test that save_yaml excludes sensitive keys"""
    settings = Settings(
        model_name="test-model",
        vector_store="chroma",
        openai_api_key="sk-secret123",
        cloud_key="super-secret",
        api_key="another-secret"
    )
    
    # Save to YAML
    success = save_yaml(settings)
    assert success is True
    
    # Read back the YAML
    yaml_path = temp_root / "config.yaml"
    content = yaml_path.read_text()
    
    # Check that secrets are NOT in the file
    assert "sk-secret123" not in content
    assert "super-secret" not in content
    assert "another-secret" not in content
    
    # Check that safe values ARE in the file
    assert "test-model" in content
    assert "chroma" in content


def test_save_json_ui_safe_only(temp_root):
    """Test that save_json only persists UI-safe settings"""
    settings = Settings(
        theme="light",
        show_advanced=True,
        vector_store="chroma",
        max_k=8,
        model_name="should-not-appear",
        openai_api_key="secret"
    )
    
    success = save_json(settings)
    assert success is True
    
    # Read back the JSON
    json_path = temp_root / "ui" / "config.json"
    data = json.loads(json_path.read_text())
    
    # Check UI-safe fields are present
    assert data["theme"] == "light"
    assert data["show_advanced"] is True
    assert data["vector_store"] == "chroma"
    assert data["max_k"] == 8
    
    # Check that non-UI fields are NOT present
    assert "model_name" not in data
    assert "openai_api_key" not in data


def test_validation_errors_fallback_to_defaults(temp_root, monkeypatch):
    """Test that invalid values fall back to defaults"""
    # Set invalid environment variable
    monkeypatch.setenv("TEMP", "invalid-number")
    monkeypatch.setenv("BATCH_SIZE", "999999")  # Exceeds max
    
    # Should not crash, should fall back to defaults
    settings = load_settings()
    
    # Invalid temp should use default
    assert settings.temperature == 0.3
    
    # Batch size should be clamped or default
    # (Pydantic validation should handle this)


def test_settings_schema_validation():
    """Test Pydantic schema validation"""
    # Valid settings
    s = Settings(model_name="test", temperature=0.5, batch_size=32)
    assert s.model_name == "test"
    assert s.temperature == 0.5
    assert s.batch_size == 32
    
    # Invalid temperature (should fail)
    with pytest.raises(Exception):  # Pydantic ValidationError
        Settings(temperature=5.0)  # Exceeds max 2.0
    
    # Invalid vector store (should fail)
    with pytest.raises(Exception):
        Settings(vector_store="invalid")  # Not in Literal
    
    # Invalid provider (should fail)
    with pytest.raises(Exception):
        Settings(provider="unknown")


def test_precedence_full_stack(temp_root, monkeypatch):
    """Test complete precedence chain: defaults < YAML < JSON < ENV"""
    # 1. Defaults (base)
    # vector_store = "faiss"
    
    # 2. YAML overrides
    yaml_path = temp_root / "config.yaml"
    yaml_path.write_text("vector_store: chroma\nmodel_name: yaml-model\ntemperature: 0.4")
    
    # 3. JSON overrides YAML for vector_store
    json_path = temp_root / "ui" / "config.json"
    json_path.write_text(json.dumps({"vector_store": "faiss", "max_k": 7}))
    
    # 4. ENV overrides JSON for vector_store
    monkeypatch.setenv("VECTOR_STORE", "chroma")
    monkeypatch.setenv("TEMP", "0.6")
    
    settings = load_settings()
    
    # ENV wins for vector_store and temperature
    assert settings.vector_store == "chroma"
    assert settings.temperature == 0.6
    
    # YAML wins for model_name (not overridden by JSON or ENV)
    assert settings.model_name == "yaml-model"
    
    # JSON wins for max_k (not overridden by ENV)
    assert settings.max_k == 7


def test_round_trip_yaml(temp_root):
    """Test save and reload from YAML"""
    settings = Settings(
        model_name="round-trip-model",
        vector_store="chroma",
        temperature=0.8,
        batch_size=128
    )
    
    # Save
    success = save_yaml(settings)
    assert success is True
    
    # Reload
    reloaded = load_settings()
    
    assert reloaded.model_name == "round-trip-model"
    assert reloaded.vector_store == "chroma"
    assert reloaded.temperature == 0.8
    assert reloaded.batch_size == 128


def test_round_trip_json(temp_root):
    """Test save and reload from JSON"""
    settings = Settings(
        theme="light",
        vector_store="chroma",
        max_k=9,
        show_advanced=True
    )
    
    # Save
    success = save_json(settings)
    assert success is True
    
    # Reload
    reloaded = load_settings()
    
    assert reloaded.theme == "light"
    assert reloaded.vector_store == "chroma"
    assert reloaded.max_k == 9
    assert reloaded.show_advanced is True

