"""
Export telemetry data and analytics results.

Usage:
    python scripts/export_data.py --format csv --output data.csv
    python scripts/export_data.py --format json --days 7
"""

import argparse
import logging
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import sqlite3

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def export_telemetry_csv(output_path: str, days: int = 30) -> bool:
    """
    Export telemetry data as CSV.

    Args:
        output_path: Output file path
        days: Days of data to export

    Returns:
        bool: Success status
    """
    logger.info(f"Exporting telemetry to CSV: {output_path}")

    try:
        db_path = str(settings.DATABASE_URL).replace("sqlite+aiosqlite:///", "")

        with sqlite3.connect(db_path) as conn:
            query = f"""
                SELECT * FROM telemetry
                WHERE timestamp > datetime('now', '-{days} days')
                ORDER BY timestamp DESC
            """

            df = pd.read_sql_query(query, conn)

        logger.info(f"Exporting {len(df)} records")

        df.to_csv(output_path, index=False)

        logger.info(f"Exported to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        return False


def export_telemetry_json(output_path: str, days: int = 30) -> bool:
    """
    Export telemetry data as JSON.

    Args:
        output_path: Output file path
        days: Days of data to export

    Returns:
        bool: Success status
    """
    logger.info(f"Exporting telemetry to JSON: {output_path}")

    try:
        db_path = str(settings.DATABASE_URL).replace("sqlite+aiosqlite:///", "")

        with sqlite3.connect(db_path) as conn:
            query = f"""
                SELECT * FROM telemetry
                WHERE timestamp > datetime('now', '-{days} days')
                ORDER BY timestamp DESC
            """

            df = pd.read_sql_query(query, conn)

        logger.info(f"Exporting {len(df)} records")

        data = {
            "export_timestamp": datetime.now().isoformat(),
            "record_count": len(df),
            "telemetry": df.to_dict(orient="records")
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Exported to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Export AegisCAN-RT data"
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Export format"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Days of data to export"
    )

    args = parser.parse_args()

    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"telemetry_export_{timestamp}.{args.format}"

    logger.info("=" * 60)
    logger.info("AegisCAN-RT Data Export")
    logger.info("=" * 60)

    if args.format == "csv":
        success = export_telemetry_csv(args.output, days=args.days)
    else:
        success = export_telemetry_json(args.output, days=args.days)

    logger.info("=" * 60)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())