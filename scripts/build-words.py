#!/usr/bin/env python3
"""Build src/data/words.json from the MIT collins-vocabulary list.

Source file is the collins.json published by cd155/collins-vocabulary
(MIT), which is generated from skywind3000/ECDICT (MIT). We keep only
entries tagged zk (中考), order them by corpus frequency, and attach
learner-facing glosses for a weak Grade 9 student.

Usage:
  python3 scripts/build-words.py /path/to/collins.json src/data/words.json
"""

from __future__ import annotations

import json
import re
import sys
from collections import OrderedDict

# Shown first for polysemous or misleading dictionary entries.
# Keys are lowercase except where noted; lookup is case-insensitive.
PRIMARY: dict[str, list[str]] = {
    "the": ["这", "那"],
    "be": ["是"],
    "and": ["和", "与"],
    "of": ["……的", "属于"],
    "a": ["一个"],
    "in": ["在……里面", "在"],
    "to": ["向", "到", "去"],
    "have": ["有"],
    "it": ["它"],
    "i": ["我"],
    "that": ["那个", "那"],
    "for": ["为了", "给", "因为"],
    "you": ["你", "你们"],
    "he": ["他"],
    "with": ["和……一起", "用"],
    "on": ["在……上面"],
    "do": ["做"],
    "say": ["说"],
    "this": ["这个", "这"],
    "they": ["他们", "她们", "它们"],
    "at": ["在"],
    "but": ["但是"],
    "we": ["我们"],
    "his": ["他的"],
    "from": ["从", "来自"],
    "not": ["不"],
    "by": ["被", "通过", "在……旁边"],
    "she": ["她"],
    "or": ["或者", "还是"],
    "as": ["作为", "像", "当"],
    "what": ["什么"],
    "go": ["去"],
    "their": ["他们的"],
    "can": ["能", "可以", "会"],
    "who": ["谁"],
    "get": ["得到", "变得", "到达"],
    "if": ["如果", "是否"],
    "would": ["会", "愿意"],
    "her": ["她的", "她"],
    "all": ["所有的", "全部"],
    "my": ["我的"],
    "make": ["做", "使"],
    "about": ["关于", "大约"],
    "know": ["知道", "认识"],
    "will": ["将", "会", "愿意"],
    "up": ["向上", "起来"],
    "one": ["一", "一个"],
    "time": ["时间", "次"],
    "there": ["那里", "在那里"],
    "year": ["年"],
    "so": ["所以", "这么"],
    "think": ["认为", "想"],
    "when": ["什么时候", "当……时候"],
    "which": ["哪一个", "哪个"],
    "them": ["他们", "她们", "它们"],
    "some": ["一些", "某个"],
    "me": ["我"],
    "people": ["人", "人们"],
    "take": ["拿", "带走", "花费"],
    "out": ["出去", "在外面"],
    "into": ["进到……里"],
    "just": ["刚刚", "只是", "正好"],
    "see": ["看见", "看到"],
    "him": ["他"],
    "your": ["你的", "你们的"],
    "come": ["来"],
    "could": ["能", "可以"],
    "now": ["现在"],
    "than": ["比"],
    "like": ["喜欢", "像"],
    "other": ["其他的", "别的"],
    "how": ["怎样", "怎么", "多么"],
    "then": ["然后", "那时"],
    "its": ["它的"],
    "our": ["我们的"],
    "two": ["二", "两个"],
    "more": ["更多", "更"],
    "these": ["这些"],
    "want": ["想要", "要"],
    "way": ["方法", "路"],
    "look": ["看", "看起来"],
    "first": ["第一", "首先"],
    "also": ["也"],
    "new": ["新的"],
    "because": ["因为"],
    "day": ["一天", "日子", "白天"],
    "use": ["使用", "用"],
    "no": ["不", "没有"],
    "man": ["男人", "人"],
    "find": ["找到", "发现"],
    "here": ["这里"],
    "thing": ["东西", "事情"],
    "give": ["给"],
    "many": ["许多"],
    "well": ["好地", "健康的", "井"],
    "only": ["只", "仅仅", "唯一的"],
    "those": ["那些"],
    "tell": ["告诉"],
    "very": ["非常", "很"],
    "even": ["甚至", "更"],
    "back": ["回来", "后面", "背"],
    "any": ["任何", "一些"],
    "good": ["好的", "好"],
    "woman": ["女人", "妇女"],
    "through": ["穿过", "通过"],
    "us": ["我们"],
    "life": ["生活", "生命"],
    "child": ["孩子", "儿童"],
    "work": ["工作"],
    "down": ["向下", "下来"],
    "may": ["可以", "也许"],
    "after": ["在……之后"],
    "should": ["应该"],
    "call": ["打电话", "叫", "称呼"],
    "world": ["世界"],
    "over": ["结束", "在……上方"],
    "school": ["学校"],
    "still": ["仍然", "还是"],
    "try": ["尝试", "试"],
    "ask": ["问", "请求"],
    "need": ["需要"],
    "too": ["也", "太"],
    "feel": ["觉得", "感觉"],
    "three": ["三", "三个"],
    "state": ["状态", "州", "国家"],
    "never": ["从不", "绝不"],
    "become": ["变成", "成为"],
    "between": ["在……之间"],
    "high": ["高的"],
    "something": ["某事", "某物"],
    "really": ["真的", "非常"],
    "most": ["最", "大多数"],
    "another": ["另一个", "再一"],
    "much": ["许多", "很"],
    "family": ["家庭", "家人"],
    "own": ["自己的"],
    "leave": ["离开", "留下"],
    "put": ["放"],
    "old": ["老的", "旧的"],
    "while": ["当……时候", "一会儿", "虽然"],
    "mean": ["意思是", "意味着"],
    "keep": ["保持", "保存"],
    "student": ["学生"],
    "why": ["为什么"],
    "let": ["让"],
    "great": ["很好的", "大的"],
    "same": ["相同的", "一样的"],
    "big": ["大的"],
    "group": ["组", "群"],
    "begin": ["开始"],
    "seem": ["似乎", "好像"],
    "country": ["国家", "乡下"],
    "help": ["帮助"],
    "talk": ["说话", "谈话"],
    "where": ["哪里", "在哪里"],
    "turn": ["转", "变成", "轮流"],
    "problem": ["问题", "困难"],
    "every": ["每一个", "每个"],
    "start": ["开始"],
    "hand": ["手"],
    "might": ["也许", "可能"],
    "show": ["给……看", "展示"],
    "part": ["部分"],
    "against": ["反对", "靠着"],
    "place": ["地方"],
    "such": ["这样的"],
    "again": ["再", "又"],
    "few": ["很少", "几个"],
    "week": ["星期", "周"],
    "company": ["公司"],
    "each": ["每个"],
    "right": ["对的", "右边", "权利"],
    "hear": ["听见", "听到"],
    "question": ["问题"],
    "during": ["在……期间"],
    "play": ["玩", "打（球）", "演奏"],
    "government": ["政府"],
    "run": ["跑"],
    "small": ["小的"],
    "number": ["数字", "号码", "数量"],
    "off": ["离开", "关掉"],
    "always": ["总是"],
    "move": ["移动", "搬家"],
    "night": ["晚上", "夜晚"],
    "live": ["住", "生活", "活着"],
    "point": ["指", "点", "要点"],
    "believe": ["相信"],
    "hold": ["握住", "举行"],
    "today": ["今天"],
    "bring": ["带来"],
    "happen": ["发生"],
    "next": ["下一个", "接下来"],
    "without": ["没有"],
    "before": ["在……之前"],
    "large": ["大的"],
    "must": ["必须"],
    "home": ["家"],
    "under": ["在……下面"],
    "water": ["水"],
    "room": ["房间"],
    "write": ["写"],
    "mother": ["妈妈", "母亲"],
    "money": ["钱"],
    "story": ["故事"],
    "young": ["年轻的"],
    "fact": ["事实"],
    "month": ["月", "月份"],
    "different": ["不同的"],
    "lot": ["很多"],
    "study": ["学习"],
    "book": ["书"],
    "eye": ["眼睛"],
    "job": ["工作"],
    "word": ["单词", "词", "话"],
    "though": ["虽然"],
    "business": ["生意", "商业"],
    "four": ["四", "四个"],
    "side": ["一边", "旁边"],
    "light": ["灯", "光", "轻的"],
    "hard": ["困难的", "硬的", "努力地"],
    "watch": ["看", "手表"],
    "match": ["比赛", "火柴", "相配"],
    "rest": ["休息", "其余"],
    "present": ["礼物", "现在", "在场的"],
    "change": ["改变", "零钱"],
    "close": ["关", "近的"],
    "last": ["最后的", "上一个", "持续"],
    "kind": ["种类", "友好的"],
    "fine": ["好的", "晴朗的"],
    "long": ["长的"],
    "left": ["左边", "离开"],
    "letter": ["信", "字母"],
    "date": ["日期"],
    "train": ["火车", "训练"],
    "park": ["公园"],
    "spring": ["春天", "泉水"],
    "fall": ["落下", "秋天"],
    "patient": ["有耐心的", "病人"],
    "mind": ["介意", "头脑"],
    "matter": ["事情", "要紧"],
    "subject": ["学科", "主题"],
    "address": ["地址"],
    "cross": ["穿过"],
    "rock": ["岩石"],
    "pretty": ["漂亮的"],
    "miss": ["错过", "想念"],
    "once": ["一次", "曾经"],
    "since": ["自从", "既然"],
    "quite": ["相当", "很"],
    "enough": ["足够的", "够"],
    "often": ["经常", "常常"],
    "sometimes": ["有时"],
    "usually": ["通常"],
    "happy": ["高兴的", "快乐的"],
    "sad": ["难过的", "伤心的"],
    "angry": ["生气的"],
    "hungry": ["饿的"],
    "thirsty": ["渴的"],
    "tired": ["累的"],
    "afraid": ["害怕的"],
    "beautiful": ["漂亮的", "美丽的"],
    "careful": ["小心的"],
    "dangerous": ["危险的"],
    "difficult": ["困难的", "难的"],
    "easy": ["容易的"],
    "important": ["重要的"],
    "interesting": ["有趣的"],
    "possible": ["可能的"],
    "ready": ["准备好的"],
    "sorry": ["对不起", "抱歉的"],
    "sure": ["确定的", "当然"],
    "useful": ["有用的"],
    "wonderful": ["极好的"],
    "fast": ["快的", "迅速的"],
    "quick": ["快的", "迅速的"],
    "slowly": ["慢慢地"],
    "quickly": ["很快地", "迅速地"],
    "early": ["早的", "早地"],
    "late": ["晚的", "迟到"],
    "open": ["打开", "开着的"],
    "stop": ["停止"],
    "finish": ["完成", "结束"],
    "remember": ["记得"],
    "forget": ["忘记"],
    "learn": ["学习", "学会"],
    "teach": ["教"],
    "read": ["读"],
    "listen": ["听"],
    "speak": ["说", "讲"],
    "buy": ["买"],
    "sell": ["卖"],
    "pay": ["付钱", "支付"],
    "spend": ["花费", "度过"],
    "cost": ["花费", "价钱"],
    "carry": ["拿", "搬运"],
    "catch": ["抓住", "赶上"],
    "choose": ["选择"],
    "decide": ["决定"],
    "enjoy": ["喜欢", "享受"],
    "hope": ["希望"],
    "wish": ["希望", "祝"],
    "agree": ["同意"],
    "answer": ["回答", "答案"],
    "meet": ["遇见", "见面"],
    "visit": ["参观", "拜访"],
    "travel": ["旅行"],
    "arrive": ["到达"],
    "return": ["回来", "归还"],
    "join": ["参加", "加入"],
    "win": ["赢"],
    "lose": ["丢失", "输"],
    "build": ["建造"],
    "grow": ["生长", "种植"],
    "cook": ["做饭", "厨师"],
    "wash": ["洗"],
    "clean": ["干净的", "打扫"],
    "dirty": ["脏的"],
    "full": ["满的"],
    "empty": ["空的"],
    "free": ["空闲的", "免费的", "自由的"],
    "busy": ["忙的"],
    "cheap": ["便宜的"],
    "expensive": ["贵的", "昂贵的"],
    "rich": ["富有的", "丰富的"],
    "poor": ["穷的", "差的"],
    "strong": ["强壮的", "强的"],
    "weak": ["弱的"],
    "healthy": ["健康的"],
    "ill": ["生病的"],
    "sick": ["生病的"],
    "hot": ["热的"],
    "cold": ["冷的", "感冒"],
    "warm": ["温暖的"],
    "cool": ["凉快的"],
    "wet": ["湿的"],
    "dry": ["干的"],
    "quiet": ["安静的"],
    "safe": ["安全的"],
    "true": ["真的", "对的"],
    "wrong": ["错误的"],
    "able": ["能够"],
    "above": ["在……上面"],
    "across": ["穿过", "在对面"],
    "along": ["沿着"],
    "among": ["在……之中"],
    "around": ["在周围", "大约"],
    "behind": ["在……后面"],
    "below": ["在……下面"],
    "beside": ["在……旁边"],
    "except": ["除了"],
    "inside": ["在里面"],
    "outside": ["在外面"],
    "until": ["直到"],
    "hello": ["你好"],
    "hi": ["嗨", "你好"],
    "yes": ["是的", "对"],
    "please": ["请"],
    "thank": ["谢谢"],
    "thanks": ["谢谢"],
    "friend": ["朋友"],
    "teacher": ["老师"],
    "class": ["课", "班级"],
    "english": ["英语", "英国的"],
    "china": ["中国"],
    "chinese": ["中文", "中国的", "中国人"],
    "food": ["食物"],
    "father": ["爸爸", "父亲"],
    "sister": ["姐姐", "妹妹"],
    "brother": ["哥哥", "弟弟"],
    "parent": ["父或母"],
    "parents": ["父母"],
    "weather": ["天气"],
    "rain": ["下雨", "雨"],
    "sun": ["太阳"],
    "moon": ["月亮"],
    "star": ["星星"],
    "red": ["红色的"],
    "blue": ["蓝色的"],
    "green": ["绿色的"],
    "yellow": ["黄色的"],
    "black": ["黑色的"],
    "white": ["白色的"],
    "morning": ["早上", "上午"],
    "afternoon": ["下午"],
    "evening": ["晚上"],
    "breakfast": ["早餐"],
    "lunch": ["午餐"],
    "dinner": ["晚餐"],
    "sport": ["运动"],
    "football": ["足球"],
    "basketball": ["篮球"],
    "music": ["音乐"],
    "song": ["歌曲"],
    "computer": ["电脑"],
    "phone": ["电话"],
    "clock": ["钟"],
    "minute": ["分钟"],
    "hour": ["小时"],
    "yesterday": ["昨天"],
    "tomorrow": ["明天"],
    "city": ["城市"],
    "house": ["房子"],
    "apple": ["苹果"],
    "cat": ["猫"],
    "dog": ["狗"],
    "bus": ["公共汽车"],
    "car": ["小汽车"],
    "hospital": ["医院"],
    "doctor": ["医生"],
    "love": ["爱", "喜欢"],
    "name": ["名字"],
    "boy": ["男孩"],
    "girl": ["女孩"],
    "mr": ["先生"],
    "mrs": ["太太", "夫人"],
    "ok": ["好的"],
    "okay": ["好的"],
    "tv": ["电视"],
    "television": ["电视"],
    "film": ["电影"],
    "movie": ["电影"],
    "game": ["游戏"],
    "ball": ["球"],
    "tree": ["树"],
    "flower": ["花"],
    "animal": ["动物"],
    "bird": ["鸟"],
    "fish": ["鱼", "钓鱼"],
    "milk": ["牛奶"],
    "rice": ["米饭", "米"],
    "bread": ["面包"],
    "egg": ["鸡蛋"],
    "fruit": ["水果"],
    "vegetable": ["蔬菜"],
    "clothes": ["衣服"],
    "shirt": ["衬衫"],
    "shoe": ["鞋"],
    "shoes": ["鞋"],
    "bag": ["包", "书包"],
    "pen": ["钢笔"],
    "pencil": ["铅笔"],
    "paper": ["纸"],
    "desk": ["书桌"],
    "table": ["桌子"],
    "chair": ["椅子"],
    "door": ["门"],
    "window": ["窗户"],
    "photo": ["照片"],
    "picture": ["图画", "照片"],
    "map": ["地图"],
    "key": ["钥匙", "关键"],
    "idea": ["主意", "想法"],
    "dream": ["梦", "梦想"],
    "holiday": ["假日"],
    "vacation": ["假期"],
    "birthday": ["生日"],
    "party": ["聚会"],
    "gift": ["礼物"],
    "present": ["礼物", "现在", "在场的"],
    "lesson": ["课"],
    "homework": ["家庭作业"],
    "exam": ["考试"],
    "test": ["测试", "考试"],
    "grade": ["成绩", "年级"],
    "library": ["图书馆"],
    "classroom": ["教室"],
    "classmate": ["同学"],
    "dictionary": ["词典"],
    "sentence": ["句子"],
    "language": ["语言"],
    "practice": ["练习"],
    "repeat": ["重复"],
    "spell": ["拼写"],
    "meaning": ["意思"],
    "understand": ["理解", "明白", "懂"],
    "wrong": ["错误的"],
    "correct": ["正确的", "改正"],
    "true": ["真的", "对的"],
    "false": ["错误的", "假的"],
    "both": ["两者都"],
    "either": ["两者之一", "也"],
    "neither": ["两者都不"],
    "none": ["没有一个"],
    "nothing": ["没有什么"],
    "everything": ["一切", "所有事物"],
    "everyone": ["每个人"],
    "everybody": ["每个人"],
    "someone": ["某人"],
    "somebody": ["某人"],
    "anyone": ["任何人"],
    "anybody": ["任何人"],
    "anything": ["任何事物"],
    "another": ["另一个"],
    "other": ["其他的"],
    "others": ["其他人", "其他的"],
    "few": ["很少"],
    "little": ["小的", "很少"],
    "less": ["更少"],
    "least": ["最少"],
    "better": ["更好的"],
    "best": ["最好的"],
    "worse": ["更差的"],
    "worst": ["最差的"],
    "many": ["许多"],
    "much": ["许多"],
    "more": ["更多"],
    "most": ["最"],
    "too": ["也", "太"],
    "also": ["也"],
    "either": ["也（不）", "任一"],
    "ago": ["以前"],
    "already": ["已经"],
    "yet": ["还", "已经"],
    "just": ["刚刚", "只是"],
    "still": ["仍然", "还"],
    "almost": ["几乎"],
    "together": ["一起"],
    "away": ["离开"],
    "far": ["远的"],
    "near": ["近的"],
    "here": ["这里"],
    "there": ["那里"],
    "where": ["哪里"],
    "why": ["为什么"],
    "because": ["因为"],
    "so": ["所以"],
    "if": ["如果"],
    "when": ["当……时候", "什么时候"],
    "while": ["当……时候", "一会儿"],
    "before": ["在……之前"],
    "after": ["在……之后"],
    "during": ["在……期间"],
    "until": ["直到"],
    "since": ["自从"],
    "although": ["虽然"],
    "though": ["虽然"],
    "however": ["然而"],
    "maybe": ["也许"],
    "perhaps": ["也许"],
    "probably": ["很可能"],
    "of course": ["当然"],
    "course": ["课程", "过程"],
    "excuse": ["原谅", "借口"],
    "pardon": ["原谅"],
    "welcome": ["欢迎"],
    "goodbye": ["再见"],
    "bye": ["再见"],
}

