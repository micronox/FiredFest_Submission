from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "var" / "project_pdf"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LOGO = Path(r"C:\Users\zionk\OneDrive\Desktop\Gauntlet\CCat_Logo_PNG.png")
PDF_OUT = ROOT / "CCat_Leash_Harness_Project_PDF.pdf"

W, H = 1700, 2200
M = 130

INK = "#111111"
MUTED = "#5D5A55"
SUBTLE = "#F4EFE7"
PAPER = "#FBF8F2"
CARD = "#FFFFFF"
LINE = "#D9D0C3"
ORANGE = "#F26A2E"
GOLD = "#C58B32"
DARK = "#171412"
GREEN = "#2F8F62"

FONT_DIR = Path(r"C:\Windows\Fonts")


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    for candidate in [
        FONT_DIR / name,
        FONT_DIR / name.lower(),
        FONT_DIR / "segoeui.ttf",
        FONT_DIR / "arial.ttf",
    ]:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


F = {
    "display": font("bahnschrift.ttf", 92),
    "display_sm": font("bahnschrift.ttf", 62),
    "h1": font("segoeuib.ttf", 56),
    "h2": font("segoeuib.ttf", 38),
    "h3": font("segoeuib.ttf", 28),
    "body": font("segoeui.ttf", 25),
    "body_b": font("segoeuib.ttf", 25),
    "small": font("segoeui.ttf", 20),
    "small_b": font("segoeuib.ttf", 20),
    "micro": font("segoeui.ttf", 17),
    "mono": font("consola.ttf", 18),
    "mono_b": font("consolab.ttf", 18),
}


@dataclass
class Page:
    image: Image.Image
    draw: ImageDraw.ImageDraw


def new_page(bg: str = PAPER) -> Page:
    img = Image.new("RGB", (W, H), bg)
    return Page(img, ImageDraw.Draw(img))


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_w: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        words = para.split()
        line = ""
        for word in words:
            test = f"{line} {word}".strip()
            if text_size(draw, test, fnt)[0] <= max_w:
                line = test
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


def draw_paragraph(
    p: Page,
    xy: tuple[int, int],
    text: str,
    max_w: int,
    fnt=None,
    fill: str = INK,
    leading: int = 34,
) -> int:
    fnt = fnt or F["body"]
    x, y = xy
    for line in wrap(p.draw, text, fnt, max_w):
        if line:
            p.draw.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y


def title(p: Page, text: str, kicker: str | None = None) -> int:
    y = 92
    if kicker:
        p.draw.text((M, y), kicker.upper(), font=F["small_b"], fill=ORANGE)
        y += 42
    p.draw.text((M, y), text, font=F["h1"], fill=INK)
    y += 72
    p.draw.line((M, y, W - M, y), fill=LINE, width=3)
    return y + 48


def footer(p: Page, n: int, label: str = "CCat Leash Harness") -> None:
    y = H - 88
    p.draw.line((M, y, W - M, y), fill=LINE, width=2)
    p.draw.text((M, y + 24), label, font=F["micro"], fill=MUTED)
    num = f"{n:02d}"
    tw, _ = text_size(p.draw, num, F["micro"])
    p.draw.text((W - M - tw, y + 24), num, font=F["micro"], fill=MUTED)


def rounded(p: Page, box, fill=CARD, outline=LINE, radius=34, width=2) -> None:
    p.draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def card_title(p: Page, x: int, y: int, label: str, accent: str = ORANGE) -> int:
    p.draw.rounded_rectangle((x, y + 4, x + 13, y + 42), radius=6, fill=accent)
    p.draw.text((x + 28, y), label, font=F["h3"], fill=INK)
    return y + 50


def stat_card(p: Page, box, value: str, label: str, note: str, accent=ORANGE):
    rounded(p, box, fill=CARD, outline="#E8DED1", radius=30)
    x1, y1, x2, _ = box
    p.draw.text((x1 + 34, y1 + 32), value, font=F["display_sm"], fill=accent)
    p.draw.text((x1 + 38, y1 + 108), label, font=F["body_b"], fill=INK)
    draw_paragraph(p, (x1 + 38, y1 + 148), note, x2 - x1 - 76, F["small"], MUTED, 28)


