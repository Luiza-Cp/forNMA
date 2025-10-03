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
        prevent_initial_call=True
    )
    def _start_run(n_clicks, pkl_path, save_path, save_imgs, channels, actions):
        # estilos do botão Stop
        hide_stop = {"display": "none"}
        show_stop = {"display": "inline-block"}

        try:
            # 1) não clicou? (por segurança, sempre retorna 3 valores)
            if not n_clicks:
                return no_update, no_update, hide_stop

            # 2) validações simples
            if not pkl_path or not os.path.isdir(pkl_path):
                return True, "Please select a valid Pickles folder.", hide_stop

            if not save_path:
                save_path = pkl_path

            if not actions:
                return True, "Select at least one action (Overlay and/or Profiles).", hide_stop

            # 3) cria progress_file e sinaliza início
            import tempfile, pathlib

            ts = int(time.time())
            progress_dir = os.path.join(tempfile.gettempdir(), "fornma_progress")
            pathlib.Path(progress_dir).mkdir(parents=True, exist_ok=True)
            progress_file = os.path.join(progress_dir, f"foci_progress_{ts}.json")

            globals()["PROGRESS_FILE"] = progress_file

            # função util para logar no progress_file sem quebrar
            def _log(status=None, percent=None, log=None, message=None):
                try:
                    payload = {}
                    if status is not None: payload["status"] = status
                    if percent is not None: payload["percent"] = percent
                    if log is not None: payload["log"] = log
                    if message is not None: payload["message"] = message
                    update_progress(progress_file, **payload)
                except Exception:
                    pass

            _log(status="running", percent=0, log="Starting…")

            # 4) worker com progressos graduais
            def _worker():
                import inspect
                try:
                    acts = list(actions or [])
                    n = max(1, len(acts))
                    span = 100 // n
                    base = 0

                    def _safe_call(fn, base_kwargs, progress_kwargs=None):
                        # filtra kwargs pela assinatura real da função
                        try:
                            sig = inspect.signature(fn)

                            def _f(d):
                                return {k: v for k, v in (d or {}).items() if k in sig.parameters}

                            # tenta com progresso
                            try:
                                return fn(**(_f(base_kwargs) | _f(progress_kwargs or {})))
                            except TypeError:
                                # tenta sem progresso (assinatura antiga)
                                return fn(**_f(base_kwargs))
                        except Exception:
                            # fallback bruto: só base_kwargs
                            return fn(**base_kwargs)

                    for action in acts:
                        if cancel_requested(progress_file):
                            _log(status="canceled", log="Canceled by user.")
                            return

                        _log(status="running", percent=base, log=f"Running {action}…")

                        if action == "overlay":
                            base_kwargs = {
                                "pkl_results_folder_path": pkl_path,
                                "path_to_save": save_path,
                                "channel_list": channels or None,
                                "save_images": bool(save_imgs),  # ignorado se função não aceitar
                            }
                            prog_kwargs = {
                                "progress_file": progress_file,
                                "pct_base": base,
                                "pct_span": span,
                            }
                            _safe_call(run_overlay_func, base_kwargs, prog_kwargs)

                        elif action == "profiles":
                            base_kwargs = {
                                "path_pickle_data": pkl_path,
                                "path_save": save_path,
                                "columns": channels or None,
                            }
                            prog_kwargs = {
                                "progress_file": progress_file,
                                "pct_base": base,
                                "pct_span": span,
                            }
                            _safe_call(plot_profiles_func, base_kwargs, prog_kwargs)

                        base = min(100, base + span)
                        _log(status="running", percent=base, log=f"Finished {action}")

                    _log(status="done", percent=100, log="Finished all actions.")

                except Exception as e:
                    _log(status="error", message=str(e), log=f"ERROR: {e}")
                    # não remover o arquivo em caso de erro (para ler no polling)
                    return
                finally:
                    # remove progress_file só se finalizou OK ou cancelado
                    try:
                        with open(progress_file, "r") as f:
                            d = json.load(f)
                        if d.get("status") in {"done", "canceled"}:
                            time.sleep(0.5)
                            os.remove(progress_file)
                    except Exception:
                        pass
                    globals()["PROGRESS_FILE"] = None

            threading.Thread(target=_worker, daemon=True).start()
            # habilita polling, mostra log e botão Stop
            return False, "Running…", show_stop

        except Exception as e:
            # qualquer erro aqui ainda PRECISA retornar 3 valores
            return True, f"Error starting run: {e}", hide_stop

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
