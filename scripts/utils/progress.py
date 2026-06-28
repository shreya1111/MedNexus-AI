"""
Progress tracking utilities for MedNexus-AI Knowledge Ingestion Framework.

Provides progress bars and tracking for long-running operations.
"""

import sys
import time
from typing import Optional, TextIO
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ProgressStats:
    """Statistics for progress tracking."""
    
    total: int
    completed: int
    failed: int = 0
    skipped: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.completed == 0:
            return 0.0
        return (self.completed - self.failed) / self.completed
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate duration."""
        if self.start_time is None:
            return None
        end = self.end_time or datetime.now()
        return end - self.start_time
    
    @property
    def items_per_second(self) -> float:
        """Calculate processing rate."""
        duration = self.duration
        if duration is None or duration.total_seconds() == 0:
            return 0.0
        return self.completed / duration.total_seconds()


class ProgressTracker:
    """Track progress of operations with visual feedback."""
    
    def __init__(
        self,
        total: int,
        description: str = "Processing",
        width: int = 50,
        show_stats: bool = True,
        file: TextIO = sys.stdout,
    ):
        """
        Initialize progress tracker.
        
        Args:
            total: Total number of items to process
            description: Description of the operation
            width: Width of progress bar in characters
            show_stats: Whether to show detailed statistics
            file: Output stream (default: stdout)
        """
        self.stats = ProgressStats(
            total=total,
            completed=0,
            start_time=datetime.now()
        )
        self.description = description
        self.width = width
        self.show_stats = show_stats
        self.file = file
        self._last_update = 0.0
        self._update_interval = 0.1  # Update every 100ms
    
    def update(self, count: int = 1, success: bool = True) -> None:
        """
        Update progress.
        
        Args:
            count: Number of items processed
            success: Whether the operation was successful
        """
        self.stats.completed += count
        
        if not success:
            self.stats.failed += count
        
        # Throttle updates
        now = time.time()
        if now - self._last_update < self._update_interval:
            if self.stats.completed < self.stats.total:
                return
        
        self._last_update = now
        self._render()
    
    def skip(self, count: int = 1) -> None:
        """
        Mark items as skipped.
        
        Args:
            count: Number of items skipped
        """
        self.stats.skipped += count
        self.stats.completed += count
        self._render()
    
    def fail(self, count: int = 1) -> None:
        """
        Mark items as failed.
        
        Args:
            count: Number of items failed
        """
        self.update(count=count, success=False)
    
    def _render(self) -> None:
        """Render progress bar."""
        if self.stats.total == 0:
            percent = 100.0
        else:
            percent = (self.stats.completed / self.stats.total) * 100
        
        filled = int(self.width * self.stats.completed / self.stats.total) if self.stats.total > 0 else 0
        bar = '█' * filled + '░' * (self.width - filled)
        
        # Basic progress
        line = f"\r{self.description}: |{bar}| {self.stats.completed}/{self.stats.total} ({percent:.1f}%)"
        
        # Add statistics if enabled
        if self.show_stats:
            duration = self.stats.duration
            if duration:
                elapsed = f"{int(duration.total_seconds())}s"
                rate = self.stats.items_per_second
                
                if rate > 0 and self.stats.completed < self.stats.total:
                    remaining = (self.stats.total - self.stats.completed) / rate
                    eta = f"ETA: {int(remaining)}s"
                else:
                    eta = "ETA: --"
                
                line += f" | {elapsed} | {rate:.1f} items/s | {eta}"
                
                if self.stats.failed > 0:
                    line += f" | Failed: {self.stats.failed}"
                
                if self.stats.skipped > 0:
                    line += f" | Skipped: {self.stats.skipped}"
        
        # Write to output
        self.file.write(line)
        self.file.flush()
    
    def finish(self) -> None:
        """Mark progress as complete."""
        self.stats.end_time = datetime.now()
        self.stats.completed = self.stats.total
        self._render()
        self.file.write('\n')
        self.file.flush()
    
    def close(self) -> None:
        """Close progress tracker (alias for finish)."""
        self.finish()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.finish()
        return False
    
    def get_stats(self) -> dict:
        """
        Get progress statistics.
        
        Returns:
            Dictionary with statistics
        """
        duration = self.stats.duration
        
        return {
            "total": self.stats.total,
            "completed": self.stats.completed,
            "failed": self.stats.failed,
            "skipped": self.stats.skipped,
            "success_rate": self.stats.success_rate,
            "duration_seconds": duration.total_seconds() if duration else 0,
            "items_per_second": self.stats.items_per_second,
        }


class SimpleProgress:
    """
    Simplified progress tracker without visual bar.
    Useful for logging-only environments.
    """
    
    def __init__(self, total: int, description: str = "Processing"):
        """
        Initialize simple progress tracker.
        
        Args:
            total: Total number of items
            description: Operation description
        """
        self.total = total
        self.description = description
        self.completed = 0
        self.failed = 0
        self.start_time = datetime.now()
    
    def update(self, count: int = 1, success: bool = True) -> None:
        """Update progress."""
        self.completed += count
        if not success:
            self.failed += count
    
    def finish(self) -> dict:
        """
        Finish tracking and return stats.
        
        Returns:
            Statistics dictionary
        """
        duration = datetime.now() - self.start_time
        
        return {
            "description": self.description,
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "duration_seconds": duration.total_seconds(),
        }


def track_progress(
    iterable,
    total: Optional[int] = None,
    description: str = "Processing",
    show_stats: bool = True,
):
    """
    Track progress of an iterable with progress bar.
    
    Args:
        iterable: Iterable to track
        total: Total number of items (detected if possible)
        description: Operation description
        show_stats: Whether to show statistics
        
    Yields:
        Items from iterable
        
    Example:
        for item in track_progress(items, description="Processing items"):
            process(item)
    """
    # Try to determine total if not provided
    if total is None:
        try:
            total = len(iterable)
        except TypeError:
            total = 0
    
    with ProgressTracker(total=total, description=description, show_stats=show_stats) as progress:
        for item in iterable:
            yield item
            progress.update()
