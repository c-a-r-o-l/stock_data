"""data — point-in-time loaders over all_merged.parquet and friends.

The central API is ``get_panel(as_of=...)`` which returns a DataFrame
containing only data that would have been observable on or before *as_of*.
No future information leaks through.
"""

from .loaders import PanelLoader

__all__ = ["PanelLoader"]
