#!/usr/bin/env python3
"""Denetim raporu üretici — DeepSeek teslimatını kontrol eder.

Claude'un kontrol noktası: her teslimat sonrası çalışır,
docs/reviews/REVIEW-{tarih}-{task}.md raporu üretir.

Kontroller:
  1. Kontrat testleri  (pytest qa/contract — Claude'un bağımsız testleri)
  2. Backend testleri  (pytest backend/tests — DeepSeek'in kendi testleri)
  3. Zorunlu model alanları statik taraması (UUID id, timestamps, soft delete)
  4. Hata formatı + audit log statik taraması
  5. qa/ dokunulmazlığı (git diff kontrolü)

Kullanım:
    python review.py --task TASK-001
    python review.py --task TASK-001 --dry-run   # testleri koşmadan rapor iskeleti
"""
import argparse
import datetime
import re
import subprocess
from pathlib import Path

HOTEL = Path(__file__).resolve().parents[1]
BACKEND = HOTEL / "backend"
QA = HOTEL / "qa"
REVIEWS = HOTEL / "docs" / "reviews"

REQUIRED_MODEL_FIELDS = ["id", "created_at", "updated_at", "deleted_at"]


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd, cwd=cwd or HOTEL, capture_output=True, text=True, timeout=600
        )
        return proc.returncode, (proc.stdout + proc.stderr)[-4000:]
    except FileNotFoundError as exc:
        return 127, str(exc)
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def python_bin() -> str:
    """Backend venv'i varsa onu tercih et (sistem paketi çakışmalarına karşı)."""
    venv_python = BACKEND / ".venv" / "bin" / "python"
    return str(venv_python) if venv_python.exists() else "python3"


def check_pytest(path: Path, label: str) -> dict:
    if not path.exists() or not any(path.rglob("test_*.py")):
        return {"label": label, "status": "SKIP", "detail": f"{path.relative_to(HOTEL)} altında test yok"}
    cwd = BACKEND if path.is_relative_to(BACKEND) else HOTEL
    code, out = run([python_bin(), "-m", "pytest", str(path), "-q", "--no-header"], cwd=cwd)
    status = "PASS" if code == 0 else "FAIL"
    return {"label": label, "status": status, "detail": out.strip()[-1500:]}


def check_model_fields() -> dict:
    """SQLAlchemy modellerinde zorunlu alanları statik tarar."""
    models_dir = BACKEND / "app" / "models"
    if not models_dir.exists():
        return {"label": "Model alanları", "status": "SKIP", "detail": "backend/app/models yok"}
    issues = []
    for py in models_dir.glob("*.py"):
        text = py.read_text(encoding="utf-8")
        # Sadece tablo tanımlayan dosyalara bak
        if "__tablename__" not in text:
            continue
        # Kabul edilmiş istisna: append-only tablolar (örn. audit_logs, FB-001)
        # dosyada "append-only" işareti varsa updated/deleted alanları aranmaz.
        if "append-only" in text:
            continue
        # BaseModel'den türeyen modeller ortak alanları miras alır
        if "(BaseModel)" in text and "from app.models.base import BaseModel" in text:
            continue
        missing = [f for f in REQUIRED_MODEL_FIELDS if f not in text]
        if missing:
            issues.append(f"{py.name}: eksik alanlar {missing}")
    if issues:
        return {"label": "Model alanları", "status": "FAIL", "detail": "\n".join(issues)}
    return {"label": "Model alanları", "status": "PASS", "detail": "UUID/timestamps/soft-delete mevcut"}


def check_error_format() -> dict:
    """Hata yanıtlarının {error:{code,message}} zarfını kullandığını tarar."""
    app_dir = BACKEND / "app"
    if not app_dir.exists():
        return {"label": "Hata formatı", "status": "SKIP", "detail": "backend/app yok"}
    text = "\n".join(p.read_text(encoding="utf-8") for p in app_dir.rglob("*.py"))
    if re.search(r'["\']error["\']\s*:', text) or "exception_handler" in text:
        return {"label": "Hata formatı", "status": "PASS", "detail": "error zarfı/handler bulundu"}
    return {"label": "Hata formatı", "status": "WARN", "detail": "error zarfı izine rastlanmadı — elle kontrol et"}


def check_audit_log() -> dict:
    app_dir = BACKEND / "app"
    if not app_dir.exists():
        return {"label": "Audit log", "status": "SKIP", "detail": "backend/app yok"}
    text = "\n".join(p.read_text(encoding="utf-8") for p in app_dir.rglob("*.py"))
    if "audit_log" in text or "AuditLog" in text:
        return {"label": "Audit log", "status": "PASS", "detail": "audit_log referansı bulundu"}
    return {"label": "Audit log", "status": "FAIL", "detail": "audit_log entegrasyonu bulunamadı"}


def check_qa_untouched() -> dict:
    """qa/ klasörüne DeepSeek teslimatında dokunulmadığını doğrular."""
    code, out = run(["git", "status", "--porcelain", str(QA)])
    if code != 0:
        return {"label": "qa/ dokunulmazlığı", "status": "SKIP", "detail": out}
    # Claude'un kendi commit'leri hariç; uncommitted qa değişikliği teslimatla
    # aynı anda geldiyse şüphelidir — raporda işaretle, karar Claude'un.
    if out.strip():
        return {"label": "qa/ dokunulmazlığı", "status": "WARN",
                "detail": f"qa/ altında commit'lenmemiş değişiklik var:\n{out}"}
    return {"label": "qa/ dokunulmazlığı", "status": "PASS", "detail": "temiz"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default="GENEL")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    checks = []
    if args.dry_run:
        checks.append({"label": "Dry-run", "status": "SKIP", "detail": "testler koşulmadı"})
    else:
        checks.append(check_pytest(QA / "contract", "Kontrat testleri (Claude)"))
        checks.append(check_pytest(BACKEND / "tests", "Backend testleri (DeepSeek)"))
    checks.append(check_model_fields())
    checks.append(check_error_format())
    checks.append(check_audit_log())
    checks.append(check_qa_untouched())

    failed = [c for c in checks if c["status"] == "FAIL"]
    verdict = "KABUL ✅" if not failed else "DÜZELTME GEREKLİ ❌"

    today = datetime.date.today().isoformat()
    REVIEWS.mkdir(parents=True, exist_ok=True)
    report = REVIEWS / f"REVIEW-{today}-{args.task}.md"

    lines = [
        f"# Denetim Raporu — {args.task}",
        f"- Tarih: {today}",
        f"- Sonuç: **{verdict}**",
        "",
        "| Kontrol | Durum |",
        "|---|---|",
    ]
    for c in checks:
        lines.append(f"| {c['label']} | {c['status']} |")
    lines.append("\n## Detaylar\n")
    for c in checks:
        lines.append(f"### {c['label']} — {c['status']}\n```\n{c['detail']}\n```\n")
    if failed:
        lines.append("## Sonraki Adım\n")
        lines.append("Claude `orchestrator/feedback/FB-NNN.md` yazacak; bulgular yukarıda.")
    report.write_text("\n".join(lines), encoding="utf-8")

    print(f"📄 Rapor: {report.relative_to(HOTEL)}")
    print(f"Sonuç: {verdict}")
    for c in checks:
        print(f"  [{c['status']:4}] {c['label']}")


if __name__ == "__main__":
    main()
