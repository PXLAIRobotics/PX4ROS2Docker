"""Lesson 10: evaluate the square CSV offline without importing ROS."""
import argparse
import csv
import math
from pathlib import Path
from statistics import mean


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    args = parser.parse_args()
    with args.csv.open() as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        parser.error('CSV contains no samples')
    for stage in dict.fromkeys(row['stage'] for row in rows):
        errors = [float(row['error_m']) for row in rows if row['stage'] == stage]
        if not all(math.isfinite(value) for value in errors):
            parser.error('CSV contains non-finite errors')
        print(f'{stage}: n={len(errors)} mean={mean(errors):.3f} m '
              f'RMSE={math.sqrt(mean(value*value for value in errors)):.3f} m '
              f'max={max(errors):.3f} m')
    print('Includes commanded step transients; this is tracking error, not localisation accuracy.')


if __name__ == '__main__':
    main()
