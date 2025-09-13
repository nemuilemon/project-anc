"""AI Analysis Manager for coordinating multiple analysis plugins.

This module provides the central management system for AI analysis plugins,
handling plugin registration, execution coordination, and result aggregation.
"""

from typing import Dict, List, Optional, Any, Callable
from threading import Event
import time
import logging

from .base_plugin import BaseAnalysisPlugin, AnalysisResult


class AIAnalysisManager:
    """Central manager for AI analysis plugins.
    
    This class coordinates multiple AI analysis plugins, providing a unified
    interface for running different types of analysis on content. It handles
    plugin registration, execution coordination, error handling, and result
    aggregation.
    
    Attributes:
        plugins (Dict[str, BaseAnalysisPlugin]): Registered analysis plugins
        logger (logging.Logger): Logger for operation tracking
    """
    
    def __init__(self):
        self.plugins: Dict[str, BaseAnalysisPlugin] = {}
        self.logger = logging.getLogger('ai_analysis')
        
    def register_plugin(self, plugin: BaseAnalysisPlugin) -> bool:
        """Register a new analysis plugin.
        
        Args:
            plugin (BaseAnalysisPlugin): Plugin instance to register
            
        Returns:
            bool: True if registration successful, False if plugin name conflicts
        """
        if plugin.name in self.plugins:
            self.logger.warning(f"Plugin '{plugin.name}' already registered, skipping")
            return False
            
        self.plugins[plugin.name] = plugin
        self.logger.info(f"Registered AI analysis plugin: {plugin.name} v{plugin.version}")
        return True
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """Unregister an analysis plugin.
        
        Args:
            plugin_name (str): Name of plugin to unregister
            
        Returns:
            bool: True if unregistration successful
        """
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
            self.logger.info(f"Unregistered AI analysis plugin: {plugin_name}")
            return True
        return False
    
    def get_available_plugins(self) -> List[str]:
        """Get list of available plugin names.
        
        Returns:
            List[str]: Names of all registered plugins
        """
        return list(self.plugins.keys())
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific plugin.
        
        Args:
            plugin_name (str): Name of the plugin
            
        Returns:
            Optional[Dict[str, Any]]: Plugin configuration or None if not found
        """
        plugin = self.plugins.get(plugin_name)
        return plugin.get_config() if plugin else None
    
    def analyze(self, content: str, plugin_name: str, **kwargs) -> AnalysisResult:
        """Run synchronous analysis using specified plugin.
        
        Args:
            content (str): Content to analyze
            plugin_name (str): Name of plugin to use
            **kwargs: Additional plugin-specific parameters
            
        Returns:
            AnalysisResult: Analysis results or error
        """
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return AnalysisResult(
                success=False,
                data={},
                message=f"Plugin '{plugin_name}' not found",
                plugin_name=plugin_name
            )
        
        if not plugin.validate_content(content):
            return AnalysisResult(
                success=False,
                data={},
                message="Content validation failed",
                plugin_name=plugin_name
            )
        
        try:
            start_time = time.time()
            result = plugin.analyze(content, **kwargs)
            result.processing_time = time.time() - start_time
            return result
            
        except Exception as e:
            self.logger.error(f"Error in plugin '{plugin_name}': {str(e)}")
            return AnalysisResult(
                success=False,
                data={},
                message=f"Analysis failed: {str(e)}",
                plugin_name=plugin_name,
                metadata={"error_type": type(e).__name__}
            )
    
    def analyze_async(self,
                     content: str,
                     plugin_name: str,
                     progress_callback: Optional[Callable[[int], None]] = None,
                     cancel_event: Optional[Event] = None,
                     **kwargs) -> AnalysisResult:
        """Run asynchronous analysis using specified plugin.
        
        Args:
            content (str): Content to analyze
            plugin_name (str): Name of plugin to use
            progress_callback (Callable, optional): Progress update function
            cancel_event (Event, optional): Cancellation event
            **kwargs: Additional plugin-specific parameters
            
        Returns:
            AnalysisResult: Analysis results or error
        """
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return AnalysisResult(
                success=False,
                data={},
                message=f"Plugin '{plugin_name}' not found",
                plugin_name=plugin_name
            )
        
        if not plugin.validate_content(content):
            return AnalysisResult(
                success=False,
                data={},
                message="Content validation failed",
                plugin_name=plugin_name
            )
        
        try:
            start_time = time.time()
            result = plugin.analyze_async(content, progress_callback, cancel_event, **kwargs)
            result.processing_time = time.time() - start_time
            return result
            
        except Exception as e:
            self.logger.error(f"Error in async plugin '{plugin_name}': {str(e)}")
            return AnalysisResult(
                success=False,
                data={},
                message=f"Async analysis failed: {str(e)}",
                plugin_name=plugin_name,
                metadata={"error_type": type(e).__name__}
            )
    
    def analyze_multiple(self,
                        content: str,
                        plugin_names: List[str],
                        parallel: bool = False,
                        **kwargs) -> Dict[str, AnalysisResult]:
        """Run analysis using multiple plugins.
        
        Args:
            content (str): Content to analyze
            plugin_names (List[str]): Names of plugins to use
            parallel (bool): Whether to run plugins in parallel (not implemented yet)
            **kwargs: Additional plugin-specific parameters
            
        Returns:
            Dict[str, AnalysisResult]: Results from each plugin
        """
        results = {}
        
        # For now, run sequentially
        # TODO: Implement parallel execution using threading
        for plugin_name in plugin_names:
            results[plugin_name] = self.analyze(content, plugin_name, **kwargs)
            
        return results
    
    def get_analysis_summary(self, results: Dict[str, AnalysisResult]) -> Dict[str, Any]:
        """Generate summary of analysis results from multiple plugins.
        
        Args:
            results (Dict[str, AnalysisResult]): Results from multiple plugins
            
        Returns:
            Dict[str, Any]: Summary information
        """
        successful = sum(1 for r in results.values() if r.success)
        total = len(results)
        total_time = sum(r.processing_time for r in results.values())
        
        return {
            "total_plugins": total,
            "successful_plugins": successful,
            "failed_plugins": total - successful,
            "total_processing_time": total_time,
            "success_rate": successful / total if total > 0 else 0,
            "plugin_results": {name: result.success for name, result in results.items()}
        }


# Global manager instance
ai_manager = AIAnalysisManager()