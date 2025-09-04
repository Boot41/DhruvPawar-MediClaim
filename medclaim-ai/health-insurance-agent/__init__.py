import sys
import os

# Add current directory to Python path for absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the agent module
from . import agent

# Expose the root agent for ADK web server
root_agent = agent.root_agent
