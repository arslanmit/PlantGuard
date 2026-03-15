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
        self.button_calls: list[dict[str, object]] = []
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
        option_list = list(options)
        value = self.selectbox_values.get(str(label), option_list[index] if option_list else None)
        self.selectbox_calls.append(
            {
                "label": str(label),
                "options": option_list,
                "index": index,
                "value": value,
            }
        )
        return value

    def button(self, label, *args, **kwargs) -> bool:
        button_call = {"label": str(label), "disabled": bool(kwargs.get("disabled", False))}
        self.button_labels.append(str(label))
        self.button_calls.append(button_call)
        return str(label) in self.clicked_buttons and not button_call["disabled"]

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


def _build_app(monkeypatch, *, adapters=None, manager_factory=None) -> tuple[mobile_spa_app.MobilePlantGuardApp, _RecordingStreamlit]:
    fake_st = _RecordingStreamlit()
    monkeypatch.setattr(mobile_spa_app, "st", fake_st)
    monkeypatch.setattr(mobile_spa_app, "load_core_adapters", lambda *args, **kwargs: adapters or (object(), object(), object()))
    monkeypatch.setattr(mobile_spa_app, "get_model_status", lambda: {"vision": "resnet50", "audio": "whisper", "text": "gpt"})
    monkeypatch.setattr(mobile_spa_app, "mobile_performance_optimizer", _FakePerformanceOptimizer())
    if manager_factory is not None:
        monkeypatch.setattr(mobile_spa_app, "load_vision_model_manager", lambda *args, **kwargs: manager_factory())

    app = mobile_spa_app.MobilePlantGuardApp()
    return app, fake_st


def _render_main_shell(monkeypatch) -> _RecordingStreamlit:
    app, fake_st = _build_app(monkeypatch)
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


def test_app_uses_public_current_model_key_accessor_on_startup(monkeypatch) -> None:
    resnet_adapter = object()

    class _FakeModelManager:
        def __init__(self) -> None:
            self.current_adapter = resnet_adapter
            self.current_model = object()

        def get_current_model_key(self) -> str:
            return "local_resnet"

        def list_available_models(self):
            return [
                {"id": "vit_best", "name": "Vision Transformer", "enabled": True},
                {"id": "local_resnet", "name": "ResNet50", "enabled": True},
            ]

    app, fake_st = _build_app(monkeypatch, adapters=(resnet_adapter, object(), object()), manager_factory=_FakeModelManager)

    app._render_web_settings_tab()

    assert fake_st.session_state.current_vision_model == "local_resnet"
    vision_call = next(call for call in fake_st.selectbox_calls if call["label"] == "Vision Model")
    assert vision_call["value"] == "local_resnet"


def test_apply_models_persists_audio_and_text_preferences_without_mutating_adapters(monkeypatch) -> None:
    current_adapter = object()
    resnet_adapter = object()
    switch_calls: list[str] = []

    class _AudioAdapter:
        def __init__(self) -> None:
            self.model_name = "openai/whisper-tiny"

    class _TextAdapter:
        pass

    audio_adapter = _AudioAdapter()
    text_adapter = _TextAdapter()

    class _FakeModelManager:
        def __init__(self) -> None:
            self.current_adapter = current_adapter
            self.current_model = object()

        def get_current_model_key(self) -> str:
            return "vit_best"

        def list_available_models(self):
            return [
                {"id": "vit_best", "name": "Vision Transformer", "enabled": True},
                {"id": "local_resnet", "name": "ResNet50", "enabled": True},
            ]

        def switch_model_for_ui(self, model_id: str) -> bool:
            switch_calls.append(model_id)
            self.current_adapter = resnet_adapter
            return True

        def get_model_config(self, model_id: str):
            return {"description": f"Config for {model_id}"}

    app, fake_st = _build_app(
        monkeypatch,
        adapters=(current_adapter, audio_adapter, text_adapter),
        manager_factory=_FakeModelManager,
    )
    fake_st.selectbox_values = {
        "Vision Model": "local_resnet",
        "Audio Model": "openai/whisper-base",
        "Text Model": "gpt-4",
    }
    fake_st.clicked_buttons = {"Apply Models"}

    app._render_web_settings_tab()

    assert switch_calls == ["local_resnet"]
    assert app.vision_adapter is resnet_adapter
    assert fake_st.session_state.preferred_audio_model == "openai/whisper-base"
    assert fake_st.session_state.preferred_text_model == "gpt-4"
    assert audio_adapter.model_name == "openai/whisper-tiny"
    assert not hasattr(text_adapter, "model_name")


def test_failed_vision_switch_uses_selected_model_reason(monkeypatch) -> None:
    class _FakeModelManager:
        def __init__(self) -> None:
            self.current_adapter = object()
            self.current_model = object()

        def get_current_model_key(self) -> str:
            return "vit_best"

        def list_available_models(self):
            return [{"id": "vit_best", "name": "Vision Transformer", "enabled": True}]

        def switch_model_for_ui(self, model_id: str) -> bool:
            return False

        def get_model_config(self, model_id: str):
            return {"description": "Vision Transformer checkpoint is unavailable"}

    app, fake_st = _build_app(monkeypatch, manager_factory=_FakeModelManager)
    fake_st.selectbox_values = {
        "Vision Model": "vit_best",
        "Audio Model": "openai/whisper-base",
        "Text Model": "gpt-4",
    }
    fake_st.clicked_buttons = {"Apply Models"}

    app._render_web_settings_tab()

    assert fake_st.error_calls
    assert "Vision Transformer checkpoint is unavailable" in fake_st.error_calls[-1]
    assert "validated ResNet50 checkpoint" not in fake_st.error_calls[-1]


def test_settings_do_not_offer_fake_vit_when_no_vision_models_are_available(monkeypatch) -> None:
    class _FakeModelManager:
        def __init__(self) -> None:
            self.current_adapter = None
            self.current_model = None

        def get_current_model_key(self) -> str | None:
            return None

        def list_available_models(self):
            return []

    app, fake_st = _build_app(monkeypatch, manager_factory=_FakeModelManager)

    app._render_web_settings_tab()

    assert any("No vision models are currently available" in message for message in fake_st.warning_calls)
    assert not any(call["label"] == "Vision Model" for call in fake_st.selectbox_calls)
    apply_models_call = next(call for call in fake_st.button_calls if call["label"] == "Apply Models")
    assert apply_models_call["disabled"] is True
