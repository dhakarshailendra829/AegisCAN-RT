"""
Central BLE-to-CAN gateway coordinator.

Manages:
- BLE receiver
- CAN translator
- Attack engine
- Event subscriptions
- Telemetry database
- System lifecycle
"""

import asyncio
import logging
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from backend.config import settings
from core.event_bus import event_bus, EventTopic
from core.task_manager import task_manager
from core.metrics_engine import metrics_engine
from src.ble_receiver import BLEReceiver
from src.can_translator import CANTranslator
from src.attack_engine import AttackEngine

logger = logging.getLogger(__name__)


class Gateway:
    """
    Central gateway coordinating BLE-to-CAN translation.

    Manages:
    - BLE input
    - CAN output
    - Attack simulation
    - Telemetry collection
    - System health
    """

    def __init__(self):
        """Initialize gateway."""
        self.running: bool = False
        self.telemetry: List[Dict[str, Any]] = []
        self.max_telemetry: int = settings.MAX_TELEMETRY_BUFFER

    # Logger FIRST
        self._logger = logging.getLogger(__name__)
        self._start_time: Optional[datetime] = None

    # Initialize components
        self.ble = BLEReceiver()
        self.can = CANTranslator()
        self.attack = AttackEngine()

    # Subscribe to events
        event_bus.subscribe(EventTopic.CAN_TX.value, self._on_can_tx)
        event_bus.subscribe(EventTopic.ATTACK_EVENT.value, self._on_attack_event)
        event_bus.subscribe(EventTopic.SYSTEM_METRICS.value, self._on_metrics)

    # Setup database
        self.db_path = Path(
            str(settings.DATABASE_URL).replace("sqlite+aiosqlite:///", "")
        )
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Ensure database tables exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Telemetry table
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
                        attack_mode TEXT,
                        extra_json TEXT
                    )
                """)

                # Indexes for performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp
                    ON telemetry (timestamp DESC)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_telemetry_type
                    ON telemetry (type)
                """)

                conn.commit()
                self._logger.debug("Telemetry tables ready")

        except sqlite3.Error as e:
            self._logger.error(f"Database initialization failed: {e}", exc_info=True)
            raise

    def _on_can_tx(self, data: Dict[str, Any]) -> None:
        """Handle CAN transmission event."""
        data["type"] = "CAN_TX"
        self._append_telemetry(data)

    def _on_attack_event(self, data: Dict[str, Any]) -> None:
        """Handle attack event."""
        data["type"] = "ATTACK"
        self._append_telemetry(data)

    def _on_metrics(self, data: Dict[str, Any]) -> None:
        """Handle system metrics event."""
        data["type"] = "METRICS"
        self._append_telemetry(data)

    def _append_telemetry(self, entry: Dict[str, Any]) -> None:
        """Append telemetry to memory and database."""
        # Memory buffer
        self.telemetry.append(entry)
        if len(self.telemetry) > self.max_telemetry:
            self.telemetry.pop(0)

        # Database persistence
        row = {
            "type": entry.get("type", "UNKNOWN"),
            "angle": entry.get("angle"),
            "latency_us": entry.get("latency_us"),
            "queue_size": entry.get("queue_size"),
            "priority": entry.get("priority"),
            "timestamp_us": entry.get("timestamp_us"),
            "attack_mode": entry.get("attack_mode"),
            "extra_json": json.dumps(
                {
                    k: v for k, v in entry.items()
                    if k not in {
                        "type", "angle", "latency_us", "queue_size",
                        "priority", "timestamp_us", "attack_mode"
                    }
                },
                default=str
            )
        }

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO telemetry
                    (type, angle, latency_us, queue_size, priority,
                     timestamp_us, attack_mode, extra_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["type"],
                    row["angle"],
                    row["latency_us"],
                    row["queue_size"],
                    row["priority"],
                    row["timestamp_us"],
                    row["attack_mode"],
                    row["extra_json"]
                ))
                conn.commit()

        except sqlite3.Error as e:
            self._logger.error(f"Database insert failed: {e}", exc_info=True)

    async def start(self) -> None:
        """Start the gateway."""
        if self.running:
            self._logger.info("Gateway already running")
            return

        self.running = True
        self._start_time = datetime.now()
        self._logger.info("Starting gateway...")

        try:
            # Start components
            await self.ble.start()
            await self.can.start()
            metrics_engine.start()

            self._logger.info("Gateway fully started")

            # Publish gateway start event
            await event_bus.publish(EventTopic.GATEWAY_START.value, {
                "timestamp": datetime.now().isoformat(),
                "status": "started"
            })

        except Exception as e:
            self._logger.error(f"Gateway start failed: {e}", exc_info=True)
            self.running = False
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the gateway gracefully."""
        if not self.running:
            return

        self.running = False
        self._logger.info("Stopping gateway...")

        try:
            # Stop components
            await asyncio.gather(
                self.ble.stop(),
                self.can.stop(),
                metrics_engine.stop(),
                return_exceptions=True
            )

            self._logger.info("Gateway stopped")

            # Publish gateway stop event
            await event_bus.publish(EventTopic.GATEWAY_STOP.value, {
                "timestamp": datetime.now().isoformat(),
                "status": "stopped"
            })

        except Exception as e:
            self._logger.error(f"Gateway stop failed: {e}", exc_info=True)

    def set_attack_mode(self, mode: Optional[str]) -> None:
        """Set attack simulation mode."""
        self.can.attack_mode = mode

        if mode:
            self._logger.warning(f"Attack mode activated: {mode}")
            try:
                if mode == "dos":
                    asyncio.create_task(
                        self.attack.dos_attack(duration_sec=3.0, rate_hz=80)
                    )
                elif mode == "flip":
                    asyncio.create_task(self.attack.bit_flip())
                elif mode == "heart":
                    asyncio.create_task(self.attack.heartbeat_drop(duration_sec=5.0))
            except Exception as e:
                self._logger.error(f"Failed to trigger attack '{mode}': {e}", exc_info=True)
        else:
            self._logger.info("Attack mode deactivated")

    def health_status(self) -> Dict[str, Any]:
        """Get comprehensive gateway health status."""
        uptime = None
        if self._start_time:
            uptime = (datetime.now() - self._start_time).total_seconds()

        return {
            "running": self.running,
            "uptime_seconds": uptime,
            "components": {
                "ble": self.ble.health_status(),
                "can": self.can.health_status(),
                "attack": self.attack.health_status(),
                "metrics": metrics_engine.health_status(),
                "event_bus": event_bus.health_status()
            },
            "telemetry": {
                "buffered_entries": len(self.telemetry),
                "max_buffer": self.max_telemetry
            }
        }