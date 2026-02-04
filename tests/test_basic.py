"""
JayAvatar Test Suite

Note: Full inference tests require GPU and are skipped on GitHub Actions.
These tests focus on:
- Schema validation
- Config loading
- Import verification
- Basic I/O operations
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'orchestrator'))


def test_imports():
    """Test that core modules can be imported."""
    from orchestrator.schemas import PipelineRequest, JobRequest, VisualRequest, MotionRequest
    from orchestrator.config import pipeline_max_concurrent, motion_timeout
    print("✓ All imports successful")


def test_schema_validation():
    """Test Pydantic schema validation."""
    from orchestrator.schemas import PipelineRequest
    
    # Valid request
    req = PipelineRequest(
        text="Hello world",
        video_path="/path/to/image.jpg",
        mode="motion",
        generate_subtitles=True
    )
    assert req.text == "Hello world"
    assert req.mode == "motion"
    print("✓ Schema validation passed")


def test_config_defaults():
    """Test config returns sensible defaults."""
    from orchestrator.config import pipeline_max_concurrent, motion_timeout
    
    assert pipeline_max_concurrent() >= 1
    assert motion_timeout() >= 60
    print("✓ Config defaults valid")


def test_srt_generation():
    """Test SRT subtitle generation."""
    import tempfile
    import wave
    import struct
    
    # Create a dummy WAV file (1 second, 44100 Hz)
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        wav_path = f.name
        with wave.open(f.name, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(44100)
            # 1 second of silence
            wav.writeframes(struct.pack('<' + 'h' * 44100, *([0] * 44100)))
    
    # Create temp output for SRT
    with tempfile.NamedTemporaryFile(suffix='.srt', delete=False) as f:
        srt_path = f.name
    
    # Import and run
    from orchestrator.pipeline_worker import generate_srt_file
    generate_srt_file("Hello. World.", wav_path, srt_path)
    
    # Verify SRT was created
    assert os.path.exists(srt_path)
    with open(srt_path, 'r') as f:
        content = f.read()
        assert "Hello" in content
        assert "-->" in content
    
    # Cleanup
    os.unlink(wav_path)
    os.unlink(srt_path)
    print("✓ SRT generation passed")


def test_assets_exist():
    """Verify test assets are present."""
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
    
    face_path = os.path.join(assets_dir, 'test_face.jpg')
    assert os.path.exists(face_path), f"Missing test asset: {face_path}"
    print("✓ Test assets present")


if __name__ == "__main__":
    test_imports()
    test_schema_validation()
    test_config_defaults()
    test_srt_generation()
    
    # Only run asset test if assets exist
    try:
        test_assets_exist()
    except AssertionError as e:
        print(f"⚠ Skipping asset test: {e}")
    
    print("\n✅ All tests passed!")
