from fastapi import APIRouter, Query, HTTPException
import sqlite3
import json
from backend.config import settings

router = APIRouter()

@router.get("/telemetry")
async def get_telemetry(limit: int = Query(200, ge=1, le=1000)):
    db_path = str(settings.DATABASE_URL).replace("sqlite+aiosqlite:///", "")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT type, angle, latency_us, queue_size, timestamp_us, extra_json
            FROM telemetry 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            extra = json.loads(row[5]) if row[5] else {}
            result.append({
                "type": row[0],
                "angle": row[1],
                "latency_us": row[2],
                "queue_size": row[3],
                "timestamp_us": row[4],
                **extra
            })
        return result

    except sqlite3.Error as db_err:
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_err)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")