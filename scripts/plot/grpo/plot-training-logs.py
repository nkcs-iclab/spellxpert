import fire
import pathlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy import stats


def main(
        path: str = 'training-logs.local',
        name: str | None = None,
        n_point_average: int = 5,
):
    # Load the data
    path = pathlib.Path(path)
    if path.is_dir():
        path = sorted(list(path.rglob('*.csv')))[-1]
    df = pd.read_csv(path, header=0)
    df = df.iloc[:, [0, -3]]
    if name is None:
        name = df.columns[-1].split(' - ')[-1]
    df.columns = ['step', 'value']

    # Convert to appropriate data types
    df = df.astype({
        'step': int,
        'value': float,
    })

    # Extract x and y for plotting
    x = df['step'].values
    y = df['value'].values

    # Calculate the trend line (linear regression)
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    trend_line = slope * x + intercept

    # Create the plot
    plt.figure(figsize=(12, 6))

    # Plot the actual data
    plt.plot(x, y, 'b-', alpha=0.3, marker='o', markersize=4, linewidth=1.5, label=name)

    # Plot the trend line
    plt.plot(x, trend_line, 'r--', linewidth=2, label=f'Trend: y = {slope:.6f}x + {intercept:.6f}')

    # Add an n-point moving average
    window_size = n_point_average
    moving_avg = np.convolve(y, np.ones(window_size) / window_size, mode='valid')
    moving_avg_x = x[window_size - 1:]
    plt.plot(moving_avg_x, moving_avg, 'g-', linewidth=2, label=f'{n_point_average}-point Moving Average')

    # Add labels and title
    plt.xlabel('Step', fontsize=12)
    plt.ylabel(name, fontsize=12)
    plt.title(f'{name} with Trend Line', fontsize=14)

    # Add legend
    plt.legend(loc='best')

    # Add grid
    plt.grid(True, alpha=0.3)

    # Add r-squared value as annotation
    plt.annotate(
        f'R² = {r_value ** 2:.4f}',
        xy=(0.05, 0.95),
        xycoords='axes fraction',
        fontsize=10,
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.7),
    )

    # Set y-axis limits to better show the data
    plt.ylim(df['value'].min() - 0.1, df['value'].max() + 0.1)

    # Display the plot
    plt.tight_layout()
    plt.show()

    # Print statistical information
    print(f'Trend line equation: y = {slope:.6f}x + {intercept:.6f}')
    print(f'R-squared value: {r_value ** 2:.6f}')
    print(f'p-value: {p_value:.6f}')
    print(f'Standard error: {std_err:.6f}')


if __name__ == '__main__':
    fire.Fire(main)
