import os
import sqlite3
import pandas as pd
import argparse

def load_data(db_path):
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")
    sql = """
    select 
    experiment_id,
    dr.result_id,
    w.id as well_id,
    w.address,
    r.accepted,
    r.locked,
    w.compound_concentration,
    dr.exclude,
    dr.response,
    w.protein_concentration,
    w.volume,
    wr.well_type,
    group_concat(distinct ra.comment) as comments,
    group_concat(a.wavelength) as wavelength,
    group_concat(a.absorbance) as absorbance
    from well w
    join wellresultlink wr
    on wr.well_id = w.id
    join result r
    on r.id = wr.result_id
    join doseresponse dr
    on dr.result_id = wr.result_id and dr.concentration = w.compound_concentration
    left join resultannotation ra
    on ra.result_id = r.id
    join absorbance a
    on a.well_id = w.id
    group by w.id
    """
    with sqlite3.connect(db_path) as con:
        df = pd.read_sql(sql, con)
    
    # Process absorbance
    o = []
    for _, row in df.iterrows():
        o.append(dict(zip(
                list(map(lambda i: int(float(i)), row['wavelength'].split(','))),
                row['absorbance'].split(','))
                     ))
    o = pd.DataFrame(o).astype(float)
    df = pd.concat([df, o], axis=1)
    df = df.drop(['wavelength', 'absorbance'], axis=1)
    return df

def main():
    parser = argparse.ArgumentParser(description="Extract data from database to CSV")
    parser.add_argument('--db_path', type=str, default='../api/db_checkpoints/071125.db', help='Path to SQLite database')
    parser.add_argument('--output', type=str, default='data.csv', help='Output CSV file')
    args = parser.parse_args()

    print(f"Loading data from {args.db_path}")
    df = load_data(args.db_path)
    print(f"Data shape: {df.shape}")
    df.to_csv(args.output, index=False)
    print(f"Saved to {args.output}")

if __name__ == "__main__":
    main()