def bullet_list(
    p: Page,
    x: int,
    y: int,
    items: list[str],
    max_w: int,
    accent=ORANGE,
    text_fill: str = INK,
) -> int:
    for item in items:
        p.draw.ellipse((x, y + 8, x + 12, y + 20), fill=accent)
        y = draw_paragraph(p, (x + 30, y), item, max_w - 30, F["small"], text_fill, 29) + 8
    return y


def draw_logo(p: Page, box: tuple[int, int, int, int], opacity: int = 255) -> None:
    logo = Image.open(LOGO).convert("RGBA")
    logo.thumbnail((box[2] - box[0], box[3] - box[1]), Image.Resampling.LANCZOS)
    if opacity < 255:
        alpha = logo.getchannel("A").point(lambda a: int(a * opacity / 255))
        logo.putalpha(alpha)
    x = box[0] + (box[2] - box[0] - logo.width) // 2
    y = box[1] + (box[3] - box[1] - logo.height) // 2
    p.image.paste(logo, (x, y), logo)


def draw_table(
    p: Page,
    x: int,
    y: int,
    widths: list[int],
    headers: list[str],
    rows: list[list[str]],
    row_h: int = 60,
    header_fill: str = DARK,
    small: bool = False,
) -> int:
    f_body = F["micro"] if small else F["small"]
    f_head = F["small_b"]
    total_w = sum(widths)
    p.draw.rounded_rectangle((x, y, x + total_w, y + row_h), radius=18, fill=header_fill)
    cx = x
    for i, h in enumerate(headers):
        p.draw.text((cx + 16, y + 16), h, font=f_head, fill="#FFFFFF")
        cx += widths[i]
    y += row_h
    for r, row in enumerate(rows):
        fill = "#FFFFFF" if r % 2 == 0 else "#FBF6EE"
        p.draw.rectangle((x, y, x + total_w, y + row_h), fill=fill, outline=LINE)
        cx = x
        max_lines = 1
        cell_lines: list[list[str]] = []
        for i, cell in enumerate(row):
            lines = wrap(p.draw, cell, f_body, widths[i] - 28)
            cell_lines.append(lines[:3])
            max_lines = max(max_lines, min(len(lines), 3))
        actual_h = max(row_h, 30 + max_lines * (24 if small else 28))
        p.draw.rectangle((x, y, x + total_w, y + actual_h), fill=fill, outline=LINE)
        for i, lines in enumerate(cell_lines):
            ty = y + 16
            for line in lines:
                p.draw.text((cx + 14, ty), line, font=f_body, fill=INK)
                ty += 24 if small else 28
            cx += widths[i]
            p.draw.line((cx, y, cx, y + actual_h), fill=LINE, width=1)
        y += actual_h
    return y + 22


def draw_flow(p: Page, x: int, y: int, labels: list[tuple[str, str]], w: int = 250) -> None:
    for i, (head, body) in enumerate(labels):
        bx = x + i * (w + 42)
        rounded(p, (bx, y, bx + w, y + 210), fill="#FFFFFF", outline="#E9DDCE", radius=30)
        p.draw.text((bx + 24, y + 24), head, font=F["body_b"], fill=INK)
        draw_paragraph(p, (bx + 24, y + 68), body, w - 48, F["small"], MUTED, 27)
        if i < len(labels) - 1:
            ax = bx + w + 14
            ay = y + 100
            p.draw.line((ax, ay, ax + 30, ay), fill=ORANGE, width=5)
            p.draw.polygon([(ax + 30, ay), (ax + 18, ay - 10), (ax + 18, ay + 10)], fill=ORANGE)


