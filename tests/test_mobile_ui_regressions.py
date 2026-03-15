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
        self.button_labels: list[str] = []

    def markdown(self, body, *args, **kwargs) -> None:
        self.markdown_calls.append(str(body))

    def columns(self, spec):
        count = spec if isinstance(spec, int) else len(spec)
        return [_FakeContext() for _ in range(count)]

    def tabs(self, names):
        return [_FakeContext() for _ in names]

    def selectbox(self, label, options, index=0, **kwargs):
        return options[index]

    def button(self, label, *args, **kwargs) -> bool:
        self.button_labels.append(str(label))
        return False

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


def test_developer_surfaces_are_absent_from_main_shell(monkeypatch) -> None:
    fake_st = _render_main_shell(monkeypatch)

    all_text = "\n".join(
        fake_st.markdown_calls
        + fake_st.info_calls
        + fake_st.success_calls
        + fake_st.error_calls
        + fake_st.warning_calls
        + fake_st.expander_labels
        + fake_st.button_labels
    )

    assert "Model Status" not in all_text
    assert "Quick Test" not in all_text
    assert "Run Model Tests" not in all_text
    assert "Component Status" not in all_text
    assert "App Info" not in all_text


def test_mobile_components_section_is_removed(monkeypatch) -> None:
    fake_st = _render_main_shell(monkeypatch)

    all_text = "\n".join(fake_st.markdown_calls + fake_st.info_calls + fake_st.button_labels)

    assert "Mobile Components" not in all_text
