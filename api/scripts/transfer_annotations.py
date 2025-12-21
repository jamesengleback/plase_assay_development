import sqlite3
import os

# Paths
checkpoint_db = '/home/james/thesis-stuff/old/201906_P450_PlateAssay_Development/api/db_checkpoints/20251128-assay-dev.db'
main_db = '/home/james/thesis-stuff/old/201906_P450_PlateAssay_Development/api/database.db'

# Connect to both DBs
conn_checkpoint = sqlite3.connect(checkpoint_db)
conn_main = sqlite3.connect(main_db)

cursor_checkpoint = conn_checkpoint.cursor()
cursor_main = conn_main.cursor()

# Function to find matching result in main DB
def find_result_id(experiment_id, compound_name, protein_concentration):
    cursor_main.execute('''
        SELECT r.id FROM result r
        JOIN experiment e ON r.experiment_id = e.id
        JOIN compound c ON r.compound_id = c.id
        WHERE e.id = ? AND c.name = ? AND r.protein_concentration = ?
    ''', (experiment_id, compound_name, protein_concentration))
    row = cursor_main.fetchone()
    return row[0] if row else None

# Function to find matching well in main DB
def find_well_id(plate_id, address):
    cursor_main.execute('''
        SELECT id FROM well WHERE plate_id = ? AND address = ?
    ''', (plate_id, address))
    row = cursor_main.fetchone()
    return row[0] if row else None

# Transfer DoseResponse excludes
print("Transferring DoseResponse excludes...")
cursor_checkpoint.execute('''
    SELECT dr.concentration, dr.exclude, r.experiment_id, c.name, r.protein_concentration
    FROM doseresponse dr
    JOIN result r ON dr.result_id = r.id
    JOIN compound c ON r.compound_id = c.id
''')
for row in cursor_checkpoint.fetchall():
    conc, exclude, exp_id, comp_name, prot_conc = row
    result_id = find_result_id(exp_id, comp_name, prot_conc)
    if result_id:
        cursor_main.execute('''
            UPDATE doseresponse SET exclude = ? WHERE result_id = ? AND concentration = ?
        ''', (exclude, result_id, conc))
        print(f"Updated DoseResponse for result {result_id}, conc {conc}")

# Transfer Result locked and accepted
print("Transferring Result locked and accepted...")
cursor_checkpoint.execute('''
    SELECT r.locked, r.accepted, r.experiment_id, c.name, r.protein_concentration
    FROM result r
    JOIN compound c ON r.compound_id = c.id
''')
for row in cursor_checkpoint.fetchall():
    locked, accepted, exp_id, comp_name, prot_conc = row
    result_id = find_result_id(exp_id, comp_name, prot_conc)
    if result_id:
        cursor_main.execute('''
            UPDATE result SET locked = ?, accepted = ? WHERE id = ?
        ''', (locked, accepted, result_id))
        print(f"Updated Result locked/accepted for result {result_id}")

# Transfer ResultAnnotation comments
print("Transferring ResultAnnotation comments...")
cursor_checkpoint.execute('''
    SELECT ra.comment, r.experiment_id, c.name, r.protein_concentration
    FROM resultannotation ra
    JOIN result r ON ra.result_id = r.id
    JOIN compound c ON r.compound_id = c.id
''')
for row in cursor_checkpoint.fetchall():
    comment, exp_id, comp_name, prot_conc = row
    result_id = find_result_id(exp_id, comp_name, prot_conc)
    if result_id:
        # Assuming one annotation per result, or update existing
        cursor_main.execute('''
            UPDATE resultannotation SET comment = ? WHERE result_id = ?
        ''', (comment, result_id))
        print(f"Updated ResultAnnotation comment for result {result_id}")

# Commit changes
conn_main.commit()

# Close connections
conn_checkpoint.close()
conn_main.close()

print("Transfer complete.")