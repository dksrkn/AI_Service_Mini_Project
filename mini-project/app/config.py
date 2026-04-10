from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DOCS_DIR = DATA_DIR / "raw_docs"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"
OUTPUT_DIR = BASE_DIR / "outputs"
REPORT_DIR = OUTPUT_DIR / "reports"
LOG_DIR = OUTPUT_DIR / "logs"

for p in [DATA_DIR, RAW_DOCS_DIR, VECTORSTORE_DIR, OUTPUT_DIR, REPORT_DIR, LOG_DIR]:
    p.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "intfloat/multilingual-e5-large"
)

MAX_LOOP_A_RETRIES = 2
MAX_LOOP_B_RETRIES = 2

COMPETITORS = ["Samsung", "Micron"]
TARGET_TECHS = ["HBM4", "PIM", "CXL"]

REPORT_TEMPLATE_SECTIONS = [
    "SUMMARY",
    "1. 분석 배경",
    "1.1. 분석 목적",
    "1.2. 분석 범위 및 기준",
    "1.3. TRL 기반 평가 기준 정의",
    "2. 분석 대상 기술 현황",
    "2.1. HBM 기술 현황",
    "2.2. PIM 기술 현황",
    "2.3. CXL 기술 현황",
    "3. 경쟁사 동향 분석",
    "3.1. 경쟁사별 기술 개발 방향",
    "3.2. TRL 기반 기술 성숙도 비교",
    "3.3. 위협 수준 평가",
    "4. 전략적 시사점",
    "4.1. 기술별 전략적 중요도",
    "4.2. 경쟁 대응 방향",
    "4.3. 한계",
    "REFERENCE",
]