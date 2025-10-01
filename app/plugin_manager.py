"""Dynamic Plugin Manager for Project A.N.C.

This module provides a dynamic plugin loading system that discovers and loads
AI analysis plugins at runtime, eliminating the need for static imports.
"""

import os
import importlib.util
import inspect
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
import logging

# Import the base plugin class
from ai_analysis.base_plugin import BaseAnalysisPlugin, AnalysisResult


class PluginManager:
    """Manages dynamic loading and execution of AI analysis plugins.

    This manager automatically discovers and loads plugins from the plugins
    directory at runtime, making it easy to add new analysis capabilities
    without modifying the core application code.

    Attributes:
        plugins (Dict[str, BaseAnalysisPlugin]): Registry of loaded plugins
        plugin_dir (Path): Directory to scan for plugin files
        logger (logging.Logger): Logger for plugin operations
    """

    def __init__(self, plugin_dir: Optional[str] = None):
        """Initialize the plugin manager.

        Args:
            plugin_dir: Directory containing plugin files. If None, uses default.
        """
        if plugin_dir is None:
            # Default to app/ai_analysis/plugins
            app_dir = Path(__file__).parent
            plugin_dir = app_dir / "ai_analysis" / "plugins"

        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, BaseAnalysisPlugin] = {}
        self.logger = logging.getLogger(__name__)

        # Load plugins on initialization
        self.load_plugins()

    def load_plugins(self) -> int:
        """Discover and load all plugins from the plugin directory.

        Scans the plugin directory for Python files, imports them dynamically,
        and registers any classes that inherit from BaseAnalysisPlugin.

        Returns:
            int: Number of plugins successfully loaded
        """
        if not self.plugin_dir.exists():
            self.logger.warning(f"Plugin directory not found: {self.plugin_dir}")
            return 0

        loaded_count = 0

        for file_path in self.plugin_dir.glob("*.py"):
            # Skip __init__.py and files starting with underscore
            if file_path.name.startswith("_"):
                continue

            try:
                plugin_instance = self._load_plugin_from_file(file_path)
                if plugin_instance:
                    self.plugins[plugin_instance.name] = plugin_instance
                    loaded_count += 1
                    self.logger.info(f"Loaded plugin: {plugin_instance.name} v{plugin_instance.version}")
            except Exception as e:
                self.logger.error(f"Failed to load plugin from {file_path.name}: {e}")

        self.logger.info(f"Successfully loaded {loaded_count} plugins")
        return loaded_count

    def _load_plugin_from_file(self, file_path: Path) -> Optional[BaseAnalysisPlugin]:
        """Load a plugin from a specific file.

        Args:
            file_path: Path to the plugin file

        Returns:
            BaseAnalysisPlugin instance or None if no valid plugin found
        """
        module_name = f"ai_analysis.plugins.{file_path.stem}"

        # Create module spec and load module
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            self.logger.warning(f"Could not create spec for {file_path}")
            return None

        module = importlib.util.module_from_spec(spec)

        # Add parent package to sys.modules to support relative imports
        import sys
        if 'ai_analysis' not in sys.modules:
            import ai_analysis
            sys.modules['ai_analysis'] = ai_analysis
        if 'ai_analysis.plugins' not in sys.modules:
            plugins_module = importlib.import_module('ai_analysis.plugins')
            sys.modules['ai_analysis.plugins'] = plugins_module

        spec.loader.exec_module(module)

        # Find plugin classes in the module
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Check if it's a subclass of BaseAnalysisPlugin but not the base class itself
            if (issubclass(obj, BaseAnalysisPlugin) and
                obj is not BaseAnalysisPlugin and
                obj.__module__ == module.__name__):

                # Instantiate the plugin
                try:
                    plugin_instance = obj()
                    return plugin_instance
                except Exception as e:
                    self.logger.error(f"Failed to instantiate plugin {name}: {e}")
                    continue

        return None

    def reload_plugins(self) -> int:
        """Reload all plugins from the plugin directory.

        Useful for development or when plugins are added/modified at runtime.

        Returns:
            int: Number of plugins successfully reloaded
        """
        self.logger.info("Reloading plugins...")
        self.plugins.clear()
        return self.load_plugins()

    def get_plugin(self, plugin_name: str) -> Optional[BaseAnalysisPlugin]:
        """Get a specific plugin by name.

        Args:
            plugin_name: Name of the plugin to retrieve

        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(plugin_name)

    def get_all_plugins(self) -> List[Dict[str, Any]]:
        """Get information about all loaded plugins.

        Returns:
            List of dictionaries containing plugin metadata
        """
        return [
            {
                "name": plugin.name,
                "description": plugin.description,
                "version": plugin.version,
                "requires_ollama": plugin.requires_ollama
            }
            for plugin in self.plugins.values()
        ]

    def get_plugin_names(self) -> List[str]:
        """Get a list of all loaded plugin names.

        Returns:
            List of plugin names
        """
        return list(self.plugins.keys())

    def execute(
        self,
        plugin_name: str,
        content: str,
        async_mode: bool = False,
        **kwargs
    ) -> AnalysisResult:
        """Execute a plugin by name.

        Args:
            plugin_name: Name of the plugin to execute
            content: Content to analyze
            async_mode: Whether to use async execution
            **kwargs: Additional plugin-specific parameters

        Returns:
            AnalysisResult from the plugin

        Raises:
            ValueError: If plugin is not found
        """
        plugin = self.get_plugin(plugin_name)
        if plugin is None:
            raise ValueError(f"Plugin '{plugin_name}' not found. Available plugins: {self.get_plugin_names()}")

        try:
            if async_mode:
                return plugin.analyze_async(content, **kwargs)
            else:
                return plugin.analyze(content, **kwargs)
        except Exception as e:
            self.logger.error(f"Error executing plugin '{plugin_name}': {e}")
            return AnalysisResult(
                success=False,
                data={},
                message=f"Plugin execution failed: {str(e)}",
                plugin_name=plugin_name
            )

    def has_plugin(self, plugin_name: str) -> bool:
        """Check if a plugin is loaded.

        Args:
            plugin_name: Name of the plugin to check

        Returns:
            True if plugin exists, False otherwise
        """
        return plugin_name in self.plugins

    def get_plugin_count(self) -> int:
        """Get the number of loaded plugins.

        Returns:
            Number of plugins
        """
        return len(self.plugins)

    def validate_plugins(self) -> Dict[str, bool]:
        """Validate all loaded plugins.

        Checks if each plugin correctly implements required methods.

        Returns:
            Dictionary mapping plugin names to validation status
        """
        validation_results = {}

        for name, plugin in self.plugins.items():
            try:
                # Check required methods
                has_analyze = hasattr(plugin, 'analyze') and callable(plugin.analyze)
                has_analyze_async = hasattr(plugin, 'analyze_async') and callable(plugin.analyze_async)

                # Check required attributes
                has_name = hasattr(plugin, 'name') and isinstance(plugin.name, str)
                has_description = hasattr(plugin, 'description') and isinstance(plugin.description, str)

                validation_results[name] = all([
                    has_analyze,
                    has_analyze_async,
                    has_name,
                    has_description
                ])
            except Exception as e:
                self.logger.error(f"Error validating plugin '{name}': {e}")
                validation_results[name] = False

        return validation_results

    def get_plugins_by_capability(self, requires_ollama: bool = True) -> List[str]:
        """Get plugins filtered by capability.

        Args:
            requires_ollama: Filter by Ollama requirement

        Returns:
            List of plugin names matching the criteria
        """
        return [
            name for name, plugin in self.plugins.items()
            if plugin.requires_ollama == requires_ollama
        ]


# Global plugin manager instance
plugin_manager = PluginManager()
