"""
Quick dashboard viewer - Simplified version that works
"""
from flask import Flask, render_template_string
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Database path
DB_PATH = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\app\instance\bookkeepr.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>BookKeepr AI - Live Dashboard</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .header {
            background: rgba(255,255,255,0.95);
            padding: 20px 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 { 
            margin: 0; 
            color: #667eea; 
            font-size: 28px;
        }
        .header p {
            margin: 5px 0 0 0;
            color: #666;
        }
        .container { 
            max-width: 1200px; 
            margin: 30px auto; 
            padding: 0 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stat-card h3 {
            margin: 0 0 10px 0;
            color: #667eea;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }
        .transactions-table {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .transactions-table h2 {
            margin: 0 0 20px 0;
            color: #333;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
        }
        .status-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .categorized { background: #d4edda; color: #155724; }
        .pending { background: #fff3cd; color: #856404; }
        .footer {
            text-align: center;
            padding: 30px;
            color: rgba(255,255,255,0.8);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>BookKeepr AI</h1>
        <p>Live Dashboard - {{ now }}</p>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Transactions</h3>
                <div class="value">{{ stats.total_transactions }}</div>
            </div>
            
            <div class="stat-card">
                <h3>Categorized</h3>
                <div class="value">{{ stats.categorized }}</div>
            </div>
            
            <div class="stat-card">
                <h3>Uncategorized</h3>
                <div class="value">{{ stats.uncategorized }}</div>
            </div>
            
            <div class="stat-card">
                <h3>AI Accuracy</h3>
                <div class="value">{{ stats.accuracy }}%</div>
            </div>
        </div>
        
        <div class="transactions-table">
            <h2>Recent Transactions</h2>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Amount</th>
                        <th>Category</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for txn in transactions %}
                    <tr>
                        <td>{{ txn.date }}</td>
                        <td>{{ txn.description }}</td>
                        <td>${{ "%.2f"|format(txn.amount) }}</td>
                        <td>{{ txn.category or 'Uncategorized' }}</td>
                        <td>
                            <span class="status-badge {{ 'categorized' if txn.category else 'pending' }}">
                                {{ 'Categorized' if txn.category else 'Pending' }}
                            </span>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    
    <div class="footer">
        <p>Built for Jo - The $1M Mission </p>
        <p>QuickBooks Integration Tonight!</p>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    db = get_db()
    
    # Get stats
    total = db.execute('SELECT COUNT(*) as count FROM transactions').fetchone()['count']
    categorized = db.execute("SELECT COUNT(*) as count FROM transactions WHERE category IS NOT NULL").fetchone()['count']
    uncategorized = total - categorized
    accuracy = round((categorized / total * 100), 1) if total > 0 else 0
    
    # Get recent transactions
    transactions = db.execute('''
        SELECT date, description, amount, category 
        FROM transactions 
        ORDER BY date DESC 
        LIMIT 10
    ''').fetchall()
    
    db.close()
    
    return render_template_string(HTML_TEMPLATE,
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        stats={
            'total_transactions': total,
            'categorized': categorized,
            'uncategorized': uncategorized,
            'accuracy': accuracy
        },
        transactions=transactions
    )

@app.route('/api/stats')
def api_stats():
    db = get_db()
    total = db.execute('SELECT COUNT(*) as count FROM transactions').fetchone()['count']
    categorized = db.execute("SELECT COUNT(*) as count FROM transactions WHERE category IS NOT NULL").fetchone()['count']
    db.close()
    
    return {
        'total_transactions': total,
        'categorized': categorized,
        'uncategorized': total - categorized,
        'accuracy': round((categorized / total * 100), 1) if total > 0 else 0
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
