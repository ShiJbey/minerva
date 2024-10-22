# type: ignore
"""Train a new anomaly detector model."""

import pathlib

import matplotlib.pyplot as plt
import pandas as pd
import torch
from anomaly_model import (
    MinervaAnomalyDetector,
    MinervaAutoEncoder,
    MinervaCharacterDataset,
)
from tqdm import tqdm


def train_anomaly_detector(
    dataset: MinervaCharacterDataset,
) -> tuple[MinervaAnomalyDetector, pd.DataFrame]:
    """Train a new anomaly detector."""

    model = MinervaAutoEncoder()

    loss_function = torch.nn.MSELoss()

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-1, weight_decay=1e-8)

    loader = torch.utils.data.DataLoader(dataset=dataset, batch_size=32, shuffle=True)

    epochs = 50
    losses = []
    for _ in range(epochs):
        for batch in tqdm(loader):

            # Output of Autoencoder
            reconstructed = model(batch)

            # Calculating the loss function
            loss = loss_function(reconstructed, batch)

            # The gradients are set to zero,
            # the gradient is computed and stored.
            # .step() performs parameter update
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # Storing the losses in a list for plotting
            losses.append(loss.detach().numpy())

    loss_df = pd.DataFrame(losses[-100:])
    quartiles = loss_df.quantile([0.25, 0.75])
    q_3 = quartiles.loc[0.75].squeeze()
    q_1 = quartiles.loc[0.25].squeeze()
    iqr = q_3 - q_1
    high_fence = q_3 + 1.5 * iqr

    return (
        MinervaAnomalyDetector(
            model=model,
            training_data_mean=dataset.data_mean.to_numpy(),
            training_data_std=dataset.data_std.to_numpy(),
            error_threshold=high_fence,
        ),
        loss_df,
    )


def plot_training_loss(detector: MinervaAnomalyDetector, loss: pd.DataFrame):
    """Plot the loss of the model and the error threshold."""
    # Defining the Plot Style
    plt.style.use("fivethirtyeight")
    plt.ylim((0, 6))
    plt.xlabel("Iterations")
    plt.ylabel("Loss")

    # Plotting the last 100 values
    plt.axhline(y=detector.error_threshold, color="r", linestyle="-")
    plt.plot(loss)

    plt.show()


def main():
    """Main Function."""

    dataset = MinervaCharacterDataset(
        pathlib.Path(__file__).parent / "output.csv", family_heads_only=True
    )

    detector, loss = train_anomaly_detector(dataset)

    plot_training_loss(detector, loss)

    detector.save(pathlib.Path(__file__).parent / "family_head_only_detector.json")


if __name__ == "__main__":
    main()