# Extra accepted answers that are not always worth showing.
ALIASES: dict[str, list[str]] = {
    "happy": ["开心", "快乐", "幸福", "高兴"],
    "sad": ["悲伤", "伤心", "难过", "不开心"],
    "angry": ["愤怒", "气愤"],
    "hungry": ["饥饿", "饿"],
    "thirsty": ["口渴", "渴"],
    "tired": ["疲劳", "疲倦", "累"],
    "afraid": ["恐惧", "怕"],
    "beautiful": ["美", "好看", "漂亮", "美丽"],
    "pretty": ["好看", "漂亮", "美丽"],
    "fast": ["快", "迅速", "快速"],
    "quick": ["快", "迅速", "快速"],
    "quickly": ["很快", "迅速", "快速地"],
    "slowly": ["慢", "缓慢地"],
    "big": ["巨大"],
    "large": ["巨大", "很大"],
    "small": ["微小"],
    "little": ["小", "一点儿"],
    "good": ["良好", "不错", "优秀"],
    "great": ["极好", "很棒", "伟大"],
    "bad": ["坏", "不好", "糟糕"],
    "difficult": ["难", "困难"],
    "hard": ["难", "困难", "努力"],
    "easy": ["简单"],
    "begin": ["起始"],
    "start": ["开头"],
    "finish": ["结束", "做完"],
    "end": ["结束", "末尾"],
    "listen": ["聆听"],
    "speak": ["讲话"],
    "say": ["讲"],
    "talk": ["聊天", "交谈"],
    "tell": ["讲述"],
    "watch": ["观看"],
    "see": ["见到", "看见"],
    "look": ["瞧", "看上去"],
    "buy": ["购买"],
    "cheap": ["廉价"],
    "expensive": ["贵", "花钱多"],
    "always": ["一直"],
    "often": ["常常", "时常"],
    "sometimes": ["有时候"],
    "never": ["决不"],
    "usually": ["平常"],
    "enjoy": ["喜爱"],
    "love": ["热爱", "爱"],
    "want": ["希望"],
    "need": ["须要"],
    "help": ["帮忙"],
    "learn": ["学"],
    "study": ["读书"],
    "remember": ["记住", "想起"],
    "forget": ["忘掉", "忘"],
    "understand": ["懂", "明白"],
    "child": ["小孩"],
    "children": ["孩子们", "小朋友"],
    "people": ["人们", "人民"],
    "friend": ["友人"],
    "teacher": ["教师"],
    "student": ["同学"],
    "book": ["书本", "书籍"],
    "word": ["字"],
    "time": ["时候"],
    "day": ["日"],
    "year": ["岁"],
    "week": ["礼拜"],
    "morning": ["早晨", "上午"],
    "afternoon": ["午后"],
    "evening": ["傍晚"],
    "night": ["夜里", "夜晚"],
    "today": ["今日"],
    "tomorrow": ["明日"],
    "yesterday": ["昨日"],
    "father": ["父亲", "爸爸"],
    "mother": ["母亲", "妈妈"],
    "parents": ["爸妈", "父母亲"],
    "brother": ["兄弟", "哥", "弟"],
    "sister": ["姐妹", "姐", "妹"],
    "man": ["男士"],
    "woman": ["女士"],
    "boy": ["男生"],
    "girl": ["女生"],
    "food": ["食品"],
    "money": ["金钱"],
    "city": ["都市"],
    "country": ["农村"],
    "home": ["家里"],
    "house": ["住宅", "房子"],
    "family": ["家里人"],
    "job": ["职业"],
    "work": ["干活", "劳动"],
    "place": ["地点"],
    "way": ["方式", "道路"],
    "thing": ["事物"],
    "problem": ["难题"],
    "question": ["提问"],
    "answer": ["答复"],
    "idea": ["想法", "念头"],
    "story": ["小说"],
    "film": ["影片"],
    "movie": ["影片"],
    "phone": ["手机"],
    "computer": ["计算机"],
    "bus": ["公交", "巴士", "公交车"],
    "car": ["汽车", "轿车"],
    "bike": ["自行车"],
    "bicycle": ["自行车"],
    "train": ["列车"],
    "doctor": ["大夫"],
    "hospital": ["医院"],
    "school": ["学堂"],
    "class": ["课堂"],
    "homework": ["作业"],
    "test": ["测验"],
    "exam": ["测验"],
    "holiday": ["假期"],
    "vacation": ["假日"],
    "gift": ["礼品"],
    "photo": ["相片"],
    "picture": ["图片"],
    "bag": ["袋子"],
    "pen": ["笔"],
    "desk": ["课桌"],
    "window": ["窗"],
    "door": ["门"],
    "clothes": ["服装"],
    "shoes": ["鞋子"],
    "shirt": ["衬衣"],
    "t-shirt": ["T恤", "体恤"],
    "tv": ["电视机"],
    "television": ["电视机"],
    "football": ["美式足球"],
    "soccer": ["足球"],
    "basketball": ["篮球"],
    "apple": ["苹果"],
    "orange": ["橙子", "橙色的", "橘子"],
    "banana": ["香蕉"],
    "water": ["水"],
    "milk": ["奶"],
    "rice": ["大米"],
    "bread": ["面包"],
    "egg": ["蛋"],
    "fruit": ["水果"],
    "vegetable": ["菜"],
    "cat": ["猫咪"],
    "dog": ["狗狗"],
    "bird": ["鸟类"],
    "fish": ["鱼肉"],
    "sun": ["日"],
    "moon": ["月球"],
    "star": ["星"],
    "rain": ["降雨"],
    "snow": ["雪", "下雪"],
    "wind": ["风"],
    "cloud": ["云"],
    "weather": ["气候"],
    "hot": ["烫"],
    "cold": ["寒冷", "着凉"],
    "warm": ["暖和"],
    "cool": ["酷", "凉"],
    "ill": ["不舒服", "病了"],
    "sick": ["不舒服", "病了"],
    "healthy": ["健康"],
    "strong": ["坚强"],
    "weak": ["虚弱"],
    "clever": ["聪明"],
    "smart": ["聪明", "机灵"],
    "bright": ["明亮的", "聪明的"],
    "funny": ["好笑的", "滑稽的"],
    "interesting": ["有意思"],
    "boring": ["无聊的", "乏味的"],
    "afraid": ["担心"],
    "worried": ["担心的", "发愁的"],
    "excited": ["兴奋的", "激动的"],
    "surprised": ["惊讶的", "吃惊的"],
    "angry": ["恼火的"],
    "glad": ["高兴", "乐意"],
    "pleased": ["高兴的", "满意的"],
    "sorry": ["遗憾", "难过"],
    "sure": ["确信", "一定"],
    "able": ["可以", "会"],
    "free": ["有空", "自由"],
    "busy": ["忙碌"],
    "ready": ["乐意"],
    "careful": ["仔细"],
    "careless": ["粗心的"],
    "dangerous": ["不安全"],
    "safe": ["平安的"],
    "clean": ["清洁的"],
    "dirty": ["不干净"],
    "full": ["饱的"],
    "empty": ["空空的"],
    "quiet": ["静"],
    "loud": ["大声的", "响的"],
    "quick": ["敏捷"],
    "slow": ["慢的"],
    "early": ["提早"],
    "late": ["迟"],
    "open": ["开"],
    "close": ["关闭", "闭上", "靠近"],
    "shut": ["关上", "闭"],
    "start": ["出发"],
    "stop": ["停"],
    "leave": ["出发"],
    "arrive": ["抵达"],
    "return": ["返回", "还"],
    "bring": ["拿来"],
    "take": ["取", "乘"],
    "carry": ["携带", "搬"],
    "get": ["拿", "变得"],
    "give": ["交给"],
    "put": ["摆"],
    "keep": ["继续"],
    "hold": ["举办", "拿着"],
    "make": ["制造", "使得"],
    "do": ["干"],
    "go": ["走"],
    "come": ["来到"],
    "run": ["跑步"],
    "walk": ["走路", "步行"],
    "sit": ["坐"],
    "stand": ["站"],
    "sleep": ["睡觉"],
    "wake": ["醒来", "叫醒"],
    "eat": ["吃"],
    "drink": ["喝"],
    "cook": ["烹饪", "烧菜"],
    "wash": ["洗漱"],
    "wear": ["穿", "戴"],
    "dress": ["连衣裙", "穿衣服"],
    "read": ["阅读"],
    "write": ["书写"],
    "draw": ["画"],
    "sing": ["唱歌"],
    "dance": ["跳舞"],
    "play": ["玩耍", "播放"],
    "swim": ["游泳"],
    "fly": ["飞", "飞行"],
    "drive": ["开车", "驾驶"],
    "ride": ["骑"],
    "travel": ["旅游"],
    "visit": ["看望"],
    "meet": ["满足", "开会"],
    "join": ["连接"],
    "help": ["援助"],
    "teach": ["教书"],
    "learn": ["学会"],
    "study": ["研究"],
    "practice": ["实践", "操练"],
    "try": ["努力", "试用"],
    "use": ["利用"],
    "need": ["必要"],
    "hope": ["但愿"],
    "wish": ["祝愿"],
    "decide": ["下决心"],
    "choose": ["挑选"],
    "agree": ["赞成"],
    "disagree": ["不同意"],
    "believe": ["认为"],
    "know": ["了解", "懂得"],
    "think": ["思考", "觉得"],
    "feel": ["摸起来", "感到"],
    "seem": ["看上去"],
    "become": ["变得"],
    "grow": ["成长", "变得"],
    "change": ["变化", "更换"],
    "turn": ["转弯"],
    "move": ["搬", "感动"],
    "live": ["居住"],
    "stay": ["停留", "待"],
    "wait": ["等待"],
    "hurry": ["赶快", "匆忙"],
    "happen": ["碰巧"],
    "mean": ["意思", "意味"],
    "call": ["呼唤", "称为"],
    "ask": ["要求", "请"],
    "answer": ["解答"],
    "tell": ["辨别"],
    "say": ["说道"],
    "speak": ["发言"],
    "talk": ["谈论"],
    "listen": ["听从"],
    "hear": ["听说"],
    "look": ["查找"],
    "watch": ["注视"],
    "see": ["明白", "看"],
    "find": ["觉得"],
    "lose": ["输掉", "丢失"],
    "win": ["获胜", "赢得"],
    "buy": ["买下"],
    "sell": ["出售"],
    "pay": ["付款", "工资"],
    "spend": ["花", "度过"],
    "cost": ["值", "费用"],
    "save": ["节约", "救", "节省", "保存"],
    "build": ["建立"],
    "break": ["打破", "休息", "损坏"],
    "cut": ["切", "割"],
    "hit": ["打", "碰撞"],
    "hurt": ["受伤", "疼痛"],
    "kill": ["杀死"],
    "die": ["死"],
    "born": ["出生"],
    "birth": ["出生"],
    "marry": ["结婚"],
    "love": ["喜爱"],
    "like": ["喜爱"],
    "hate": ["讨厌", "恨", "不愿意"],
    "enjoy": ["欣赏", "享有"],
    "prefer": ["更喜欢"],
    "miss": ["思念", "错过", "小姐"],
    "worry": ["担心", "烦恼"],
    "fear": ["害怕", "恐惧"],
    "smile": ["微笑"],
    "laugh": ["笑", "大笑"],
    "cry": ["哭", "喊"],
    "shout": ["喊", "叫"],
    "quiet": ["轻声"],
    "noise": ["噪音", "响声"],
    "sound": ["声音", "听起来"],
    "voice": ["嗓音", "声音"],
    "music": ["乐曲"],
    "song": ["歌"],
    "sport": ["体育"],
    "game": ["比赛"],
    "team": ["队", "组"],
    "player": ["选手", "运动员"],
    "match": ["匹配"],
    "race": ["赛跑", "种族"],
    "win": ["胜利"],
    "club": ["俱乐部"],
    "holiday": ["节日"],
    "festival": ["节日"],
    "birthday": ["诞辰"],
    "party": ["政党", "派对"],
    "meeting": ["会议"],
    "trip": ["旅行"],
    "journey": ["旅程"],
    "travel": ["游历"],
    "way": ["方向"],
    "road": ["路", "道路"],
    "street": ["街", "街道"],
    "station": ["车站"],
    "airport": ["机场"],
    "hotel": ["旅馆", "酒店"],
    "restaurant": ["餐馆", "饭店"],
    "shop": ["商店", "购物"],
    "store": ["商店", "储存"],
    "market": ["市场"],
    "bank": ["银行", "岸"],
    "post": ["邮寄", "邮政", "帖子"],
    "office": ["办公室"],
    "factory": ["工厂"],
    "farm": ["农场"],
    "village": ["村庄", "乡村"],
    "town": ["城镇"],
    "city": ["都市"],
    "capital": ["首都", "大写"],
    "country": ["乡村"],
    "world": ["世间"],
    "earth": ["地球", "泥土"],
    "map": ["图"],
    "river": ["河"],
    "lake": ["湖"],
    "sea": ["海"],
    "mountain": ["山"],
    "hill": ["小山"],
    "island": ["岛"],
    "forest": ["森林"],
    "field": ["田地", "领域"],
    "garden": ["花园"],
    "park": ["停车"],
    "zoo": ["动物园"],
    "museum": ["博物馆"],
    "cinema": ["电影院"],
    "theatre": ["剧院"],
    "theater": ["剧院"],
    "hospital": ["病院"],
    "school": ["上学"],
    "university": ["大学"],
    "college": ["学院", "大学"],
    "library": ["图书室"],
    "classroom": ["课堂"],
    "lesson": ["功课"],
    "subject": ["科目"],
    "math": ["数学"],
    "maths": ["数学"],
    "chinese": ["汉语", "语文"],
    "history": ["历史"],
    "science": ["科学"],
    "art": ["艺术", "美术"],
    "music": ["音乐课"],
    "pe": ["体育"],
    "sport": ["体育运动"],
    "homework": ["功课"],
    "exercise": ["练习", "锻炼"],
    "practice": ["练习"],
    "exam": ["考试"],
    "mark": ["分数", "标记"],
    "score": ["得分", "分数"],
    "grade": ["等级", "年级"],
    "result": ["结果"],
    "mistake": ["错误"],
    "error": ["错误"],
    "example": ["例子", "榜样"],
    "sentence": ["句"],
    "paragraph": ["段落"],
    "passage": ["文章", "段落"],
    "article": ["文章"],
    "text": ["课文", "文本"],
    "title": ["标题", "题目"],
    "topic": ["话题", "题目"],
    "question": ["疑问"],
    "answer": ["答案"],
    "meaning": ["含义", "意义"],
    "spell": ["拼"],
    "pronounce": ["发音"],
    "pronunciation": ["发音", "读音"],
    "grammar": ["语法"],
    "vocabulary": ["词汇"],
    "dictionary": ["字典"],
    "page": ["页"],
    "line": ["行", "线"],
    "letter": ["字母"],
    "word": ["话语"],
    "name": ["姓名", "名称"],
    "age": ["年龄", "时代"],
    "birthday": ["出生日期"],
    "address": ["住址"],
    "number": ["数目"],
    "telephone": ["电话"],
    "phone": ["电话机"],
    "computer": ["电脑"],
    "internet": ["互联网", "网络"],
    "email": ["电子邮件"],
    "message": ["消息", "信息"],
    "news": ["新闻", "消息"],
    "information": ["信息"],
    "photo": ["照片"],
    "picture": ["画"],
    "camera": ["相机", "照相机"],
    "radio": ["收音机"],
    "video": ["视频"],
    "program": ["节目", "程序"],
    "programme": ["节目"],
    "show": ["演出", "表明"],
    "movie": ["电影"],
    "film": ["胶卷"],
    "ticket": ["票"],
    "seat": ["座位"],
    "card": ["卡片", "名片"],
    "money": ["钞票"],
    "dollar": ["美元"],
    "yuan": ["元"],
    "price": ["价格"],
    "cheap": ["低廉"],
    "expensive": ["贵"],
    "free": ["自由的"],
    "pay": ["付"],
    "buy": ["购买"],
    "sell": ["卖出"],
    "shop": ["买东西"],
    "customer": ["顾客"],
    "menu": ["菜单"],
    "bill": ["账单", "钞票"],
    "order": ["点菜", "命令", "顺序"],
    "delicious": ["好吃的", "美味的"],
    "hungry": ["饥饿的"],
    "thirsty": ["渴"],
    "breakfast": ["早饭"],
    "lunch": ["午饭"],
    "dinner": ["晚饭", "正餐"],
    "meal": ["一餐", "饭"],
    "food": ["食品"],
    "drink": ["饮料"],
    "tea": ["茶"],
    "coffee": ["咖啡"],
    "juice": ["果汁"],
    "water": ["浇水"],
    "milk": ["乳"],
    "cake": ["蛋糕"],
    "candy": ["糖果"],
    "chocolate": ["巧克力"],
    "sugar": ["糖"],
    "salt": ["盐"],
    "meat": ["肉"],
    "chicken": ["鸡", "鸡肉"],
    "beef": ["牛肉"],
    "fish": ["鱼"],
    "rice": ["米饭"],
    "noodle": ["面条"],
    "noodles": ["面条"],
    "dumpling": ["饺子"],
    "soup": ["汤"],
    "vegetable": ["青菜"],
    "potato": ["土豆", "马铃薯"],
    "tomato": ["西红柿", "番茄"],
    "apple": ["苹果"],
    "banana": ["香蕉"],
    "orange": ["橘子", "橙"],
    "fruit": ["果实"],
    "ice": ["冰"],
    "cream": ["奶油"],
    "ice cream": ["冰淇淋", "冰激凌"],
    "breakfast": ["早餐"],
    "kitchen": ["厨房"],
    "bowl": ["碗"],
    "plate": ["盘子"],
    "cup": ["杯子"],
    "glass": ["玻璃杯", "玻璃"],
    "bottle": ["瓶子"],
    "knife": ["刀"],
    "fork": ["叉"],
    "spoon": ["勺", "勺子"],
    "chopsticks": ["筷子"],
    "cook": ["烹调"],
    "smell": ["闻", "气味"],
    "taste": ["尝", "味道"],
    "sweet": ["甜的"],
    "sour": ["酸的"],
    "bitter": ["苦的"],
    "hot": ["辣的"],
    "fresh": ["新鲜的"],
    "healthy": ["有益健康的"],
    "body": ["身体"],
    "head": ["头"],
    "face": ["脸"],
    "eye": ["眼"],
    "ear": ["耳朵"],
    "nose": ["鼻子"],
    "mouth": ["嘴", "口"],
    "tooth": ["牙齿"],
    "teeth": ["牙齿"],
    "hair": ["头发"],
    "neck": ["脖子"],
    "arm": ["手臂", "胳膊"],
    "hand": ["手"],
    "finger": ["手指"],
    "leg": ["腿"],
    "foot": ["脚", "英尺"],
    "feet": ["脚"],
    "back": ["背部"],
    "heart": ["心", "心脏"],
    "health": ["健康"],
    "illness": ["疾病"],
    "cold": ["寒冷"],
    "fever": ["发烧"],
    "cough": ["咳嗽"],
    "headache": ["头痛"],
    "pain": ["疼痛", "痛"],
    "medicine": ["药"],
    "hospital": ["医院"],
    "doctor": ["大夫"],
    "nurse": ["护士"],
    "ill": ["有病的"],
    "sick": ["恶心的"],
    "tired": ["累"],
    "rest": ["休息"],
    "sleep": ["睡眠"],
    "exercise": ["运动"],
    "family": ["家庭"],
    "parent": ["家长"],
    "parents": ["双亲"],
    "father": ["父亲"],
    "mother": ["母亲"],
    "dad": ["爸爸"],
    "mom": ["妈妈"],
    "mum": ["妈妈"],
    "son": ["儿子"],
    "daughter": ["女儿"],
    "brother": ["兄弟"],
    "sister": ["姐妹"],
    "uncle": ["叔叔", "伯伯", "舅舅"],
    "aunt": ["阿姨", "姑姑", "伯母"],
    "cousin": ["堂表兄弟", "堂表姐妹", "表亲"],
    "grandparent": ["祖父母"],
    "grandfather": ["爷爷", "外公", "祖父"],
    "grandmother": ["奶奶", "外婆", "祖母"],
    "husband": ["丈夫"],
    "wife": ["妻子"],
    "baby": ["婴儿"],
    "child": ["儿童"],
    "kid": ["小孩"],
    "boy": ["男孩"],
    "girl": ["女孩"],
    "man": ["人"],
    "woman": ["女性"],
    "person": ["人"],
    "people": ["人民"],
    "friend": ["友人"],
    "visitor": ["游客", "来访者"],
    "neighbor": ["邻居"],
    "neighbour": ["邻居"],
    "stranger": ["陌生人"],
    "job": ["活儿"],
    "worker": ["工人"],
    "farmer": ["农民"],
    "driver": ["司机"],
    "police": ["警察"],
    "policeman": ["男警察"],
    "officer": ["官员", "军官"],
    "king": ["国王"],
    "queen": ["女王"],
    "president": ["总统", "主席"],
    "manager": ["经理"],
    "boss": ["老板"],
    "star": ["明星"],
    "actor": ["演员"],
    "singer": ["歌手"],
    "artist": ["艺术家"],
    "scientist": ["科学家"],
    "inventor": ["发明家"],
    "writer": ["作家"],
    "reporter": ["记者"],
    "pilot": ["飞行员"],
    "soldier": ["士兵"],
    "hero": ["英雄"],
    "member": ["成员"],
    "group": ["小组"],
    "team": ["队伍"],
    "class": ["班"],
    "grade": ["年级"],
    "school": ["学校"],
    "student": ["生徒"],  # removed below if unwanted
}

