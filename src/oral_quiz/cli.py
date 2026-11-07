# -*- coding: utf-8 -*-
"""口腔医学终端答题系统

安装后在终端输入：
  exercise_enter  进入答题（选择章节，再选择级别）
  exercise_exit   在程序内任何位置退出
单选输入一个字母；多选输入全部正确字母；排序按顺序连写全部字母。
字母也可换成序号（如 134）。输入 q 返回上一级。

可设置环境变量 ORAL_QUIZ_DIR 指向自己的题库目录（ch*.json）。
"""
import json
import os
import random
import re
import sys
from importlib import resources

LETTERS = "ABCDEFGH"
DEFAULT_TOTAL_COUNT = 30
TYPE_LABEL = {"single": "单选", "multi": "多选", "order": "排序"}
LEVELS = {1: "I级（旧题）", 2: "II级（新题）", 3: "III级（排序）", 4: "IV级（多选）"}
INPUT_HINT = {
    "single": "请输入一个选项字母",
    "multi": "请输入全部正确选项的字母，可连写，不要重复",
    "order": "请把全部字母按顺序连写，每个字母一次",
}

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


def question_type(q):
    return q.get("type", "single")


def question_level(q):
    """未标注级别的题目是基础题，属于 I 级。"""
    return q.get("level", 1)


def is_valid(q):
    n = len(q.get("options", []))
    answer = q.get("answer")
    qtype = question_type(q)
    if not 2 <= n <= len(LETTERS) or question_level(q) not in LEVELS:
        return False
    if qtype == "single":
        return isinstance(answer, int) and 0 <= answer < n
    if not isinstance(answer, list):
        return False
    if qtype == "multi":
        return len(answer) > 0 and len(set(answer)) == len(answer) and all(a in range(n) for a in answer)
    return qtype == "order" and sorted(answer) == list(range(n))


def load_chapters():
    chapters = []
    for name, read in question_files():
        try:
            data = json.loads(read())
        except (OSError, json.JSONDecodeError) as e:
            print(red(f"读取失败，已跳过：{name}（{e}）"))
            continue
        questions = [q for q in data.get("questions", []) if is_valid(q)]
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


def shuffled_view(q):
    """打乱选项，返回 (选项列表, 正确答案的新位置)；排序题保证不会恰好是正确顺序。"""
    order = list(range(len(q["options"])))
    random.shuffle(order)
    while question_type(q) == "order" and order == q["answer"]:
        random.shuffle(order)
    options = [q["options"][i] for i in order]
    if question_type(q) == "single":
        return options, order.index(q["answer"])
    return options, [order.index(a) for a in q["answer"]]


def parse_letters(text, n):
    """把 “ACD”“a c d”“A,C,D”“134” 解析为下标列表；无效或重复时返回 None。"""
    picked = []
    for ch in re.sub(r"[\s,，、]", "", text).upper():
        if ch in LETTERS[:n]:
            i = LETTERS.index(ch)
        elif ch.isdigit() and 1 <= int(ch) <= n:
            i = int(ch) - 1
        else:
            return None
        if i in picked:
            return None
        picked.append(i)
    return picked or None


def parse_answer(qtype, text, n):
    picked = parse_letters(text, n)
    if picked is None:
        return None
    if qtype == "single" and len(picked) != 1:
        return None
    if qtype == "order" and len(picked) != n:
        return None
    return picked


def is_correct(qtype, picked, answer):
    if qtype == "single":
        return picked[0] == answer
    if qtype == "multi":
        return set(picked) == set(answer)
    return picked == answer


def answer_text(qtype, options, answer):
    if qtype == "single":
        return f"{LETTERS[answer]}. {options[answer]}"
    if qtype == "multi":
        return "；".join(f"{LETTERS[a]}. {options[a]}" for a in sorted(answer))
    return " → ".join(f"{LETTERS[a]}. {options[a]}" for a in answer)


def run_quiz(title, questions):
    questions = questions[:]
    random.shuffle(questions)
    total = len(questions)
    correct = 0
    wrong_list = []

    print()
    print(bold(f"====== {title}（共 {total} 题）======"))
    print(dim("单选输入一个字母；多选输入全部正确字母；排序按顺序连写全部字母。q 返回，exercise_exit 退出"))

    for idx, q in enumerate(questions, 1):
        qtype = question_type(q)
        options, answer = shuffled_view(q)
        print()
        where = q.get("_chapter_title")
        head = f"[{idx}/{total}] 【{TYPE_LABEL[qtype]}】"
        if where:
            head += f"{where} · "
        if q.get("section"):
            head += q["section"]
        print(cyan(head))
        print(bold(q["question"]))
        for i, opt in enumerate(options):
            print(f"  {LETTERS[i]}. {opt}")

        while True:
            text = ask("你的答案：")
            if text.lower() == "q":
                raise BackToMenu
            picked = parse_answer(qtype, text, len(options))
            if picked is not None:
                break
            print(yellow(INPUT_HINT[qtype]))

        right_text = answer_text(qtype, options, answer)
        if is_correct(qtype, picked, answer):
            correct += 1
            print(green("✔ 回答正确"))
        else:
            wrong_list.append((q, right_text))
            print(red("✘ 回答错误") + f"  正确答案：{green(right_text)}")
        if q.get("explanation"):
            print(dim("解析：") + q["explanation"])
        if q.get("source"):
            label = "原文" if question_level(q) == 1 else "来源"
            print(dim(f"{label}：" + q["source"]))

    print()
    rate = correct * 100 // total if total else 0
    print(bold(f"====== 本轮结束：{correct}/{total} 正确（{rate}%）======"))
    if wrong_list:
        print(yellow("错题回顾："))
        for q, right_text in wrong_list:
            print(f"  · {q['question']}")
            print(f"    → {green(right_text)}")


def ask_count(total):
    """总章抽题数量：回车默认，all 为全部。"""
    raw = ask(f"抽题数量（回车默认 {DEFAULT_TOTAL_COUNT}，输入 all 为全部）：")
    if raw.lower() == "all":
        return total
    count = int(raw) if raw.isdigit() and int(raw) > 0 else DEFAULT_TOTAL_COUNT
    return min(count, total)


def level_menu(title, questions, sample=False):
    """选择随机或某一级别后答题；q 返回章节选择。sample 为 True 时先询问抽题数量。"""
    groups = [("随机", questions)]
    for level, label in LEVELS.items():
        groups.append((label, [q for q in questions if question_level(q) == level]))

    while True:
        print()
        print(bold(f"========== {title} =========="))
        for i, (label, qs) in enumerate(groups):
            print(f"  {i}. {label}（{len(qs)} 题）")
        print(dim(f"输入序号开始答题，q 返回章节选择，{EXIT_CMD} 退出"))

        text = ask("请选择级别：")
        if text.lower() == "q":
            return
        if not text.isdigit() or int(text) >= len(groups):
            print(yellow("无效的序号，请重新输入"))
            continue
        label, qs = groups[int(text)]
        if not qs:
            print(yellow("该级别暂无题目"))
            continue

        try:
            if sample:
                qs = random.sample(qs, ask_count(len(qs)))
            run_quiz(f"{title} · {label}", qs)
        except BackToMenu:
            print(yellow("已返回级别选择"))


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

        if n == 0:
            level_menu("总章", all_questions, sample=True)
        else:
            c = chapters[n - 1]
            level_menu(f"{chapter_label(c['chapter'])} {c['title']}", c["questions"])


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
