from __future__ import annotations

from types import SimpleNamespace

import mobile_spa_app


class _FakeContext:
    def __enter__(self) -> _FakeContext:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakeSessionState(dict):
    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value) -> None:
        self[name] = value


class _FakePerformanceOptimizer:
    def __init__(self) -> None:
        self.cache = SimpleNamespace(clear=lambda: None)

    def get_optimized_css(self) -> str:
        return ""


class _RecordingStreamlit:
    def __init__(self) -> None:
        self.session_state = _FakeSessionState(
            {
                "mobile_app_initialized": True,
                "mobile_css_loaded": True,
                "current_tab": "image_analysis",
            }
        )
        self.cache_resource = SimpleNamespace(clear=lambda: None)
        self.markdown_calls: list[str] = []
        self.info_calls: list[str] = []
        self.success_calls: list[str] = []
        self.error_calls: list[str] = []
        self.warning_calls: list[str] = []
        self.expander_labels: list[str] = []
        self.tab_groups: list[list[str]] = []
        self.button_labels: list[str] = []
        self.selectbox_values: dict[str, str] = {}
        self.selectbox_calls: list[dict[str, object]] = []
        self.clicked_buttons: set[str] = set()

    def markdown(self, body, *args, **kwargs) -> None:
        self.markdown_calls.append(str(body))

    def columns(self, spec):
        count = spec if isinstance(spec, int) else len(spec)
        return [_FakeContext() for _ in range(count)]

    def tabs(self, names):
        captured = list(names)
        self.tab_groups.append(captured)
        return [_FakeContext() for _ in captured]

    def selectbox(self, label, options, index=0, **kwargs):
        value = self.selectbox_values.get(str(label), options[index])
        self.selectbox_calls.append(
            {
                "label": str(label),
                "options": list(options),
                "index": index,
                "value": value,
            }
        )
        return value

    def button(self, label, *args, **kwargs) -> bool:
        self.button_labels.append(str(label))
        return str(label) in self.clicked_buttons

    def file_uploader(self, *args, **kwargs):
        return None

    def info(self, message, *args, **kwargs) -> None:
        self.info_calls.append(str(message))

    def success(self, message, *args, **kwargs) -> None:
        self.success_calls.append(str(message))

    def error(self, message, *args, **kwargs) -> None:
        self.error_calls.append(str(message))

    def warning(self, message, *args, **kwargs) -> None:
        self.warning_calls.append(str(message))

    def json(self, *args, **kwargs) -> None:
        return None

    def image(self, *args, **kwargs) -> None:
        return None

    def audio(self, *args, **kwargs) -> None:
        return None

    def text_area(self, *args, **kwargs) -> None:
        return None

    def metric(self, *args, **kwargs) -> None:
        return None

    def expander(self, label, *args, **kwargs) -> _FakeContext:
        self.expander_labels.append(str(label))
        return _FakeContext()

    def spinner(self, *args, **kwargs) -> _FakeContext:
        return _FakeContext()


def _render_main_shell(monkeypatch) -> _RecordingStreamlit:
    fake_st = _RecordingStreamlit()

    monkeypatch.setattr(mobile_spa_app, "st", fake_st)
    monkeypatch.setattr(mobile_spa_app, "load_core_adapters", lambda: (object(), object(), object()))
    monkeypatch.setattr(mobile_spa_app, "get_model_status", lambda: {"vision": "resnet50", "audio": "whisper", "text": "gpt"})
    monkeypatch.setattr(mobile_spa_app, "mobile_performance_optimizer", _FakePerformanceOptimizer())

    app = mobile_spa_app.MobilePlantGuardApp()
    monkeypatch.setattr(app, "_ui_components_available", lambda: True)
    monkeypatch.setattr(app, "initialize_components", lambda: None)

    app._run_main_app()
    return fake_st


def test_app_exposes_only_product_tabs(monkeypatch) -> None:
    fake_st = _render_main_shell(monkeypatch)

    assert fake_st.tab_groups == [["Image Analysis", "Voice & Audio", "Chat", "Settings"]]


def test_chat_tab_is_direct_not_placeholder(monkeypatch) -> None:
    fake_st = _render_main_shell(monkeypatch)

    all_messages = fake_st.markdown_calls + fake_st.info_calls + fake_st.success_calls + fake_st.button_labels
    joined = "\n".join(all_messages)

    assert "Use Chat Interface tab for full functionality" not in joined
    assert "Open Chat" not in joined


def test_apply_models_switches_vision_adapter_through_model_manager(monkeypatch) -> None:
    fake_st = _RecordingStreamlit()
    fake_st.selectbox_values = {
        "Vision Model": "local_resnet",
        "Audio Model": "openai/whisper-base",
        "Text Model": "gpt-4",
    }
    fake_st.clicked_buttons = {"Apply Models"}

    current_adapter = object()
    resnet_adapter = object()
    switch_calls: list[str] = []

    class _FakeModelManager:
        def __init__(self) -> None:
            self.current_adapter = current_adapter

        def list_available_models(self):
            return [
                {"id": "vit_best", "name": "Vision Transformer", "enabled": True},
                {"id": "local_resnet", "name": "ResNet50", "enabled": True},
            ]

        def switch_model_for_ui(self, model_id: str) -> bool:
            switch_calls.append(model_id)
            self.current_adapter = resnet_adapter
            return True

    monkeypatch.setattr(mobile_spa_app, "st", fake_st)
    monkeypatch.setattr(mobile_spa_app, "load_core_adapters", lambda: (current_adapter, object(), object()))
    monkeypatch.setattr(mobile_spa_app, "mobile_performance_optimizer", _FakePerformanceOptimizer())
    monkeypatch.setattr(mobile_spa_app, "load_vision_model_manager", lambda: _FakeModelManager())

    app = mobile_spa_app.MobilePlantGuardApp()
    app._render_web_settings_tab()

    assert switch_calls == ["local_resnet"]
    assert app.vision_adapter is resnet_adapter


def test_app_starts_with_local_resnet_default_when_valid_checkpoint_is_available(monkeypatch) -> None:
    fake_st = _RecordingStreamlit()
    resnet_adapter = object()

    class _FakeModelManager:
        def __init__(self) -> None:
            self.current_adapter = resnet_adapter
            self.current_model = object()

        def _get_current_model_key(self) -> str:
            return "local_resnet"

        def list_available_models(self):
            return [
                {"id": "vit_best", "name": "Vision Transformer", "enabled": True},
                {"id": "local_resnet", "name": "ResNet50", "enabled": True},
            ]

    monkeypatch.setattr(mobile_spa_app, "st", fake_st)
    monkeypatch.setattr(mobile_spa_app, "load_core_adapters", lambda: (resnet_adapter, object(), object()))
    monkeypatch.setattr(mobile_spa_app, "mobile_performance_optimizer", _FakePerformanceOptimizer())
    monkeypatch.setattr(mobile_spa_app, "load_vision_model_manager", lambda: _FakeModelManager())

    app = mobile_spa_app.MobilePlantGuardApp()
    app._render_web_settings_tab()

    assert fake_st.session_state.current_vision_model == "local_resnet"
    assert not fake_st.warning_calls

    vision_call = next(call for call in fake_st.selectbox_calls if call["label"] == "Vision Model")
    assert vision_call["value"] == "local_resnet"
