from typing import Dict, List, Tuple


TRL_DEFINITIONS: Dict[str, str] = {
    "TRL 1": "기초 원리 관찰, 아이디어/이론 수준",
    "TRL 2": "기술 개념 정립, 적용 가능성 검토",
    "TRL 3": "개념 검증, 실험실 수준 실증",
    "TRL 4": "부품 검증, 실험실 환경 통합",
    "TRL 5": "부품 검증(실환경), 유사 환경 통합 테스트",
    "TRL 6": "시스템 시연, 실제 환경 유사 조건 시연",
    "TRL 7": "시스템 시제품, 실제 운용 환경 시연",
    "TRL 8": "시스템 완성, 양산 적합성 검증 완료",
    "TRL 9": "실제 운용, 상용 양산 및 납품",
}

PUBLIC_SIGNAL_GUIDE = {
    "TRL 1-3": [
        "논문",
        "학회 발표",
        "특허 출원",
        "기초 연구 발표",
        "기술 개념 소개",
    ],
    "TRL 4-6": [
        "프로토타입",
        "시험 평가",
        "검증",
        "샘플",
        "테스트 칩",
        "유사 환경 시연",
        "공동 개발",
    ],
    "TRL 7-9": [
        "고객사 샘플 공급",
        "양산 발표",
        "실적 공시",
        "납품",
        "상용화",
        "production",
        "qualification",
    ],
}


def infer_trl_from_evidence(text: str) -> Tuple[str, str, str]:
    """
    return:
      - trl_label
      - confidence_mode
      - justification
    confidence_mode:
      - direct
      - estimated
      - unknown
    """
    t = text.lower()

    # TRL 9
    if any(k in t for k in [
        "mass production", "high-volume manufacturing", "commercial shipment",
        "customer delivery", "in production", "양산", "납품", "상용화"
    ]):
        return (
            "TRL 9",
            "direct",
            "상용 양산·납품·실제 운용에 해당하는 공개 신호가 확인되어 TRL 9로 판단"
        )

    # TRL 8
    if any(k in t for k in [
        "qualification completed", "production qualification", "양산 적합성",
        "qualification", "system completed"
    ]):
        return (
            "TRL 8",
            "direct",
            "시스템 완성 및 양산 적합성 검증 완료 정황이 있어 TRL 8로 판단"
        )

    # TRL 7
    if any(k in t for k in [
        "prototype in real environment", "field trial", "customer sample",
        "actual operating environment", "시제품", "실제 환경 시연", "고객사 샘플"
    ]):
        return (
            "TRL 7",
            "direct",
            "실제 운용 환경 시연 또는 고객사 샘플 공급 정황이 있어 TRL 7로 판단"
        )

    # TRL 4~6은 항상 estimated
    if any(k in t for k in [
        "prototype", "pilot", "validation", "evaluation", "test chip",
        "demonstration", "integration test", "joint development",
        "검증", "시연", "유사 환경", "테스트", "통합", "평가"
    ]):
        return (
            "TRL 4-6 (추정)",
            "estimated",
            "프로토타입·검증·시연·평가 관련 공개 신호는 있으나, 수율·공정 파라미터·실성능 수치가 비공개인 경우가 많아 TRL 4~6 구간은 추정으로만 판단"
        )

    # TRL 1~3
    if any(k in t for k in [
        "paper", "conference", "patent", "research", "concept", "feasibility",
        "논문", "학회", "특허", "개념", "기초 연구", "이론"
    ]):
        return (
            "TRL 1-3",
            "direct",
            "논문·학회 발표·특허 출원 등 초기 연구 단계 공개 신호가 확인되어 TRL 1~3으로 판단"
        )

    return (
        "판단 불가",
        "unknown",
        "공개 정보만으로는 TRL을 특정할 수 있는 직접 신호가 부족하여 판단 불가"
    )


def build_trl_limitations_note() -> str:
    return (
        "본 보고서의 TRL 평가는 공개 정보 기반 추정에 의존한다. "
        "특히 TRL 4~6 구간은 수율, 공정 파라미터, 실제 성능 수치가 핵심 영업 비밀인 경우가 많아 "
        "직접 확인이 어렵다. 따라서 해당 구간은 특허 출원 패턴, 학회 발표 빈도 변화, "
        "채용 공고 키워드, 샘플 공급 언급, 테스트/검증 관련 표현 등 간접 지표를 근거로 추정하였다."
    )


def assess_threat_level(trl_label: str, evidence_count: int, has_market_signal: bool) -> str:
    if trl_label in ["TRL 8", "TRL 9"]:
        return "High"
    if trl_label == "TRL 7":
        return "High" if has_market_signal else "Medium"
    if "TRL 4-6" in trl_label:
        return "Medium" if evidence_count >= 2 else "Low"
    if trl_label == "TRL 1-3":
        return "Low"
    return "정보 부족"