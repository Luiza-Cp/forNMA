import numpy as np
import pandas as pd

from fornma.api.main import foci_channels
from fornma.api.schemas import FociChannelsRequest
from fornma.core.Foci_overlay.foci_overlay import perform_foci_overlay


def test_foci_overlay_uses_only_channels_with_foci_contours(tmp_path):
    nucleus = np.array([[[5, 5]], [[16, 5]], [[16, 16]], [[5, 16]], [[5, 5]]], dtype=np.int32)
    focus = np.array([[[8, 8]], [[10, 8]], [[10, 10]], [[8, 10]], [[8, 8]]], dtype=np.int32)
    image = np.zeros((24, 24), dtype=np.uint8)

    df = pd.DataFrame(
        {
            "Cell": [1],
            "Image_DAPI": [image],
            "Image_name_DAPI": ["img.tif"],
            "Nuc_cnt_DAPI": [nucleus],
            "Foci_cnt_DAPI": [[focus]],
            "Image_LC3": [image],
            "Image_name_LC3": ["img.tif"],
            "Nuc_cnt_LC3": [nucleus],
        }
    )

    perform_foci_overlay(
        dfs=[df],
        df_names=["img"],
        save_images=False,
        path_save=str(tmp_path),
    )

    result = pd.read_csv(tmp_path / "Overlay Pixel Counts.csv")
    assert "Total_pixel_DAPI" in result.columns
    assert "Total_pixel_LC3" not in result.columns
    assert int(result["Total_pixel_DAPI"].iloc[0]) > 0


def test_foci_channels_lists_only_channels_with_foci_contours(tmp_path):
    df = pd.DataFrame(
        {
            "Cell": [1],
            "Image_name_DAPI": ["img.png"],
            "Foci_cnt_DAPI": [[]],
            "Image_name_LC3": ["img.png"],
        }
    )
    pkl_dir = tmp_path / "pkl-data"
    pkl_dir.mkdir()
    df.to_pickle(pkl_dir / "img results.pkl")

    response = foci_channels(FociChannelsRequest(pkl_path=str(pkl_dir)))

    assert response.channels == ["DAPI"]
