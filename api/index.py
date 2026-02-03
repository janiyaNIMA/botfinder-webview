import sys
import os

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the combined app module
from app import app

# Vercel needs 'app' to be available at the module level
# This is our entry point for Vercel functions
