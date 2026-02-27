import asyncio
import json
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Any

from backend.config import settings
from core.event_bus import event_bus
from core.logger_engine import logger
from core.task_manager import task_manager
from src.ble_receiver import BLEReceiver
from src.can_translator import CANTranslator
from src.attack_engine import AttackEngine


class Gateway:
    def __init__(self):
        self.running: bool = False
        self.telemetry: List[Dict[str, Any]] = []  
        self.max_telemetry: int = 500

        self.ble = BLEReceiver()
        self.can = CANTranslator()
        self.attack = AttackEngine()

        event_bus.subscribe("can.tx", self._on_can_tx)
        event_bus.subscribe("attack.event", self._on_attack_event)

        os.makedirs("data", exist_ok=True)

        self.db_path = Path(str(settings.DATABASE_URL).replace("sqlite+aiosqlite:///", ""))
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS telemetry (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        type TEXT NOT NULL,
                        angle REAL,
                        latency_us INTEGER,
                        queue_size INTEGER,
                        priority INTEGER,
                        timestamp_us INTEGER,
                        extra_json TEXT
                    )
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp 
                    ON telemetry (timestamp DESC)
                """)
                conn.commit()
                logger.debug("Telemetry table and index ready")
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize telemetry table: {e}", exc_info=True)

    def _on_can_tx(self, data: Dict[str, Any]) -> None:
        data["type"] = "CAN_TX"
        self._append_telemetry(data)

    def _on_attack_event(self, data: Dict[str, Any]) -> None:
        data["type"] = "ATTACK"
        self._append_telemetry(data)

    def _append_telemetry(self, entry: Dict[str, Any]) -> None:
        """Append telemetry entry to in-memory buffer and SQLite DB."""
        self.telemetry.append(entry)
        if len(self.telemetry) > self.max_telemetry:
            self.telemetry.pop(0)

        row = {
            "type": entry.get("type", "UNKNOWN"),
            "angle": entry.get("angle"),
            "latency_us": entry.get("latency_us"),
            "queue_size": entry.get("queue_size"),
            "priority": entry.get("priority"),
            "timestamp_us": entry.get("timestamp_us"),
            "extra_json": json.dumps(
                {k: v for k, v in entry.items() if k not in {
                    "type", "angle", "latency_us", "queue_size", "priority", "timestamp_us"
                }},
                default=str  
            )
        }

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO telemetry 
                    (type, angle, latency_us, queue_size, priority, timestamp_us, extra_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["type"],
                    row["angle"],
                    row["latency_us"],
                    row["queue_size"],
                    row["priority"],
                    row["timestamp_us"],
                    row["extra_json"]
                ))
                conn.commit()
                logger.debug(f"Telemetry saved: type={row['type']}, latency={row['latency_us']}")
        except sqlite3.Error as e:
            logger.error(f"DB insert failed: {e} | entry: {entry}", exc_info=True)

    async def start(self) -> None:
        if self.running:
            logger.info("Gateway already running")
            return

        self.running = True
        logger.info("Gateway starting...")

        try:
            await self.ble.start()
            await self.can.start()
            logger.info("Gateway fully started")
        except Exception as e:
            logger.error(f"Gateway start failed: {e}", exc_info=True)
            await self.stop()  
            raise

    async def stop(self) -> None:
        if not self.running:
            return

        self.running = False
        logger.info("Gateway stopping...")

        try:
            await asyncio.gather(
                self.ble.stop(),
                self.can.stop(),
                return_exceptions=True
            )
            logger.info("Gateway stopped")
        except Exception as e:
            logger.error(f"Gateway stop failed: {e}", exc_info=True)

    def set_attack_mode(self, mode: str | None) -> None:
        self.can.attack_mode = mode

        if mode:
            logger.warning(f"Attack mode activated: {mode}")
            try:
                if mode == "dos":
                    asyncio.create_task(self.attack.dos_attack(duration_sec=3.0, rate_hz=80))
                elif mode == "flip":
                    asyncio.create_task(self.attack.bit_flip())
                elif mode == "heart":
                    asyncio.create_task(self.attack.heartbeat_drop())
            except Exception as e:
                logger.error(f"Failed to trigger attack '{mode}': {e}", exc_info=True)
        else:
            logger.info("Attack mode deactivated")