# -*- coding: utf-8 -*-
"""口腔医学终端答题系统

安装后在终端输入：
  exercise_enter  进入答题（选择章节）
  exercise_exit   在程序内任何位置退出
答题时输入 A/B/C（或 1/2/3），输入 q 返回章节选择。

可设置环境变量 ORAL_QUIZ_DIR 指向自己的题库目录（ch*.json）。
"""
import json
import os
import random
import sys
from importlib import resources

LETTERS = "ABC"
DEFAULT_TOTAL_COUNT = 30

ENTER_CMD = "exercise_enter"
EXIT_CMD = "exercise_exit"

# 让 Windows 终端也能正常显示中文
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
if os.name == "nt":
    os.system("")  # 开启 Windows 终端的 ANSI 颜色支持

USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def color(text, code):
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def green(t): return color(t, "32")
def red(t): return color(t, "31")
def yellow(t): return color(t, "33")
def cyan(t): return color(t, "36")
def dim(t): return color(t, "2")
def bold(t): return color(t, "1")


class ExitProgram(Exception):
    pass


class BackToMenu(Exception):
    pass


def ask(prompt):
    """读取一行输入；任何时候输入 exercise_exit 都会退出。"""
    try:
        text = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise ExitProgram
    if text.lower() == EXIT_CMD:
        raise ExitProgram
    return text


def question_files():
    """返回 (文件名, 读取函数) 列表：优先使用 ORAL_QUIZ_DIR，否则使用包内题库。"""
    custom = os.environ.get("ORAL_QUIZ_DIR")
    if custom:
        names = sorted(n for n in os.listdir(custom) if n.startswith("ch") and n.endswith(".json"))
        return [(n, lambda p=os.path.join(custom, n): open(p, encoding="utf-8").read()) for n in names]
    base = resources.files("oral_quiz").joinpath("questions")
    entries = sorted((e for e in base.iterdir()
                      if e.name.startswith("ch") and e.name.endswith(".json")), key=lambda e: e.name)
    return [(e.name, lambda e=e: e.read_text(encoding="utf-8")) for e in entries]


def load_chapters():
    chapters = []
    for name, read in question_files():
        try:
            data = json.loads(read())
        except (OSError, json.JSONDecodeError) as e:
            print(red(f"读取失败，已跳过：{name}（{e}）"))
            continue
        questions = [q for q in data.get("questions", [])
                     if len(q.get("options", [])) == 3 and q.get("answer") in (0, 1, 2)]
        if questions:
            chapters.append({
                "chapter": data.get("chapter"),
                "title": data.get("chapter_title", name),
                "questions": questions,
            })
    chapters.sort(key=lambda c: (c["chapter"] is None, c["chapter"]))
    return chapters


def chapter_label(n):
    nums = "零一二三四五六七八九十"
    if n is None:
        return ""
    if n <= 10:
        return f"第{nums[n]}章"
    if n < 20:
        return f"第十{nums[n - 10]}章"
    return f"第{n}章"


def shuffled_options(q):
    """打乱选项顺序，返回 (选项列表, 正确答案的新位置)。"""
    order = [0, 1, 2]
    random.shuffle(order)
    options = [q["options"][i] for i in order]
    return options, order.index(q["answer"])


def parse_choice(text):
    t = text.strip().upper()
    if t in ("A", "B", "C"):
        return "ABC".index(t)
    if t in ("1", "2", "3"):
        return int(t) - 1
    return None


def run_quiz(title, questions):
    questions = questions[:]
    random.shuffle(questions)
    total = len(questions)
    correct = 0
    wrong_list = []

    print()
    print(bold(f"====== {title}（共 {total} 题）======"))
    print(dim("输入 A/B/C 作答，q 返回章节选择，exercise_exit 退出"))

    for idx, q in enumerate(questions, 1):
        options, answer_pos = shuffled_options(q)
        print()
        where = q.get("_chapter_title")
        head = f"[{idx}/{total}]"
        if where:
            head += f" {where}"
        if q.get("section"):
            head += f" · {q['section']}"
        print(cyan(head))
        print(bold(q["question"]))
        for i, opt in enumerate(options):
            print(f"  {LETTERS[i]}. {opt}")

        while True:
            text = ask("你的答案：")
            if text.lower() == "q":
                raise BackToMenu
            choice = parse_choice(text)
            if choice is not None:
                break
            print(yellow("请输入 A、B 或 C（也可输入 1/2/3）"))

        right_text = f"{LETTERS[answer_pos]}. {options[answer_pos]}"
        if choice == answer_pos:
            correct += 1
            print(green("✔ 回答正确"))
        else:
            wrong_list.append((q, right_text))
            print(red("✘ 回答错误") + f"  正确答案：{green(right_text)}")
        if q.get("explanation"):
            print(dim("解析：") + q["explanation"])
        if q.get("source"):
            print(dim("原文：" + q["source"]))

    print()
    rate = correct * 100 // total if total else 0
    print(bold(f"====== 本轮结束：{correct}/{total} 正确（{rate}%）======"))
    if wrong_list:
        print(yellow("错题回顾："))
        for q, right_text in wrong_list:
            print(f"  · {q['question']}")
            print(f"    → {green(right_text)}")


def chapter_menu(chapters):
    all_questions = []
    for c in chapters:
        for q in c["questions"]:
            q2 = dict(q)
            q2["_chapter_title"] = f"{chapter_label(c['chapter'])} {c['title']}"
            all_questions.append(q2)

    while True:
        print()
        print(bold("========== 章节选择 =========="))
        print(f"  0. 总章（全部知识点随机抽题，共 {len(all_questions)} 题）")
        for i, c in enumerate(chapters, 1):
            print(f"  {i}. {chapter_label(c['chapter'])} {c['title']}（{len(c['questions'])} 题）")
        print(dim(f"输入序号开始答题，{EXIT_CMD} 退出"))

        text = ask("请选择章节：")
        if not text.isdigit() or not (0 <= int(text) <= len(chapters)):
            print(yellow("无效的序号，请重新输入"))
            continue
        n = int(text)

        try:
            if n == 0:
                count = DEFAULT_TOTAL_COUNT
                raw = ask(f"抽题数量（回车默认 {DEFAULT_TOTAL_COUNT}，输入 all 为全部）：")
                if raw.lower() == "all":
                    count = len(all_questions)
                elif raw.isdigit() and int(raw) > 0:
                    count = int(raw)
                count = min(count, len(all_questions))
                run_quiz("总章 · 随机抽题", random.sample(all_questions, count))
            else:
                c = chapters[n - 1]
                run_quiz(f"{chapter_label(c['chapter'])} {c['title']}", c["questions"])
        except BackToMenu:
            print(yellow("已返回章节选择"))


def main():
    """终端命令 exercise_enter 的入口：直接进入章节选择。"""
    chapters = load_chapters()
    if not chapters:
        print(red("没有找到题库文件（ch*.json）"))
        return 1
    print(bold("口腔医学答题系统") + dim(f"  · 随时输入 {EXIT_CMD} 退出"))
    try:
        chapter_menu(chapters)
    except ExitProgram:
        print("你已退出程序。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
