# 핏틈

## 실행법

- Python 3.13
- `uv`가 필요합니다.

### 초기화

```bash
make init
```

### 앱 실행

```bash
make run
```

### 개발 명령

```bash
make fix      # ruff 자동 수정 및 포맷 적용
make check    # 포맷 검사, 린트, 테스트 실행
make lint     # ruff lint 자동 수정
make format   # ruff format 실행
make test     # unittest 실행
```

## 구현 메모

현재 `linkup` 모듈 하위에 다룬 모듈을 추가하면 되며, 특히 UI와 외부 로직을 연결하는 부분은 `linkup/ui/port.py`를 구현하면 됩니다.
