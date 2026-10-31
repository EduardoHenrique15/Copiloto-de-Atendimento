from copiloto.ds.risk.split import temporal_split
from tests.fakes.risk_data import make_risk_frame


def test_split_is_temporal_and_disjoint():
    df = make_risk_frame(2000)
    s = temporal_split(df)
    assert s.train["feature_cutoff_at"].max() < s.val_start
    assert s.val["feature_cutoff_at"].min() >= s.val_start
    assert s.val["feature_cutoff_at"].max() < s.test_start
    assert s.test["feature_cutoff_at"].min() >= s.test_start
    ids = [set(p["order_id"]) for p in (s.train, s.val, s.test)]
    assert not (ids[0] & ids[1] or ids[0] & ids[2] or ids[1] & ids[2])


def test_labels_must_exist_before_next_part_starts():
    df = make_risk_frame(2000)
    s = temporal_split(df)
    assert (s.train["review_created_at"] < s.val_start).all()
    assert (s.val["review_created_at"] < s.test_start).all()
    assert len(s.train) + len(s.val) + len(s.test) + s.dropped_unlabeled == len(df)
    assert s.dropped_unlabeled > 0  # avaliações até 5 dias depois da entrega


def test_test_fraction_is_respected():
    s = temporal_split(make_risk_frame(2000), val_frac=0.2, test_frac=0.1)
    assert abs(len(s.test) / 2000 - 0.1) < 0.01
