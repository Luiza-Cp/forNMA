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