def page_cover() -> Page:
    p = new_page(PAPER)
    p.draw.rectangle((0, 0, W, 260), fill="#F0E7DA")
    p.draw.rectangle((0, H - 280, W, H), fill=DARK)
    p.draw_logo = None
    draw_logo(p, (M, 120, W - M, 560))
    p.draw.text((M, 700), "CCat Leash Harness", font=F["display"], fill=INK)
    p.draw.text((M, 812), "Project PDF", font=F["display_sm"], fill=ORANGE)
    y = draw_paragraph(
        p,
        (M, 925),
        "A production-ready CCAT practice platform with a full Next.js/Postgres web application, timed quiz workflow, analytics, and a governed AI question-generation lab.",
        W - 2 * M,
        F["h2"],
        INK,
        50,
    )
    y += 58
    for label, value in [
        ("Live web app", "https://quizcat-web-production.up.railway.app"),
        ("Repository", "https://github.com/micronox/FiredFest_Submission"),
        ("Builder", "Larry Vallely / Blace Houle"),
        ("Submission", "Fired Festival"),
    ]:
        p.draw.text((M, y), label.upper(), font=F["micro"], fill=ORANGE)
        p.draw.text((M + 240, y - 6), value, font=F["small_b"], fill=INK)
        y += 50
    p.draw.text((M, H - 210), "If I Fits, I Harness Sits", font=F["h2"], fill="#FFFFFF")
    p.draw.text((M, H - 150), "A beautiful little engine for disciplined practice, measurable progress, and safe question generation.", font=F["small"], fill="#D8CEC1")
    return p


def page_snapshot() -> Page:
    p = new_page()
    y = title(p, "Project Snapshot", "01 / executive overview")
    draw_paragraph(
        p,
        (M, y),
        "CCat Leash Harness converts a terminal-first CCAT trainer into a deployed browser application. It preserves a carefully structured 400-question seed bank, adds persistent attempts and statistics, and introduces Question Lab: an AI generation workflow that never writes directly to production data without deterministic review.",
        W - 2 * M,
        F["body"],
        INK,
        36,
    )
    y += 190
    gap = 30
    sw = (W - 2 * M - 3 * gap) // 4
    stat_card(p, (M, y, M + sw, y + 250), "400", "Seed questions", "Imported from eight CCAT-style sample exams.", ORANGE)
    stat_card(p, (M + (sw + gap), y, M + 2 * sw + gap, y + 250), "1,952", "Choices", "Preserved labels, order, answer key, and explanations.", GOLD)
    stat_card(p, (M + 2 * (sw + gap), y, M + 3 * sw + 2 * gap, y + 250), "8", "Base tests", "Fifty-question exam forms with 15-minute timers.", GREEN)
    stat_card(p, (M + 3 * (sw + gap), y, M + 4 * sw + 3 * gap, y + 250), "6", "Core tables", "Questions, choices, tests, mappings, attempts, answers.", ORANGE)
    y += 330
    rounded(p, (M, y, W - M, y + 500), fill="#171412", outline="#171412", radius=40)
    p.draw.text((M + 44, y + 44), "What the product does", font=F["h2"], fill="#FFFFFF")
    bullet_list(
        p,
        M + 54,
        y + 115,
        [
            "Lets users launch full source exams or create generated practice tests from the validated bank.",
            "Runs timed quizzes with answer persistence, immediate correctness checks, explanations, and finish states.",
            "Tracks completed attempts for a stats screen that makes progress visible after every run.",
            "Provides an LLM-powered Question Lab gated by schema validation, similarity checks, safety checks, and deterministic arithmetic verification.",
        ],
        W - 2 * M - 108,
        ORANGE,
        "#EFE7DD",
    )
    y += 570
    rounded(p, (M, y, W - M, y + 315), fill="#FFF7EC", outline="#E7D6C0", radius=34)
    card_title(p, M + 40, y + 38, "Design thesis")
    draw_paragraph(
        p,
        (M + 40, y + 100),
        "The application is built around a simple promise: practice should feel focused, measurable, and trustworthy. The interface is intentionally direct, while the back end keeps the source dataset, quiz sessions, scoring, and AI-generated candidates auditable.",
        W - 2 * M - 80,
        F["body"],
        INK,
        36,
    )
    footer(p, 1)
    return p


