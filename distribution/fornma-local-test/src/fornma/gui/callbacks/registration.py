# src/fornma/gui/callbacks/registration.py
from dash import Input, Output, State, ALL, no_update, ctx, html

import os, json, tempfile, threading, time,  traceback, importlib
from uuid import uuid4
from datetime import datetime


def _ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _pretty(obj):
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return repr(obj)

def register(app, pick_dir):

    # 1) Opções de canais (vêm do store-images, preenchido pelo modal global)
    @app.callback(
        Output({"type":"reg-field","group":"channels","name":ALL,"field":"channels"}, "options"),
        Input("store-images", "data"),
        State({"type":"reg-field","group":"channels","name":ALL,"field":"channels"}, "id"),
        prevent_initial_call=False
    )
    def _fill_reg_channel_options(data, ids):
        chans = (data or {}).get("channels", [])
        opts = [{"label": ch.get("name", ch.get("id","")), "value": ch.get("id")} for ch in chans]
        return [opts]*len(ids)

    # 2) Browse do "Saving path" (Registration)
    @app.callback(
        Output("reg-save-path", "value"),
        Input("btn-browse-save-reg", "n_clicks"),
        State("reg-save-path", "value"),
        prevent_initial_call=True
    )
    def _browse_save(_, current):
        chosen = pick_dir()
        return chosen or current or ""

    # 3) Sync para o store-reg (sem input_folder)
    @app.callback(
        Output("store-reg", "data"),
        Input("reg-save-path", "value"),
        Input({"type":"reg-field","group":"channels","name":"ref","field":"channels"}, "value"),
        Input({"type":"reg-field","group":"channels","name":"moving","field":"channels"}, "value"),
        prevent_initial_call=False
    )
    def _sync_store_reg(save_path, ref_ch, moving_chs):
        return {
            "io": {"save_path": (save_path or "").strip()},
            "channels": {"reference": ref_ch, "moving": moving_chs or []}
        }

    # --- IMPORT no topo da função create_app() ou no início do arquivo:
    # from fornma.Registration.run import registration as run_registration
    # ^ ajuste o import conforme seu pacote; abaixo, uso um try para evitar crash durante wiring:
    try:
        from fornma.Registration.registration import registration as run_registration
    except Exception:
        run_registration = None

    # ================== REGISTRATION: START ==================

    @app.callback(
        Output("reg-progress-file", "data"),  # 1º: progress file path
        Output("reg-poll", "disabled", allow_duplicate=True),  # 2º: enable polling
        Output("reg-log", "children", allow_duplicate=True),  # 3º: log on screen
        Output("btn-stop-reg", "style", allow_duplicate=True),  # 4º: show Stop button
        Output("reg-warn", "children"),
        Input("btn-run-reg", "n_clicks"),
        State("store-images", "data"),
        State("store-reg", "data"),
        State("reg-crop-flag", "value"),  # <-- crop toggle
        prevent_initial_call=True,
    )
    def _start_reg_run(n_run, images_data, reg_data, crop_flag):
        if not n_run:
            return no_update, no_update, no_update, no_update

        rows = (images_data or {}).get("rows", [])
        channels_meta = (images_data or {}).get("channels", [])
        id2name = {ch["id"]: ch.get("name", ch["id"]) for ch in channels_meta}

        save_path = (reg_data or {}).get("io", {}).get("save_path") or ""
        ref_id = (reg_data or {}).get("channels", {}).get("reference")
        mov_ids = (reg_data or {}).get("channels", {}).get("moving", []) or []

        # crop toggle
        crop = True if crop_flag is None else bool(crop_flag)

        # DEBUG snapshot
        snapshot = {
            "rows": len(rows),
            "save_path": save_path,
            "ref": ref_id,
            "movings": mov_ids,
            "crop": crop,
        }
        dbg = f"[DEBUG] START snapshot: {snapshot}"

        # --- validations ---
        errs = []
        if run_registration is None:
            errs.append("Registration backend not available (import failed).")
        if not save_path:
            errs.append("Please define an output path (Saving path).")
        if not ref_id:
            errs.append("Select a reference channel.")
        if not rows:
            errs.append("No conditions loaded (use 'Load images').")

        sel_ids = [ch_id for ch_id in [ref_id] + list(mov_ids or []) if ch_id]
        for i, r in enumerate(rows, start=1):
            for ch_id in sel_ids:
                if not (r.get(ch_id) or "").strip():
                    errs.append(
                        f"Row {i}: empty path for '{id2name.get(ch_id, ch_id)}'."
                    )

        if errs:
            hide_stop = {"display": "none"}
            warning_html = html.Div(
                [
                    html.H6("⚠️ Missing or invalid parameters:", style={"color": "#b00020"}),
                    html.Ul([html.Li(e, style={"color": "#b00020"}) for e in sorted(set(errs))])
                ]
            )
            return None, True, [dbg, warning_html], hide_stop,  warning_html

        # --- progress file ---
        progress_path = os.path.join(
            tempfile.gettempdir(), f"_fornma_reg_progress_{uuid4().hex}.json"
        )
        with open(progress_path, "w") as f:
            json.dump(
                {"status": "starting", "total": len(rows), "done": 0, "percent": 0,
                 "cancel": False, "log": "Starting registration…", "crop": crop},
                f
            )

        # --- worker thread ---
        def _worker_reg(progress_path, rows, ref_id, mov_ids, save_path, crop):
            def load_state():
                try:
                    with open(progress_path, "r") as _f:
                        return json.load(_f)
                except Exception:
                    return {}

            def write_state(**kw):
                d = load_state()
                d.update(kw)
                try:
                    with open(progress_path, "w") as _f:
                        json.dump(d, _f)
                except Exception:
                    pass

            try:
                total, done = len(rows), 0
                for idx, r in enumerate(rows, start=1):
                    st = load_state()
                    if st.get("cancel"):
                        write_state(status="canceled", log=f"Canceled at condition {idx}/{total}.")
                        break

                    cond_name = r.get("condition") or f"cond_{idx}"
                    folders_to_register = [r.get(ref_id)] + [r.get(mid) for mid in mov_ids]
                    write_state(status="running", log=f"[{idx}/{total}] Registering '{cond_name}'…")

                    try:
                        run_registration(
                            folders_to_register=folders_to_register,
                            path_to_save=save_path,
                            crop=crop
                        )
                    except Exception as e:
                        write_state(status="error", log=f"Error on '{cond_name}': {e}")
                        break

                    done += 1
                    pct = int(done * 100 / total) if total else 100
                    write_state(done=done, percent=pct, log=f"[{idx}/{total}] Done '{cond_name}'.")

                st = load_state()
                if st.get("status") not in ("error", "canceled"):
                    write_state(status="done", percent=100, log="Registration finished.")

                time.sleep(1.0)
                try:
                    if os.path.exists(progress_path):
                        os.remove(progress_path)
                except Exception:
                    pass

            except Exception as e:
                try:
                    with open(progress_path, "w") as _f:
                        json.dump({"status": "error", "message": str(e)}, _f)
                except Exception:
                    pass

        threading.Thread(
            target=_worker_reg,
            args=(progress_path, rows, ref_id, mov_ids, save_path, crop),
            daemon=True
        ).start()

        header = (
            f"{dbg}\nRUN started…\n"
            f"Reference: {id2name.get(ref_id, ref_id)}\n"
            f"Moving: {', '.join(id2name.get(x, x) for x in mov_ids)}\n"
            f"Output: {save_path}\n"
            f"Crop: {crop}"
        )
        show_stop = {"marginLeft": "8px", "color": "#b00020", "display": "inline-block"}

        return progress_path, False, header, show_stop, None

    # ================== REGISTRATION: POLL ==================
    @app.callback(
        Output("reg-progress", "value"),
        Output("reg-progress-text", "children"),
        Output("reg-log", "children", allow_duplicate=True),
        Output("reg-poll", "disabled", allow_duplicate=True),
        Output("btn-stop-reg", "style", allow_duplicate=True),
        Input("reg-poll", "n_intervals"),
        State("reg-progress-file", "data"),  # caminho do arquivo
        prevent_initial_call=True,
    )
    def _poll_reg(_n, progress_path):
        from dash import no_update
        import json, os

        hide_stop = {"display": "none"}
        show_stop = {"display": "inline-block"}

        if not progress_path or not os.path.exists(progress_path):
            # não começou ainda ou o worker já removeu → desliga o polling
            return no_update, no_update, no_update, True, hide_stop

        try:
            with open(progress_path, "r") as f:
                d = json.load(f)
        except Exception:
            return no_update, no_update, no_update, True, hide_stop

        status = d.get("status", "running")
        percent = int(d.get("percent", 0))
        log = d.get("log", "") or ""
        text = f"{percent}%"

        if status == "error":
            return percent, "Error", (log or "Unknown error."), True, hide_stop
        if status == "canceled":
            return percent, "Canceled", (log or "Canceled by user."), True, hide_stop
        if status == "done":
            return 100, "100% (done)", (log or "Finished."), True, hide_stop

        return percent, text, log, False, show_stop

    # ================== REGISTRATION: STOP ==================
    @app.callback(
        Output("reg-log", "children", allow_duplicate=True),
        Output("reg-poll", "disabled", allow_duplicate=True),
        Output("btn-stop-reg", "style", allow_duplicate=True),
        Input("btn-stop-reg", "n_clicks"),
        State("reg-progress-file", "data"),  # caminho do arquivo
        prevent_initial_call=True
    )
    def _stop_reg(n, progress_path):

        hide_stop = {"marginLeft": "8px", "color": "#b00020", "display": "none"}

        if not n:
            return no_update, no_update, hide_stop

        try:
            if progress_path and os.path.exists(progress_path):
                with open(progress_path, "r") as f:
                    try:
                        d = json.load(f)
                    except Exception:
                        d = {}
                d.update({"cancel": True, "status": d.get("status", "running")})
                with open(progress_path, "w") as f:
                    json.dump(d, f)

            return "Stopping… requested. Waiting current condition to finish.", False, hide_stop
        except Exception as e:
            return f"Stop failed: {e}", False, hide_stop


    @app.callback(
        Output("reg-run-ui", "style"),
        Output("reg-footer", "style"),
        Input("reg-poll", "disabled"),
        prevent_initial_call=True,
    )
    def _toggle_reg_run_ui(disabled):
        base = {"display": "block", "width": "100%", "maxWidth": "100%", "overflow": "hidden"}
        if disabled:
            footer_hide = {"display": "none"}
            return base, footer_hide
        else:
            footer_show = {
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "center",
                "gap": "6px",
            }
            return base, footer_show
    @app.callback(
        Output("reg-debug", "children"),
        Input("btn-debug-reg", "n_clicks"),
        State("store-images", "data"),
        State("reg-save-path", "value"),
        State({"type":"reg-field","group":"channels","name":"ref","field":"channels"}, "value"),
        State({"type":"reg-field","group":"channels","name":"moving","field":"channels"}, "value"),
        prevent_initial_call=True,
    )
    def _dump_registration_params(n_clicks, table_state, save_path, ref_ch, moving_chs):
        """
        NÃO executa nada; só imprime um snapshot dos parâmetros atuais.
        """
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # preview leve das linhas para não lotar a UI
        rows_preview = None
        if isinstance(table_state, dict) and "rows" in (table_state or {}):
            rows = table_state.get("rows") or []
            rows_preview = rows[:3]  # mostra no máximo 3 linhas
        else:
            rows_preview = table_state

        snapshot = {
            "timestamp": ts,
            "saving_path": save_path,
            "reference_channel": ref_ch,
            "moving_channels": moving_chs,
            "table_state_keys": list(table_state.keys()) if isinstance(table_state, dict) else None,
            "rows_preview_(up_to_3)": rows_preview,
        }
        return _pretty(snapshot)



    @app.callback(
        Output("reg-run-debug", "children"),
        Input("btn-run-reg", "n_clicks"),
        State("store-images", "data"),
        State("reg-save-path", "value"),
        State({"type":"reg-field","group":"channels","name":"ref","field":"channels"}, "value"),
        State({"type":"reg-field","group":"channels","name":"moving","field":"channels"}, "value"),
        prevent_initial_call=True,
    )
    def _diagnose_run(n, table_state, save_path, ref_ch, moving_chs):
        """
        Não interfere no seu fluxo. Apenas DIAGNOSTICA:
        - parâmetros escolhidos
        - existência de pastas
        - import do backend fornma.Registration.registration:registration
        - possíveis exceptions c/ traceback
        """
        lines = []
        add = lines.append

        add(f"[{_ts()}] [RUN DEBUG] btn-run-reg clicado (n_clicks={n})")
        add(f"- Saving path: {repr(save_path)}  | exists={os.path.isdir(save_path) if save_path else None}")
        add(f"- Reference channel: {repr(ref_ch)}")
        add(f"- Moving channels: {repr(moving_chs)}")

        # Estado da tabela
        try:
            rows = (table_state or {}).get("rows", [])
            add(f"- rows: {len(rows)} linha(s)")
            # valida caminhos por linha e canal
            missing = []
            for i, row in enumerate(rows, start=1):
                for ch in ([ref_ch] + (moving_chs or [])) if ref_ch else (moving_chs or []):
                    p = row.get(ch)
                    ok = bool(p) and os.path.isdir(p)
                    if not ok:
                        missing.append((i, ch, p))
            if missing:
                add("! Caminhos ausentes/invalidos:")
                for i, ch, p in missing[:8]:  # limita listagem
                    add(f"  - linha {i} | {ch} -> {repr(p)} (dir_ok={os.path.isdir(p) if p else None})")
                if len(missing) > 8:
                    add(f"  ...(+{len(missing)-8} itens)")
        except Exception:
            add("! Erro ao inspecionar table_state:")
            add(traceback.format_exc())

        # checa import do backend
        try:
            mod = importlib.import_module("fornma.Registration.registration")
            func = getattr(mod, "registration", None)
            add(f"- import fornma.Registration.registration OK: {bool(mod)}")
            add(f"- função 'registration' encontrada: {callable(func)}")
            if not callable(func):
                # alguns projetos nomeiam de 'run' ou 'run_registration'
                alt = None
                for name in ("run", "run_registration", "registration_main"):
                    if hasattr(mod, name) and callable(getattr(mod, name)):
                        alt = name
                        break
                add(f"- alternativa encontrada: {repr(alt)}")
        except Exception:
            add("! Falha no import do backend fornma.Registration.registration:")
            add(traceback.format_exc())

        # sanidade final
        ready = (
            bool(save_path and os.path.isdir(save_path)) and
            ref_ch is not None and
            len((table_state or {}).get("rows", [])) > 0
        )
        add(f"- Pronto para executar (pré-validação): {ready}")

        return "\n".join(lines)
