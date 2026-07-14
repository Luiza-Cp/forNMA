import pandas as pd
import pytest

from fornma.api.main import _apply_gate, _gate_summary_table
from fornma.api.schemas import GatingPreviewRequest


def test_gate_summary_counts_cells_by_condition():
    req = GatingPreviewRequest(x_col="Area", y_col="NII")
    df = pd.DataFrame(
        {
            "__source__": ["Dataset 1", "Dataset 1", "Dataset 1", "Dataset 1"],
            "__source_path__": ["a.csv", "a.csv", "a.csv", "a.csv"],
            "Condition": ["Control", "Control", "DOX", "DOX"],
            "Area": [1, 2, 10, 20],
            "NII": [1, 2, 10, 20],
        }
    )
    df["__gate_keep__"] = _apply_gate(df, "Area", "NII", 1.5, 15, 1.5, 15)

    summary = _gate_summary_table(df, req, 1.5, 15, 1.5, 15)

    rows = summary.rows
    assert [(row["dataset"], row["condition"]) for row in rows] == [
        ("Dataset 1", "Control"),
        ("Dataset 1", "DOX"),
        ("All datasets", "All conditions"),
    ]
    assert rows[0]["total"] == 2
    assert rows[0]["kept"] == 1
    assert rows[0]["removed"] == 1
    assert rows[1]["total"] == 2
    assert rows[1]["kept"] == 1
    assert rows[1]["removed"] == 1
    assert rows[0]["Area_min_percentile"] == pytest.approx(50.0)
    assert rows[1]["Area_min_percentile"] == pytest.approx(0.0)
    assert rows[1]["Area_max_percentile"] == pytest.approx(50.0)
