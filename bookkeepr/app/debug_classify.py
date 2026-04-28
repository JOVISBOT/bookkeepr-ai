import sqlite3
conn = sqlite3.connect(r'instance\bookkeepr.db')
cur = conn.cursor()

cur.execute("SELECT categorization_status, COUNT(*) FROM transactions GROUP BY categorization_status")
print('Transactions by status:')
for r in cur.fetchall():
    print(f'  {r[0] or "null"}: {r[1]}')

cur.execute("SELECT category, COUNT(*) FROM transactions WHERE category IS NOT NULL GROUP BY category ORDER BY COUNT(*) DESC LIMIT 10")
print()
print('Top categories:')
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]}')

cur.execute("SELECT COUNT(*) FROM transactions WHERE category IS NULL")
null = cur.fetchone()[0]
total = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
print(f'\nUncategorized: {null} / {total}')

cur.execute("SELECT id, description, category, categorization_status, amount FROM transactions WHERE categorization_status = 'uncategorized' OR category IS NULL LIMIT 10")
print()
print('Uncategorized samples:')
for r in cur.fetchall():
    print(f'  id={r[0]} desc={(r[1] or "")[:50]} cat={r[2]} status={r[3]} amount={r[4]}')
conn.close()