def page_architecture() -> Page:
    p = new_page()
    y = title(p, "System Architecture", "02 / application map")
    draw_flow(
        p,
        M,
        y,
        [
            ("Browser UI", "Dashboard, Quiz Runner, Stats, and Question Lab screens."),
            ("Next.js App", "Route handlers and server components coordinate the user flows."),
            ("Data Layer", "Typed query module uses pg Pool and transactional writes."),
            ("Postgres", "Seed bank, tests, attempts, answers, and generated exams."),
            ("OpenAI", "Question Lab calls Responses API only when enabled."),
        ],
        245,
    )
    y += 300
    left = M
    right = W // 2 + 20
    rounded(p, (left, y, W // 2 - 20, y + 640), fill=CARD, outline="#E7D6C0", radius=34)
    rounded(p, (right, y, W - M, y + 640), fill=CARD, outline="#E7D6C0", radius=34)
    card_title(p, left + 36, y + 34, "Runtime components")
    bullet_list(
        p,
        left + 46,
        y + 102,
        [
            "Next.js 16 / React 19 application under web/.",
            "Postgres schema in web/db/schema.sql.",
            "CSV migration and seed scripts preserve the original question bank.",
            "Static image stimuli are served from web/public/images/.",
            "Railway deploys web/ as the service root with npm run start.",
        ],
        610,
    )
    card_title(p, right + 36, y + 34, "Operational boundaries")
    bullet_list(
        p,
        right + 46,
        y + 102,
        [
            "No auth in the practice app; intended for public demo and personal use.",
            "Answer keys stay server-side until a question is answered.",
            "Question Lab is disabled unless OPENAI_API_KEY and QUESTION_LAB_ENABLED are set.",
            "The access token creates an HttpOnly session rather than exposing secrets client-side.",
            "Generated candidates are review-only and never auto-inserted into the bank.",
        ],
        610,
        GREEN,
    )
    y += 720
    rounded(p, (M, y, W - M, y + 380), fill="#FFFDF8", outline="#E7D6C0", radius=34)
    card_title(p, M + 40, y + 38, "End-to-end quiz lifecycle")
    draw_flow(
        p,
        M + 42,
        y + 112,
        [
            ("Select test", "Fetch test summaries from /api/tests."),
            ("Create attempt", "POST /api/attempts records start state."),
            ("Submit answers", "POST answers with elapsed time and choice."),
            ("Finish", "POST finish updates final counts and status."),
        ],
        300,
    )
    footer(p, 2)
    return p


def page_database_one() -> Page:
    p = new_page()
    y = title(p, "Complete Database Schema", "03 / core content tables")
    draw_paragraph(
        p,
        (M, y),
        "The schema separates reusable question content from test assembly and user performance. This keeps the imported CCAT bank immutable in spirit while allowing randomized generated exams and persistent attempt history.",
        W - 2 * M,
        F["body"],
        INK,
        35,
    )
    y += 150
    rows = [
        ["questions", "id", "SERIAL PK", "Primary question identifier."],
        ["questions", "external_id", "TEXT UNIQUE", "Stable imported source id."],
        ["questions", "origin", "TEXT NOT NULL", "Import origin / source family."],
        ["questions", "source_exam", "TEXT", "Exam grouping from seed data."],
        ["questions", "source_file", "TEXT", "Original source file reference."],
        ["questions", "source_category", "TEXT", "Raw imported category."],
        ["questions", "source_question_number", "TEXT", "Question number in source."],
        ["questions", "category", "TEXT NOT NULL", "Normalized broad category."],
        ["questions", "question_type", "TEXT NOT NULL", "Normalized skill type."],
        ["questions", "prompt", "TEXT NOT NULL DEFAULT ''", "Reusable instruction text."],
        ["questions", "stimulus", "TEXT NOT NULL", "Question-specific text, table, or image filename."],
        ["questions", "stimulus_type", "TEXT CHECK", "One of text, text_table, image."],
        ["questions", "correct_choice_label", "TEXT NOT NULL", "Correct answer label."],
        ["questions", "correct_choice_text", "TEXT NOT NULL", "Correct answer text."],
        ["questions", "explanation", "TEXT NOT NULL DEFAULT ''", "Plain-text rationale."],
    ]
    y = draw_table(p, M, y, [190, 350, 305, 595], ["Table", "Column", "Type", "Purpose"], rows, row_h=52, small=True)
    rows2 = [
        ["choices", "id", "SERIAL PK", "Choice identifier."],
        ["choices", "question_id", "INTEGER FK -> questions.id ON DELETE CASCADE", "Parent question."],
        ["choices", "label", "TEXT NOT NULL", "A-D label preserved from source."],
        ["choices", "position", "INTEGER NOT NULL", "Rendered ordering."],
        ["choices", "text", "TEXT NOT NULL", "Choice body."],
        ["choices", "UNIQUE", "(question_id, label), (question_id, position)", "Prevents duplicate labels or order slots."],
        ["tests", "id", "SERIAL PK", "Test identifier."],
        ["tests", "title", "TEXT NOT NULL", "Exam or generated-test title."],
        ["tests", "kind", "TEXT NOT NULL", "Seed/source exam or generated practice type."],
        ["tests", "source_exam", "TEXT UNIQUE", "Original exam id for seeded tests."],
        ["tests", "question_count", "INTEGER NOT NULL", "Number of assigned questions."],
        ["tests", "time_limit_seconds", "INTEGER DEFAULT 900", "Timer limit; generated tests use one minute per question."],
        ["test_questions", "test_id", "INTEGER FK -> tests.id ON DELETE CASCADE", "Parent test."],
        ["test_questions", "question_id", "INTEGER FK -> questions.id ON DELETE CASCADE", "Assigned question."],
        ["test_questions", "position", "INTEGER NOT NULL", "Position inside the test."],
        ["test_questions", "PRIMARY KEY", "(test_id, question_id)", "Prevents duplicate question assignment."],
        ["test_questions", "UNIQUE", "(test_id, position)", "Prevents duplicate test positions."],
    ]
    draw_table(p, M, y, [190, 350, 385, 515], ["Table", "Column", "Type", "Purpose"], rows2, row_h=52, small=True)
    footer(p, 3)
    return p


def page_database_two() -> Page:
    p = new_page()
    y = title(p, "Complete Database Schema", "04 / attempts, answers, indexes")
    rows = [
        ["attempts", "id", "SERIAL PK", "Attempt identifier."],
        ["attempts", "test_id", "INTEGER FK -> tests.id", "Attempted test."],
        ["attempts", "status", "TEXT CHECK", "in_progress, completed, timed_out, or aborted."],
        ["attempts", "started_at", "TIMESTAMPTZ NOT NULL", "Server start timestamp."],
        ["attempts", "finished_at", "TIMESTAMPTZ", "Server finish timestamp."],
        ["attempts", "elapsed_seconds", "DOUBLE PRECISION DEFAULT 0", "Current or final elapsed time."],
        ["attempts", "answered_count", "INTEGER DEFAULT 0", "Stored denormalized answered count."],
        ["attempts", "correct_count", "INTEGER DEFAULT 0", "Stored denormalized correct count."],
        ["attempts", "total_questions", "INTEGER NOT NULL", "Total expected questions."],
        ["attempt_answers", "id", "SERIAL PK", "Answer identifier."],
        ["attempt_answers", "attempt_id", "INTEGER FK -> attempts.id ON DELETE CASCADE", "Parent attempt."],
        ["attempt_answers", "question_id", "INTEGER FK -> questions.id", "Answered question."],
        ["attempt_answers", "question_position", "INTEGER NOT NULL", "Position in test at answer time."],
        ["attempt_answers", "selected_choice_label", "TEXT NOT NULL", "Selected label."],
        ["attempt_answers", "selected_choice_text", "TEXT NOT NULL", "Selected answer body."],
        ["attempt_answers", "is_correct", "BOOLEAN NOT NULL", "Server-scored correctness."],
        ["attempt_answers", "elapsed_seconds", "DOUBLE PRECISION NOT NULL", "Elapsed time when answer was submitted."],
        ["attempt_answers", "UNIQUE", "(attempt_id, question_id), (attempt_id, question_position)", "One answer per question and position."],
    ]
    y = draw_table(p, M, y, [210, 345, 430, 455], ["Table", "Column", "Type", "Purpose"], rows, row_h=54, small=True)
    rounded(p, (M, y + 15, W - M, y + 365), fill="#171412", outline="#171412", radius=34)
    card_title(p, M + 40, y + 50, "Indexes", ORANGE)
    p.draw.text((M + 45, y + 118), "idx_choices_question_position", font=F["mono_b"], fill="#FFFFFF")
    p.draw.text((M + 455, y + 118), "ON choices(question_id, position)", font=F["mono"], fill="#EADFD2")
    p.draw.text((M + 45, y + 176), "idx_test_questions_position", font=F["mono_b"], fill="#FFFFFF")
    p.draw.text((M + 455, y + 176), "ON test_questions(test_id, position)", font=F["mono"], fill="#EADFD2")
    p.draw.text((M + 45, y + 234), "idx_attempt_answers_attempt", font=F["mono_b"], fill="#FFFFFF")
    p.draw.text((M + 455, y + 234), "ON attempt_answers(attempt_id, question_position)", font=F["mono"], fill="#EADFD2")
    p.draw.text((M + 45, y + 305), "Design note: relational constraints preserve answer ordering and scoring integrity across retries.", font=F["small"], fill="#FFFFFF")
    footer(p, 4)
    return p


def page_api() -> Page:
    p = new_page()
    y = title(p, "API Contract", "05 / routes and behavior")
    rows = [
        ["GET", "/api/tests", "List seed and generated tests."],
        ["POST", "/api/tests", "Create a generated 8-10 question practice test."],
        ["GET", "/api/tests/[id]", "Fetch a test definition with client-safe questions and choices."],
        ["POST", "/api/attempts", "Create an in-progress attempt for a selected test."],
        ["GET", "/api/attempts/[id]", "Read current attempt state."],
        ["POST", "/api/attempts/[id]/answers", "Record or update an answer; return answer key, explanation, and correctness."],
        ["POST", "/api/attempts/[id]/finish", "Finish, time out, or abort an attempt and calculate result summary."],
        ["POST", "/api/question-lab", "Generate a governed candidate question when the lab is enabled and authorized."],
    ]
    y = draw_table(p, M, y, [150, 475, 815], ["Method", "Route", "Responsibility"], rows, row_h=70)
    rounded(p, (M, y + 20, W - M, y + 530), fill="#FFF7EC", outline="#E7D6C0", radius=34)
    card_title(p, M + 40, y + 58, "TypeScript domain schema")
    left_items = [
        "ClientQuestion: id, externalId, category, questionType, prompt, stimulus, stimulusType, choices.",
        "Question: server-side extension with origin, source metadata, correct choice, and explanation.",
        "TestSummary/TestDefinition: title, kind, source exam, question count, time limit, and questions.",
    ]
    right_items = [
        "QuizAttempt: status, timestamps, elapsed seconds, answered count, correct count, total.",
        "AttemptAnswer/AnswerResult: selected choice, correctness, elapsed time, answer key, explanation.",
        "QuizResult/AttemptSummary: final scoring and history rows for the stats screen.",
    ]
    bullet_list(p, M + 52, y + 132, left_items, 660, ORANGE)
    bullet_list(p, W // 2 + 10, y + 132, right_items, 660, GREEN)
    y += 610
    rounded(p, (M, y, W - M, y + 330), fill=CARD, outline="#E7D6C0", radius=34)
    card_title(p, M + 40, y + 38, "Privacy and scoring posture")
    draw_paragraph(
        p,
        (M + 40, y + 105),
        "The client receives no answer key in the test payload. Scoring happens server-side when an answer is submitted, then the API returns correctness, explanation, and the correct answer for immediate learning feedback.",
        W - 2 * M - 80,
        F["body"],
        INK,
        36,
    )
    footer(p, 5)
    return p


def page_harness() -> Page:
    p = new_page()
    y = title(p, "Question Lab Governance", "06 / AI harness schema")
    draw_paragraph(
        p,
        (M, y),
        "Question Lab is a controlled generation loop. It asks a model for one original CCAT-style candidate, validates it against deterministic checkpoints, and gives the model one revision pass with structured feedback. Accepted candidates remain review artifacts, not automatic production inserts.",
        W - 2 * M,
        F["body"],
        INK,
        35,
    )
    y += 165
    rows = [
        ["CandidateQuestion", "category, questionType, prompt, stimulus, choices, correctChoiceLabel, explanation, verificationExpression"],
        ["CandidateChoice", "label, text"],
        ["HarnessCheckpoint", "name, passed, detail"],
        ["HarnessAttempt", "revision, candidate, checkpoints"],
        ["HarnessResult", "accepted, model, attempts, candidate, checkpoints"],
    ]
    y = draw_table(p, M, y, [360, 1080], ["Schema object", "Fields"], rows, row_h=72)
    rounded(p, (M, y + 16, W - M, y + 650), fill="#171412", outline="#171412", radius=34)
    card_title(p, M + 40, y + 56, "Checkpoint battery", ORANGE)
    checks = [
        ("Schema", "Required fields plus exactly four choices."),
        ("Single answer", "Unique A-D labels and one declared correct choice."),
        ("Explanation", "Substantive rationale that names the correct choice text."),
        ("Category", "Question type must exactly match the requested seed type."),
        ("Similarity", "Highest seed-question token similarity must stay under 0.72."),
        ("Math", "Arithmetic types must pass a safe deterministic calculator."),
        ("Content safety", "Basic study-tool screen for unsafe content."),
        ("Export readiness", "Candidate must serialize cleanly for review/export."),
    ]
    x1, x2 = M + 54, W // 2 + 10
    yy = y + 132
    for i, (name, desc) in enumerate(checks):
        x = x1 if i < 4 else x2
        row_y = yy + (i % 4) * 112
        p.draw.rounded_rectangle((x, row_y, x + 650, row_y + 82), radius=20, fill="#241F1B", outline="#3B332C")
        p.draw.text((x + 22, row_y + 14), name, font=F["body_b"], fill="#FFFFFF")
        p.draw.text((x + 22, row_y + 48), desc, font=F["micro"], fill="#EADFD2")
    y += 730
    rounded(p, (M, y, W - M, y + 285), fill="#FFF7EC", outline="#E7D6C0", radius=34)
    card_title(p, M + 40, y + 38, "Model boundary")
    draw_paragraph(
        p,
        (M + 40, y + 100),
        "The model is configured through OPENAI_MODEL, defaults to gpt-4o-mini, has a 20-second timeout, zero SDK retries, a 1,200-token cap, and a strict Zod response schema. Public generation is rate-limited by session and request budget.",
        W - 2 * M - 80,
        F["body"],
        INK,
        35,
    )
    footer(p, 6)
    return p


def page_ux_ops() -> Page:
    p = new_page()
    y = title(p, "Experience + Operations", "07 / shipped workflows")
    rounded(p, (M, y, W - M, y + 420), fill=CARD, outline="#E7D6C0", radius=34)
    card_title(p, M + 40, y + 38, "User-facing screens")
    draw_flow(
        p,
        M + 44,
        y + 112,
        [
            ("Dashboard", "Choose source exams, create generated practice, launch Question Lab."),
            ("Quiz", "Timed practice, persistent answers, explanations, and result state."),
            ("Stats", "Completed attempts sorted by finish time with scoring summary."),
            ("Lab", "Generate governed candidates and inspect checkpoint feedback."),
        ],
        315,
    )
    y += 500
    left = M
    right = W // 2 + 20
    rounded(p, (left, y, W // 2 - 20, y + 540), fill="#FFF7EC", outline="#E7D6C0", radius=34)
    rounded(p, (right, y, W - M, y + 540), fill="#171412", outline="#171412", radius=34)
    card_title(p, left + 36, y + 34, "Deployment")
    bullet_list(
        p,
        left + 46,
        y + 100,
        [
            "Railway service: quizcat-web.",
            "Start command: npm run start.",
            "Service root: web/ with path-as-root deployment.",
            "Required database variable: POSTGRES_URL.",
            "Production seed state: 400 questions, 1,952 choices, 8 tests.",
        ],
        W // 2 - 120,
        ORANGE,
    )
    p.draw.text((right + 36, y + 34), "Environment switches", font=F["h3"], fill="#FFFFFF")
    envs = [
        "POSTGRES_URL",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "QUESTION_LAB_ENABLED",
        "QUESTION_LAB_ACCESS_TOKEN",
    ]
    yy = y + 102
    for e in envs:
        p.draw.rounded_rectangle((right + 46, yy, W - M - 46, yy + 58), radius=18, fill="#241F1B", outline="#3B332C")
        p.draw.text((right + 72, yy + 15), e, font=F["mono_b"], fill="#FFFFFF")
        yy += 74
    y += 610
    rounded(p, (M, y, W - M, y + 350), fill=CARD, outline="#E7D6C0", radius=34)
    card_title(p, M + 40, y + 38, "Submission links")
    for label, value in [
        ("Production", "https://quizcat-web-production.up.railway.app"),
        ("Repository", "https://github.com/micronox/FiredFest_Submission"),
        ("Textual browser app", "https://quizcat-textual-production.up.railway.app"),
    ]:
        p.draw.text((M + 44, y + 112), label.upper(), font=F["micro"], fill=ORANGE)
        p.draw.text((M + 260, y + 105), value, font=F["body_b"], fill=INK)
        y += 62
    footer(p, 7)
    return p


def page_final() -> Page:
    p = new_page(DARK)
    draw_logo(p, (M, 140, W - M, 520), opacity=235)
    p.draw.text((M, 690), "Built to make practice measurable.", font=F["display_sm"], fill="#FFFFFF")
    y = draw_paragraph(
        p,
        (M, 790),
        "CCat Leash Harness is more than a quiz UI: it is a schema-respecting practice system, a deployed web product, and a controlled AI workflow for expanding the bank without losing trust in the answers.",
        W - 2 * M,
        F["h2"],
        "#F2E9DC",
        52,
    )
    y += 80
    for label, value in [
        ("Core stack", "Next.js, React, TypeScript, Postgres, Railway"),
        ("Data integrity", "Relational constraints, ordered choices, server-side answer keys"),
        ("AI safety", "Typed schema, deterministic checkpoints, similarity limit, calculator verification"),
        ("Reader promise", "Fast practice, clear feedback, visible progress"),
    ]:
        p.draw.rounded_rectangle((M, y, W - M, y + 112), radius=26, fill="#241F1B", outline="#3B332C")
        p.draw.text((M + 34, y + 24), label, font=F["body_b"], fill=ORANGE)
        p.draw.text((M + 310, y + 24), value, font=F["body"], fill="#FFFFFF")
        y += 140
    p.draw.text((M, H - 220), "CCat Leash Harness", font=F["h1"], fill="#FFFFFF")
    p.draw.text((M, H - 150), "If I Fits, I Harness Sits", font=F["h2"], fill=ORANGE)
    return p


def build() -> None:
    pages = [
        page_cover(),
        page_snapshot(),
        page_architecture(),
        page_database_one(),
        page_database_two(),
        page_api(),
        page_harness(),
        page_ux_ops(),
        page_final(),
    ]
    image_paths: list[Path] = []
    for idx, page in enumerate(pages, 1):
        path = OUT_DIR / f"page_{idx:02d}.png"
        page.image.save(path, "PNG")
        image_paths.append(path)

    rgb_pages = [Image.open(path).convert("RGB") for path in image_paths]
    rgb_pages[0].save(
        PDF_OUT,
        save_all=True,
        append_images=rgb_pages[1:],
        resolution=200.0,
        quality=95,
    )
    print(PDF_OUT)
    for path in image_paths:
        print(path)


if __name__ == "__main__":
    build()
