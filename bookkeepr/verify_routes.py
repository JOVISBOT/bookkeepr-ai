# Verify all routes are registered correctly
import os
os.chdir(r'C:\Users\jovis\.openclaw\workspace\bookkeepr')

from app import create_app
app = create_app()

print("=" * 60)
print("REGISTERED ROUTES:")
print("=" * 60)

for rule in app.url_map.iter_rules():
    methods = ','.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))
    print(f"{rule.endpoint:30s} {methods:15s} {rule.rule}")

print("\n" + "=" * 60)
print("CHECKING REQUIRED ROUTES:")
print("=" * 60)

required = [
    ('auth.login', '/auth/login'),
    ('auth.connect', '/auth/connect'),
    ('auth.callback', '/auth/callback'),
    ('auth.disconnect', '/auth/disconnect'),
    ('dashboard.index', '/'),
]

all_ok = True
for endpoint, expected in required:
    try:
        with app.test_request_context():
            from flask import url_for
            url = url_for(endpoint)
            print(f"OK  {endpoint:30s} -> {url}")
    except Exception as e:
        print(f"ERR {endpoint:30s} -> ERROR: {e}")
        all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("ALL ROUTES VERIFIED - APP IS READY!")
else:
    print("SOME ROUTES MISSING - CHECK ERRORS ABOVE")
print("=" * 60)
