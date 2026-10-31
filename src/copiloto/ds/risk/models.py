"""Os três modelos comparados: regra simples, regressão logística e LightGBM."""

from dataclasses import dataclass, field

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from copiloto.ds.risk.features import (
    BOOLEAN_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TARGET,
    to_model_frame,
)

SEED = 42


@dataclass
class BaselineRule:
    """Regra "negativo se atrasou". A probabilidade é a taxa observada no treino
    para atrasados e para não atrasados, para poder comparar calibração também."""

    rate_late: float = 0.0
    rate_on_time: float = 0.0

    def fit(self, df: pd.DataFrame) -> "BaselineRule":
        late = df["is_late"].astype(bool)
        self.rate_late = float(df.loc[late, TARGET].mean())
        self.rate_on_time = float(df.loc[~late, TARGET].mean())
        return self

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        return np.where(df["is_late"].astype(bool), self.rate_late, self.rate_on_time)


@dataclass
class LogisticModel:
    """Regressão logística com numéricas padronizadas e categorias em one-hot."""

    pipeline: Pipeline | None = None

    def fit(self, df: pd.DataFrame) -> "LogisticModel":
        pre = ColumnTransformer(
            [
                (
                    "num",
                    make_pipeline(
                        SimpleImputer(strategy="median", add_indicator=True), StandardScaler()
                    ),
                    NUMERIC_FEATURES + BOOLEAN_FEATURES,
                ),
                (
                    "cat",
                    OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=50),
                    CATEGORICAL_FEATURES,
                ),
            ]
        )
        self.pipeline = Pipeline([("pre", pre), ("clf", LogisticRegression(max_iter=3000, C=1.0))])
        self.pipeline.fit(to_model_frame(df), df[TARGET].astype(int))
        return self

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        return self.pipeline.predict_proba(to_model_frame(df))[:, 1]


@dataclass
class LightGBMModel:
    """LightGBM com categorias nativas e parada antecipada na validação."""

    params: dict = field(
        default_factory=lambda: {
            "n_estimators": 3000,
            "learning_rate": 0.03,
            "num_leaves": 31,
            "min_child_samples": 50,
            "subsample": 0.8,
            "subsample_freq": 1,
            "colsample_bytree": 0.8,
            "reg_lambda": 1.0,
            "random_state": SEED,
            "verbose": -1,
        }
    )
    model: lgb.LGBMClassifier | None = None
    categories: dict[str, list[str]] = field(default_factory=dict)
    best_iteration: int | None = None

    def _frame(self, df: pd.DataFrame) -> pd.DataFrame:
        x = to_model_frame(df)
        for col in CATEGORICAL_FEATURES:
            # Categoria nunca vista no treino vira ausente, em vez de quebrar.
            known = x[col].where(x[col].isin(self.categories[col]))
            x[col] = pd.Categorical(known, categories=self.categories[col])
        return x

    def fit(self, train: pd.DataFrame, val: pd.DataFrame) -> "LightGBMModel":
        base = to_model_frame(train)
        self.categories = {c: sorted(base[c].unique()) for c in CATEGORICAL_FEATURES}
        self.model = lgb.LGBMClassifier(**self.params)
        self.model.fit(
            self._frame(train),
            train[TARGET].astype(int),
            eval_X=self._frame(val),
            eval_y=val[TARGET].astype(int),
            eval_metric="average_precision",
            callbacks=[lgb.early_stopping(100, verbose=False)],
        )
        self.best_iteration = int(self.model.best_iteration_ or self.params["n_estimators"])
        return self

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        return self.model.predict_proba(self._frame(df))[:, 1]

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Matriz de features no formato do modelo (usada pelo SHAP)."""
        return self._frame(df)
