部分学生反应学校自编题库质量低下，难以通过做题来检测知识点掌握度，所以尝试做了这个刷题系统，目前只有口腔医学的题目。

后续可能会更新吧，如果同学反响良好的话，因为确实没有什么技术含量，只要把知识点整理好就能自己搓一个。

## 安装


*有问题多用ai，查一下就知道怎么装了*


需要 Python 3.9 及以上。推荐用 [pipx](https://pipx.pypa.io/) 安装（会自动放进独立环境并把命令加到 PATH）：

```bash
pipx install git+https://github.com/Suiich/Tests.git
```

也可以直接用 pip：

```bash
pip install git+https://github.com/Suiich/Tests.git
```

更新到最新题库：

```bash
pipx upgrade Tests
# 或
pip install --upgrade git+https://github.com/Suiich/Tests.git
```

## 使用

在终端输入：

```bash
exercise_enter
```

- `0`：总章，从全部题目中随机抽题（默认 30 题，可输入数量或 `all`）
- `1`–`13`：按章节答题，本章题目随机顺序出现
- 答题时输入 `A/B/C`（或 `1/2/3`），输入 `q` 返回章节选择
- 任何时候输入 `exercise_exit` 退出

每题作答后显示正确答案、解析和笔记原文；每章结束显示得分和错题回顾。选项顺序每次随机打乱。

## 章节

| 章 | 内容 | 题数 |
|---|---|---|
| 1 | 口腔颌面部解剖生理 | 46 |
| 2 | 口腔颌面部检查 | 11 |
| 3 | 口腔卫生保健 | 4 |
| 4 | 牙体、牙髓病 | 38 |
| 5 | 牙周疾病 | 27 |
| 6 | 口腔粘膜常见疾病 | 34 |
| 7 | 口腔局部麻醉 | 24 |
| 8 | 牙拔除术 | 25 |
| 9 | 口腔颌面部感染 | 24 |
| 10 | 口腔颌面部损伤 | 30 |
| 11 | 颞下颌关节常见病 | 13 |
| 12 | 唾液腺常见疾病 | 22 |
| 13 | 口腔颌面部肿瘤 | 33 |

## 题库格式与贡献

题库在 `src/oral_quiz/questions/`，每章一个 JSON 文件：

```json
{
  "id": "ch04-001",
  "section": "龋病",
  "question": "题干",
  "options": ["选项一", "选项二", "选项三"],
  "answer": 0,
  "source": "笔记原文",
  "explanation": "解析"
}
```

`answer` 是正确选项的下标（0/1/2）。发现错题欢迎提 Issue 或 PR。

想用自己的题库，可以把 `ch*.json` 放进一个文件夹，然后：

```bash
ORAL_QUIZ_DIR=/path/to/my_questions exercise_enter
```

## 免责声明

题目由学习笔记整理而来，仅供复习参考，请以教材和老师讲授内容为准。
