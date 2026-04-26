import sqlite3
conn = sqlite3.connect(r'instance\bookkeepr.db')
cur = conn.cursor()

# Delete fake seed transactions
cur.execute("DELETE FROM transactions WHERE description LIKE 'Transaction %'")
deleted = cur.rowcount
conn.commit()
print(f'Deleted {deleted} demo transactions')

# Delete demo companies (DEMO realm or pending-)
cur.execute("SELECT id, qbo_realm_id, qbo_company_name FROM companies WHERE qbo_realm_id LIKE 'DEMO%' OR qbo_realm_id LIKE 'pending-%'")
demos = cur.fetchall()
for c in demos:
    print(f'Removing demo company: id={c[0]} name={c[2]} realm={c[1]}')
    cur.execute('DELETE FROM transactions WHERE company_id=?', (c[0],))
    cur.execute('DELETE FROM companies WHERE id=?', (c[0],))
conn.commit()

cur.execute('SELECT id, qbo_company_name, qbo_realm_id, is_connected FROM companies WHERE is_active=1')
print()
print('REMAINING COMPANIES:')
for r in cur.fetchall():
    print(f'  id={r[0]} name={r[1] or "(no name)"} realm={r[2]} connected={r[3]}')

cur.execute('SELECT COUNT(*) FROM transactions')
print(f'Total transactions: {cur.fetchone()[0]}')
conn.close()