# The line above accidentally adds a bad alias. Remove it explicitly.
ALIASES["student"] = ["同学", "学员"]
ALIASES["school"] = ["学堂"]
ALIASES["football"] = []
ALIASES["meet"] = ["开会", "见面", "碰头"]

EXAMPLES: dict[str, tuple[str, str]] = {
    "the": ("The book is new.", "这本书是新的。"),
    "be": ("I am a student.", "我是一名学生。"),
    "and": ("You and I are friends.", "你和我是朋友。"),
    "of": ("a cup of tea", "一杯茶"),
    "a": ("This is a pen.", "这是一支钢笔。"),
    "in": ("The cat is in the box.", "猫在盒子里。"),
    "to": ("I go to school.", "我去上学。"),
    "have": ("I have a sister.", "我有一个姐姐。"),
    "it": ("It is a dog.", "它是一只狗。"),
    "i": ("I like apples.", "我喜欢苹果。"),
    "that": ("That bag is mine.", "那个包是我的。"),
    "for": ("This gift is for you.", "这份礼物是给你的。"),
    "you": ("You are kind.", "你人很好。"),
    "he": ("He is my brother.", "他是我哥哥。"),
    "with": ("I go with my mom.", "我和妈妈一起去。"),
    "on": ("The book is on the desk.", "书在书桌上。"),
    "do": ("I do my homework.", "我做作业。"),
    "say": ("Please say it again.", "请再说一遍。"),
    "this": ("This is my school.", "这是我的学校。"),
    "they": ("They are students.", "他们是学生。"),
    "at": ("I get up at seven.", "我七点起床。"),
    "but": ("I am tired but happy.", "我很累，但很高兴。"),
    "we": ("We play football.", "我们踢足球。"),
    "his": ("His name is Tom.", "他叫汤姆。"),
    "from": ("I am from Shanghai.", "我来自上海。"),
    "not": ("It is not cold.", "天气不冷。"),
    "by": ("I go by bus.", "我坐公交车去。"),
    "she": ("She likes music.", "她喜欢音乐。"),
    "or": ("Tea or coffee?", "茶还是咖啡？"),
    "as": ("She works as a nurse.", "她是护士。"),
    "what": ("What is this?", "这是什么？"),
    "go": ("I go home at five.", "我五点回家。"),
    "their": ("Their room is big.", "他们的房间很大。"),
    "can": ("I can swim.", "我会游泳。"),
    "who": ("Who is she?", "她是谁？"),
    "get": ("I get up early.", "我起得很早。"),
    "if": ("Call me if you need help.", "需要帮忙就打电话给我。"),
    "would": ("I would like some water.", "我想要一些水。"),
    "her": ("Her bag is red.", "她的包是红的。"),
    "all": ("All students are here.", "学生都到了。"),
    "my": ("My name is Li Ming.", "我叫李明。"),
    "make": ("Mom can make cakes.", "妈妈会做蛋糕。"),
    "about": ("This book is about animals.", "这本书讲动物。"),
    "know": ("I know the answer.", "我知道答案。"),
    "will": ("I will call you.", "我会给你打电话。"),
    "up": ("Please stand up.", "请站起来。"),
    "one": ("I have one brother.", "我有一个哥哥。"),
    "time": ("What time is it?", "现在几点？"),
    "there": ("The park is over there.", "公园在那边。"),
    "year": ("A year has 12 months.", "一年有 12 个月。"),
    "so": ("I was ill, so I rested.", "我病了，所以休息了。"),
    "think": ("I think you are right.", "我觉得你是对的。"),
    "when": ("When do you get up?", "你什么时候起床？"),
    "which": ("Which one do you want?", "你要哪一个？"),
    "them": ("I can help them.", "我能帮助他们。"),
    "some": ("I want some water.", "我想要一些水。"),
    "me": ("Please help me.", "请帮帮我。"),
    "people": ("Many people walk here.", "很多人在这里走路。"),
    "take": ("Take your book.", "带上你的书。"),
    "out": ("Let's go out.", "我们出去吧。"),
    "into": ("Come into the room.", "进房间来。"),
    "just": ("I just arrived.", "我刚到。"),
    "see": ("I can see a bird.", "我能看见一只鸟。"),
    "him": ("I know him.", "我认识他。"),
    "your": ("Is this your pen?", "这是你的钢笔吗？"),
    "come": ("Please come here.", "请到这里来。"),
    "could": ("Could you help me?", "你能帮我吗？"),
    "now": ("I am busy now.", "我现在很忙。"),
    "than": ("She is taller than me.", "她比我高。"),
    "like": ("I like apples.", "我喜欢苹果。"),
    "other": ("Any other question?", "还有别的问题吗？"),
    "how": ("How are you?", "你好吗？"),
    "then": ("Eat first, then rest.", "先吃饭，然后休息。"),
    "its": ("The dog likes its ball.", "狗喜欢它的球。"),
    "our": ("Our teacher is kind.", "我们的老师很和气。"),
    "two": ("I have two pens.", "我有两支笔。"),
    "more": ("I need more time.", "我需要更多时间。"),
    "these": ("These books are new.", "这些书是新的。"),
    "want": ("I want a rest.", "我想休息一下。"),
    "way": ("This is the way home.", "这是回家的路。"),
    "look": ("Look at the board.", "看黑板。"),
    "first": ("She comes first.", "她得了第一。"),
    "also": ("I also like music.", "我也喜欢音乐。"),
    "new": ("This bag is new.", "这个包是新的。"),
    "because": ("I stay home because I am ill.", "因为生病了，我待在家里。"),
    "day": ("Have a good day.", "祝你今天顺利。"),
    "use": ("May I use your pen?", "我可以用你的笔吗？"),
    "no": ("No, thank you.", "不，谢谢。"),
    "man": ("That man is a doctor.", "那位男士是医生。"),
    "find": ("I can't find my key.", "我找不到钥匙。"),
    "here": ("Please come here.", "请到这里来。"),
    "thing": ("What is this thing?", "这是什么东西？"),
    "give": ("Give me the book.", "把书给我。"),
    "many": ("Many students walk.", "很多学生走路来。"),
    "well": ("She sings well.", "她唱得很好。"),
    "only": ("I only have one pen.", "我只有一支笔。"),
    "those": ("Those shoes are old.", "那些鞋旧了。"),
    "tell": ("Tell me your name.", "告诉我你的名字。"),
    "very": ("The soup is very hot.", "汤很烫。"),
    "even": ("Even I can do it.", "连我也会做。"),
    "back": ("I will come back.", "我会回来。"),
    "any": ("Do you have any water?", "你有水吗？"),
    "good": ("Good morning.", "早上好。"),
    "woman": ("That woman is a teacher.", "那位女士是老师。"),
    "through": ("We walk through the park.", "我们穿过公园。"),
    "us": ("The teacher helps us.", "老师帮助我们。"),
    "life": ("School life is busy.", "学校生活很忙。"),
    "child": ("The child is six.", "这个孩子六岁。"),
    "work": ("My father works hard.", "我爸爸工作很努力。"),
    "down": ("Please sit down.", "请坐。"),
    "may": ("May I come in?", "我可以进来吗？"),
    "after": ("We play after school.", "我们放学后玩。"),
    "should": ("You should sleep early.", "你应该早点睡。"),
    "call": ("Please call me tonight.", "请今晚给我打电话。"),
    "world": ("Maps show the world.", "地图展示世界。"),
    "over": ("Class is over.", "下课了。"),
    "school": ("I go to school.", "我去上学。"),
    "still": ("He is still at school.", "他还在学校。"),
    "try": ("Try again.", "再试一次。"),
    "ask": ("Ask the teacher.", "问问老师。"),
    "need": ("I need a pen.", "我需要一支笔。"),
    "too": ("I like it too.", "我也喜欢。"),
    "feel": ("I feel happy.", "我感到高兴。"),
    "three": ("I have three books.", "我有三本书。"),
    "never": ("I never smoke.", "我从不抽烟。"),
    "become": ("She became a doctor.", "她成了一名医生。"),
    "between": ("Sit between Tom and me.", "坐在汤姆和我之间。"),
    "high": ("The mountain is high.", "这座山很高。"),
    "something": ("I want something to eat.", "我想吃点东西。"),
    "really": ("I really like this song.", "我真的喜欢这首歌。"),
    "most": ("Most students walk.", "大多数学生走路。"),
    "another": ("Have another apple.", "再吃一个苹果。"),
    "much": ("Thank you very much.", "非常感谢你。"),
    "family": ("I love my family.", "我爱我的家人。"),
    "own": ("This is my own pen.", "这是我自己的笔。"),
    "leave": ("I leave home at seven.", "我七点出门。"),
    "put": ("Put the book here.", "把书放在这里。"),
    "old": ("My shoes are old.", "我的鞋旧了。"),
    "while": ("Wait a while.", "等一会儿。"),
    "mean": ("What does this word mean?", "这个词是什么意思？"),
    "keep": ("Please keep quiet.", "请保持安静。"),
    "student": ("I am a student.", "我是学生。"),
    "why": ("Why are you late?", "你为什么迟到？"),
    "let": ("Let me help you.", "让我来帮你。"),
    "great": ("You did a great job.", "你做得很好。"),
    "same": ("We are in the same class.", "我们在同一个班。"),
    "big": ("Shanghai is a big city.", "上海是一座大城市。"),
    "begin": ("Class begins at eight.", "八点开始上课。"),
    "seem": ("You seem tired.", "你看起来累了。"),
    "country": ("China is our country.", "中国是我们的国家。"),
    "help": ("Can you help me?", "你能帮我吗？"),
    "talk": ("Don't talk in class.", "上课不要讲话。"),
    "where": ("Where is the library?", "图书馆在哪里？"),
    "turn": ("Turn left here.", "在这里左转。"),
    "problem": ("This problem is easy.", "这道题很容易。"),
    "every": ("I read every day.", "我每天阅读。"),
    "start": ("Let's start.", "我们开始吧。"),
    "hand": ("Wash your hands.", "洗洗你的手。"),
    "show": ("Show me your book.", "给我看看你的书。"),
    "part": ("This is part one.", "这是第一部分。"),
    "place": ("This place is quiet.", "这个地方很安静。"),
    "again": ("Please try again.", "请再试一次。"),
    "few": ("I have a few friends.", "我有几个朋友。"),
    "week": ("See you next week.", "下周见。"),
    "each": ("Each student has a book.", "每个学生有一本书。"),
    "right": ("Your answer is right.", "你的答案是对的。"),
    "hear": ("I can hear a song.", "我能听见一首歌。"),
    "question": ("May I ask a question?", "我可以问个问题吗？"),
    "play": ("We play basketball.", "我们打篮球。"),
    "run": ("He can run fast.", "他跑得很快。"),
    "small": ("The room is small.", "房间很小。"),
    "number": ("What is your number?", "你的号码是多少？"),
    "always": ("She always smiles.", "她总是微笑。"),
    "move": ("Don't move the chair.", "别动那把椅子。"),
    "night": ("Good night.", "晚安。"),
    "live": ("I live in Shanghai.", "我住在上海。"),
    "believe": ("I believe you.", "我相信你。"),
    "today": ("Today is Monday.", "今天星期一。"),
    "bring": ("Bring your book.", "把你的书带来。"),
    "happen": ("What happened?", "发生了什么事？"),
    "next": ("See you next week.", "下周见。"),
    "without": ("Don't go without me.", "别丢下我。"),
    "before": ("Wash your hands before lunch.", "午饭前洗手。"),
    "must": ("You must wear a coat.", "你必须穿外套。"),
    "home": ("I am at home.", "我在家。"),
    "under": ("The cat is under the chair.", "猫在椅子下面。"),
    "water": ("Please drink some water.", "请喝点水。"),
    "room": ("My room is clean.", "我的房间很干净。"),
    "write": ("Write your name.", "写下你的名字。"),
    "mother": ("My mother cooks well.", "我妈妈菜做得好。"),
    "money": ("I don't have money.", "我没有钱。"),
    "story": ("Tell me a story.", "给我讲个故事。"),
    "young": ("The boy is young.", "这个男孩很年轻。"),
    "different": ("We like different sports.", "我们喜欢不同的运动。"),
    "lot": ("Thanks a lot.", "非常感谢。"),
    "study": ("I study English.", "我学英语。"),
    "book": ("This book is easy.", "这本书很容易。"),
    "eye": ("Open your eyes.", "睁开眼睛。"),
    "job": ("She has a new job.", "她有一份新工作。"),
    "word": ("This word means happy.", "这个词的意思是高兴。"),
    "though": ("I went out though it rained.", "虽然下雨，我还是出门了。"),
    "happy": ("I am happy today.", "我今天很高兴。"),
    "fast": ("Don't run too fast.", "别跑得太快。"),
    "quick": ("Be quick, please.", "请快一点。"),
    "beautiful": ("The park is beautiful.", "公园很美。"),
    "difficult": ("This question is difficult.", "这个问题很难。"),
    "easy": ("This question is easy.", "这道题很容易。"),
    "remember": ("I remember your name.", "我记得你的名字。"),
    "forget": ("Don't forget your key.", "别忘了钥匙。"),
    "listen": ("Listen to the teacher.", "听老师讲。"),
    "speak": ("Please speak slowly.", "请说慢一点。"),
    "buy": ("I want to buy a pen.", "我想买一支笔。"),
    "open": ("Please open the window.", "请打开窗户。"),
    "stop": ("Please stop talking.", "请停止讲话。"),
    "friend": ("She is my friend.", "她是我的朋友。"),
    "teacher": ("Our teacher is kind.", "我们的老师很和气。"),
    "class": ("We have an English class.", "我们有一节英语课。"),
    "food": ("The food is good.", "食物很好吃。"),
    "father": ("My father is tall.", "我爸爸很高。"),
    "sister": ("I have a sister.", "我有一个姐姐。"),
    "brother": ("My brother is ten.", "我弟弟十岁。"),
    "weather": ("The weather is fine.", "天气很好。"),
    "rain": ("It may rain today.", "今天可能会下雨。"),
    "sun": ("The sun is bright.", "太阳很亮。"),
    "morning": ("Good morning.", "早上好。"),
    "afternoon": ("Good afternoon.", "下午好。"),
    "evening": ("Good evening.", "晚上好。"),
    "breakfast": ("I have breakfast at seven.", "我七点吃早饭。"),
    "lunch": ("Lunch is at twelve.", "午饭在十二点。"),
    "dinner": ("Dinner is ready.", "晚饭好了。"),
    "football": ("We play football.", "我们踢足球。"),
    "music": ("I listen to music.", "我听音乐。"),
    "computer": ("I use a computer.", "我用电脑。"),
    "phone": ("This is my phone.", "这是我的电话。"),
    "yesterday": ("I was ill yesterday.", "我昨天病了。"),
    "tomorrow": ("See you tomorrow.", "明天见。"),
    "often": ("I often walk to school.", "我经常走路去上学。"),
    "sometimes": ("I sometimes watch TV.", "我有时看电视。"),
    "usually": ("I usually get up at six.", "我通常六点起床。"),
    "sorry": ("I am sorry.", "对不起。"),
    "please": ("Please sit down.", "请坐。"),
    "hello": ("Hello, I am Li Ming.", "你好，我是李明。"),
    "yes": ("Yes, I do.", "是的。"),
    "apple": ("I eat an apple.", "我吃一个苹果。"),
    "cat": ("The cat is small.", "这只猫很小。"),
    "dog": ("The dog is friendly.", "这只狗很友好。"),
    "red": ("My bag is red.", "我的包是红色的。"),
    "blue": ("The sky is blue.", "天空是蓝色的。"),
    "green": ("Leaves are green.", "叶子是绿色的。"),
    "black": ("He has a black coat.", "他有一件黑外套。"),
    "white": ("Snow is white.", "雪是白的。"),
    "bus": ("I take the bus.", "我坐公交车。"),
    "car": ("My uncle has a car.", "我叔叔有一辆车。"),
    "hospital": ("The hospital is near.", "医院很近。"),
    "doctor": ("The doctor is kind.", "医生很和气。"),
    "clock": ("Look at the clock.", "看钟。"),
    "watch": ("I watch TV at night.", "我晚上看电视。"),
    "minute": ("Wait a minute.", "等一下。"),
    "hour": ("Wait an hour.", "等一个小时。"),
    "city": ("Shanghai is a big city.", "上海是一座大城市。"),
    "house": ("Their house is new.", "他们的房子是新的。"),
    "love": ("I love my family.", "我爱我的家人。"),
    "name": ("My name is Amy.", "我叫埃米。"),
    "boy": ("The boy is reading.", "男孩在读书。"),
    "girl": ("The girl is singing.", "女孩在唱歌。"),
    "read": ("I read every night.", "我每天晚上阅读。"),
    "write": ("Write it in English.", "用英语写下来。"),
    "learn": ("We learn English.", "我们学英语。"),
    "teach": ("She teaches music.", "她教音乐。"),
    "eat": ("I eat breakfast at seven.", "我七点吃早饭。"),
    "drink": ("Drink some water.", "喝点水。"),
    "sleep": ("I sleep at ten.", "我十点睡觉。"),
    "walk": ("I walk to school.", "我走路去上学。"),
    "sit": ("Please sit down.", "请坐下。"),
    "stand": ("Please stand up.", "请站起来。"),
    "wait": ("Please wait here.", "请在这里等。"),
    "stay": ("Stay at home today.", "今天待在家里。"),
    "hope": ("I hope you are well.", "希望你身体好。"),
    "wish": ("I wish you success.", "祝你成功。"),
    "agree": ("I agree with you.", "我同意你的看法。"),
    "decide": ("We decide to go.", "我们决定去。"),
    "choose": ("Choose one book.", "选一本书。"),
    "enjoy": ("I enjoy the song.", "我喜欢这首歌。"),
    "visit": ("We visit the museum.", "我们参观博物馆。"),
    "travel": ("They travel by train.", "他们坐火车旅行。"),
    "arrive": ("We arrive at eight.", "我们八点到。"),
    "return": ("I return the book.", "我把书还回去。"),
    "join": ("Join us, please.", "请加入我们。"),
    "win": ("Our team can win.", "我们队能赢。"),
    "lose": ("Don't lose your key.", "别把钥匙弄丢了。"),
    "buy": ("I buy a new pen.", "我买一支新笔。"),
    "sell": ("The shop sells milk.", "这家店卖牛奶。"),
    "pay": ("I pay for the book.", "我付钱买这本书。"),
    "spend": ("Don't spend too much.", "别花太多钱。"),
    "cost": ("The pen costs five yuan.", "这支笔五块钱。"),
    "save": ("Save some money.", "存一些钱。"),
    "clean": ("Keep the room clean.", "保持房间干净。"),
    "dirty": ("My shoes are dirty.", "我的鞋脏了。"),
    "hot": ("The tea is hot.", "茶是热的。"),
    "cold": ("It is cold today.", "今天很冷。"),
    "warm": ("The room is warm.", "房间很暖和。"),
    "hungry": ("I am hungry.", "我饿了。"),
    "thirsty": ("I am thirsty.", "我渴了。"),
    "tired": ("I am tired.", "我累了。"),
    "afraid": ("Don't be afraid.", "别害怕。"),
    "angry": ("Don't be angry.", "别生气。"),
    "sad": ("She looks sad.", "她看起来难过。"),
    "sorry": ("I am sorry.", "对不起。"),
    "sure": ("I am sure.", "我确定。"),
    "ready": ("Are you ready?", "你准备好了吗？"),
    "busy": ("I am busy today.", "我今天很忙。"),
    "free": ("I am free tonight.", "我今晚有空。"),
    "early": ("I get up early.", "我起得早。"),
    "late": ("Don't be late.", "别迟到。"),
    "important": ("Sleep is important.", "睡眠很重要。"),
    "interesting": ("The story is interesting.", "这个故事很有趣。"),
    "careful": ("Be careful.", "小心。"),
    "dangerous": ("The road is dangerous.", "这条路危险。"),
    "safe": ("This place is safe.", "这个地方安全。"),
    "true": ("The story is true.", "这个故事是真的。"),
    "wrong": ("This answer is wrong.", "这个答案是错的。"),
    "cheap": ("The pen is cheap.", "这支笔很便宜。"),
    "expensive": ("The bag is expensive.", "这个包很贵。"),
    "strong": ("He is strong.", "他很强壮。"),
    "weak": ("I feel weak.", "我感到虚弱。"),
    "healthy": ("She is healthy.", "她很健康。"),
    "ill": ("I was ill yesterday.", "我昨天病了。"),
    "sick": ("He is sick today.", "他今天不舒服。"),
    "quiet": ("Please be quiet.", "请安静。"),
    "full": ("The glass is full.", "杯子满了。"),
    "empty": ("The box is empty.", "盒子是空的。"),
    "light": ("Please turn on the light.", "请开灯。"),
    "hard": ("This work is hard.", "这工作很难。"),
    "close": ("Please close the door.", "请关门。"),
    "last": ("December is the last month.", "十二月是最后一个月。"),
    "kind": ("She is a kind teacher.", "她是一位和气的老师。"),
    "fine": ("I am fine, thank you.", "我很好，谢谢。"),
    "long": ("The river is long.", "这条河很长。"),
    "left": ("Turn left.", "向左转。"),
    "letter": ("I write a letter.", "我写一封信。"),
    "train": ("We take a train.", "我们坐火车。"),
    "park": ("The park is beautiful.", "公园很美。"),
    "spring": ("I like spring.", "我喜欢春天。"),
    "fall": ("Leaves fall in autumn.", "叶子在秋天落下。"),
    "miss": ("I miss my family.", "我想念我的家人。"),
    "enough": ("I have enough time.", "我有足够的时间。"),
    "quite": ("The film is quite good.", "这部电影相当好。"),
    "once": ("I go there once a week.", "我一周去那里一次。"),
    "since": ("I have lived here since May.", "我从五月起住在这里。"),
    "above": ("The light is above us.", "灯在我们上方。"),
    "across": ("Walk across the street.", "走过马路。"),
    "behind": ("The cat is behind the door.", "猫在门后面。"),
    "beside": ("Sit beside me.", "坐在我旁边。"),
    "inside": ("Come inside.", "进来。"),
    "outside": ("Wait outside.", "在外面等。"),
    "until": ("Wait until six.", "等到六点。"),
    "without": ("I can't go without you.", "没有你我去不了。"),
    "hello": ("Hello, nice to meet you.", "你好，很高兴见到你。"),
    "thanks": ("Thanks a lot.", "非常感谢。"),
    "thank": ("Thank you.", "谢谢你。"),
    "goodbye": ("Goodbye.", "再见。"),
    "parents": ("My parents love me.", "我的父母爱我。"),
    "dad": ("My dad is a driver.", "我爸爸是司机。"),
    "mom": ("My mom is a teacher.", "我妈妈是老师。"),
    "homework": ("I do homework at night.", "我晚上做作业。"),
    "library": ("I read in the library.", "我在图书馆看书。"),
    "classmate": ("She is my classmate.", "她是我的同学。"),
    "dictionary": ("Look it up in a dictionary.", "在词典里查一查。"),
    "understand": ("I understand this word.", "我懂这个词。"),
    "practice": ("Practice a little every day.", "每天练一点。"),
    "meaning": ("What is the meaning?", "是什么意思？"),
    "city": ("I live in the city.", "我住在城里。"),
    "street": ("Our street is quiet.", "我们这条街很安静。"),
    "shop": ("The shop is open.", "商店开着。"),
    "hospital": ("He is in hospital.", "他在医院里。"),
    "nurse": ("The nurse is kind.", "护士很和气。"),
    "police": ("Call the police.", "报警。"),
    "money": ("Don't lose your money.", "别把钱弄丢了。"),
    "price": ("The price is low.", "价格不高。"),
    "delicious": ("The soup is delicious.", "汤很好喝。"),
    "chicken": ("I like chicken.", "我喜欢鸡肉。"),
    "rice": ("I eat rice.", "我吃饭。"),
    "milk": ("Drink some milk.", "喝点牛奶。"),
    "bread": ("I eat bread.", "我吃面包。"),
    "egg": ("I eat an egg.", "我吃一个鸡蛋。"),
    "fruit": ("Fruit is healthy.", "水果对健康有好处。"),
    "vegetable": ("Eat more vegetables.", "多吃蔬菜。"),
    "tea": ("I drink tea.", "我喝茶。"),
    "coffee": ("Coffee is hot.", "咖啡是热的。"),
    "clothes": ("These clothes are new.", "这些衣服是新的。"),
    "shoes": ("My shoes are dirty.", "我的鞋脏了。"),
    "bag": ("My bag is heavy.", "我的包很重。"),
    "pen": ("This pen is blue.", "这支笔是蓝色的。"),
    "pencil": ("I need a pencil.", "我需要一支铅笔。"),
    "paper": ("Write it on paper.", "写在纸上。"),
    "desk": ("The book is on the desk.", "书在书桌上。"),
    "chair": ("Sit on the chair.", "坐在椅子上。"),
    "door": ("Close the door.", "把门关上。"),
    "window": ("Open the window.", "打开窗户。"),
    "key": ("Where is my key?", "我的钥匙在哪里？"),
    "photo": ("This is an old photo.", "这是一张旧照片。"),
    "picture": ("Draw a picture.", "画一幅画。"),
    "map": ("Look at the map.", "看地图。"),
    "clock": ("The clock is slow.", "这只钟慢了。"),
    "tree": ("The tree is tall.", "这棵树很高。"),
    "flower": ("The flower is red.", "这朵花是红的。"),
    "animal": ("A dog is an animal.", "狗是一种动物。"),
    "bird": ("The bird can fly.", "鸟会飞。"),
    "fish": ("Fish live in water.", "鱼生活在水里。"),
    "bike": ("I ride a bike.", "我骑自行车。"),
    "bicycle": ("I have a bicycle.", "我有一辆自行车。"),
    "station": ("The station is near.", "车站很近。"),
    "ticket": ("I buy a ticket.", "我买一张票。"),
    "holiday": ("Summer holiday is long.", "暑假很长。"),
    "birthday": ("Today is my birthday.", "今天是我的生日。"),
    "party": ("We have a party.", "我们举办聚会。"),
    "gift": ("This gift is for you.", "这份礼物是给你的。"),
    "idea": ("That's a good idea.", "那是个好主意。"),
    "dream": ("I have a dream.", "我有一个梦想。"),
    "game": ("Let's play a game.", "我们玩个游戏吧。"),
    "ball": ("Throw the ball.", "把球扔出去。"),
    "song": ("Sing a song.", "唱一首歌。"),
    "film": ("The film is funny.", "这部电影很好笑。"),
    "movie": ("We watch a movie.", "我们看一场电影。"),
    "tv": ("Don't watch too much TV.", "别看太多电视。"),
    "computer": ("The computer is new.", "电脑是新的。"),
    "internet": ("I use the Internet.", "我使用互联网。"),
    "message": ("I got your message.", "我收到你的消息了。"),
    "news": ("I read the news.", "我看新闻。"),
    "email": ("Send me an email.", "给我发一封电子邮件。"),
    "information": ("I need more information.", "我需要更多信息。"),
    "mistake": ("Don't worry about the mistake.", "别为这个错误担心。"),
    "example": ("Give me an example.", "给我举个例子。"),
    "sentence": ("Read this sentence.", "读这个句子。"),
    "language": ("English is a language.", "英语是一种语言。"),
    "grammar": ("Grammar can be hard.", "语法有时很难。"),
    "spell": ("How do you spell it?", "这个词怎么拼？"),
    "meaning": ("I know the meaning.", "我知道意思。"),
    "correct": ("Your answer is correct.", "你的答案是正确的。"),
    "both": ("Both answers are right.", "两个答案都对。"),
    "nothing": ("Nothing is in the box.", "盒子里什么也没有。"),
    "everything": ("Everything is ready.", "一切都准备好了。"),
    "everyone": ("Everyone is here.", "每个人都在。"),
    "someone": ("Someone is at the door.", "有人在门口。"),
    "anyone": ("Anyone can try.", "任何人都可以试。"),
    "anything": ("I don't want anything.", "我什么都不要。"),
    "already": ("I already know it.", "我已经知道了。"),
    "yet": ("He is not here yet.", "他还没到。"),
    "almost": ("I almost forgot.", "我差点忘了。"),
    "together": ("Let's go together.", "我们一起去吧。"),
    "away": ("Don't run away.", "别跑开。"),
    "far": ("The school is not far.", "学校不远。"),
    "near": ("The shop is near.", "商店很近。"),
    "maybe": ("Maybe it will rain.", "也许会下雨。"),
    "perhaps": ("Perhaps she is ill.", "也许她病了。"),
    "probably": ("It will probably rain.", "很可能会下雨。"),
    "although": ("Although it rained, we went.", "虽然下雨，我们还是去了。"),
    "however": ("It is hard. However, try.", "这很难。不过，试一试。"),
    "welcome": ("You are welcome.", "不客气。"),
    "excuse": ("Excuse me.", "打扰一下。"),
    "ago": ("I met her two days ago.", "我两天前见过她。"),
    "better": ("This one is better.", "这个更好。"),
    "best": ("She is my best friend.", "她是我最好的朋友。"),
    "less": ("Use less sugar.", "少放点糖。"),
    "little": ("I have a little milk.", "我有一点牛奶。"),
    "few": ("Few people know it.", "很少有人知道。"),
    "another": ("I need another day.", "我还需要一天。"),
    "others": ("Others are waiting.", "其他人在等。"),
    "either": ("Either answer is fine.", "哪个答案都可以。"),
    "neither": ("Neither book is mine.", "两本书都不是我的。"),
    "none": ("None of them came.", "他们一个都没来。"),
    "able": ("I am able to swim.", "我会游泳。"),
    "across": ("The school is across the street.", "学校在街对面。"),
    "along": ("Walk along the river.", "沿着河走。"),
    "among": ("She sits among friends.", "她坐在朋友们中间。"),
    "around": ("Look around.", "看看四周。"),
    "below": ("Write your name below.", "把名字写在下面。"),
    "except": ("Everyone came except Tom.", "除了汤姆，大家都来了。"),
    "during": ("Don't talk during class.", "上课时不要讲话。"),
    "until": ("Stay until five.", "待到五点。"),
    "since": ("I have been here since Monday.", "我从星期一起就在这里。"),
    "once": ("Read it once more.", "再读一遍。"),
    "enough": ("That is enough.", "够了。"),
    "quite": ("The room is quite small.", "房间相当小。"),
    "almost": ("It is almost six.", "快六点了。"),
    "already": ("She has already left.", "她已经离开了。"),
    "yet": ("Have you eaten yet?", "你吃饭了吗？"),
    "still": ("I still don't know.", "我仍然不知道。"),
    "even": ("He didn't even call.", "他甚至没打电话。"),
    "just": ("I just want water.", "我只要水。"),
    "only": ("Only two students came.", "只有两个学生来了。"),
    "also": ("She also likes art.", "她也喜欢美术。"),
    "too": ("This is too hard.", "这太难了。"),
    "very": ("Thank you very much.", "非常感谢。"),
    "really": ("I really don't know.", "我真的不知道。"),
    "always": ("He is always late.", "他总是迟到。"),
    "never": ("Never give up.", "永不放弃。"),
    "sometimes": ("Sometimes I walk.", "有时我走路。"),
    "often": ("We often talk.", "我们经常聊天。"),
    "usually": ("I usually read at night.", "我通常晚上阅读。"),
    "soon": ("See you soon.", "回头见。"),
    "later": ("See you later.", "回头见。"),
    "again": ("Say it again.", "再说一遍。"),
    "once": ("I met him once.", "我见过他一次。"),
    "twice": ("I called twice.", "我打了两次电话。"),
    "first": ("This is my first day.", "这是我的第一天。"),
    "second": ("Monday is the second day.", "星期一是第二天。"),
    "third": ("This is the third time.", "这是第三次。"),
    "last": ("This is the last one.", "这是最后一个。"),
    "next": ("The next bus is late.", "下一班车晚点了。"),
    "another": ("Give me another chance.", "再给我一次机会。"),
    "same": ("We have the same bag.", "我们的包一样。"),
    "different": ("They are different.", "它们不一样。"),
    "important": ("Friends are important.", "朋友很重要。"),
    "possible": ("It is possible.", "这是可能的。"),
    "useful": ("This book is useful.", "这本书有用。"),
    "wonderful": ("What a wonderful day.", "多好的一天。"),
    "interesting": ("English is interesting.", "英语很有趣。"),
    "boring": ("The film is boring.", "这部电影很无聊。"),
    "funny": ("The story is funny.", "这个故事很好笑。"),
    "clever": ("She is clever.", "她很聪明。"),
    "smart": ("That is a smart idea.", "那是个聪明的主意。"),
    "careful": ("Be careful with the glass.", "小心玻璃杯。"),
    "careless": ("Don't be careless.", "别粗心。"),
    "polite": ("Be polite.", "要有礼貌。"),
    "friendly": ("The dog is friendly.", "这只狗很友好。"),
    "kind": ("Thank you. You are kind.", "谢谢。你人真好。"),
    "nice": ("Have a nice day.", "祝你有美好的一天。"),
    "lovely": ("The flower is lovely.", "这朵花很可爱。"),
    "famous": ("She is famous.", "她很有名。"),
    "popular": ("Football is popular.", "足球很受欢迎。"),
    "special": ("Today is special.", "今天很特别。"),
    "usual": ("I take the usual bus.", "我坐平时那班车。"),
    "common": ("This word is common.", "这个词很常见。"),
    "simple": ("Use a simple word.", "用一个简单的词。"),
    "clear": ("Your answer is clear.", "你的答案很清楚。"),
    "heavy": ("The bag is heavy.", "包很重。"),
    "light": ("This bag is light.", "这个包很轻。"),
    "tall": ("He is tall.", "他很高。"),
    "short": ["Wait, short is a tuple"],
}

