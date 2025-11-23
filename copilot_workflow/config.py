"""Centralized configuration management for Research Copilot.

Handles loading and validation of:
- LLM provider keys (Gemini - required)
- Toolkit service keys (Research, storage, social - optional)
- Application settings (debug mode, retry limits, etc.)
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    """Configuration for LLM and service providers."""
    
    # Required providers
    gemini_api_key: Optional[str] = None
    
    # Optional toolkit services
    Research_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    
    # Application settings
    debug_mode: bool = False
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_delay: float = 3.0
    
    # Availability flags
    available_providers: List[str] = field(default_factory=list)
    available_tools: List[str] = field(default_factory=list)


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


class ConfigManager:
    """Manages application configuration and environment validation."""
    
    def __init__(self, env_file: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            env_file: Optional path to .env file (default: project root)
        """
        self.config = ProviderConfig()
        self._load_environment(env_file)
        self._validate_configuration()
        self._log_availability()
    
    def _load_environment(self, env_file: Optional[Path] = None):
        """Load configuration from environment variables.
        
        Args:
            env_file: Optional path to .env file
        """
        # Load from .env file if it exists
        if env_file is None:
            # Try to find .env in project root
            current = Path(__file__).resolve()
            for parent in [current.parent.parent, current.parent.parent.parent]:
                env_path = parent / ".env"
                if env_path.exists():
                    env_file = env_path
                    break
        
        if env_file and env_file.exists():
            logger.info(f"Loading configuration from {env_file}")
            self._load_env_file(env_file)
        
        # Load configuration values
        self.config.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.config.Research_api_key = os.getenv("Research_API_KEY")
        self.config.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.config.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.config.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        
        # Application settings
        self.config.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        self.config.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.config.retry_delay = float(os.getenv("RETRY_DELAY", "1.0"))
        self.config.rate_limit_delay = float(os.getenv("RATE_LIMIT_DELAY", "3.0"))
    
    def _load_env_file(self, env_path: Path):
        """Load environment variables from .env file.
        
        Args:
            env_path: Path to .env file
        """
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    # Parse KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        # Only set if not already in environment
                        if key not in os.environ:
                            os.environ[key] = value
        except Exception as e:
            logger.warning(f"Failed to load .env file: {e}")
    
    def _validate_configuration(self):
        """Validate required configuration is present.
        
        Raises:
            ConfigurationError: If required configuration is missing
        """
        errors = []
        
        # Check required providers
        if not self.config.gemini_api_key:
            errors.append(
                "GEMINI_API_KEY not found in environment. "
                "This is required for LLM-powered operations. "
                "Please add it to your .env file or set the environment variable."
            )
        else:
            self.config.available_providers.append("gemini")
        
        # Check optional providers (log warnings, don't fail)
        if self.config.openai_api_key:
            self.config.available_providers.append("openai")
        
        if self.config.anthropic_api_key:
            self.config.available_providers.append("anthropic")
        
        if self.config.deepseek_api_key:
            self.config.available_providers.append("deepseek")
        
        # Check optional tools
        if self.config.Research_api_key:
            self.config.available_tools.append("Research")
        else:
            logger.warning(
                "Research_API_KEY not found. Academic search functionality will be limited. "
                "Set Research_API_KEY in .env to enable full literature search."
            )
        
        # Raise error if any required configuration is missing
        if errors:
            raise ConfigurationError(
                "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )
    
    def _log_availability(self):
        """Log available providers and tools."""
        logger.info(f"Available LLM providers: {', '.join(self.config.available_providers) or 'none'}")
        logger.info(f"Available toolkit services: {', '.join(self.config.available_tools) or 'none'}")
        
        if self.config.debug_mode:
            logger.info("Debug mode enabled - verbose logging active")
    
    def get_provider_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider.
        
        Args:
            provider: Provider name (gemini, openai, anthropic, deepseek)
            
        Returns:
            API key if available, None otherwise
        """
        key_map = {
            "gemini": self.config.gemini_api_key,
            "openai": self.config.openai_api_key,
            "anthropic": self.config.anthropic_api_key,
            "deepseek": self.config.deepseek_api_key,
        }
        return key_map.get(provider.lower())
    
    def is_provider_available(self, provider: str) -> bool:
        """Check if a provider is available.
        
        Args:
            provider: Provider name
            
        Returns:
            True if provider has valid API key
        """
        return provider.lower() in self.config.available_providers
    
    def is_tool_available(self, tool: str) -> bool:
        """Check if a toolkit service is available.
        
        Args:
            tool: Tool name (e.g., 'Research')
            
        Returns:
            True if tool has valid configuration
        """
        return tool.lower() in self.config.available_tools
    
    def get_retry_config(self) -> Dict[str, float]:
        """Get retry configuration.
        
        Returns:
            Dict with max_retries, retry_delay, rate_limit_delay
        """
        return {
            "max_retries": self.config.max_retries,
            "retry_delay": self.config.retry_delay,
            "rate_limit_delay": self.config.rate_limit_delay,
        }


# Global configuration instance (singleton pattern)
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get or create global configuration instance.
    
    Returns:
        ConfigManager instance
        
    Raises:
        ConfigurationError: If required configuration is missing
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance


def reset_config():
    """Reset global configuration (mainly for testing)."""
    global _config_instance
    _config_instance = None
