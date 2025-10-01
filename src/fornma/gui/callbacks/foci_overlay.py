# src/fornma/gui/callbacks/foci_overlay.py
from dash import Input, Output, State, no_update, ctx
import json, os, time, threading, re, glob
from datetime import datetime

import pandas as pd  # <== necessário para ler o .pkl

def _extract_df_columns_from_pkl(pkl_path: str):
    """
    Lê um .pkl (DataFrame direto ou estrutura contendo um DF) e retorna a lista de colunas.
    Tenta formatos comuns: DataFrame, dict com 'df'/'data', tuple/list cujo primeiro item é DF.
    """
    try:
        obj = pd.read_pickle(pkl_path)
    except Exception:
        return []

    # Caso seja DataFrame direto
    if isinstance(obj, pd.DataFrame):
        return list(obj.columns)

    # Dict com chave 'df' ou 'data'
    if isinstance(obj, dict):
        for key in ("df", "data", "table"):
            val = obj.get(key)
            if isinstance(val, pd.DataFrame):
                return list(val.columns)

    # Lista/tupla cujo primeiro elemento é DF
    if isinstance(obj, (list, tuple)) and obj:
        if isinstance(obj[0], pd.DataFrame):
            return list(obj[0].columns)

    # Última tentativa: procurar qualquer DataFrame aninhado
    try:
        for v in (obj.values() if isinstance(obj, dict) else []):
            if isinstance(v, pd.DataFrame):
                return list(v.columns)
    except Exception:
        pass

    return []