# Fix the accidental bad entry above.
EXAMPLES["short"] = ("The pencil is short.", "铅笔很短。")
EXAMPLES["tall"] = ("She is tall.", "她很高。")
EXAMPLES["heavy"] = ("The box is heavy.", "箱子很重。")
EXAMPLES["fat"] = ("The cat is fat.", "这只猫很胖。")
EXAMPLES["thin"] = ("The book is thin.", "这本书很薄。")
EXAMPLES["young"] = ("They are young.", "他们很年轻。")
EXAMPLES["old"] = ("The tree is old.", "这棵树很老。")
EXAMPLES["new"] = ("I have a new bag.", "我有一个新包。")
EXAMPLES["nice"] = ("Have a nice day.", "祝你今天愉快。")
EXAMPLES["friendly"] = ("He is friendly.", "他很友好。")
EXAMPLES["polite"] = ("Please be polite.", "请有礼貌。")
EXAMPLES["famous"] = ("The city is famous.", "这座城市很有名。")
EXAMPLES["popular"] = ("This song is popular.", "这首歌很受欢迎。")
EXAMPLES["special"] = ("Today is a special day.", "今天是特别的一天。")
EXAMPLES["simple"] = ("The question is simple.", "这个问题很简单。")
EXAMPLES["clear"] = ("Please speak in a clear voice.", "请说清楚一点。")
EXAMPLES["common"] = ("It is a common word.", "这是一个常见词。")
EXAMPLES["useful"] = ("A dictionary is useful.", "词典很有用。")
EXAMPLES["possible"] = ("Is it possible?", "这可能吗？")
EXAMPLES["wonderful"] = ("The trip was wonderful.", "这次旅行棒极了。")
EXAMPLES["boring"] = ("The class is not boring.", "这节课并不无聊。")
EXAMPLES["funny"] = ("He tells funny stories.", "他会讲好笑的故事。")
EXAMPLES["clever"] = ("The girl is clever.", "这个女孩很聪明。")
EXAMPLES["smart"] = ("That is smart.", "那样做很聪明。")
EXAMPLES["glad"] = ("I am glad to see you.", "见到你我很高兴。")
EXAMPLES["pleased"] = ("I am pleased.", "我很满意。")
EXAMPLES["excited"] = ("The children are excited.", "孩子们很兴奋。")
EXAMPLES["surprised"] = ("I am surprised.", "我很惊讶。")
EXAMPLES["worried"] = ("Don't be worried.", "别担心。")
EXAMPLES["worry"] = ("Don't worry.", "别担心。")
EXAMPLES["smile"] = ("She smiles at me.", "她对我微笑。")
EXAMPLES["laugh"] = ("We laugh together.", "我们一起笑。")
EXAMPLES["cry"] = ("The baby may cry.", "婴儿可能会哭。")
EXAMPLES["shout"] = ("Don't shout.", "别喊。")
EXAMPLES["sing"] = ("She can sing well.", "她唱得很好。")
EXAMPLES["dance"] = ("They dance after class.", "他们课后跳舞。")
EXAMPLES["swim"] = ("I can swim.", "我会游泳。")
EXAMPLES["fly"] = ("Birds can fly.", "鸟会飞。")
EXAMPLES["drive"] = ("My father can drive.", "我爸爸会开车。")
EXAMPLES["ride"] = ("I ride to school.", "我骑车去上学。")
EXAMPLES["draw"] = ("Draw a cat.", "画一只猫。")
EXAMPLES["wear"] = ("I wear a coat.", "我穿着外套。")
EXAMPLES["dress"] = ("She wears a red dress.", "她穿着一条红裙子。")
EXAMPLES["wash"] = ("Wash your hands.", "洗手。")
EXAMPLES["cook"] = ("Dad can cook fish.", "爸爸会做鱼。")
EXAMPLES["wake"] = ("I wake up at six.", "我六点醒来。")
EXAMPLES["hurry"] = ("Hurry up.", "快点。")
EXAMPLES["prefer"] = ("I prefer tea.", "我更喜欢茶。")
EXAMPLES["hate"] = ("I hate being late.", "我讨厌迟到。")
EXAMPLES["fear"] = ("Don't fear mistakes.", "别害怕犯错。")
EXAMPLES["break"] = ("Don't break the glass.", "别打碎玻璃杯。")
EXAMPLES["cut"] = ("Cut the apple.", "把苹果切开。")
EXAMPLES["hurt"] = ("My leg hurts.", "我的腿疼。")
EXAMPLES["die"] = ("Plants die without water.", "植物没有水会死。")
EXAMPLES["born"] = ("I was born in Shanghai.", "我出生在上海。")
EXAMPLES["marry"] = ("They will marry.", "他们要结婚了。")
EXAMPLES["build"] = ("They build a house.", "他们盖房子。")
EXAMPLES["grow"] = ("Plants grow in spring.", "植物在春天生长。")
EXAMPLES["carry"] = ("I carry my bag.", "我拿着我的包。")
EXAMPLES["catch"] = ("Catch the ball.", "接住球。")
EXAMPLES["save"] = ("The doctor can save him.", "医生能救他。")
EXAMPLES["sound"] = ("The music sounds nice.", "音乐听起来很好。")
EXAMPLES["voice"] = ("She has a kind voice.", "她的声音很温和。")
EXAMPLES["noise"] = ("Don't make noise.", "别制造噪音。")
EXAMPLES["road"] = ("The road is long.", "这条路很长。")
EXAMPLES["street"] = ("I live on this street.", "我住在这条街上。")
EXAMPLES["station"] = ("Meet me at the station.", "在车站见我。")
EXAMPLES["airport"] = ("The airport is far.", "机场很远。")
EXAMPLES["hotel"] = ("The hotel is clean.", "这家旅馆很干净。")
EXAMPLES["restaurant"] = ("We eat at a restaurant.", "我们在餐馆吃饭。")
EXAMPLES["market"] = ("Mom goes to the market.", "妈妈去市场。")
EXAMPLES["bank"] = ("The bank is closed.", "银行关门了。")
EXAMPLES["office"] = ("Dad is in the office.", "爸爸在办公室。")
EXAMPLES["factory"] = ("The factory is big.", "工厂很大。")
EXAMPLES["farm"] = ("They live on a farm.", "他们住在农场。")
EXAMPLES["village"] = ("It is a small village.", "那是一个小村庄。")
EXAMPLES["town"] = ("Our town is quiet.", "我们的小镇很安静。")
EXAMPLES["capital"] = ("Beijing is the capital.", "北京是首都。")
EXAMPLES["earth"] = ("We live on the earth.", "我们住在地球上。")
EXAMPLES["river"] = ("The river is wide.", "这条河很宽。")
EXAMPLES["lake"] = ("We walk by the lake.", "我们在湖边走。")
EXAMPLES["sea"] = ("The sea is blue.", "大海是蓝色的。")
EXAMPLES["mountain"] = ("The mountain is high.", "山很高。")
EXAMPLES["forest"] = ("Animals live in the forest.", "动物住在森林里。")
EXAMPLES["garden"] = ("Flowers grow in the garden.", "花长在花园里。")
EXAMPLES["zoo"] = ("We visit the zoo.", "我们参观动物园。")
EXAMPLES["museum"] = ("The museum is free.", "博物馆免费。")
EXAMPLES["cinema"] = ("Let's go to the cinema.", "我们去电影院吧。")
EXAMPLES["university"] = ("She studies at a university.", "她在大学学习。")
EXAMPLES["math"] = ("Math is useful.", "数学很有用。")
EXAMPLES["maths"] = ("I like maths.", "我喜欢数学。")
EXAMPLES["history"] = ("History is interesting.", "历史很有趣。")
EXAMPLES["science"] = ("We have a science class.", "我们有一节科学课。")
EXAMPLES["art"] = ("I like art.", "我喜欢美术。")
EXAMPLES["chinese"] = ("I speak Chinese.", "我说中文。")
EXAMPLES["english"] = ("I study English.", "我学英语。")
EXAMPLES["china"] = ("I live in China.", "我住在中国。")
EXAMPLES["result"] = ("The result is good.", "结果很好。")
EXAMPLES["score"] = ("My score is 90.", "我的分数是 90。")
EXAMPLES["mark"] = ("She got a high mark.", "她得了高分。")
EXAMPLES["grade"] = ("He is in Grade 9.", "他上九年级。")
EXAMPLES["exercise"] = ("Do more exercise.", "多锻炼。")
EXAMPLES["practice"] = ("Practice makes you better.", "练习会让你更好。")
EXAMPLES["mistake"] = ("A mistake is okay.", "错了也没关系。")
EXAMPLES["error"] = ("There is an error.", "这里有一个错误。")
EXAMPLES["page"] = ("Open page ten.", "打开第十页。")
EXAMPLES["title"] = ("Read the title.", "读标题。")
EXAMPLES["topic"] = ("The topic is family.", "话题是家庭。")
EXAMPLES["article"] = ("Read the short article.", "读这篇短文。")
EXAMPLES["text"] = ("Read the text.", "读课文。")
EXAMPLES["passage"] = ("The passage is short.", "这篇短文不长。")
EXAMPLES["paragraph"] = ("Read the first paragraph.", "读第一段。")
EXAMPLES["sentence"] = ("Make a sentence.", "造一个句子。")
EXAMPLES["grammar"] = ("Check the grammar.", "检查语法。")
EXAMPLES["spell"] = ("Can you spell it?", "你能拼出来吗？")
EXAMPLES["pronunciation"] = ("Check the pronunciation.", "核对一下读音。")
EXAMPLES["vocabulary"] = ("Learn new vocabulary.", "学习新词汇。")
EXAMPLES["language"] = ("Language needs practice.", "语言需要练习。")
EXAMPLES["dictionary"] = ("Use a dictionary.", "用词典。")
EXAMPLES["classmate"] = ("He is my classmate.", "他是我的同学。")
EXAMPLES["classroom"] = ("The classroom is clean.", "教室很干净。")
EXAMPLES["lesson"] = ("This lesson is easy.", "这一课很容易。")
EXAMPLES["subject"] = ("English is my subject.", "英语是我的学科。")
EXAMPLES["homework"] = ("Finish your homework.", "把作业做完。")
EXAMPLES["exam"] = ("The exam is tomorrow.", "考试在明天。")
EXAMPLES["test"] = ("We have a test.", "我们有一个小测验。")
EXAMPLES["library"] = ("Be quiet in the library.", "图书馆里要安静。")
EXAMPLES["uncle"] = ("My uncle lives in Beijing.", "我叔叔住在北京。")
EXAMPLES["aunt"] = ("My aunt is a doctor.", "我阿姨是医生。")
EXAMPLES["cousin"] = ("My cousin is twelve.", "我表弟十二岁。")
EXAMPLES["grandfather"] = ("My grandfather tells stories.", "我爷爷会讲故事。")
EXAMPLES["grandmother"] = ("My grandmother cooks well.", "我奶奶菜做得好。")
EXAMPLES["son"] = ("Their son is a student.", "他们的儿子是学生。")
EXAMPLES["daughter"] = ("Their daughter can sing.", "他们的女儿会唱歌。")
EXAMPLES["baby"] = ("The baby is sleeping.", "宝宝在睡觉。")
EXAMPLES["husband"] = ("Her husband is a teacher.", "她丈夫是老师。")
EXAMPLES["wife"] = ("His wife is a nurse.", "他妻子是护士。")
EXAMPLES["neighbor"] = ("Our neighbor is kind.", "我们的邻居很和气。")
EXAMPLES["neighbour"] = ("Our neighbour is kind.", "我们的邻居很和气。")
EXAMPLES["worker"] = ("The worker is busy.", "工人很忙。")
EXAMPLES["farmer"] = ("The farmer grows rice.", "农民种水稻。")
EXAMPLES["driver"] = ("The driver is careful.", "司机很小心。")
EXAMPLES["policeman"] = ("The policeman helps us.", "警察帮助我们。")
EXAMPLES["nurse"] = ("The nurse helps the doctor.", "护士帮助医生。")
EXAMPLES["singer"] = ("She wants to be a singer.", "她想成为歌手。")
EXAMPLES["scientist"] = ("The scientist asks questions.", "科学家提出问题。")
EXAMPLES["writer"] = ("The writer tells a story.", "作家讲了一个故事。")
EXAMPLES["hero"] = ("He is a hero.", "他是一位英雄。")
EXAMPLES["member"] = ("I am a member of the team.", "我是队里的一员。")
EXAMPLES["team"] = ("Our team won.", "我们队赢了。")
EXAMPLES["player"] = ("He is a good player.", "他是一名好选手。")
EXAMPLES["club"] = ("I join the music club.", "我加入音乐社团。")
EXAMPLES["meeting"] = ("The meeting is at three.", "会议在三点。")
EXAMPLES["trip"] = ("Have a good trip.", "旅途愉快。")
EXAMPLES["journey"] = ("The journey is long.", "旅程很长。")
EXAMPLES["ticket"] = ("I lost my ticket.", "我把票弄丢了。")
EXAMPLES["seat"] = ("This seat is free.", "这个座位空着。")
EXAMPLES["price"] = ("What is the price?", "价格是多少？")
EXAMPLES["dollar"] = ("It costs one dollar.", "它要一美元。")
EXAMPLES["customer"] = ("The customer is waiting.", "顾客在等。")
EXAMPLES["menu"] = ("Look at the menu.", "看看菜单。")
EXAMPLES["bill"] = ("Can I have the bill?", "请给我账单。")
EXAMPLES["order"] = ("I order some rice.", "我点了米饭。")
EXAMPLES["delicious"] = ("The cake is delicious.", "蛋糕很好吃。")
EXAMPLES["juice"] = ("I drink orange juice.", "我喝橙汁。")
EXAMPLES["cake"] = ("The cake is sweet.", "蛋糕是甜的。")
EXAMPLES["candy"] = ("Don't eat too much candy.", "别吃太多糖。")
EXAMPLES["chocolate"] = ("I like chocolate.", "我喜欢巧克力。")
EXAMPLES["sugar"] = ("Tea with no sugar.", "不加糖的茶。")
EXAMPLES["meat"] = ("I don't eat much meat.", "我不太吃肉。")
EXAMPLES["beef"] = ("Beef is expensive.", "牛肉很贵。")
EXAMPLES["noodle"] = ("I like noodles.", "我喜欢面条。")
EXAMPLES["noodles"] = ("Noodles are hot.", "面条是热的。")
EXAMPLES["dumpling"] = ("We eat dumplings.", "我们吃饺子。")
EXAMPLES["soup"] = ("The soup is hot.", "汤很烫。")
EXAMPLES["potato"] = ("I like potatoes.", "我喜欢土豆。")
EXAMPLES["tomato"] = ("The tomato is red.", "番茄是红的。")
EXAMPLES["banana"] = ("The banana is yellow.", "香蕉是黄的。")
EXAMPLES["orange"] = ("I eat an orange.", "我吃一个橙子。")
EXAMPLES["sweet"] = ("The apple is sweet.", "苹果是甜的。")
EXAMPLES["fresh"] = ("The fish is fresh.", "鱼很新鲜。")
EXAMPLES["kitchen"] = ("Mom is in the kitchen.", "妈妈在厨房。")
EXAMPLES["cup"] = ("A cup of tea.", "一杯茶。")
EXAMPLES["glass"] = ("A glass of water.", "一杯水。")
EXAMPLES["bottle"] = ("A bottle of milk.", "一瓶牛奶。")
EXAMPLES["bowl"] = ("A bowl of rice.", "一碗米饭。")
EXAMPLES["plate"] = ("Put it on the plate.", "把它放在盘子上。")
EXAMPLES["knife"] = ("Use a knife carefully.", "用刀要小心。")
EXAMPLES["spoon"] = ("I need a spoon.", "我需要一把勺子。")
EXAMPLES["chopsticks"] = ("I use chopsticks.", "我用筷子。")
EXAMPLES["smell"] = ("The flower smells nice.", "花闻起来很香。")
EXAMPLES["taste"] = ("Taste the soup.", "尝尝这汤。")
EXAMPLES["body"] = ("Exercise helps the body.", "锻炼对身体有好处。")
EXAMPLES["head"] = ("My head hurts.", "我头疼。")
EXAMPLES["face"] = ("Wash your face.", "洗洗脸。")
EXAMPLES["ear"] = ("I hear with my ears.", "我用耳朵听。")
EXAMPLES["nose"] = ("The dog has a wet nose.", "狗的鼻子是湿的。")
EXAMPLES["mouth"] = ("Open your mouth.", "张开嘴。")
EXAMPLES["tooth"] = ("Brush your teeth.", "刷牙。")
EXAMPLES["teeth"] = ("Brush your teeth.", "刷牙。")
EXAMPLES["hair"] = ("Her hair is black.", "她的头发是黑的。")
EXAMPLES["arm"] = ("Raise your arm.", "举起手臂。")
EXAMPLES["finger"] = ("I have ten fingers.", "我有十根手指。")
EXAMPLES["leg"] = ("My leg is tired.", "我的腿累了。")
EXAMPLES["foot"] = ("My foot hurts.", "我的脚疼。")
EXAMPLES["heart"] = ("My heart is fine.", "我的心脏没问题。")
EXAMPLES["health"] = ("Health is important.", "健康很重要。")
EXAMPLES["medicine"] = ("Take the medicine.", "把药吃了。")
EXAMPLES["fever"] = ("He has a fever.", "他发烧了。")
EXAMPLES["cough"] = ("I have a cough.", "我咳嗽。")
EXAMPLES["headache"] = ("I have a headache.", "我头疼。")
EXAMPLES["pain"] = ("I feel pain.", "我感到疼。")
EXAMPLES["illness"] = ("The illness is not serious.", "病得不重。")
EXAMPLES["rest"] = ("Have a rest.", "休息一下。")
EXAMPLES["sleep"] = ("Sleep early.", "早点睡。")
EXAMPLES["person"] = ("She is a kind person.", "她是一个和气的人。")
EXAMPLES["kid"] = ("The kid is playing.", "小孩在玩。")
EXAMPLES["visitor"] = ("A visitor is coming.", "有客人要来。")
EXAMPLES["stranger"] = ("Don't talk to strangers.", "别和陌生人说话。")
EXAMPLES["boss"] = ("The boss is busy.", "老板很忙。")
EXAMPLES["manager"] = ("She is the manager.", "她是经理。")
EXAMPLES["king"] = ("The king is old.", "国王老了。")
EXAMPLES["hero"] = ("The doctor is a hero.", "这位医生是英雄。")
EXAMPLES["pilot"] = ("He wants to be a pilot.", "他想当飞行员。")
EXAMPLES["soldier"] = ("The soldier is brave.", "士兵很勇敢。")
EXAMPLES["brave"] = ("Be brave.", "勇敢一点。")
EXAMPLES["honest"] = ("Be honest.", "要诚实。")
EXAMPLES["lazy"] = ("Don't be lazy.", "别偷懒。")
EXAMPLES["active"] = ("She is active in class.", "她在课堂上很积极。")
EXAMPLES["serious"] = ("He looks serious.", "他看起来很严肃。")
EXAMPLES["strict"] = ("The teacher is strict.", "老师很严格。")
EXAMPLES["patient"] = ("Please be patient.", "请耐心一点。")
EXAMPLES["lonely"] = ("He feels lonely.", "他感到孤单。")
EXAMPLES["proud"] = ("I am proud of you.", "我为你骄傲。")
EXAMPLES["shy"] = ("The boy is shy.", "男孩很害羞。")
EXAMPLES["nervous"] = ("I feel nervous.", "我感到紧张。")
EXAMPLES["confident"] = ("Be confident.", "要有信心。")
EXAMPLES["successful"] = ("Hard work makes you successful.", "努力会让你成功。")
EXAMPLES["success"] = ("I wish you success.", "祝你成功。")
EXAMPLES["fail"] = ("Don't fear to fail.", "别害怕失败。")
EXAMPLES["failure"] = ("Failure is a teacher.", "失败也能让人学到东西。")
EXAMPLES["win"] = ("We want to win.", "我们想赢。")
EXAMPLES["lose"] = ("We may lose.", "我们可能会输。")
EXAMPLES["try"] = ("Just try.", "试一试就好。")
EXAMPLES["effort"] = ("Thank you for your effort.", "谢谢你的努力。")
EXAMPLES["habit"] = ("Reading is a good habit.", "阅读是一个好习惯。")
EXAMPLES["hobby"] = ("My hobby is music.", "我的爱好是音乐。")
EXAMPLES["interest"] = ("I have an interest in art.", "我对美术有兴趣。")
EXAMPLES["plan"] = ("What is your plan?", "你的计划是什么？")
EXAMPLES["future"] = ("Think about the future.", "想想将来。")
EXAMPLES["past"] = ("Don't live in the past.", "别一直活在过去。")
EXAMPLES["present"] = ("Live in the present.", "活在当下。")
EXAMPLES["chance"] = ("Give me a chance.", "给我一个机会。")
EXAMPLES["choice"] = ("It is your choice.", "这是你的选择。")
EXAMPLES["decision"] = ("It is a hard decision.", "这是一个难做的决定。")
EXAMPLES["advice"] = ("Thank you for your advice.", "谢谢你的建议。")
EXAMPLES["suggestion"] = ("That is a good suggestion.", "那是个好建议。")
EXAMPLES["opinion"] = ("What is your opinion?", "你的看法是什么？")
EXAMPLES["idea"] = ("I have an idea.", "我有一个主意。")
EXAMPLES["problem"] = ("We can solve the problem.", "我们能解决这个问题。")
EXAMPLES["trouble"] = ("Don't look for trouble.", "别自找麻烦。")
EXAMPLES["danger"] = ("Stay away from danger.", "远离危险。")
EXAMPLES["safety"] = ("Safety comes first.", "安全第一。")
EXAMPLES["rule"] = ("Follow the rule.", "遵守规则。")
EXAMPLES["law"] = ("Everyone should follow the law.", "人人都应该守法。")
EXAMPLES["right"] = ("You have the right to rest.", "你有休息的权利。")
EXAMPLES["duty"] = ("It is our duty.", "这是我们的责任。")
EXAMPLES["promise"] = ("I promise.", "我保证。")
EXAMPLES["truth"] = ("Tell the truth.", "说实话。")
EXAMPLES["lie"] = ("Don't tell a lie.", "别说谎。")
EXAMPLES["secret"] = ("Can you keep a secret?", "你能保守秘密吗？")
EXAMPLES["fact"] = ("It is a fact.", "这是事实。")
EXAMPLES["reason"] = ("Tell me the reason.", "告诉我原因。")
EXAMPLES["result"] = ("Wait for the result.", "等结果。")
EXAMPLES["success"] = ("Success takes time.", "成功需要时间。")
EXAMPLES["goal"] = ("My goal is to pass.", "我的目标是通过。")
EXAMPLES["dream"] = ("Follow your dream.", "追随你的梦想。")
EXAMPLES["hope"] = ("There is still hope.", "还有希望。")
EXAMPLES["wish"] = ("Best wishes.", "祝你一切顺利。")
EXAMPLES["luck"] = ("Good luck.", "祝好运。")
EXAMPLES["lucky"] = ("I feel lucky.", "我觉得很幸运。")
EXAMPLES["happy"] = ("Stay happy.", "保持开心。")
EXAMPLES["sad"] = ("Don't be sad.", "别难过。")
EXAMPLES["angry"] = ("She is not angry.", "她没有生气。")
EXAMPLES["afraid"] = ("I am not afraid.", "我不害怕。")
EXAMPLES["brave"] = ("You are brave.", "你很勇敢。")
EXAMPLES["care"] = ("I care about you.", "我在乎你。")
EXAMPLES["careful"] = ("Be careful on the road.", "路上要小心。")
EXAMPLES["help"] = ("Thanks for your help.", "谢谢你的帮助。")
EXAMPLES["kindness"] = ("Thank you for your kindness.", "谢谢你的好意。")
EXAMPLES["friendship"] = ("Friendship is important.", "友谊很重要。")
EXAMPLES["love"] = ("Love your family.", "爱你的家人。")
EXAMPLES["peace"] = ("We want peace.", "我们想要和平。")
EXAMPLES["war"] = ("War is terrible.", "战争很可怕。")
EXAMPLES["terrible"] = ("The news is terrible.", "这个消息很糟。")
EXAMPLES["awful"] = ("I feel awful.", "我感觉很糟。")
EXAMPLES["wonderful"] = ("You did a wonderful job.", "你做得非常好。")
EXAMPLES["excellent"] = ("Excellent work.", "做得非常好。")
EXAMPLES["perfect"] = ("Nobody is perfect.", "没有人是完美的。")
EXAMPLES["good"] = ("Have a good rest.", "好好休息。")
EXAMPLES["bad"] = ("That is a bad idea.", "那是个坏主意。")
EXAMPLES["better"] = ("You can do better.", "你可以做得更好。")
EXAMPLES["best"] = ("Do your best.", "尽你所能。")
EXAMPLES["worse"] = ("It is getting worse.", "情况更糟了。")
EXAMPLES["worst"] = ("This is the worst day.", "这是最糟的一天。")
EXAMPLES["enough"] = ("You have done enough.", "你做得够多了。")
EXAMPLES["ready"] = ("I am ready to try.", "我准备好试一试了。")
EXAMPLES["able"] = ("You are able to learn.", "你能学会。")
EXAMPLES["unable"] = ("I am unable to go.", "我去不了。")
EXAMPLES["possible"] = ("Everything is possible.", "一切皆有可能。")
EXAMPLES["impossible"] = ("Nothing is impossible.", "没有什么是不可能的。")
EXAMPLES["necessary"] = ("Sleep is necessary.", "睡眠是必要的。")
EXAMPLES["important"] = ("Family is important.", "家人很重要。")
EXAMPLES["useful"] = ("English is useful.", "英语很有用。")
EXAMPLES["useless"] = ("Worry is useless.", "担心没有用。")
EXAMPLES["careless"] = ("A careless mistake.", "一个粗心的错误。")
EXAMPLES["serious"] = ("It is not serious.", "情况不严重。")
EXAMPLES["strict"] = ("Be strict with yourself.", "严格要求自己。")
EXAMPLES["patient"] = ("The teacher is patient.", "老师很有耐心。")
EXAMPLES["active"] = ("Be active in class.", "课堂上积极一点。")
EXAMPLES["lazy"] = ("He is not lazy.", "他不懒。")
EXAMPLES["honest"] = ("An honest answer.", "一个诚实的回答。")
EXAMPLES["brave"] = ("A brave student.", "一个勇敢的学生。")
EXAMPLES["shy"] = ("Don't be shy.", "别害羞。")
EXAMPLES["nervous"] = ("I am a little nervous.", "我有一点紧张。")
EXAMPLES["confident"] = ("Speak in a confident voice.", "自信地说。")
EXAMPLES["proud"] = ("I am proud of you.", "我为你感到骄傲。")
EXAMPLES["lonely"] = ("Call me if you feel lonely.", "孤单的话就打电话给我。")
EXAMPLES["excited"] = ("I am excited.", "我很兴奋。")
EXAMPLES["surprised"] = ("I am surprised.", "我很吃惊。")
EXAMPLES["worried"] = ("Mom looks worried.", "妈妈看起来很担心。")
EXAMPLES["pleased"] = ("I am pleased with you.", "我对你很满意。")
EXAMPLES["glad"] = ("Glad to meet you.", "很高兴见到你。")
EXAMPLES["sorry"] = ("Sorry, I am late.", "对不起，我迟到了。")
EXAMPLES["welcome"] = ("Welcome to our school.", "欢迎来到我们学校。")
EXAMPLES["goodbye"] = ("Say goodbye.", "说再见。")
EXAMPLES["bye"] = ("Bye.", "再见。")
EXAMPLES["hi"] = ("Hi, how are you?", "嗨，你好吗？")
EXAMPLES["hello"] = ("Hello.", "你好。")
EXAMPLES["yes"] = ("Yes, please.", "好的，请。")
EXAMPLES["please"] = ("Sit down, please.", "请坐。")
EXAMPLES["thank"] = ("Thank you for your help.", "谢谢你的帮助。")
EXAMPLES["thanks"] = ("Thanks.", "谢谢。")
EXAMPLES["ok"] = ("OK, let's go.", "好，我们走吧。")
EXAMPLES["okay"] = ("Okay, I understand.", "好的，我明白了。")

