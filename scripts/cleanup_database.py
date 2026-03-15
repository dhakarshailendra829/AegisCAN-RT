"""
Clean up and maintain the telemetry database.

Usage:
    python scripts/cleanup_database.py --days 30 --vacuum
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

import sqlite3

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def delete_old_records(days: int = 30) -> int:
    """
    Delete telemetry records older than specified days.

    Args:
        days: Age threshold in days

    Returns:
        int: Number of deleted records
    """
    logger.info(f"Deleting records older than {days} days...")

    try:
        db_path = str(settings.DATABASE_URL).replace("sqlite+aiosqlite:///", "")

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                f"DELETE FROM telemetry WHERE timestamp < datetime('now', '-{days} days')"
            )

            deleted = cursor.rowcount
            conn.commit()

        logger.info(f"Deleted {deleted} records")
        return deleted

    except Exception as e:
        logger.error(f"Delete failed: {e}", exc_info=True)
        return 0


def vacuum_database() -> bool:
    """
    Vacuum database to reclaim space.

    Returns:
        bool: Success status
    """
    logger.info("Vacuuming database...")

    try:
        db_path = str(settings.DATABASE_URL).replace("sqlite+aiosqlite:///", "")

        with sqlite3.connect(db_path) as conn:
            conn.execute("VACUUM")

        logger.info("Database vacuumed")
        return True

    except Exception as e:
        logger.error(f"Vacuum failed: {e}", exc_info=True)
        return False


def get_database_stats() -> dict:
    """
    Get database statistics.

    Returns:
        dict: Database statistics
    """
    try:
        db_path = str(settings.DATABASE_URL).replace("sqlite+aiosqlite:///", "")

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM telemetry")
            record_count = cursor.fetchone()[0]

            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM telemetry")
            min_date, max_date = cursor.fetchone()

            db_file = Path(db_path)
            file_size = db_file.stat().st_size if db_file.exists() else 0

        return {
            "record_count": record_count,
            "oldest_record": min_date,
            "newest_record": max_date,
            "database_size_mb": file_size / (1024 * 1024)
        }

    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        return {}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Maintain AegisCAN-RT database"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Delete records older than N days"
    )
    parser.add_argument(
        "--vacuum",
        action="store_true",
        help="Vacuum database after cleanup"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show database statistics"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("AegisCAN-RT Database Maintenance")
    logger.info("=" * 60)

    # Show stats
    if args.stats:
        stats = get_database_stats()
        logger.info("\nDatabase Statistics:")
        logger.info(f"  Records: {stats.get('record_count', 0)}")
        logger.info(f"  Oldest: {stats.get('oldest_record', 'N/A')}")
        logger.info(f"  Newest: {stats.get('newest_record', 'N/A')}")
        logger.info(f"  Size: {stats.get('database_size_mb', 0):.2f} MB\n")

    deleted = delete_old_records(days=args.days)

    if args.vacuum:
        vacuum_database()

    logger.info("=" * 60)
    logger.info("Maintenance Complete")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())