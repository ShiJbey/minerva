# type: ignore
"""PyTorch Subclasses for Datasets and Neural Net Models."""

from __future__ import annotations

import json
import pathlib
from typing import Union

import numpy as np
import numpy.typing as npt
import pandas as pd
import torch
from feature_extraction import FeatureVectorFactory, get_default_vector_factory
from torch import nn
from torch.utils.data import Dataset

from minerva.ecs import GameObject

FEATURE_VECT_SIZE = 25


class MinervaAutoEncoder(nn.Module):
    """The autoencoder for Minerva characters.

    FEATURE_VECT_SIZE => 32 => 16 => 8 => 16 => 32 => FEATURE_VECT_SIZE
    """

    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            # nn.Linear(FEATURE_VECT_SIZE, 32, dtype=torch.float32),
            # nn.ReLU(),
            nn.Linear(FEATURE_VECT_SIZE, 16, dtype=torch.float32),
            nn.ReLU(),
            nn.Linear(16, 8, dtype=torch.float32),
        )
        self.decoder = nn.Sequential(
            nn.Linear(8, 16, dtype=torch.float32),
            nn.ReLU(),
            nn.Linear(16, FEATURE_VECT_SIZE, dtype=torch.float32),
            # nn.ReLU(),
            # nn.Linear(32, FEATURE_VECT_SIZE, dtype=torch.float32),
        )

    def forward(self, x):
        """Run the forward model."""
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


class MinervaCharacterDataset(Dataset):
    """Minerva character dataset."""

    def __init__(
        self,
        csv_file_path: str,
        no_family_heads=False,
        family_heads_only=False,
        transform=None,
    ) -> None:
        super().__init__()
        self.data = pd.read_csv(csv_file_path)
        if no_family_heads:
            self.data = self.data[self.data["is family head?"] == 0.0]
        if family_heads_only:
            self.data = self.data[self.data["is family head?"] == 1.0]
        self.data_mean = self.data.mean(0)
        self.data_std = self.data.std(0)
        self.transform = transform

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        if torch.is_tensor(index):
            idx = idx.tolist()

        sample = (
            ((self.data.iloc[index] - self.data_mean) / (self.data_std + 1e-10))
            .astype("float32")
            .to_numpy()
        )

        if self.transform:
            sample = self.transform(sample)

        return sample


class MinervaAnomalyDetector:
    """Predicts if minerva characters are anomalies."""

    __slots__ = (
        "training_data_mean",
        "training_data_std",
        "model",
        "error_threshold",
        "vector_factory",
    )

    training_data_mean: npt.NDArray[np.float32]
    """The mean of the training data."""
    training_data_std: npt.NDArray[np.float32]
    """The std deviation of the training data."""
    model: MinervaAutoEncoder
    """The model used for prediction."""
    error_threshold: float
    """The threshold for a character to be considered anomalous."""
    vector_factory: FeatureVectorFactory
    """Extracts feature vectors from characters."""

    def __init__(
        self,
        model: MinervaAutoEncoder,
        training_data_mean: npt.NDArray[np.float32],
        training_data_std: npt.NDArray[np.float32],
        error_threshold: float,
    ) -> None:
        self.model = model
        self.training_data_mean = training_data_mean
        self.training_data_std = training_data_std
        self.error_threshold = error_threshold
        self.vector_factory = get_default_vector_factory()

    def save(self, file_path: Union[str, pathlib.Path]) -> None:
        """Save model configuration information to a file."""

        file_path = pathlib.Path(file_path)

        relative_model_path = file_path.stem + ".model.pt"
        model_path = file_path.parent / relative_model_path

        torch.save(self.model.state_dict(), model_path)

        detector_data = {
            "training_data_mean": self.training_data_mean.tolist(),
            "training_data_std": self.training_data_std.tolist(),
            "error_threshold": self.error_threshold,
            "model_path": relative_model_path,
        }

        with open(file_path, mode="w", encoding="utf8") as f:
            json.dump(detector_data, f, indent=2)

    @staticmethod
    def load(file_path: Union[str, pathlib.Path]) -> MinervaAnomalyDetector:
        """Load model configuration information from a file."""
        with open(file_path, mode="r", encoding="utf8") as f:
            detector_data = json.load(f)
            relative_model_path = detector_data["model_path"]
            error_threshold = detector_data["error_threshold"]
            training_data_mean = np.array(detector_data["training_data_mean"])
            training_data_std = np.array(detector_data["training_data_std"])

        model = MinervaAutoEncoder()
        model.load_state_dict(
            torch.load(
                pathlib.Path(file_path.parent) / relative_model_path, weights_only=True
            )
        )
        model.eval()

        return MinervaAnomalyDetector(
            model=model,
            training_data_mean=training_data_mean,
            training_data_std=training_data_std,
            error_threshold=error_threshold,
        )

    def predict(self, character: GameObject) -> tuple[bool, npt.NDArray[np.float32]]:
        """Predict if a character is an anomaly.

        Returns
        -------
        tuple[bool, npt.NDArray[np.float32]]
            The final classification (True if a character is an anomaly)
            And the columns of the feature vector with errors that contributed to
            the classification.
        """
        feature_vector = self.vector_factory.create_feature_vector(character)

        normalized_vector = (
            (feature_vector - self.training_data_mean)
            / (self.training_data_std + 1e-10)
        ).astype("float32")

        input_tensor = torch.from_numpy(normalized_vector)

        reconstruction = self.model(input_tensor).detach().numpy()

        squared_error = np.square(reconstruction - normalized_vector)

        mean_squared_error = squared_error.mean()

        is_anomaly = mean_squared_error > self.error_threshold

        return is_anomaly, squared_error > self.error_threshold
