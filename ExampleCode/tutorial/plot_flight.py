"""Plot recorded N/E tracking; run inside Docker where matplotlib is installed."""
import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--output', type=Path, default=Path.home()/'Data/tutorial/square.png')
    args = parser.parse_args()
    with args.csv.open() as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        parser.error('CSV contains no samples')
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    axes[0].plot([float(r['east_m']) for r in rows], [float(r['north_m']) for r in rows], label='Measured')
    axes[0].plot([float(r['target_e_m']) for r in rows], [float(r['target_n_m']) for r in rows], '--', label='Target')
    axes[0].set(xlabel='East [m]', ylabel='North [m]', title='Local position', aspect='equal')
    axes[0].legend()
    axes[1].plot([float(r['elapsed_s']) for r in rows], [float(r['error_m']) for r in rows])
    axes[1].set(xlabel='Wall elapsed time [s]', ylabel='3D target error [m]', title='Takeoff and waypoint steps')
    for ax in axes:
        ax.grid(alpha=0.3)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=150)
    plt.close(fig)
    print(args.output)


if __name__ == '__main__':
    main()
