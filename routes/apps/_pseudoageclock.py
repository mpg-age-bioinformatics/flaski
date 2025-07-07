import joblib
import pandas as pd
import numpy as np

import torch
import torch.nn as nn

path_dir="/flaski_private/aaprotlake/"
path_to_encoder = f"{path_dir}/model_20250617.pt"
path_to_features = f"{path_dir}/entire_features.pkl"
path_to_regressor = f"{path_dir}/clock_regressor.pkl"


class AE(nn.Module):
    def __init__(self, input_len):
        super(AE, self).__init__()

        # Encoder
        self.encoder = nn.Sequential(
            nn.Dropout(0.2),  # Dropout to improve robustness
            nn.Linear(input_len, 512),
            # nn.Dropout(0.2),  # Dropout to improve robustness
            nn.LeakyReLU(0.2),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.LeakyReLU(0.2),
            # nn.Dropout(0.2),  # Dropout to improve robustness
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),  # Fixed size (was incorrectly 256 before)
            nn.LeakyReLU(0.2),
            # nn.Dropout(0.2),
            nn.Linear(128, 64)  # Bottleneck (compressed representation)
        )

        # Decoder (symmetric to encoder)
        self.decoder = nn.Sequential(
            nn.Linear(64, 128),
            # nn.BatchNorm1d(128),
            nn.LeakyReLU(0.2),
            nn.Linear(128, 256),
            # nn.BatchNorm1d(256),
            nn.LeakyReLU(0.2),
            nn.Linear(256, input_len),
            nn.Sigmoid()  # Output range (0,1) for normalized data
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

    def add_noise(self, x, noise_factor=0.2):
        """Adds Gaussian noise to input data."""
        noise = noise_factor * torch.randn_like(x)
        return torch.clamp(x + noise, 0.0, 1.0)  # Keep values in range [0,1]

    def fit(self, x):
        encoded = self.encoder(x)
        return encoded


def load_torch_model(cache):
    @cache.memoize(60*60*2) # 2 hours
    def _load_model():
        _model = AE(9766)
        checkpoint = torch.load(path_to_encoder, map_location=torch.device('cpu'))
        _model.load_state_dict(checkpoint)
        _model.eval()
        return _model
    return _load_model()


def load_regressor(cache):
    @cache.memoize(60*60*2) # 2 hours
    def _load_model():
        _model = joblib.load(path_to_regressor)
        return _model
    return _load_model()


def load_features(cache):
    @cache.memoize(60*60*2) # 2 hours
    def _load_data():
        _data = joblib.load(path_to_features)
        return _data
    return _load_data()



def inference(target_df, gene_id_column, cache):
    entire_features = load_features(cache)
    model = load_torch_model(cache)
    best_regr = load_regressor(cache)

    # normalize
    target_df.index = target_df[gene_id_column]
    del(target_df[gene_id_column])
    target_df = target_df[target_df.index != 'NA']
    target_df = target_df[~target_df.index.duplicated(keep='first')]
    target_df = target_df.sort_index()

    target_df = target_df.reindex(entire_features)
    target_df = target_df.T
    target_df = target_df.astype(np.float32)
    target_df[pd.isnull(target_df)] = 0
    target_df[target_df == np.nan] = 0

    target_df = target_df.div(np.sum(target_df, axis=1), axis=0) * 1e4
    target_df = target_df.div(np.max(target_df, axis=1), axis=0)
    target_df[pd.isnull(target_df)] = 0
    target_df[target_df == np.nan] = 0
 
    # feature vector inference
    target_embed = model.fit(torch.Tensor(target_df.to_numpy()))

    # biological age inference
    page = best_regr.predict(target_embed.detach().numpy())

    # output df format
    condition = ['_'.join(x.split('_')[:-1]) for x in target_df.index]
    result_df = pd.DataFrame(target_df.index)
    result_df.columns = ['sampleID']
    result_df['condition'] = condition
    result_df['PseudoAge'] = page

    return result_df
