import json, os, time, threading, re, glob
from datetime import datetime
import pandas as pd
from dash import Input, Output, State, no_update, ctx

# >>> progress utils (seu arquivo)
try:
    from fornma.gui.utils.progress import update_progress, cancel_requested
except Exception:
    # fallback para desenvolvimento local, caso o path do pacote esteja diferente
    from progress import update_progress, cancel_requested

# >>> foci functions (tenta pelo pacote; se não, importa direto do arquivo)
try:
    from fornma.Foci_overlay.foci_overlay import foci_overlay as run_overlay_func, plot_profile as plot_profiles_func
except Exception:
    from foci_overlay import foci_overlay as run_overlay_func, plot_profile as plot_profiles_func


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

        # estilos padrão que SEMPRE existem
        hide_stop = {"marginLeft": "8px", "color": "#b00020", "display": "none"}
        show_stop = {"marginLeft": "8px", "color": "#b00020", "display": "inline-block"}

        try:
            if not n:
                # 3 retornos SEMPRE
                return no_update, no_update, hide_stop

            # normaliza entradas
            actions = actions or []
            channels = channels or []

            # validações
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
                return True, "Errors:\n- " + "\n- ".join(errs), hide_stop

            # cria/zera progress file
            global PROGRESS_FILE
            PROGRESS_FILE = os.path.join(tempfile.gettempdir(), f"_fornma_progress_{uuid4().hex}.json")
            update_progress(
                PROGRESS_FILE,
                status="starting", total=0, done=0, percent=0, cancel=False,
                started_at=datetime.now().isoformat(timespec="seconds"),
                log="Initializing…"
            )

            # worker em thread
            def _worker():
                global PROGRESS_FILE
                try:
                    num_actions = max(1, len(actions))
                    span = 100 // num_actions
                    base = 0

                    update_progress(PROGRESS_FILE, status="running", percent=0,
                                    log=f"Starting… actions={actions}, channels={channels}")

                    for action in actions:
                        if cancel_requested(PROGRESS_FILE):
                            update_progress(PROGRESS_FILE, status="canceled", log="Canceled by user.")
                            return

                        update_progress(PROGRESS_FILE, status="running", percent=base,
                                        log=f"Running {action} — channels={channels}")

                        if action == "overlay":
                            run_overlay_func(
                                pkl_results_folder_path=pkl_path,
                                path_to_save=save_path,
                                channel_list=channels or None,
                            )
                        elif action == "profiles":
                            plot_profiles_func(
                                path_pickle_data=pkl_path,
                                path_save=save_path,
                                columns=channels or None,
                            )

                        base = min(100, base + span)
                        update_progress(PROGRESS_FILE, status="running", percent=base,
                                        log=f"Finished {action}")

                    update_progress(PROGRESS_FILE, status="done", percent=100,
                                    log="Finished all actions.")

                except Exception as e:
                    update_progress(PROGRESS_FILE, status="error", message=str(e))
                finally:
                    try:
                        time.sleep(0.8)
                        if PROGRESS_FILE and os.path.exists(PROGRESS_FILE):
                            os.remove(PROGRESS_FILE)
                    except Exception:
                        pass
                    PROGRESS_FILE = None

            threading.Thread(target=_worker, daemon=True).start()

            # habilita polling, printa log inicial e mostra STOP
            return False, "Starting…", show_stop

        except Exception as e:
            # Se QUALQUER coisa der errado, ainda assim retornamos 3 itens
            return True, f"Setup failed: {e}", hide_stop

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
                    try:
                        d = json.load(f)
                    except Exception:
                        d = {}
                d.update({"cancel": True, "status": d.get("status", "running")})
                with open(pf, "w") as f:
                    json.dump(d, f)
            return "Stopping… requested. Waiting current file to finish.", False, hide_stop
        except Exception as e:
            return f"Stop failed: {e}", False, hide_stop
