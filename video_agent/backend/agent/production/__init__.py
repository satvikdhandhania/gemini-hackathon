"""
Production agent module

Handles sequential content generation through format-specific generators.
"""
import logging

from .orchestrator import process_sections

# Configure logging for production agent
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

__all__ = ['process_sections']