DENY = (
    "装罐",
    "遗嘱",
    "生殖",
    "幼兽",
    "棋子",
    "主教",
    "蒸馏",
    "剧照",
    "鱼群",
    "女仆",
    "贬称",
    "假公济私",
    "代客",
    "修女",
    "未发酵",
    "女腔",
    "配备人手",
    "叫牌",
    "成群地游",
    "股票",
    "笨蛋",
    "生叶",
    "救球",
    "雄性",
    "字母",
    "惊起",
    "卖弄",
    "狭小",
    "流口水",
    "抓阄",
    "用言辞",
    "幼小",
    "依法",
    "网球",
    "性情",
    "弹性",
    "生徒",
)

POS_RE = re.compile(
    r"(?:^|[\n;；])\s*((?:aux|adj|adv|prep|conj|pron|num|art|interj|int|vt|vi|n|v|a|pl|abbr)\.)\s*",
    re.I,
)

POS_ZH = {
    "n.": "名词",
    "v.": "动词",
    "vt.": "动词",
    "vi.": "动词",
    "aux.": "助动词",
    "a.": "形容词",
    "adj.": "形容词",
    "adv.": "副词",
    "prep.": "介词",
    "conj.": "连词",
    "pron.": "代词",
    "num.": "数词",
    "art.": "冠词",
    "interj.": "感叹词",
    "int.": "感叹词",
}

