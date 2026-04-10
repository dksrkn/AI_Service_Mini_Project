# 반도체 R&D 전략 보고서

## SUMMARY
- HBM, PIM, CXL 기술의 현재 위치를 분석하고, 경쟁사인 Samsung과 Micron의 기술 성숙도(TRL) 및 위협 수준을 비교하였다.
- SK hynix의 R&D 담당자가 의사결정에 활용할 수 있는 전략적 시사점을 제시하였다.

## 1. 분석 배경
### 1.1. 분석 목적
- HBM, PIM, CXL 기술은 AI 및 데이터 센터의 발전에 따라 중요성이 증가하고 있으며, 이들 기술의 성숙도와 시장 동향을 분석하는 것이 필요하다.
- 특히, HBM 기술은 메모리 대역폭의 한계를 극복하는 데 중요한 역할을 하고 있으며, PIM과 CXL은 데이터 처리 효율성을 높이는 데 기여할 수 있다.

### 1.2. 분석 범위 및 기준
- 분석 대상 기술: HBM, PIM, CXL
- 경쟁사: Samsung, Micron
- 활용 데이터: 공개 정보만 사용

### 1.3. TRL 기반 평가 기준 정의
- TRL 9단계는 상용 양산 및 실제 운용에 해당하는 기술을 의미한다.
- TRL 4~6 구간은 공개 정보 기반으로 "추정"으로 명시한다.

## 2. 분석 대상 기술 현황
### 2.1. HBM 기술 현황
- HBM(High Bandwidth Memory)은 높은 대역폭과 낮은 지연 시간을 제공하는 메모리 기술로, AI 및 고성능 컴퓨팅에 필수적이다.
- 현재 SK hynix는 HBM4 기술을 개발 중이며, 10 GT/s의 데이터 전송 속도와 2.8 TB/s의 대역폭을 제공한다. 이는 JEDEC 사양을 25% 초과하는 성능이다.

### 2.2. PIM 기술 현황
- PIM(Process-In-Memory) 기술은 메모리 내에서 데이터 처리를 수행하여 데이터 전송 지연을 줄이는 기술이다.
- 현재 PIM 기술의 성숙도에 대한 정보가 부족하여 구체적인 TRL을 판단하기 어렵다. 정보 부족으로 판단 불가.

### 2.3. CXL 기술 현황
- CXL(Compute Express Link)은 CPU와 메모리 간의 고속 인터페이스를 제공하여 데이터 전송 속도를 높이는 기술이다.
- CXL의 현재 개발 단계에 대한 정보가 부족하여 TRL을 판단하기 어렵다. 정보 부족으로 판단 불가.

## 3. 경쟁사 동향 분석
### 3.1. 경쟁사별 기술 개발 방향
- **Samsung**: HBM4 및 HBM4E 기술을 개발 중이며, HBM4E는 4.0 TB/s의 대역폭을 목표로 하고 있다. 삼성은 HBM4의 양산을 시작했으며, NVIDIA와의 협력을 통해 시장 점유율을 확대하고 있다.
- **Micron**: HBM4의 양산을 시작하였으며, 11 Gb/s의 핀 속도와 2.8 TB/s의 대역폭을 제공한다. Micron은 NVIDIA와의 협력을 통해 HBM 시장 점유율을 증가시키고 있다.

### 3.2. TRL 기반 기술 성숙도 비교

| 기술 | 기업   | TRL | 추정 여부 | 판단 근거 |
|------|--------|-----|----------|----------|
| HBM4 | SK hynix | 9   | -        | 상용 양산 및 납품 신호 확인 |
| HBM4 | Samsung  | 9   | -        | 상용 양산 및 납품 신호 확인 |
| HBM4 | Micron   | 판단 불가 | 정보 부족으로 판단 불가 | 공개 정보 부족 |
| PIM  | SK hynix | 추정 보류 | 정보 부족으로 판단 불가 | 공개 정보 부족 |
| CXL  | SK hynix | 추정 보류 | 정보 부족으로 판단 불가 | 공개 정보 부족 |

### 3.3. 위협 수준 평가
- **Samsung**: HBM4 및 HBM4E의 기술 완성도가 높고, NVIDIA와의 협력으로 시장에서의 위협 수준은 High로 평가된다.
- **Micron**: HBM4의 양산을 시작하였으나, TRL 정보 부족으로 인해 위협 수준은 Medium으로 평가된다.

## 4. 전략적 시사점
### 4.1. 기술별 전략적 중요도
- HBM 기술에 집중할 필요가 있으며, 특히 HBM4의 성능 개선과 양산을 통해 시장 점유율을 확대해야 한다.

### 4.2. 경쟁 대응 방향
- Samsung과 Micron의 HBM 기술에 대한 대응 전략으로는, SK hynix의 HBM4 기술을 지속적으로 개선하고, 고객과의 협력을 강화하여 시장 점유율을 유지하는 것이 필요하다.

### 4.3. 한계
- 공개 정보 기반 분석의 한계로 인해 TRL 4~6 구간의 추정이 어려운 점을 인지해야 한다.
- PIM 및 CXL 기술에 대한 추가 조사와 정보 수집이 필요하다.

## REFERENCE
[PDF]
- Comparative Study of Thermal Dissipation in Increa.pdf
- hbm.pdf

[WEB]
- https://introl.com/blog/hbm-evolution-hbm3-hbm3e-hbm4-memory-ai-gpu-2025
- https://www.linkedin.com/posts/markdhirsch_ai-semiconductors-hbm-activity-7439680623948046337-oEts
- https://www.digitimes.com/news/a20260318VL208/sk-hynix-hbm4-demand-hbm-production.html
- https://investors.micron.com/news-releases/news-release-details/micron-high-volume-production-hbm4-designed-nvidia-vera-rubin
- https://globalxetfs.com.br/memory-is-the-new-bottleneck-in-ai-semiconductors/
- https://finance.biggo.com/news/202603190622_Samsung_HBM4_Production_Target_and_Tech_Roadmap
- https://www.trendforce.com/news/2026/03/03/news-samsung-reportedly-targets-hbm4e-power-bottleneck-with-structural-overhaul-slashes-defects-97/