"""
Shared configuration loader for JayAvatar services.
Loads from config.yaml with environment variable overrides.
"""
import os
import yaml

# Find config file relative to this module
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')

_config = None

def load_config():
    """Load and cache configuration from config.yaml"""
    global _config
    if _config is not None:
        return _config
    
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            _config = yaml.safe_load(f) or {}
    else:
        _config = {}
    
    return _config

def get(section: str, key: str, default=None, env_var: str = None):
    """
    Get a config value with optional environment variable override.
    
    Priority: ENV_VAR > config.yaml > default
    
    Example:
        get('motion', 'timeout_seconds', default=300, env_var='MOTION_TIMEOUT')
    """
    config = load_config()
    
    # Check environment variable first
    if env_var and os.environ.get(env_var):
        val = os.environ.get(env_var)
        # Try to convert to same type as default
        if isinstance(default, bool):
            return val.lower() in ('true', '1', 'yes')
        elif isinstance(default, int):
            return int(val)
        elif isinstance(default, float):
            return float(val)
        return val
    
    # Check config file
    section_data = config.get(section, {})
    if section_data and key in section_data:
        return section_data[key]
    
    return default


# Convenience accessors for common settings
def pipeline_max_concurrent():
    return get('pipeline', 'max_concurrent', default=3, env_var='MAX_CONCURRENT_PIPELINES')

def motion_timeout():
    return get('motion', 'timeout_seconds', default=300, env_var='MOTION_TIMEOUT')

def motion_size():
    return get('motion', 'size', default=512, env_var='MOTION_SIZE')

def motion_still():
    return get('motion', 'still', default=True, env_var='MOTION_STILL')

def audio_timeout():
    return get('audio', 'timeout_seconds', default=120, env_var='AUDIO_TIMEOUT')

def visual_timeout():
    return get('visual', 'timeout_seconds', default=180, env_var='VISUAL_TIMEOUT')

def redis_host():
    return get('redis', 'host', default='localhost', env_var='REDIS_HOST')

def redis_port():
    return get('redis', 'port', default=6379, env_var='REDIS_PORT')
