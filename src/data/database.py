"""
SQLite Database Setup with Mock Data

Simulates Air NZ operational data:
- Flights
- Aircraft
- Crew
- Gates
- Policies
- Work Orders
- Users
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os


class AirNZDatabase:
    """Air NZ operational database"""

    def __init__(self, db_path: str = "airnz.db"):
        self.db_path = db_path
        self.conn = None
        self.initialize_database()

    def initialize_database(self):
        """Initialize database with schema and mock data"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Return dict-like rows

        self.create_tables()
        self.populate_mock_data()

    def create_tables(self):
        """Create database schema"""
        cursor = self.conn.cursor()

        # Flights table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS flights (
            flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_number TEXT NOT NULL,
            route TEXT NOT NULL,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            scheduled_departure TEXT NOT NULL,
            scheduled_arrival TEXT NOT NULL,
            actual_departure TEXT,
            actual_arrival TEXT,
            status TEXT NOT NULL,
            aircraft_registration TEXT,
            gate TEXT,
            pax_count INTEGER,
            pax_capacity INTEGER,
            delay_minutes INTEGER DEFAULT 0,
            delay_reason TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)

        # Aircraft table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS aircraft (
            aircraft_id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration TEXT UNIQUE NOT NULL,
            aircraft_type TEXT NOT NULL,
            manufacturer TEXT NOT NULL,
            model TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            status TEXT NOT NULL,
            base TEXT NOT NULL,
            last_maintenance TEXT,
            next_maintenance_due TEXT,
            flight_hours INTEGER DEFAULT 0,
            cycles INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """)

        # Crew table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS crew (
            crew_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            base TEXT NOT NULL,
            aircraft_qualifications TEXT,
            status TEXT NOT NULL,
            duty_start TEXT,
            duty_end TEXT,
            flight_duty_period_remaining INTEGER,
            created_at TEXT NOT NULL
        )
        """)

        # Gates table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS gates (
            gate_id INTEGER PRIMARY KEY AUTOINCREMENT,
            gate_number TEXT UNIQUE NOT NULL,
            terminal TEXT NOT NULL,
            aircraft_type_allowed TEXT NOT NULL,
            status TEXT NOT NULL,
            current_flight TEXT,
            available_from TEXT,
            created_at TEXT NOT NULL
        )
        """)

        # Policies table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS policies (
            policy_id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            version TEXT NOT NULL,
            effective_date TEXT NOT NULL,
            effective_until TEXT,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            aircraft_types TEXT,
            route_regions TEXT,
            business_domain TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        # Work Orders table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_orders (
            work_order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            wo_number TEXT UNIQUE NOT NULL,
            aircraft_registration TEXT NOT NULL,
            work_type TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            description TEXT NOT NULL,
            assigned_to TEXT,
            created_at TEXT NOT NULL,
            due_date TEXT,
            completed_at TEXT,
            FOREIGN KEY (aircraft_registration) REFERENCES aircraft(registration)
        )
        """)

        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            business_domains TEXT NOT NULL,
            aircraft_types TEXT,
            bases TEXT,
            route_regions TEXT,
            sensitivity_clearance TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
        """)

        # Audit Log table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            trace_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            user_id TEXT NOT NULL,
            component TEXT NOT NULL,
            action TEXT NOT NULL,
            status TEXT NOT NULL,
            details TEXT,
            timestamp TEXT NOT NULL
        )
        """)

        # System Metrics table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_metrics (
            metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
            risk_tier TEXT NOT NULL,
            citation_coverage_rate REAL,
            hallucination_rate REAL,
            tool_success_rate REAL,
            privilege_block_rate REAL,
            avg_latency_ms REAL,
            p95_latency_ms REAL,
            total_requests INTEGER,
            failed_requests INTEGER,
            timestamp TEXT NOT NULL
        )
        """)

        self.conn.commit()

    def populate_mock_data(self):
        """Populate database with mock data"""
        cursor = self.conn.cursor()

        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM flights")
        if cursor.fetchone()[0] > 0:
            return  # Data already populated

        now = datetime.now()

        # Mock Flights
        flights = [
            ("NZ1", "AKL-SYD", "AKL", "SYD", "14:00", "17:00", None, None, "delayed", "ZK-OKM", "23", 182, 220, 150, "Hydraulic system maintenance", now, now),
            ("NZ2", "SYD-AKL", "SYD", "AKL", "18:30", "21:30", None, None, "on_time", "ZK-OKN", "25", 195, 220, 0, None, now, now),
            ("NZ5", "AKL-LAX", "AKL", "LAX", "20:00", "12:00", None, None, "on_time", "ZK-NZA", "30", 240, 275, 0, None, now, now),
            ("NZ101", "AKL-CHC", "AKL", "CHC", "09:00", "10:15", None, None, "on_time", "ZK-MCY", "15", 140, 168, 0, None, now, now),
            ("NZ8", "AKL-SIN", "AKL", "SIN", "22:00", "05:00", None, None, "boarding", "ZK-NZB", "28", 265, 275, 0, None, now, now),
        ]

        cursor.executemany("""
        INSERT INTO flights (flight_number, route, origin, destination, scheduled_departure,
                           scheduled_arrival, actual_departure, actual_arrival, status,
                           aircraft_registration, gate, pax_count, pax_capacity, delay_minutes,
                           delay_reason, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, flights)

        # Mock Aircraft
        aircraft = [
            ("ZK-OKM", "B787-9", "Boeing", "787-9 Dreamliner", 275, "maintenance", "AKL", now - timedelta(days=1), now + timedelta(days=7), 12500, 3200, now),
            ("ZK-OKN", "B787-9", "Boeing", "787-9 Dreamliner", 275, "available", "AKL", now - timedelta(days=30), now + timedelta(days=60), 11200, 2950, now),
            ("ZK-NZA", "B787-9", "Boeing", "787-9 Dreamliner", 275, "in_flight", "AKL", now - timedelta(days=15), now + timedelta(days=75), 13100, 3450, now),
            ("ZK-NZB", "B787-9", "Boeing", "787-9 Dreamliner", 275, "boarding", "AKL", now - timedelta(days=20), now + timedelta(days=70), 12800, 3380, now),
            ("ZK-MCY", "A320", "Airbus", "A320neo", 168, "in_flight", "AKL", now - timedelta(days=5), now + timedelta(days=85), 8500, 2100, now),
        ]

        cursor.executemany("""
        INSERT INTO aircraft (registration, aircraft_type, manufacturer, model, capacity,
                            status, base, last_maintenance, next_maintenance_due,
                            flight_hours, cycles, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, aircraft)

        # Mock Crew
        crew = [
            ("EMP-1001", "Sarah Chen", "Captain", "AKL", json.dumps(["B787-9", "A320"]), "available", None, None, 480, now),
            ("EMP-1002", "Mike Johnson", "First Officer", "AKL", json.dumps(["B787-9"]), "on_duty", now, now + timedelta(hours=8), 240, now),
            ("EMP-2001", "Lisa Wang", "Cabin Manager", "AKL", json.dumps(["B787-9", "A320"]), "available", None, None, 480, now),
            ("EMP-3001", "Tom Brown", "Engineer", "AKL", json.dumps(["B787-9", "A320", "ATR72"]), "on_duty", now, now + timedelta(hours=8), 480, now),
        ]

        cursor.executemany("""
        INSERT INTO crew (employee_id, name, role, base, aircraft_qualifications, status,
                         duty_start, duty_end, flight_duty_period_remaining, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, crew)

        # Mock Gates
        gates = [
            ("15", "Domestic", "A320,ATR72", "occupied", "NZ101", now + timedelta(hours=1), now),
            ("23", "International", "B787-9,B787-10", "available", None, now, now),
            ("25", "International", "B787-9,B787-10", "available", None, now, now),
            ("28", "International", "B787-9,B787-10", "occupied", "NZ8", now + timedelta(hours=4), now),
            ("30", "International", "B787-9,B787-10", "occupied", "NZ5", now + timedelta(hours=2), now),
        ]

        cursor.executemany("""
        INSERT INTO gates (gate_number, terminal, aircraft_type_allowed, status,
                         current_flight, available_from, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, gates)

        # Mock Policies
        policies = [
            ("POL-BAGGAGE-001", "Checked Baggage Allowance Policy", "3.2", "2024-01-01", None,
             "customer_service", "Economy passengers are entitled to 2 pieces of checked baggage, each not exceeding 23kg. Business Premier passengers are entitled to 3 pieces, each not exceeding 32kg. Excess baggage charges apply beyond this allowance.",
             json.dumps(["all"]), json.dumps(["all"]), "customer_service", now),

            ("OPS-DISRUPT-001", "Flight Delay Recovery Procedures", "2.1", "2024-01-01", None,
             "operations", "For delays exceeding 120 minutes, consider aircraft swap if available. Priority: protect connections, minimize passenger impact. Consult with OCC before executing swap. Document all decisions in operational log.",
             json.dumps(["all"]), json.dumps(["all"]), "operations", now),

            ("MAINT-MEL-001", "Minimum Equipment List Procedures", "4.5", "2023-06-01", None,
             "maintenance", "MEL items must be reviewed by certified engineer. Category A: rectify within time limit. Category B: rectify within 3 days. Category C: rectify within 10 days. Category D: rectify within 120 days. All deferrals require captain acknowledgment.",
             json.dumps(["B787-9", "A320"]), json.dumps(["all"]), "engineering", now),
        ]

        cursor.executemany("""
        INSERT INTO policies (document_id, title, version, effective_date, effective_until,
                            category, content, aircraft_types, route_regions,
                            business_domain, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, policies)

        # Mock Work Orders
        work_orders = [
            ("WO-2024-001", "ZK-OKM", "corrective", "high", "in_progress",
             "Hydraulic system pressure fluctuation - System 1. Replace hydraulic pump per AMM 29-21-00.",
             "EMP-3001", now - timedelta(hours=3), now + timedelta(hours=2), None),

            ("WO-2024-002", "ZK-NZA", "preventive", "medium", "completed",
             "500-hour inspection complete. All items within limits.",
             "EMP-3002", now - timedelta(days=2), now - timedelta(days=1), now - timedelta(days=1)),
        ]

        cursor.executemany("""
        INSERT INTO work_orders (wo_number, aircraft_registration, work_type, priority,
                               status, description, assigned_to, created_at, due_date,
                               completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, work_orders)

        # Mock Users
        users = [
            ("cs_agent_001", "Emma Wilson", "customer_service", json.dumps(["customer_service"]),
             json.dumps(["all"]), json.dumps(["AKL", "CHC", "WLG"]), json.dumps(["Domestic", "Trans-Tasman"]),
             "internal", 1, now),

            ("dispatcher_001", "James Lee", "dispatch_occ", json.dumps(["operations"]),
             json.dumps(["B787-9", "A320"]), json.dumps(["AKL"]), json.dumps(["all"]),
             "internal", 1, now),

            ("engineer_001", "Tom Brown", "maintenance", json.dumps(["engineering"]),
             json.dumps(["B787-9", "A320", "ATR72"]), json.dumps(["AKL"]), json.dumps(["Domestic"]),
             "confidential", 1, now),

            ("admin_001", "Admin User", "admin", json.dumps(["all"]),
             json.dumps(["all"]), json.dumps(["all"]), json.dumps(["all"]),
             "restricted", 1, now),
        ]

        cursor.executemany("""
        INSERT INTO users (username, name, role, business_domains, aircraft_types, bases,
                         route_regions, sensitivity_clearance, active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, users)

        self.conn.commit()

    def get_flight_status(self, flight_number: str) -> Optional[Dict]:
        """Get flight status"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT * FROM flights WHERE flight_number = ? ORDER BY created_at DESC LIMIT 1
        """, (flight_number,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_aircraft_availability(self, base: str = "AKL") -> List[Dict]:
        """Get available aircraft at base"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT * FROM aircraft WHERE base = ? AND status = 'available'
        """, (base,))

        return [dict(row) for row in cursor.fetchall()]

    def get_crew_availability(self, base: str = "AKL", aircraft_type: str = None) -> List[Dict]:
        """Get available crew at base"""
        cursor = self.conn.cursor()

        if aircraft_type:
            cursor.execute("""
            SELECT * FROM crew
            WHERE base = ? AND status = 'available'
            AND aircraft_qualifications LIKE ?
            """, (base, f'%{aircraft_type}%'))
        else:
            cursor.execute("""
            SELECT * FROM crew WHERE base = ? AND status = 'available'
            """, (base,))

        return [dict(row) for row in cursor.fetchall()]

    def get_gate_availability(self, aircraft_type: str = None) -> List[Dict]:
        """Get available gates"""
        cursor = self.conn.cursor()

        if aircraft_type:
            cursor.execute("""
            SELECT * FROM gates
            WHERE status = 'available'
            AND aircraft_type_allowed LIKE ?
            """, (f'%{aircraft_type}%',))
        else:
            cursor.execute("SELECT * FROM gates WHERE status = 'available'")

        return [dict(row) for row in cursor.fetchall()]

    def search_policies(self, query: str, business_domain: str = None) -> List[Dict]:
        """Search policies by content"""
        cursor = self.conn.cursor()

        if business_domain:
            cursor.execute("""
            SELECT * FROM policies
            WHERE (title LIKE ? OR content LIKE ?)
            AND business_domain = ?
            ORDER BY effective_date DESC
            """, (f'%{query}%', f'%{query}%', business_domain))
        else:
            cursor.execute("""
            SELECT * FROM policies
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY effective_date DESC
            """, (f'%{query}%', f'%{query}%'))

        return [dict(row) for row in cursor.fetchall()]

    def get_work_order(self, wo_number: str) -> Optional[Dict]:
        """Get work order details"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM work_orders WHERE wo_number = ?", (wo_number,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def create_work_order(self, data: Dict) -> str:
        """Create new work order (R3 action)"""
        cursor = self.conn.cursor()

        wo_number = f"WO-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"

        cursor.execute("""
        INSERT INTO work_orders
        (wo_number, aircraft_registration, work_type, priority, status,
         description, assigned_to, created_at, due_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            wo_number,
            data['aircraft_registration'],
            data['work_type'],
            data['priority'],
            'pending',
            data['description'],
            data.get('assigned_to'),
            datetime.now().isoformat(),
            data.get('due_date')
        ))

        self.conn.commit()
        return wo_number

    def get_user(self, username: str) -> Optional[Dict]:
        """Get user details"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND active = 1", (username,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def log_audit_event(self, trace_id: str, event_type: str, user_id: str,
                       component: str, action: str, status: str, details: Dict):
        """Log audit event to database"""
        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO audit_log (trace_id, event_type, user_id, component, action, status, details, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trace_id, event_type, user_id, component, action, status,
            json.dumps(details), datetime.now().isoformat()
        ))

        self.conn.commit()

    def record_metrics(self, metrics: Dict):
        """Record system metrics"""
        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO system_metrics
        (risk_tier, citation_coverage_rate, hallucination_rate, tool_success_rate,
         privilege_block_rate, avg_latency_ms, p95_latency_ms, total_requests,
         failed_requests, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics.get('risk_tier'),
            metrics.get('citation_coverage_rate'),
            metrics.get('hallucination_rate'),
            metrics.get('tool_success_rate'),
            metrics.get('privilege_block_rate'),
            metrics.get('avg_latency_ms'),
            metrics.get('p95_latency_ms'),
            metrics.get('total_requests'),
            metrics.get('failed_requests'),
            datetime.now().isoformat()
        ))

        self.conn.commit()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
