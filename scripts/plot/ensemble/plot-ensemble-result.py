import fire
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def main(path: str):
    # Load the data
    data = pd.read_csv(path)

    # Set figure size
    plt.figure(figsize=(12, 6))

    # Set width of bars
    bar_width = 0.3
    precision_width = bar_width * 0.8  # Thinner bar for precision
    recall_width = bar_width * 1.2  # Thicker bar for recall

    # Set position of bars on X axis
    r1 = np.arange(len(data))
    r2 = [x + bar_width for x in r1]

    # Create bars
    plt.bar(r1, data['Precision'], color='blue', width=precision_width, edgecolor='black', label='Precision', alpha=0.8)
    plt.bar(r2, data['Recall'], color='orange', width=recall_width, edgecolor='black', label='Recall', alpha=0.8)

    # Add labels and title
    plt.xlabel('Models', fontweight='bold', fontsize=12)
    plt.ylabel('Scores', fontweight='bold', fontsize=12)
    plt.title('Precision and Recall Scores by Model', fontweight='bold', fontsize=14)
    plt.xticks([r + bar_width / 2 for r in range(len(data))], data['Model'], rotation=45)

    # Add text on top of bars
    for i, v in enumerate(data['Precision']):
        plt.text(i, v + 0.02, f'{v:.2f}', ha='center', va='bottom', fontsize=12)

    for i, v in enumerate(data['Recall']):
        plt.text(i + bar_width, v + 0.02, f'{v:.2f}', ha='center', va='bottom', fontsize=12)

    # Add gridlines to y-axis
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Add legend
    plt.legend(loc='lower right')

    # Adjust layout and display the plot
    plt.tight_layout()
    plt.ylim(0, 1.1)  # Set y-axis limits with some padding for text

    plt.show()


if __name__ == '__main__':
    fire.Fire(main)
