import sqlite3
import os
import json
from typing import List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "experience.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Table for tracking strategies applied to specific failure types
    # This powers "Strategy Selection via Experience" and "Cost-Aware Decision Making"
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS strategy_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            failure_type TEXT,
            strategy_name TEXT,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            total_latency_ms REAL DEFAULT 0.0,
            total_cost REAL DEFAULT 0.0
        )
    ''')
    
    # Table for "Trauma Memory" - remembering specific queries to explicitly proactively heal them
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trauma_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_pattern TEXT UNIQUE,
            known_failure_type TEXT,
            best_proactive_strategy TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def log_strategy_execution(failure_type: str, strategy_name: str, success: bool, latency_ms: float, cost: float):
    """Logs the outcome of a chosen strategy to optimize future selections."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id FROM strategy_metrics WHERE failure_type = ? AND strategy_name = ?
    ''', (failure_type, strategy_name))
    row = cursor.fetchone()
    
    if row:
        if success:
            cursor.execute('''
                UPDATE strategy_metrics 
                SET success_count = success_count + 1, total_latency_ms = total_latency_ms + ?, total_cost = total_cost + ?
                WHERE id = ?
            ''', (latency_ms, cost, row[0]))
        else:
            cursor.execute('''
                UPDATE strategy_metrics 
                SET failure_count = failure_count + 1, total_latency_ms = total_latency_ms + ?, total_cost = total_cost + ?
                WHERE id = ?
            ''', (latency_ms, cost, row[0]))
    else:
        s_count = 1 if success else 0
        f_count = 0 if success else 1
        cursor.execute('''
            INSERT INTO strategy_metrics (failure_type, strategy_name, success_count, failure_count, total_latency_ms, total_cost)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (failure_type, strategy_name, s_count, f_count, latency_ms, cost))
        
    conn.commit()
    conn.close()

def get_optimized_strategies(failure_type: str) -> List[Dict[str, Any]]:
    """Returns a ranked list of strategies based on historical success rate and cost efficiency."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT strategy_name, success_count, failure_count, total_latency_ms, total_cost
        FROM strategy_metrics WHERE failure_type = ?
    ''', (failure_type,))
    
    rows = cursor.fetchall()
    conn.close()
    
    strategies = []
    for row in rows:
        strat, sc, fc, lat, cost = row
        total = sc + fc
        success_rate = (sc / total) if total > 0 else 0
        avg_latency = lat / total if total > 0 else 0
        avg_cost = cost / total if total > 0 else 0
        
        strategies.append({
            "strategy_name": strat,
            "success_rate": success_rate,
            "avg_latency": avg_latency,
            "avg_cost": avg_cost,
            "total_attempts": total
        })
        
    # Sort primarily by success rate, secondarily by cheapest cost
    strategies.sort(key=lambda x: (x["success_rate"], -x["avg_cost"]), reverse=True)
    return strategies

def log_trauma_memory(query: str, failure_type: str, winning_strategy: str):
    """Stores a problematic query so AegisAI can proactively bypass the error next time."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO trauma_memory (query_pattern, known_failure_type, best_proactive_strategy)
        VALUES (?, ?, ?)
    ''', (query, failure_type, winning_strategy))
    conn.commit()
    conn.close()

def check_trauma_memory(query: str) -> Dict[str, str]:
    """Pre-execution check to see if this exact query has traumatized the AI before."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT known_failure_type, best_proactive_strategy FROM trauma_memory WHERE query_pattern = ?
    ''', (query,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"known_failure": row[0], "prescribed_strategy": row[1]}
    return {}
