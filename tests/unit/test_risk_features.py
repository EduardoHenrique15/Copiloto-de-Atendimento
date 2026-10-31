import pandas as pd
import pytest

from copiloto.ds.risk.features import (
    FEATURES,
    LeakageError,
    check_feature_list,
    check_no_leakage,
    to_model_frame,
)
from tests.fakes.risk_data import make_risk_frame


def test_feature_list_has_no_post_review_column():
    check_feature_list(FEATURES)
    assert not any(f.startswith("review_") or f == "is_negative" for f in FEATURES)


@pytest.mark.parametrize("bad", ["review_score", "review_created_at", "is_negative", "review_x"])
def test_forbidden_feature_is_rejected(bad):
    with pytest.raises(LeakageError):
        check_feature_list([*FEATURES, bad])


def test_purchase_after_cutoff_is_rejected():
    df = make_risk_frame(50)
    df.loc[0, "purchased_at"] = df.loc[0, "feature_cutoff_at"] + pd.Timedelta(days=1)
    with pytest.raises(LeakageError):
        check_no_leakage(df)


def test_missing_feature_is_reported():
    with pytest.raises(LeakageError, match="ausentes"):
        check_no_leakage(make_risk_frame(50).drop(columns=["distance_km"]))


def test_model_frame_types():
    df = make_risk_frame(50)
    df.loc[0, "main_category"] = None
    x = to_model_frame(df)
    assert list(x.columns) == FEATURES
    assert x["is_late"].dtype == "float64"
    assert x.loc[0, "main_category"] == "missing"
