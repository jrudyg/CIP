"""Quick test to verify approvals updated in database"""
from database import get_connection

with get_connection() as conn:
    result = conn.execute('''
        SELECT id, status, file_count, total_size
        FROM duplicate_groups
        WHERE id IN (2, 3, 98)
        ORDER BY id
    ''').fetchall()

    print('ID | Status   | Files | Size (MB)')
    print('-' * 45)
    for r in result:
        print(f'{r[0]:3d} | {r[1]:8s} | {r[2]:5d} | {r[3]/1024/1024:8.1f}')
