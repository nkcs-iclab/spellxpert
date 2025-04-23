import fire
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def main(path: str):
    sns.set_theme()

    # Load the data
    data = pd.read_csv(path)

    # Set figure size
    plt.figure(figsize=(12, 6))

    # Set width of bars
    bar_width = 0.3
    precision_width = bar_width * 2 / 3
    recall_width = bar_width * 2 / 3 * 2

    # Set position of bars on X axis
    r1 = np.arange(len(data))
    r2 = [x + bar_width for x in r1]

    # Create bars
    plt.bar(r1, data['Precision'], width=precision_width, label='Precision')
    plt.bar(r2, data['Recall'], width=recall_width, label='Recall')

    # Add labels and title
    plt.xlabel('Models')
    plt.ylabel('Scores')
    plt.title('Precision and Recall Scores by Model')
    plt.xticks([r + bar_width / 2 for r in range(len(data))], data['Model'], rotation=45)

    # Add text on top of bars
    for i, v in enumerate(data['Precision']):
        plt.text(i, v + 0.02, f'{v:.2f}', ha='center', va='bottom')
    for i, v in enumerate(data['Recall']):
        plt.text(i + bar_width, v + 0.02, f'{v:.2f}', ha='center', va='bottom')
    # Add gridlines to y-axis
    plt.grid(axis='x')

    # Add legend
    plt.legend()

    # Adjust layout and display the plot
    plt.tight_layout()
    plt.ylim(0, 1.1)
    plt.show()


if __name__ == '__main__':
    fire.Fire(main)
