# src/fornma/gui/utils/params_builder.py
from pathlib import Path


# === GUI (flex) builder: não exige root comum; usa formato "interface" ===

_CHANNEL_DEFAULTS = {
    "rescale_intensity": True,
    "remove_bg": True,
    "radius_bg": 40,
    "match_hist": False,
    "wants_ktr": False,      # measure_translocation
    "ring_size": False,
    "use_ellipse": False,
    "wants_foci": True,      # measure_foci
    "foci_min_size": 7,
    "foci_max_size": False,
    "foci_min_int": False,
    "foci_max_int": False,
    "foci_proeminence": 1.2,  # nome usado no pipeline
}

def _norm(s):
    return (s or "").strip()

def _default_channel_name(index: int) -> str:
    return f"Channel {index + 1}"

def build_interface_params(images_data: dict, seg_data: dict) -> tuple[dict, list[str]]:
    """
    Constrói o dicionário no formato aceito por adjust_parameters_interface()
    (chave 'global' + 'fornma' + 'cellpose' + 'Channel <name>' com 'paths').
    Não exige mesmo root por canal.
    Retorna (params, errors).
    """
    errors: list[str] = []

    images = images_data or {}
    seg    = seg_data or {}
    per_channel = seg.get("channels", {})  # <- NOVO

    channels = images.get("channels", [])       # [{"id":"ch1","name":"Channel 1"}, ...]
    rows     = images.get("rows", [])           # [{"condition":"...", "ch1":"/abs/..", ...}, ...]

    if not channels:
        errors.append("No image channels were loaded. Click 'Load images' and add at least one channel.")
        return {}, errors
    if not rows:
        errors.append("No experimental conditions were loaded. Click 'Load images' and add at least one condition row.")
        return {}, errors

    ch_ids   = [c["id"] for c in channels]
    ch_names = [_norm(c.get("name")) or _default_channel_name(i) for i, c in enumerate(channels)]

    general      = seg.get("general", {})
    segmentation = seg.get("segmentation", {})
    fornma       = seg.get("fornma", {})
    cellpose     = seg.get("cellpose", {})
    filters      = seg.get("filters", {})

    # Saída e canal com núcleos (no modo interface, é NOME do canal)
    # Saving path é obrigatório
    output_folder = (general.get("path_to_save") or "").strip()
    if not output_folder:
        errors.append("Choose a Saving path before running. This is where forNMA will write tables, images, and logs.")
        return {}, errors

    # (opcional, recomendado) tentar criar a pasta se não existir
    import os
    try:
        os.makedirs(output_folder, exist_ok=True)
    except Exception as e:
        errors.append(f"Cannot create or access the Saving path '{output_folder}'. Check folder permissions or choose another location. Details: {e}")
        return {}, errors

    ch_nuc_id = general.get("channel_with_nuclei")
    channel_with_nuclei = None
    if ch_nuc_id in ch_ids:
        channel_with_nuclei = ch_names[ch_ids.index(ch_nuc_id)]
    elif ch_nuc_id:
        errors.append("The selected Nuclear Detection channel is no longer available. Choose one of the current channels.")

    params = {
        # <<< chave 'global' primeiro: o run() usa isso para escolher o caminho "interface"
        "global": {
            "output_folder": output_folder,
            "channel_with_nuclei": channel_with_nuclei,
            # você pode incluir "overtime" aqui quando quiser expor
            "magnification":  segmentation.get("magnification"),
            "pixel_size":    segmentation.get("pixel-size"),
            "rescale_intensity": bool(segmentation.get("rescale-intensity", False)),
            "remove_background": bool(segmentation.get("remove-bg", False)),
            "radius_bg":         segmentation.get("rolling-radius"),
            # filtros globais
            "shape":        filters.get("shape"),
            "eccentricity": filters.get("eccentricity"),
            "min_size":     filters.get("minimum_size"),
            "max_size":     filters.get("maximum_size"),
            "min_radius":   filters.get("minimum_radius"),
            "max_radius":   filters.get("maximum_radius"),
        },
        "fornma": {
            "threshold": fornma.get("threshold", "triangle"),
            "offset": fornma.get("offset", 5),
            "blur": fornma.get("smooth", 12),
            "adjust_size": fornma.get("adjust_size", 0),
            "cut_edges": fornma.get("cut_edges", 0.7),
            "find_low_intensity_nucleus": bool(fornma.get("find_low_intensity_nucleus", False)),
            "weakly_labeled": bool(fornma.get("weakly_labeled", False)),
        },
        "cellpose": {
            "use_cellpose": segmentation.get("seg_method") == "cellpose",
            "model_type": cellpose.get("model_type", "nuclei"),
            "diameter": cellpose.get("diameter", 25),
            "flow_threshold": cellpose.get("flow_threshold", 0.4),
            "mask_threshold": cellpose.get("mask_threshold", 0.0),
            "invert": bool(cellpose.get("invert", True)),
            # o run() fixa use_gpu=False no caminho interface; manter aqui é inofensivo para futuro
            "use_gpu": bool(cellpose.get("use_gpu", False)),
            "cellprob_threshold": cellpose.get("cellprob_threshold", -3),
        },
    }

    # Por-canal: 'Channel <name>' com 'paths' mapeando condition -> path absoluto
    for ch_id, ch_name in zip(ch_ids, ch_names):
        cond_to_path = {}
        for r in rows:
            cond = _norm(r.get("condition", ""))
            p    = _norm(r.get(ch_id, ""))
            if not cond:
                errors.append("One condition row has no name. Open 'Load images' and fill the Condition column.")
            if not p:
                condition_label = cond or "unnamed condition"
                errors.append(f"Missing image folder for channel '{ch_name}' in condition '{condition_label}'. Open 'Load images' and choose a folder for that cell.")
            cond_to_path[cond] = p

        ch_dict = dict(_CHANNEL_DEFAULTS)

        # overrides vindos do store-seg (se existirem) — mapeia nomes da UI p/ nomes do pipeline
        ov = per_channel.get(ch_id, {})

        # básicos
        if "rescale_intensity" in ov: ch_dict["rescale_intensity"] = bool(ov["rescale_intensity"])
        if "remove_background" in ov: ch_dict["remove_bg"] = bool(ov["remove_background"])
        if "rolling_ball_radius" in ov: ch_dict["radius_bg"] = ov["rolling_ball_radius"]
        if "match_histograms" in ov: ch_dict["match_hist"] = bool(ov["match_histograms"])

        # translocation / ring
        if "ring_size" in ov: ch_dict["ring_size"] = ov["ring_size"]
        if "use_ellipse" in ov: ch_dict["use_ellipse"] = bool(ov["use_ellipse"])

        # foci
        if "wants_foci" in ov: ch_dict["wants_foci"] = bool(ov["wants_foci"])
        if "foci_min_size" in ov: ch_dict["foci_min_size"] = ov["foci_min_size"]
        if "foci_max_size" in ov: ch_dict["foci_max_size"] = ov["foci_max_size"]
        if "foci_min_int" in ov: ch_dict["foci_min_int"] = ov["foci_min_int"]
        if "foci_max_int" in ov: ch_dict["foci_max_int"] = ov["foci_max_int"]
        if ("foci_prominence" in ov) or ("foci_proeminence" in ov):
            ch_dict["foci_proeminence"] = ov.get("foci_prominence", ov.get("foci_proeminence"))

        # por fim, os paths
        ch_dict["channel_name"] = ch_name
        ch_dict["paths"] = cond_to_path
        params[f"Channel {ch_id}"] = ch_dict


    return params, errors
