# 핏틈

## 실행법

- Python 3.13
- `uv`가 필요합니다.
- 앱 실행:

```bash
uv run main.py
```

- Makefile을 사용할 수 있으면 다음 명령으로도 실행할 수 있습니다.

```bash
make run
```

## 구현 메모

현재 `linkup` 모듈 하위에는 `ui`만 구현되어 있습니다. 다른 모듈은 같은 위치에 추가하면 되며, 특히 UI와 외부 로직을 연결하는 부분은 `linkup/ui/port.py`를 구현하면 됩니다.
