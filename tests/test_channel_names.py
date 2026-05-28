from fornma.gui.utils.params_builder import build_interface_params


def test_empty_channel_name_uses_visible_default():
    images = {
        "channels": [{"id": "ch1", "name": ""}, {"id": "ch2", "name": "Channel 2"}],
        "rows": [{"condition": "Control", "ch1": "/tmp/channel-one", "ch2": "/tmp/channel-two"}],
    }
    seg = {
        "general": {"path_to_save": "/tmp/fornma-channel-name-test", "channel_with_nuclei": "ch1"},
        "segmentation": {},
        "fornma": {},
        "cellpose": {},
        "filters": {},
        "channels": {},
    }

    params, errors = build_interface_params(images, seg)

    assert errors == []
    assert params["global"]["channel_with_nuclei"] == "Channel 1"
    assert params["Channel ch1"]["channel_name"] == "Channel 1"
    assert params["Channel ch2"]["channel_name"] == "Channel 2"


def test_interface_params_support_nucleus_and_cytoplasm_measurements(tmp_path):
    nuc = tmp_path / "nuc"
    cyto = tmp_path / "cyto"
    out = tmp_path / "out"
    nuc.mkdir()
    cyto.mkdir()

    images = {
        "channels": [{"id": "ch1", "name": "DAPI"}, {"id": "ch2", "name": "Whole cell"}],
        "rows": [{"condition": "Control", "ch1": str(nuc), "ch2": str(cyto)}],
    }
    seg = {
        "general": {
            "path_to_save": str(out),
            "segmentation_mode": "both",
            "channel_with_nuclei": "ch1",
            "channel_with_cytoplasm": "ch2",
            "overtime": True,
        },
        "segmentation": {"seg_method": "cellpose"},
        "fornma": {},
        "cellpose": {},
        "cytoplasm_cellpose": {
            "model_type": "cyto3",
            "diameter": 40,
            "rescale_intensity": True,
            "remove_bg": True,
            "radius_bg": 75,
        },
        "filters": {"minimum_size": 10},
        "cytoplasm_filters": {"minimum_size": 200},
        "channels": {
            "ch1": {"measure_nucleus": True, "measure_cytoplasm": False},
            "ch2": {"measure_nucleus": True, "measure_cytoplasm": True, "wants_ktr": True},
        },
    }

    params, errors = build_interface_params(images, seg)

    assert errors == []
    assert params["global"]["segmentation_mode"] == "both"
    assert params["global"]["channel_with_nuclei"] == "DAPI"
    assert params["global"]["channel_with_cytoplasm"] == "Whole cell"
    assert params["global"]["overtime"] is True
    assert params["cytoplasm_cellpose"]["model_type"] == "cyto3"
    assert params["cytoplasm_cellpose"]["diameter"] == 40
    assert params["cytoplasm_cellpose"]["rescale_intensity"] is True
    assert params["cytoplasm_cellpose"]["remove_bg"] is True
    assert params["cytoplasm_cellpose"]["radius_bg"] == 75
    assert params["global"]["min_size"] == 10
    assert params["cytoplasm_cellpose"]["min_size"] == 200
    assert params["Channel ch1"]["channel_name"] == "DAPI"
    assert params["Channel ch1"]["measure_nucleus"] is True
    assert params["Channel ch1"]["measure_cytoplasm"] is False
    assert params["Channel ch2"]["channel_name"] == "Whole cell"
    assert params["Channel ch2"]["measure_nucleus"] is True
    assert params["Channel ch2"]["measure_cytoplasm"] is True
    assert params["Channel ch2"]["wants_ktr"] is True


def test_create_subfolder_dict_preserves_cytoplasm_segmentation_flag(tmp_path):
    from fornma.core.Segmentation.run import create_subfolder_dict

    condition = tmp_path / "Control"
    condition.mkdir()
    image = condition / "image.tif"
    image.write_bytes(b"not-a-real-image")
    folder_dict = {"Whole cell": [[str(condition)], {"paths": {}}, False, True]}

    subfolder_dict = create_subfolder_dict(folder_dict, 0)

    assert subfolder_dict["Whole cell"][0] == [str(image)]
    assert subfolder_dict["Whole cell"][2] is False
    assert subfolder_dict["Whole cell"][3] is True
