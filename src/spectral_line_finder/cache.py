from pathlib import Path

from diskcache import Cache
from platformdirs import user_cache_dir

# Get platform-specific cache directory
# platformdirs handles Windows/macOS/Linux differences automatically
cache_dir = Path(user_cache_dir(appname="spectral-line-finder"))

# Create a single cache instance
cache = Cache(str(cache_dir))
