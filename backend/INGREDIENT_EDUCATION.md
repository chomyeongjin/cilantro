# 성분 설명과 for 표시

2026-09-20: 공개 카탈로그 106종 / 고유 성분 키 46종에 적용.

- `products/ingredient_education.py`: 버전 관리되는 짧은 한국어 성분 설명과 출처.
- `products/presenter.py`: 모든 API 제품 응답의 `ingredientFacts`와 다이어그램에 연결.
- `detail.js`: 원 클릭 시 effects / side effects를 표시. 펼친 성분 정보에는 하위 성분을 포함한 설명·제한·출처도 표시.
- `test_ingredient_education.py`: 전체 카탈로그의 누락, 키워드 길이, 제품 원본·분류 보존 검증.

## 의미 구분

`effects`는 일반적인 영양소 역할이지 해당 제품을 먹으면 생기는 치료 효과가 아니다.
`sideEffects`는 가능한 부작용 외에 과량·약물 상호작용·안전성 검토 필요도 포함한다.
짧은 표현에서 중요한 조건(고용량, 니코틴산형, 신장질환 등)은 생략하지 않는다.
자료가 부족한 원료는 `효과 근거 제한`으로 표시하고 `educationNote`에 제한을 기록한다.
일반 안전성 페이지는 개별 원료 효능의 근거가 아니라 미검증 상태에서의 확인 필요성을 설명한다.

NIH ODS 영양소 자료, NEI, NCCIH, EFSA, MSK, Cleveland Clinic, Mayo Clinic 및 논문을 확인했다.
각 항목의 실제 URL은 `educationSources`, 검토일은 `educationReviewedAt`에 있다.
이는 의료 전문가의 임상 검토를 받았다는 표시가 아니다.

`for`는 표시 성분에 기반한 관심 대상이다. 구강용·여성용 유산균은 제품명에 명시된 용도도 구분한다.
어린이·임신·질환별 적합성을 새로 추론하지 않는다. 이전 라벨 대상은 `labelAudience`에 보존한다.

## 추천 안전성

기존 `analysis.claims`, 함량, 출처, 연령 분류와 매칭 규칙은 변경하지 않았다.
성분 교육 문구는 `claims`로 승격하지 않으며 추천 점수에 사용하지 않는다.
신규 원료는 명시적인 미검토 기본값을 사용하므로 추가할 때 출처를 확인하고 사전도 확장한다.
DB에 생성 문구를 복제하지 않으므로 사전 수정은 모든 해당 제품에 일관되게 반영된다.

## 검증

```powershell
.venv\Scripts\python.exe -X utf8 -m unittest discover -s backend -p "test_*.py"
node --test backend/test_chart.cjs
```

브라우저에서 바이오액티브 B-컴플렉스의 비오틴 팝업과 for 표시도 확인했다.
