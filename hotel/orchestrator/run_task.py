#!/usr/bin/env python3
"""Görev yürütücü — Claude'un yazdığı TASK dosyasını DeepSeek'e gönderir,
dönen kodu backend/ altına yazar, ardından review.py'yi çağırır.

Kullanım:
    python run_task.py TASK-001              # API modu (DeepSeek'e otomatik gönderir)
    python run_task.py TASK-001 --manual     # Manuel mod: prompt dosyası üretir
    python run_task.py TASK-001 --ingest     # inbox/TASK-001.md yanıtını işler
    python run_task.py TASK-001 --feedback FB-001   # düzeltme turunu gönderir

Manuel mod akışı (API erişimi olmayan ortamlar için):
    1. --manual → orchestrator/outbox/TASK-001.prompt.md üretilir
    2. Kullanıcı bu dosyayı DeepSeek'e (chat.deepseek.com) yapıştırır
    3. Yanıtı orchestrator/inbox/TASK-001.md olarak kaydeder
    4. --ingest → dosyalar backend/'e yazılır, review tetiklenir
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

HOTEL = Path(__file__).resolve().parents[1]
TASKS = HOTEL / "orchestrator" / "tasks"
FEEDBACK = HOTEL / "orchestrator" / "feedback"
INBOX = HOTEL / "orchestrator" / "inbox"
OUTBOX = HOTEL / "orchestrator" / "outbox"

SYSTEM_PROMPT = (HOTEL / "docs" / "05_DEEPSEEK_PROTOKOL.md").read_text(
    encoding="utf-8"
) if (HOTEL / "docs" / "05_DEEPSEEK_PROTOKOL.md").exists() else ""

# DeepSeek yanıtındaki "### FILE: yol" bloklarını yakalar
FILE_BLOCK = re.compile(
    r"###\s*FILE:\s*(?P<path>[^\n]+)\n+```[a-zA-Z]*\n(?P<body>.*?)```",
    re.DOTALL,
)

ALLOWED_PREFIXES = ("backend/", "docs/api/")  # DeepSeek sadece buralara yazabilir


def build_system_prompt() -> str:
    """05 protokol dokümanındaki sistem promptu bölümünü çıkarır."""
    match = re.search(r"## 6\. Sistem Promptu.*?```\n(.*?)```", SYSTEM_PROMPT, re.DOTALL)
    return match.group(1).strip() if match else (
        "Sen kıdemli bir Python backend geliştiricisisin. FastAPI + SQLAlchemy 2.0 "
        "async + PostgreSQL kullan. Her dosyayı '### FILE: <yol>' başlığı + kod "
        "bloğu ile eksiksiz üret. Açıklamalar Türkçe."
    )


def build_user_prompt(task_id: str, fb_id: str | None) -> str:
    task_file = TASKS / f"{task_id}.md"
    if not task_file.exists():
        sys.exit(f"❌ Görev bulunamadı: {task_file}")
    parts = [
        "Aşağıdaki görevi 02_DEEPSEEK_TALIMATLARI.md kurallarına göre uygula.\n",
        f"# GÖREV\n{task_file.read_text(encoding='utf-8')}",
    ]
    talimat = HOTEL / "docs" / "02_DEEPSEEK_TALIMATLARI.md"
    if talimat.exists():
        parts.append(f"\n# TEKNİK TALİMATLAR (uyulacak)\n{talimat.read_text(encoding='utf-8')}")
    if fb_id:
        fb_file = FEEDBACK / f"{fb_id}.md"
        if not fb_file.exists():
            sys.exit(f"❌ Geri bildirim bulunamadı: {fb_file}")
        parts.append(
            f"\n# DÜZELTME TALEBİ (öncelikli!)\n{fb_file.read_text(encoding='utf-8')}"
            "\nÖnce bulguyu reproduce eden test ekle, sonra düzelt."
        )
    return "\n".join(parts)


def write_files(response: str) -> list[str]:
    """Yanıttaki FILE bloklarını diske yazar; izinli yol kontrolü yapar."""
    written, rejected = [], []
    for match in FILE_BLOCK.finditer(response):
        rel = match.group("path").strip().lstrip("/")
        if not rel.startswith(ALLOWED_PREFIXES) or ".." in rel:
            rejected.append(rel)
            continue
        target = HOTEL / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(match.group("body"), encoding="utf-8")
        written.append(rel)
    if rejected:
        print(f"⚠️  İzinsiz yol reddedildi (qa/ ve dış yollar yasak): {rejected}")
    return written


def run_review(task_id: str) -> None:
    subprocess.run(
        [sys.executable, str(HOTEL / "orchestrator" / "review.py"), "--task", task_id],
        check=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="DeepSeek görev yürütücü")
    parser.add_argument("task_id", help="Örn: TASK-001")
    parser.add_argument("--manual", action="store_true", help="API yerine prompt dosyası üret")
    parser.add_argument("--ingest", action="store_true", help="inbox/ yanıtını işle")
    parser.add_argument("--feedback", help="Düzeltme turu için FB-NNN id'si")
    args = parser.parse_args()

    if args.ingest:
        inbox_file = INBOX / f"{args.task_id}.md"
        if not inbox_file.exists():
            sys.exit(f"❌ inbox yanıtı yok: {inbox_file}")
        written = write_files(inbox_file.read_text(encoding="utf-8"))
        print(f"✅ {len(written)} dosya yazıldı: {written}")
        run_review(args.task_id)
        return

    user_prompt = build_user_prompt(args.task_id, args.feedback)

    if args.manual:
        OUTBOX.mkdir(exist_ok=True)
        out = OUTBOX / f"{args.task_id}.prompt.md"
        out.write_text(
            f"# SİSTEM PROMPTU\n{build_system_prompt()}\n\n---\n\n{user_prompt}",
            encoding="utf-8",
        )
        print(f"📋 Prompt hazır: {out}")
        print("→ İçeriği DeepSeek'e yapıştırın, yanıtı şuraya kaydedin: "
              f"orchestrator/inbox/{args.task_id}.md")
        print(f"→ Sonra: python run_task.py {args.task_id} --ingest")
        return

    from deepseek_client import chat  # API modu — bağlantı gerektirir
    print(f"🚀 {args.task_id} DeepSeek'e gönderiliyor...")
    response = chat(build_system_prompt(), user_prompt)
    INBOX.mkdir(exist_ok=True)
    (INBOX / f"{args.task_id}.md").write_text(response, encoding="utf-8")
    written = write_files(response)
    print(f"✅ {len(written)} dosya yazıldı: {written}")
    run_review(args.task_id)


if __name__ == "__main__":
    main()