CJK = re.compile(r"[\u4e00-\u9fff]")

PHONETIC_FIX = {
    "theatre": "ˈθiətə",
    "cd": "ˌsiːˈdiː",
    "ice cream": "aɪs kriːm",
}


def normalize_phonetic(raw: str) -> str:
    phonetic = (raw or "").strip().strip("/")
    if not phonetic:
        return ""
    phonetic = (
        phonetic.replace("ә", "ə")
        .replace("є", "e")
        .replace("’", "'")
        .replace("ˈ", "'")
    )
    phonetic = phonetic.replace("ɒ:", "ɔ:").replace("ɒː", "ɔː")
    phonetic = phonetic.replace(":", "ː")
    phonetic = phonetic.replace("'", "ˈ")
    phonetic = phonetic.replace("hw", "w")
    # ASCII digraphs used by the source dictionary, after lookalike fixes.
    phonetic = phonetic.replace("aɪ", "AI").replace("eɪ", "EI").replace("ɔɪ", "OI")
    phonetic = phonetic.replace("aʊ", "AU").replace("əʊ", "OU")
    phonetic = (
        phonetic.replace("ai", "aɪ")
        .replace("ei", "eɪ")
        .replace("oi", "ɔɪ")
        .replace("au", "aʊ")
        .replace("ou", "əʊ")
    )
    phonetic = (
        phonetic.replace("AI", "aɪ")
        .replace("EI", "eɪ")
        .replace("OI", "ɔɪ")
        .replace("AU", "aʊ")
        .replace("OU", "əʊ")
    )
    phonetic = phonetic.replace("əu", "əʊ")
    phonetic = re.sub(r"\s+", "", phonetic)
    return phonetic


