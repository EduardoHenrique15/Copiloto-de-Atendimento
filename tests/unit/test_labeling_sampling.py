import numpy as np
import pandas as pd
import pytest

from copiloto.ai.labeling.sampling import add_strata, allocate, stratified_sample


def _complaints(n=1000, seed=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "complaint_id": [f"c{i}" for i in range(n)],
            "review_score": rng.choice([1, 2, 3], n, p=[0.6, 0.15, 0.25]),
            "review_created_at": pd.Timestamp("2017-01-01")
            + pd.to_timedelta(rng.integers(0, 600, n), unit="D"),
            "comment_message": ["texto"] * n,
        }
    )


def test_allocation_sums_exactly_and_is_proportional():
    sizes = pd.Series({"a": 600, "b": 150, "c": 250})
    alloc = allocate(sizes, 100)
    assert alloc.sum() == 100
    assert alloc.to_dict() == {"a": 60, "b": 15, "c": 25}


def test_allocation_rejects_oversized_sample():
    with pytest.raises(ValueError):
        allocate(pd.Series({"a": 5}), 10)


def test_strata_combine_score_and_semester():
    df = add_strata(_complaints(5))
    assert df["stratum"].str.match(r"^[123]\|20\d\dS[12]$").all()


def test_sample_is_reproducible_and_stratified():
    df = _complaints()
    a = stratified_sample(df, 100, seed=1)
    b = stratified_sample(df, 100, seed=1)
    assert a["complaint_id"].tolist() == b["complaint_id"].tolist()
    assert len(a) == 100 and a["complaint_id"].is_unique
    share = a["review_score"].value_counts(normalize=True)
    expected = df["review_score"].value_counts(normalize=True)
    assert (share - expected).abs().max() < 0.05


def test_excluded_ids_are_never_sampled():
    df = _complaints()
    first = set(stratified_sample(df, 100, seed=1)["complaint_id"])
    second = stratified_sample(df, 300, seed=2, exclude=first)
    assert not first & set(second["complaint_id"])
