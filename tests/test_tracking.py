# tests/test_tracking.py
import os
import time
from pathlib import Path
import pandas as pd
import pytest

from fornma.Tracking.tracking import tracking, draw_track

# -------------------------
# Diretórios de teste
# -------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "tracking"

TRACK_TABLE = DATA_DIR / "Results.csv"   # seu CSV de entrada p/ tracking
IMAGES_DIR  = BASE_DIR / "data" / 'tracking'/ 'red'           # se draw_track precisar de imagens por frame

RESULTS_BASE = BASE_DIR / "results" / "tracking"
RESULTS_TRACK = RESULTS_BASE / "tracks"         # onde o tracking vai salvar
RESULTS_DRAW  = RESULTS_BASE / "draw"           # onde o draw_track vai salvar


@pytest.fixture(scope="module", autouse=True)
def _ensure_dirs():
    RESULTS_TRACK.mkdir(parents=True, exist_ok=True)
    RESULTS_DRAW.mkdir(parents=True, exist_ok=True)


def _most_recent_csv(folder: Path) -> Path | None:
    csvs = list(folder.glob("*.csv"))
    if not csvs:
        return None
    return max(csvs, key=lambda p: p.stat().st_mtime)


def _has_any_image(root: Path) -> bool:
    image_exts = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
    for r, _dirs, files in os.walk(root):
        for f in files:
            if Path(f).suffix.lower() in image_exts:
                return True
    return False


def test_tracking_creates_output():
    assert TRACK_TABLE.exists(), f"Arquivo de entrada não existe: {TRACK_TABLE}"

    # roda tracking salvando em RESULTS_TRACK
    tracking(
        path_to_table=str(TRACK_TABLE),
        saving_path=str(RESULTS_TRACK),
        max_distance=30,
        time_window=5,
        max_split_distance=10,
        max_gap_closing_distance=10,
    )

    time.sleep(0.1)  # pequeno respiro pro FS

    out = _most_recent_csv(RESULTS_TRACK)
    assert out is not None, "Tracking não gerou nenhum CSV em RESULTS_TRACK"
    df = pd.read_csv(out)

    # ajuste os nomes dessas colunas conforme sua saída real
    essentials = {"frame", "x", "y"}
    assert essentials.issubset({c.lower() for c in df.columns.map(str)}), (
        f"CSV de tracking não contém colunas essenciais; colunas: {list(df.columns)}"
    )


def test_tracking_split_distance_changes_track_count():
    assert TRACK_TABLE.exists()

    tracking(path_to_table=str(TRACK_TABLE), saving_path=str(RESULTS_TRACK), max_split_distance=5)
    time.sleep(0.1)
    out1 = _most_recent_csv(RESULTS_TRACK)
    assert out1, "Sem CSV após max_split_distance=5"
    df1 = pd.read_csv(out1)

    tracking(path_to_table=str(TRACK_TABLE), saving_path=str(RESULTS_TRACK), max_split_distance=20)
    time.sleep(0.1)
    out2 = _most_recent_csv(RESULTS_TRACK)
    assert out2, "Sem CSV após max_split_distance=20"
    df2 = pd.read_csv(out2)

    # tente detectar a coluna de ID de trilha; ajuste se souber o nome exato
    id_candidates = ["track_id"]
    track_col = next((c for c in id_candidates if c in df1.columns and c in df2.columns), None)
    if track_col is None:
        pytest.skip("Coluna de ID de trilha não encontrada (ajuste o nome no teste).")

    n1 = df1[track_col].nunique()
    n2 = df2[track_col].nunique()

    assert n2 <= n1, f"Esperava mais (ou igual) trilhas com max_split_distance=20 (obtido {n2} vs {n1})."


def test_draw_track_saves_images():
    # pega o CSV de tracking mais recente gerado no teste anterior
    out = _most_recent_csv(RESULTS_TRACK)
    assert out, "Rode o tracking antes: não encontrei CSV de trilhas em RESULTS_TRACK"
    df = pd.read_csv(out)

    RESULTS_DRAW.mkdir(parents=True, exist_ok=True)

    draw_track(
        df=df,
        folder=str(IMAGES_DIR),
        save=str(RESULTS_DRAW),
        img_col='Image_name_red',
        trail_window=15,
        point_radius=2,
        point_thickness=2,
        font_scale=0.7,
        text_thickness=1
    )

    assert _has_any_image(RESULTS_DRAW), "Nenhuma imagem foi gerada por draw_track()"