def clean_gloss(gloss: str) -> str:
    text = re.sub(r"（[^）]*）|\([^)]*\)", "", gloss)
    text = text.replace("...", "……").replace("..", "……")
    text = re.sub(r"\s+", "", text).strip(" .。;；,，、")
    if not text or not CJK.search(text):
        return ""
    if any(bad in text for bad in DENY):
        return ""
    if len(text) > 12:
        return ""
    return text


def parse_senses(translation: str) -> list[tuple[str, list[str]]]:
    text = (translation or "").replace("\\n", "\n")
    matches = list(POS_RE.finditer(text))
    senses: list[tuple[str, list[str]]] = []
    if not matches:
        glosses = [clean_gloss(part) for part in re.split(r"[,，;；]", text)]
        glosses = [g for g in glosses if g]
        if glosses:
            senses.append(("", glosses[:2]))
        return senses
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        chunk = text[start:end]
        glosses = []
        for part in re.split(r"[,，;；]", chunk):
            gloss = clean_gloss(part)
            if gloss and gloss not in glosses:
                glosses.append(gloss)
            if len(glosses) == 2:
                break
        if glosses:
            senses.append((match.group(1).lower(), glosses))
    return senses


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        text = item.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def rank_key(entry: dict) -> tuple[int, int, str]:
    def num(value: object) -> int:
        try:
            number = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 10**9
        return number if number > 0 else 10**9

    return (num(entry.get("frq")), num(entry.get("bnc")), str(entry.get("word") or ""))


