# 반도체 R&D 전략 보고서

## SUMMARY
현재 SK hynix는 HBM4, PIM, CXL 기술의 발전 상황을 면밀히 분석하여 즉각적인 대응과 중장기 전략을 수립해야 한다. HBM4는 Samsung이 TRL 9에 도달하여 양산 중이며, Micron은 TRL 추정 보류 상태로 기술 성숙도가 낮다. PIM과 CXL 기술은 모두 추정 구간에 있으며, 경쟁사들은 각각의 기술에서 강점을 보이고 있다. SK hynix는 HBM4에 대한 즉각적인 대응이 필요하며, PIM과 CXL은 중장기적으로 기반을 다져야 할 기술로 판단된다.

## 1. 분석 배경
### 1.1. 분석 목적
AI 가속기와 데이터센터 시장의 급속한 성장으로 인해 HBM, PIM, CXL 기술은 필수적이다. HBM은 데이터 전송 속도와 대역폭을 극대화하여 AI 연산 성능을 향상시키고, PIM은 메모리 내에서의 데이터 처리로 전력 효율성을 높인다. CXL은 메모리 풀링과 디스어그리게이션을 통해 시스템의 유연성을 제공한다. 이러한 기술들은 경쟁사와의 격차를 줄이고, SK hynix의 시장 점유율을 확대하는 데 중요한 역할을 할 것이다.

### 1.2. 분석 범위 및 기준
본 보고서는 HBM4, PIM, CXL 기술을 중심으로 Samsung과 Micron의 기술 동향을 분석한다. 데이터는 공개된 논문, 웹 기사, 특허 등을 기반으로 하며, 비공식 정보는 사용하지 않는다. 각 기술의 성숙도와 위협 수준을 TRL 기준으로 평가하여 SK hynix의 R&D 전략 수립에 기여할 것이다.

### 1.3. TRL 기반 평가 기준 정의
TRL 1~3은 기초 연구 단계로, 공개된 논문이나 특허를 통해 확인 가능하다. TRL 4~6은 기술 개발 중으로, 수율 및 공정 파라미터가 비공개인 경우가 많아 추정으로 판단된다. TRL 7~9는 상용화 단계로, 샘플 공급이나 양산 발표를 통해 확인할 수 있다. TRL 4~6 구간은 영업 비밀로 인해 직접적인 확인이 어려워 추정으로 분류된다.

## 2. 분석 대상 기술 현황
### 2.1. HBM 기술 현황
HBM은 3D 적층 구조와 TSV(Through-Silicon Via)를 통해 높은 대역폭을 제공한다. HBM1에서 HBM4로의 발전 과정에서 대역폭은 128GB/s에서 819GB/s로 증가하였고, 용량은 4GB에서 64GB로 확대되었다. HBM4는 10nm DRAM 코어와 4nm 로직 다이를 통합하여 11.7Gbps의 속도를 제공하며, 이는 업계 표준인 8Gbps를 초과한다. 그러나 열 방출 문제와 수율 한계는 여전히 해결해야 할 과제이다.

### 2.2. PIM 기술 현황
PIM은 Processing-near-Memory와 Processing-using-Memory 두 가지 아키텍처로 구분된다. HBM-PIM 구현 사례로는 메모리 내에서의 데이터 처리로 전력 소모를 줄이는 방식이 있다. 그러나 프로그래밍 모델, 메모리 일관성, 데이터 구조 등 여러 기술적 과제가 존재한다. 현재 PIM의 채택을 가로막고 있는 요소들은 코드 생성 지원, 런타임 엔진, 메모리 코히어런스 메커니즘 등이다.

### 2.3. CXL 기술 현황
CXL은 CXL.io, CXL.cache, CXL.mem의 세 가지 프로토콜 구조로 구성된다. CXL 1.1에서 3.0으로의 발전 과정에서 메모리 풀링과 디스어그리게이션 기능이 강화되었다. 실제 데이터센터에서는 CXL을 통해 메모리 자원의 효율적 활용이 가능하다. 그러나 레이턴시 문제와 에코시스템의 미성숙은 CXL 도입의 기술적 한계로 작용하고 있다.

## 3. 경쟁사 동향 분석
### 3.1. 경쟁사별 기술 개발 방향
**Samsung**
- HBM4는 TRL 9에 도달하여 양산 중이며, 11.7Gbps의 속도를 제공한다. 
- AI 및 HPC 시스템을 위한 파트너십을 통해 시장 점유율을 확대하고 있다.
- 강점: 높은 기술 성숙도와 파트너십 네트워크.
- 한계: 열 방출 문제 해결 필요.