def register(app, pick_directory_dialog):
    # --- Browse handlers
    @app.callback(
        Output("foci-pkl-path", "value"),
        Input("btn-foci-browse-pkl", "n_clicks"),
        State("foci-pkl-path", "value"),
        prevent_initial_call=True
    )
    def _browse_pkl(n, current):
        chosen = pick_directory_dialog()
        return chosen or current or ""

    @app.callback(
        Output("foci-save-path", "value"),
        Input("btn-foci-browse-save", "n_clicks"),
        State("foci-save-path", "value"),
        prevent_initial_call=True
    )
    def _browse_save(n, current):
        chosen = pick_directory_dialog()
        return chosen or current or ""

    # --- Channels: ler um .pkl da pasta e extrair colunas *_channel
    @app.callback(
        Output("foci-channels", "options"),
        Output("foci-channels", "value"),
        Input("foci-pkl-path", "value"),
        prevent_initial_call=True
    )
    def _fill_channels_from_pkl_folder(pkl_folder):
        if not (pkl_folder and os.path.isdir(pkl_folder)):
            return [], []

        import glob
        pkl_files = sorted(glob.glob(os.path.join(pkl_folder, "*.pkl")))
        if not pkl_files:
            return [], []

        cols = _extract_df_columns_from_pkl(pkl_files[0])
        if not cols:
            return [], []

        # pega só colunas que começam com "Image_name_"
        image_name_cols = [c for c in cols if c.startswith("Image_name_")]
        if not image_name_cols:
            return [], []

        # extrai o canal (parte depois do último "_")
        channel_names = [c.split("Image_name_")[-1] for c in image_name_cols]

        options = [{"label": nm, "value": nm} for nm in channel_names]
        return options, channel_names  # seleciona todos por padrão

    # --- Summary
    @app.callback(
        Output("foci-summary", "children"),
        Input("foci-pkl-path", "value"),
        Input("foci-save-path", "value"),
        Input("foci-save-images", "value"),
        Input("foci-channels", "value"),
        Input("foci-actions", "value"),
    )
    def _summary(pkl_path, save_path, save_imgs, channels, actions):
        actions_txt = ", ".join(actions) if actions else "—"
        lines = [
            "Foci Overlay selection:",
            f"- Pickles: {pkl_path or '—'}",
            f"- Output:  {save_path or '—'}",
            f"- Save images: {'Yes' if save_imgs else 'No'}",
            f"- Channels: {', '.join(channels) if channels else '—'}",
            f"- Actions: {actions_txt}",
        ]
        return "\n".join(lines)

    # --- Run (base infra): liga polling, cria arquivo de progresso, etc.
    @app.callback(
        Output("foci-poll", "disabled", allow_duplicate=True),
        Output("foci-log", "children", allow_duplicate=True),
        Output("btn-foci-stop", "style", allow_duplicate=True),
        Input("btn-foci-run", "n_clicks"),
        State("foci-pkl-path", "value"),
        State("foci-save-path", "value"),
        State("foci-save-images", "value"),
        State("foci-channels", "value"),
        State("foci-actions", "value"),
        prevent_initial_call=True,
    )
    def _start_run(n, pkl_path, save_path, save_imgs, channels, actions):
        from uuid import uuid4
        import tempfile
        global PROGRESS_FILE

        if not n:
            return no_update, no_update, no_update

        errs = []
        if not (pkl_path and os.path.isdir(pkl_path)):
            errs.append("Pickle folder is missing or does not exist.")
        if not save_path:
            errs.append("Saving path is required.")
        else:
            try:
                os.makedirs(save_path, exist_ok=True)
            except Exception as e:
                errs.append(f"Cannot create/access saving path: {e}")
        if not channels:
            errs.append("Select at least one channel.")
        if not actions:
            errs.append("Select at least one action (Overlay and/or Plot profiles).")

        if errs:
            hide_stop = {"marginLeft": "8px", "color": "#b00020", "display": "none"}
            return True, "Errors:\n- " + "\n- ".join(errs), hide_stop

        PROGRESS_FILE = os.path.join(tempfile.gettempdir(), f"_fornma_progress_{uuid4().hex}.json")
        try:
            with open(PROGRESS_FILE, "w") as f:
                json.dump({
                    "status": "starting", "total": 0, "done": 0, "percent": 0,
                    "cancel": False, "started_at": datetime.now().isoformat(timespec="seconds"),
                }, f)
        except Exception:
            pass

        # Worker: executa as ações em sequência
        def _worker():
            global PROGRESS_FILE
            try:
                # Dividimos o progresso igualmente entre as ações selecionadas
                steps_per_action = 100 // max(1, len(actions))
                pct = 0

                for action in actions:
                    # Checa cancelamento
                    if not PROGRESS_FILE or not os.path.exists(PROGRESS_FILE):
                        break

                    # >>> Plugue aqui as funções reais:
                    # if action == "overlay":
                    #     run_overlay(pkl_path, save_path, save_imgs, channels, progress_file=PROGRESS_FILE, pct_base=pct, pct_span=steps_per_action)
                    # elif action == "profiles":
                    #     plot_profiles(pkl_path, save_path, channels, progress_file=PROGRESS_FILE, pct_base=pct, pct_span=steps_per_action)

                    # Simulação (remover quando plugar real)
                    for k in range(0, steps_per_action + 1, max(1, steps_per_action // 10)):
                        if not PROGRESS_FILE or not os.path.exists(PROGRESS_FILE):
                            break
                        with open(PROGRESS_FILE, "r") as f:
                            d = json.load(f)
                        if d.get("cancel"):
                            d.update({"status": "canceled"})
                            with open(PROGRESS_FILE, "w") as f:
                                json.dump(d, f)
                            return
                        current_pct = min(100, pct + k)
                        d.update({
                            "status": "running",
                            "percent": current_pct,
                            "log": f"Running {action} — channels={channels} — {current_pct}%"
                        })
                        with open(PROGRESS_FILE, "w") as f:
                            json.dump(d, f)
                        time.sleep(0.25)

                    pct = min(100, pct + steps_per_action)

                # final
                try:
                    with open(PROGRESS_FILE, "r") as f:
                        d = json.load(f)
                except Exception:
                    d = {}
                if d.get("status") not in ("error", "canceled"):
                    d.update({"status": "done", "percent": 100, "log": "Finished all actions."})
                    with open(PROGRESS_FILE, "w") as f: json.dump(d, f)

            except Exception as e:
                with open(PROGRESS_FILE, "w") as f:
                    json.dump({"status": "error", "message": str(e)}, f)
            finally:
                try:
                    time.sleep(1.0)
                    if PROGRESS_FILE and os.path.exists(PROGRESS_FILE):
                        os.remove(PROGRESS_FILE)
                except Exception:
                    pass
                PROGRESS_FILE = None

        threading.Thread(target=_worker, daemon=True).start()

        show_stop = {"marginLeft": "8px", "color": "#b00020", "display": "inline-block"}
        return False, "Starting…", show_stop

    # --- Polling (igual antes)
    @app.callback(
        Output("foci-progress", "value"),
        Output("foci-progress-text", "children"),
        Output("foci-log", "children"),
        Output("foci-poll", "disabled"),
        Output("btn-foci-stop", "style", allow_duplicate=True),
        Input("foci-poll", "n_intervals"),
        prevent_initial_call=True
    )
    def _poll(_n):
        from dash import no_update
        hide_stop = {"display": "none"}
        show_stop = {"display": "inline-block"}

        if not (globals().get("PROGRESS_FILE") and os.path.exists(globals()["PROGRESS_FILE"])):
            return no_update, no_update, no_update, True, hide_stop

        try:
            with open(globals()["PROGRESS_FILE"], "r") as f:
                d = json.load(f)
        except Exception:
            return no_update, no_update, no_update, True, hide_stop

        status = d.get("status", "running")
        percent = int(d.get("percent", 0))
        log = d.get("log", "") or ""

        if status == "error":
            return percent, "Error", (d.get("message") or "Unknown error."), True, hide_stop
        if status == "canceled":
            return percent, "Canceled", (log or "Canceled by user."), True, hide_stop
        if status == "done":
            return 100, "100% (done)", (log or "Finished."), True, hide_stop

        return percent, f"{percent}%", log, False, show_stop

    # --- Stop
    @app.callback(
        Output("foci-log", "children", allow_duplicate=True),
        Output("foci-poll", "disabled", allow_duplicate=True),
        Output("btn-foci-stop", "style", allow_duplicate=True),
        Input("btn-foci-stop", "n_clicks"),
        prevent_initial_call=True
    )
    def _stop(n):
        from dash import no_update
        hide_stop = {"marginLeft": "8px", "color": "#b00020", "display": "none"}
        if not n:
            return no_update, no_update, hide_stop

        try:
            d = {}
            pf = globals().get("PROGRESS_FILE")
            if pf and os.path.exists(pf):
                with open(pf, "r") as f:
                    try: d = json.load(f)
                    except Exception: d = {}
                d.update({"cancel": True, "status": d.get("status", "running")})
                with open(pf, "w") as f:
                    json.dump(d, f)
            return "Stopping… requested. Waiting current file to finish.", False, hide_stop
        except Exception as e:
            return f"Stop failed: {e}", False, hide_stop