def build(source: list[dict]) -> list[dict]:
    zk = [row for row in source if "zk" in (row.get("tags") or [])]
    zk.sort(key=rank_key)
    words = []
    seen_ids: set[str] = set()
    for row in zk:
        surface = str(row.get("word") or "").strip()
        if not surface:
            continue
        key = surface.lower()
        word_id = key
        if word_id in seen_ids:
            continue
        primary = PRIMARY.get(key, [])
        senses = parse_senses(str(row.get("translation") or ""))
        dict_glosses: list[str] = []
        pos_labels: list[str] = []
        for pos, glosses in senses:
            if pos in POS_ZH and POS_ZH[pos] not in pos_labels:
                pos_labels.append(POS_ZH[pos])
            for gloss in glosses:
                if gloss not in dict_glosses:
                    dict_glosses.append(gloss)
        if primary:
            meanings = dedupe(primary)[:4]
        else:
            meanings = dict_glosses[:4]
        if not meanings:
            found = CJK.search(str(row.get("translation") or ""))
            if not found:
                continue
            chunk = CJK.findall(str(row.get("translation") or ""))
            if not chunk:
                continue
            meanings = ["".join(chunk)[:8]]
        accept = list(meanings)
        accept.extend(ALIASES.get(key, []))
        # If we hand-picked the learner meaning, don't also accept obscure
        # dictionary senses such as 门派 for school. Otherwise keep the
        # cleaned dictionary glosses so a real second meaning still counts.
        if not primary:
            for gloss in dict_glosses:
                if len(gloss) >= 2:
                    accept.append(gloss)
        accept = dedupe(accept)
        example = EXAMPLES.get(key)
        item = {
            "id": word_id,
            "word": surface,
            "phonetic": PHONETIC_FIX.get(key) or normalize_phonetic(str(row.get("phonetic") or "")),
            "meanings": meanings,
            "accept": accept,
        }
        if not primary and len(pos_labels) == 1:
            item["pos"] = pos_labels[0]
        if example and isinstance(example, tuple) and len(example) == 2:
            en, zh = example
            if isinstance(en, str) and isinstance(zh, str) and en and zh:
                item["example"] = en
                item["exampleZh"] = zh
        words.append(item)
        seen_ids.add(word_id)
    return words


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: build-words.py collins.json words.json")
    with open(sys.argv[1], encoding="utf-8") as handle:
        source = json.load(handle)
    words = build(source)
    payload = {
        "version": 1,
        "order": "ECDICT/collins frequency rank (frq, then bnc), most frequent first",
        "source": "zk-tagged entries from cd155/collins-vocabulary, derived from skywind3000/ECDICT. Both MIT. Learner glosses, aliases, and short examples were edited for a weak Shanghai Grade 9 student.",
        "count": len(words),
        "words": words,
    }
    with open(sys.argv[2], "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with_example = sum(1 for word in words if word.get("example"))
    with_phonetic = sum(1 for word in words if word.get("phonetic"))
    print(f"words {len(words)} examples {with_example} phonetics {with_phonetic}")
    print("--- head ---")
    for word in words[:12]:
        print(word["word"], word["phonetic"], " / ".join(word["meanings"]))
    print("--- checks ---")
    by_id = {word["id"]: word for word in words}
    for sample in ("can", "will", "even", "still", "mean", "fast", "happy", "school", "light", "right"):
        word = by_id.get(sample)
        if not word:
            print("MISSING", sample)
            continue
        print(sample, word["meanings"], "accept", word["accept"][:8])


if __name__ == "__main__":
    main()