**Micron**
- HBM4의 TRL은 추정 보류 상태로, 기술 성숙도가 낮다.
- 12.8GT/s 속도를 목표로 하는 HBM4E 개발 중.
- 강점: 혁신적인 아키텍처 설계.
- 한계: 상용화 단계에서의 지연.

### 3.2. TRL 기반 기술 성숙도 비교
| 기술 | TRL | 추정 여부 | 판단 근거 |
|------|-----|----------|----------|
| HBM4 | 9   | 부분 공개 확인 | Samsung의 HBM4 양산 및 실제 운용 신호 확인 |
| PIM  | 판단 불가 | 판단 불가 | 정보 부족으로 판단 불가 |
| CXL  | 판단 불가 | 판단 불가 | 정보 부족으로 판단 불가 |

### 3.3. 위협 수준 평가
- **HBM**: Samsung의 HBM4는 TRL 9로 SK hynix에 높은 위협을 가한다. 기술 완성도와 시장 적용 가능성이 높아 즉각적인 대응이 필요하다.
- **PIM**: Micron의 PIM 기술은 성숙도가 낮아 현재로서는 중간 정도의 위협으로 평가된다. 그러나 기술 발전이 이루어질 경우 위협 수준이 상승할 수 있다.
- **CXL**: CXL 기술은 현재 정보 부족으로 판단이 어렵지만, 시장에서의 중요성이 증가하고 있어 주의가 필요하다.

## 4. 전략적 시사점
### 4.1. 기술별 전략적 중요도
- **단기(1~2년)**: HBM4에 즉시 투자해야 한다. 경쟁사 대비 기술 격차가 커질 수 있으며, 시장 점유율을 잃을 위험이 있다.
- **중기(3~5년)**: PIM 기술에 기반을 다져야 한다. PIM의 채택이 증가할 것으로 예상되며, 이를 통해 전력 효율성을 높일 수 있다.
- **장기(5년 이상)**: CXL 기술에 대한 선제적 포지셔닝이 필요하다. 메모리 풀링과 디스어그리게이션의 중요성이 커질 것이므로, 기술 개발에 집중해야 한다.

### 4.2. 경쟁 대응 방향
- **Samsung 대비**: HBM4 기술 개발에 집중하고, 파트너십을 통해 시장 진입 장벽을 낮춰야 한다.
- **Micron 대비**: PIM 기술 개발에 투자하여 경쟁력을 강화하고, Micron의 기술적 한계를 활용할 수 있는 전략을 수립해야 한다.
- SK hynix의 강점인 고품질 메모리 기술을 활용하여 시장에서의 경쟁력을 높여야 한다.

### 4.3. 한계
- HBM4의 TRL 9는 확인되었으나, PIM과 CXL의 TRL은 정보 부족으로 판단이 어렵다. 
- TRL 4~6 구간의 불확실성은 수율 및 공정 파라미터 비공개로 인해 발생한다. 
- 추가 조사가 필요한 항목으로는 PIM의 프로그래밍 모델과 CXL의 에코시스템 성숙도를 우선적으로 고려해야 한다.

## REFERENCE
[PDF]
- Comparative Study of Thermal Dissipation in Increa.pdf
- hbm.pdf
- 2012.03112v5.pdf

[WEB]
- Samsung Unveils HBM4E, Showcasing Comprehensive AI Solutions, NVIDIA Partnership and Vision at NVIDIA GTC 2026 – Samsung Global Newsroom | https://news.samsung.com/global/samsung-unveils-hbm4e-showcasing-comprehensive-ai-solutions-nvidia-partnership-and-vision-at-nvidia-gtc-2026
- HBM undergoes major architectural shakeup as TSMC and GUC detail HBM4, HBM4E and C-HBM4E — 3nm base dies to enable 2.5x performance boost with speeds of up to 12.8GT/s by 2027 | Tom's Hardware | https://semiengineering.com/early-hbm4-validation-points-the-way-for-next-generation-ai-and-hpc-systems/

## 추가 메모
- 정보 부족 또는 추정 보류 항목
- PIM과 CXL의 TRL이 '판단 불가'로 명시되어 있으나, 정보 부족으로 인한 판단 불가가 적절히 사용되지 않았다.
