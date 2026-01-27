"""
Keyring Manager for AgentHub

Handles secure credential retrieval for MCP servers.
"""

import logging
from typing import Any, Dict, Optional

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

logger = logging.getLogger(__name__)


class KeyringManager:
    """Manages secure credential retrieval from system keyring."""

    def __init__(self, service_name: str = "agenthub"):
        self.service_name = service_name
        self.enabled = KEYRING_AVAILABLE

        if not self.enabled:
            logger.warning(
                "keyring package not installed. "
                "Install with: pip install keyring"
            )

    def get_credential(self, key: str) -> Optional[str]:
        """
        Retrieve a credential from the keyring.

        Args:
            key: The key name (e.g., "obsidian_api_key")

        Returns:
            The credential value or None if not found
        """
        if not self.enabled:
            logger.error(f"Cannot retrieve {key}: keyring not available")
            return None

        try:
            value = keyring.get_password(self.service_name, key)
            if value:
                logger.debug(f"Retrieved credential: {key}")
            else:
                logger.warning(f"Credential not found: {key}")
            return value
        except Exception as e:
            logger.error(f"Error retrieving credential {key}: {e}")
            return None

    def set_credential(self, key: str, value: str) -> bool:
        """
        Store a credential in the keyring.

        Args:
            key: The key name
            value: The credential value

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.error(f"Cannot store {key}: keyring not available")
            return False

        try:
            keyring.set_password(self.service_name, key, value)
            logger.info(f"Stored credential: {key}")
            return True
        except Exception as e:
            logger.error(f"Error storing credential {key}: {e}")
            return False

    def delete_credential(self, key: str) -> bool:
        """
        Delete a credential from the keyring.

        Args:
            key: The key name

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.error(f"Cannot delete {key}: keyring not available")
            return False

        try:
            keyring.delete_password(self.service_name, key)
            logger.info(f"Deleted credential: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting credential {key}: {e}")
            return False

    def process_env_config(self, env_config: Dict[str, Any]) -> Dict[str, str]:
        """
        Process environment configuration, retrieving values from keyring as needed.

        Supports two formats:
        1. Simple string: {"KEY": "value"}
        2. Keyring reference: {"KEY": {"source": "keyring", "service": "agenthub", "key": "api_key"}}

        Args:
            env_config: Environment configuration dictionary

        Returns:
            Processed environment variables with credentials resolved
        """
        processed = {}

        for env_key, env_value in env_config.items():
            # Skip comments
            if env_key.startswith("_"):
                continue

            # Handle keyring reference
            if isinstance(env_value, dict) and env_value.get("source") == "keyring":
                service = env_value.get("service", self.service_name)
                key = env_value.get("key")

                if not key:
                    logger.error(f"Missing 'key' in keyring config for {env_key}")
                    continue

                # Retrieve from keyring
                value = self.get_credential(key)
                if value is None:
                    logger.error(
                        f"Failed to retrieve {env_key} from keyring. "
                        f"Set with: keyring.set_password('{service}', '{key}', 'YOUR_VALUE')"
                    )
                    # Don't add to env if missing - let MCP server fail with clear error
                    continue

                processed[env_key] = value

            # Handle static string value
            elif isinstance(env_value, str):
                processed[env_key] = env_value

            else:
                logger.warning(f"Unknown env value type for {env_key}: {type(env_value)}")

        return processed


# Global instance
_keyring_manager: Optional[KeyringManager] = None


def get_keyring_manager(service_name: str = "agenthub") -> KeyringManager:
    """Get or create the global KeyringManager instance."""
    global _keyring_manager
    if _keyring_manager is None:
        _keyring_manager = KeyringManager(service_name)
    return _keyring_manager
