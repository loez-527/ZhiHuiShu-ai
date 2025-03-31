"""
===============================================
流程图
打开浏览器 → 输入网址 → 判断是否需要登录 → 等待页面加载完成 → 点击我的任务-全部(已修改不点击全部) → 获取到页面html → 解析html
                              ↓                                                               ↓
                          执行登录函数    ↗                                              获取学习状态（进度）
                                                                                              ↓
                                                                                      点击未完成章节进行学习
                                                                                              ↓
                                                                                      页面右侧再次获取并解析html
                                                                                              ↓
                                                                            检查进度未满100%或者掌握度未满100%（后续开发....）的进行学习
                                                                                              ↓
                                                                                    找到页面需要学习的资源（必学） → 掌握度（可选）
                                                                                    ↙         ↓             ↘
                                                                                  视频       文档              链接
                                                                                ↙             ↓                   ↘
                                                            检测标签text()是否含有"已完成"   点击后等待3s"已完成"      点击后出现新标签页，等待2s
                                                                        ↙                     ↓                       ↘
                                                                有则跳过，无则观看     检测标签text()是否含有"已完成"  ←    关闭新标签（注意！不要把课程标签页误关了）
                                                                     ↙                        ↓
                                                        提取视频时长再加2s延时      没有的话尝试再次点击（不做检测）并提示用户
                                                                 ↙
                                                再次调用函数检测标签text()是否含有"已完成"
                                                            ↙
                                            有则继续下一个，无则持续20s，如果还是没有则跳过并提示用户
                                                        =============================================================================
                                                                                             ↓
                                                                                    返回我的任务界面（刷新进度）
                                                                                             ↓
                                                                                      ↻ 再次重复上述步骤






======================
      导入区
======================
"""

import logging
import os
import re
import traceback
from datetime import datetime
from time import time, sleep
from DrissionPage import Chromium, ChromiumOptions
import json
import hashlib
from pathlib import Path
from difflib import SequenceMatcher
from configparser import ConfigParser
import sys
# from GUI import RedirectText, ConsoleInput  # 如果放在同一个文件中可以省略


# ======================
#  全局异常处理 & 日志配置
# ======================
def global_exception_handler(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 写入错误日志
    with open("error.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] 错误详情:\n{error_msg}\n{'=' * 50}\n")

    # 控制台输出
    print(f"\n发生错误，日志已保存至：{os.path.abspath('error.log')}")
    print("=" * 50)
    print(error_msg)
    # input("\n按 Enter 键退出程序...")
    print("\n按 Enter 键退出程序...")
    sys.stdin.readline().strip()
    sys.exit(1)


def setup_logger():
    """配置日志记录"""
    logging.basicConfig(
        filename='app.log',
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


# 初始化配置
sys.excepthook = global_exception_handler  # 必须放在最前面
setup_logger()


# 题库文件路径
QUESTION_BANK = Path("question_bank.json")
"""
=============
    函数区
=============
"""


# 执行登录功能

def login(tab,conf):
    """无限重试的极简登录函数"""


    while True:
        # 输入账号密码
        username = conf['username']
        password = conf['password']


        tab.ele('xpath://*[@id="lUsername"]').clear()
        tab.ele('xpath://*[@id="lUsername"]').input(username)
        tab.ele('xpath://*[@id="lPassword"]').clear()
        tab.ele('xpath://*[@id="lPassword"]').input(password)

        # 点击登录
        tab.ele('xpath://*[@id="f_sign_up"]/div[1]/span').click()

        print("登录中......\n请进行滑块验证后再继续...")
        wait()

        # 验证登录是否成功
        if "login" not in tab.url:
            print("✅ 登录成功")
            break

        print("登录失败，3秒后重试...")
        tab.wait(3)


def load_config():
    """读取配置文件"""
    config = ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')

    if not os.path.exists(config_path):
        raise FileNotFoundError(f'❌ 配置文件 {config_path} 不存在，请检查路径')

    config.read(config_path, encoding='utf-8')

    return {
        'username': config.get('Credentials', 'username'),
        'password': config.get('Credentials', 'password'),
        'chrome_path': config.get('Browser', 'chrome_path'),
        'course_url': config.get('Course', 'url')
    }



# 等待用户操作完成
def wait():
    while 1:
        # l = input("是否继续:y/n\n")
        print('是否继续:y/n (输入法切换到英文输入)')
        l = sys.stdin.readline().strip()
        if l == 'y':
            break
        else:
            continue


# 进度条
def wait_with_progress(seconds):
    start = time()
    width = 35  # 进度条长度

    while (elapsed := time() - start) < seconds:
        percent = elapsed / seconds
        bar = ('█' * int(width * percent)).ljust(width, ' ')
        remain = seconds - elapsed
        m, s = divmod(remain, 60)
        # print(f'\r[ {bar} ] {percent:.1%} | 剩余 {int(m)}分{int(s)}秒', end='')
        print(f'\r[ {bar} ] {percent:.1%} | 剩余 {int(m)}分{int(s)}秒', end='', flush=True)
        sleep(0.5)  # 更新进度条频率/s
    print('\n完成！')


# 处理任务数据（过滤过期+智能排序）
def process_tasks(raw_data):
    """简化过滤排序（排除过期+进度100%）"""
    from datetime import datetime
    import re

    now = datetime.now().timestamp()

    filtered_data = [
        item for item in raw_data
        # 过滤条件：未过期 且 进度未完成
        if (
            datetime.strptime(
                item['任务期限'].split(' - ')[1].strip(),
                "%Y-%m-%d %H:%M:%S"
            ).timestamp() > now
            and item['学习进度'].strip() != '100%'  # 清理空格后判断
        )
    ]

    return sorted(
        filtered_data,
        key=lambda x: (
            # 原排序逻辑保持不变
            datetime.strptime(
                x['任务期限'].split(' - ')[1].strip(),
                "%Y-%m-%d %H:%M:%S"
            ).timestamp(),
            0 if x['学习状态'] == '学习中' else 1,
            int(re.findall(r'\d+', x['章节'])[0]) if re.findall(r'\d+', x['章节']) else 999
        )
    )


# 小节学习状态
def parse_knowledge_points(tab):
    points = []

    # 获取所有知识点容器
    items = tab.eles('xpath://div[@class="collapse-item"]/div[@class="text"]')

    for item in items:
        try:
            # 提取知识点名称
            name = item.ele('xpath:.//span[@class="text-content"]').text.strip()

            # 定位状态容器（关键修改）
            status_div = item.ele('xpath:.//div[not(@class) and @data-v-08f65cc7]')  # 定位没有class的div容器

            # 初始化默认值
            progress = '0%'
            mastery = '0%'  # 根据示例结构默认设为100%
            special = ''

            # 获取所有状态span（关键修改）
            status_spans = status_div.eles('xpath:.//span[contains(@class, "addition")]')

            # 解析状态信息
            for span in status_spans:
                text = span.text.strip()
                if not text:
                    continue

                # 处理进度
                if "进度" in text:
                    progress_match = re.search(r'(\d+)%', text)
                    progress = f"{progress_match.group(1)}%" if progress_match else '0%'

                # 处理掌握度
                elif "掌握度" in text:
                    mastery_match = re.search(r'(\d+)%', text)
                    mastery = f"{mastery_match.group(1)}%" if mastery_match else '100%'

                # 处理免考核
                elif "免考核" in text:
                    special = "免考核"
                    mastery = '100%'  # 免考核项默认掌握度100%

            # 特殊逻辑：当有免考核且未明确掌握度时
            if special and not any("掌握度" in s.text for s in status_spans):
                mastery = '100%'

            points.append({
                '名称': name,
                '进度': progress,
                '掌握度': mastery,
                '特殊状态': special
            })

        except Exception as e:
            print(f"解析知识点异常：{str(e)}")
            continue

    return points


# 小节学习功能
def study_knowledge_points(tab, browser):
    items = tab.eles('xpath://div[@class="resources-section"][1]//div[@class="resources-item"]')  # 定位到必学资源
    # print(items)
    for item in items:
        # print(item.text)
        lwxk_2 = item.ele('xpath:.//div[@class="video-wrap"]//div[@class="video-img-bg"]').next(2, ele_only=False)  # 3个占位符，第1个是文档型（包括外链），2是视频，3是已完成
        lwxk_3 = item.ele('xpath:.//div[@class="video-wrap"]//div[@class="video-img-bg"]').next(3, ele_only=False)  # 3个占位符，第1个是文档型（包括外链），2是视频，3是已完成
        # 先判断是否完成
        if lwxk_3:
            print("\n该资源已完成...")
            tab.wait(1)
            continue
        else:
            # 判断是什么类型：视频/文档
            if lwxk_2:
                # 调用视频学习功能
                print("该资源为视频")
                video_study(lwxk_2, item, tab)
                continue
            else:
                # 调用文档学习功能
                print("该资源为非视频")
                documentation_study(item, tab, browser, item)
                continue

# 清理括号内全角空格
def clean_brackets(text):
    # 1. 移除括号内仅含空白（含全角空格）的情况
    text = re.sub(r"（[\s\u3000]*）", "", text)

    # 2. 清理括号内的所有全角空格（保留其他内容）
    text = re.sub(
        r"（([^）]*)）",
        lambda m: "（" + m.group(1).replace("\u3000", "") + "）",
        text
    )
    return text


# ======================
# 题库相关函数
# ======================
def load_question_bank():
    """加载现有题库"""
    if QUESTION_BANK.exists():
        with open(QUESTION_BANK, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


# 搜索题库答案
def search_in_bank(question, options, bank_path='question_bank.json'):
    """返回匹配到的答案文本列表（直接对应选项内容）"""
    try:
        with open(bank_path, 'r', encoding='utf-8') as f:
            bank = json.load(f)
    except FileNotFoundError:
        return None

    def clean(text):
        return re.sub(r'[^\w\u4e00-\u9fff]', '', text).lower().replace('\u3000', '')

    current_clean = clean(question)
    current_opts = [clean(opt) for opt in options]

    for item in bank:
        # 题目模糊匹配
        bank_clean = clean(item['question'])
        if SequenceMatcher(None, current_clean, bank_clean).ratio() < 0.9:
            continue

        # 选项内容匹配（顺序无关）
        bank_opts = [clean(opt) for opt in item['options']]
        if set(current_opts) != set(bank_opts):
            continue

        # 直接返回题库中的答案文本列表
        return item['answer']

    return None

# 新增的题库保存函数
def save_to_bank(question_text, options, answers, question_type, file_path='question_bank.json'):
    # 生成题目唯一标识（避免重复）
    content_hash = hashlib.md5(f"{question_text}{''.join(options)}".encode('utf-8')).hexdigest()

    # 构建题目数据
    question_data = {
        "question": question_text,
        "options": options,
        "answer": answers,
        "type": question_type,
        "hash": content_hash  # 用于后续快速查重
    }

    # 读取现有题库
    bank = []
    if Path(file_path).exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            bank = json.load(f)

    # 检查是否已存在
    if not any(item['hash'] == content_hash for item in bank):
        bank.append(question_data)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(bank, f, ensure_ascii=False, indent=2)
        print("已保存到题库\n")
    else:
        print("题库中已存在该题\n")

# 从当前页面提取题目信息
def extract_question(tab):
    """从当前页面提取题目信息"""
    global options
    try:
        # 进入解析页面
        tab.ele('x://span[text()="查看作答记录与解析"]').click(by_js=True)
        tab.wait.load_start(timeout=3,raise_err=False)

        items = tab.eles('x://div[@class="exam-item relative"]') # 获取题目列表对象
        for item in items:

            # 提取题目正文
            question_text = item.ele('xpath:.//div[@class="quest-title"]//p//p').text
            question_text = clean_brackets(question_text)
            print(question_text)

            # 提取所有选项
            if item.ele('x:.//div[@class="quest-type"]',timeout=1):   # 选择题型
                options = [opt.text for opt in item.eles('xpath:.//span[@class="el-checkbox__label"]//p | .//span[@class="preStyle"]//div[@class="inner-box"]//p')]

                # 提取正确答案（提交后显示的答案）
                correct_options = item.ele('xpath:.//p[@class="answer-title"]')
                parts = re.split(r'[、：]', correct_options.text)
                answer = parts[1:] # 去除"参考答案"

                # 将选项abcd转换为对应文字选项
                answers = []
                for letter in answer:
                    answers.append(options[ord(letter) - ord('A')])
                # print(answers)

                # 确定题型
                question_type = '多选题' if len(answers) > 1 else '单选题'
                # print(question_type)

                # 新增保存调用
                save_to_bank(question_text, options, answers, question_type)
            elif item.ele('x:.//div[@class="quest-type judge"]'):   # 判断题型
                options = ['对','错']

                # 提取正确答案（提交后显示的答案）
                correct_options = item.ele('xpath:.//p[@class="answer-title"]')
                parts = re.split(r'[、：]', correct_options.text)
                answer = parts[1:]  # 去除"参考答案"

                # 将选项转换为列表，保证与选择题格式一致
                answers = list(answer)
                # print(answers)

                question_type = '判断题'
                # print(question_type)

                # 新增保存调用
                save_to_bank(question_text, options, answers, question_type)


    except Exception as e:
        print("题目提取失败：", str(e))
        return None


# ======================
# 完善后的掌握度功能
# ======================
def mastery(tab, browser):
    # 初始化题库
    question_bank = load_question_bank()

    # 进入答题流程
    tab.ele('xpath://div[text()=" 提升掌握度 "]').click()
    tab.wait.doc_loaded()

    while True:
        try:


            # 如果题库中没有则默认选第1个选项提交答案（触发显示正确答案）
            if tab.ele('xpath://span[text()="提交作业"]', timeout=2):

                # 按照题目数量循环答题
                content = len(tab.eles('xpath://div[@class="el-tree-node__content" and @style="padding-left: 18px;"]'))
                for num in range(1, content + 1):

                    # 按顺序点击题目：1，2，3...
                    tab.ele(f'xpath://div[@class="el-tree-node__content" and @style="padding-left: 18px;"]//span[@class="font-sec-style-node" and text()="{num}"]').click(by_js=True)
                    tab.wait(1)

                    # 获取题目及选项、题型
                    question_type = tab.ele('x://span[@class="letterSortNum fl"]').text.split()[-1] #题型

                    question_text = tab.ele('x://div[@class="centent-pre"]//p').text # 题目
                    options = [i.text for i in tab.eles('x://label[@class="el-checkbox"]//p//span | //div[@class="preStyle fl stem"]')]# 选项

                    # 去题库搜索答案，如果没有则默认选第一个
                    # ========== 新增题库搜索逻辑 ==========
                    answer_indices = search_in_bank(question_text, options)
                    if answer_indices:
                        # 点击题库中找到的答案选项
                        for idx in answer_indices:
                            # 通用定位所有可能元素
                            candidates = tab.eles('x://label[@class="el-checkbox"]//p//span | //div[@class="preStyle fl stem"]//p | //div[@class="preStyle fl stem"]')
                            # 过滤匹配项
                            target = next((
                                el for el in candidates
                                if idx in el.text.replace(' ', '').replace('\n', '')
                            ), None)
                            if target:
                                target.click(by_js=True)

                    else:
                        print('题库中没有该题，默认选A')
                        # 随机选择答案（比如都选第一个）确保能触发结果页
                        tab.ele('xpath://li[@class="clearfix"][1] | //label[@class="el-checkbox"][1]').click(by_js=True)



                tab.ele('xpath://span[text()="提交作业"]').click(by_js=True)
                # 等待5s
                browser.wait(5)



            # 在结果页获取掌握度是否达到100%
            if (num := tab.ele('xpath://div[contains(@class, "charts-label-rate")]', timeout=5)):

                if '100' not in num.text:
                    # 提取题目信息并保存到题库
                    extract_question(tab)


                    # 调用封装好的重新答题函数
                    if click_retry(tab,browser):
                        continue  # 成功跳转则继续循环
                    else:
                        tab.wait(3)
                        if tab.ele('xpath://span[text()="提交作业"]'):
                            continue
                        else:
                            print('⛔ 严重错误，终止程序')
                            break  # 彻底失败时退出循环


                else:
                    tab.ele('xpath://div[@class="backup-icon"]').click(by_js=True) # 从答题结束界面，返回到小节资源学习界面
                    tab.wait(2)
                    break

        except Exception as e:
            print("答题流程异常：", str(e))
            # 尝试恢复状态
            if tab.ele('xpath://div[text()="关闭"]', timeout=2):
                tab.ele('xpath://div[text()="关闭"]').click()
            break


# 视频学习功能
def video_study(ocs, item, tab):
    tab.wait(1)
    item.ele('xpath:.//div[@class="video-wrap"]').click(by_js=True)

    uiih = ocs.text
    # print(uiih)
    print("开始播放视频")

    # 计算视频时长，展示进度条
    wait_with_progress(sum(x * int(t) for x, t in zip([3600, 60, 1], f"{uiih}".split(':'))))
    print("播放完成,即将学习下一个资源")
    tab.wait(10)


# 文档或链接学习功能
def documentation_study(doc, tab, browser, item):
    doc.ele('xpath:.//div[@class="video-wrap"]').click(by_js=True)

    tab.wait(2)

    # 判断是否有新标签页出现，是则关闭
    if browser.tabs_count > 2:
        print("已自动关闭新标签，继续学习下一个资源")
        tab.close(others=True)
    else:
        print("非第三方链接，正在检查是否已完成....")
        if item.ele('xpath:.//div[@class="video-wrap"]//div[@class="video-img-bg"]').next(3, ele_only=False):
            print("已完成，即将学习下一个资源")


def click_retry(tab,browser, max_retries=10, check_interval=1):
    """
    智能重试点击重新答题按钮直到成功跳转或达到最大重试次数
    :param tab: 页面对象
    :param max_retries: 最大重试次数(默认10次)
    :param check_interval: 每次检测间隔(秒)
    :return: True表示成功跳转，False表示失败
    """
    # 目标界面特征元素选择器（根据实际情况修改）
    target_selector = 'xpath://span[text()="提交作业"]'  # 示例：题目面板元素
    retry_button_selector = 'xpath://div[@class="submit"]//span[text()="重新答题"]'

    for attempt in range(1, max_retries + 1):
        try:
            print(f'▶ 尝试第 {attempt}/{max_retries} 次操作...')

            # 优先检查是否已到达目标界面
            if tab.ele(target_selector, timeout=0.5):
                print('✅ 已检测到目标界面，无需重试')
                return True

            # 动态查找重新答题按钮（避免陈旧元素引用）
            retry_btn = tab.ele(retry_button_selector, timeout=2)
            if not retry_btn:
                print('⚠ 未找到重新答题按钮')
                continue

            # 执行点击操作
            print('🖱 点击重新答题按钮')
            retry_btn.click(by_js=True)  # 拟人化点击

            # 点击后等待2s检查是否跳转成功
            browser.wait(2)
            if tab.ele(target_selector, timeout=3):
                print('✅ 成功进入答题界面')
                return True

            # 双重验证：检测按钮是否消失
            if not retry_btn.stale:
                print('⚠ 点击后按钮仍存在，可能未跳转')
                tab.wait(check_interval)
                continue

            print('🔄 页面可能正在跳转，等待验证...')
            tab.wait(check_interval)

        except Exception as e:
            error_type = type(e).__name__
            print(f'⚠ 操作异常: {error_type} - {str(e)}')
            tab.wait(check_interval)
            continue

    # 自动重试失败处理
    print(f'''
    ========== 需要人工协助 ==========
    自动重试{max_retries}次未成功，请手动：
    1. 检查页面是否卡顿
    2. 手动点击 [重新答题] 按钮
    3. 确认进入答题界面后按回车继续
    ================================''')

    # 人工干预后验证
    while True:
        # input('>> 请按回车键确认已手动处理...')
        print('>> 请按回车键确认已手动处理...')
        sys.stdin.readline().strip()
        if tab.ele(target_selector, timeout=3):
            print('✅ 人工干预成功')
            return True
        print('❌ 未检测到目标界面，请确认操作')


def get_valid_input(prompt, valid_choices,Tab,max_attempts=3):
    """获取有效输入，最多尝试max_attempts次"""
    attempts = 0
    while attempts < max_attempts:
        print(prompt,end='')
        enter = sys.stdin.readline().strip()

        if enter in valid_choices:
            return enter

        attempts += 1
        remaining = max_attempts - attempts

        if remaining > 0:
            if attempts == 1:
                print("输错了，再来！")
            elif attempts == 2:
                print("再给你一次几会！")
            print(f"（剩余尝试次数: {remaining}）\n")
        else:
            print("....... .........\n不！学！算！了！")
            Tab.quit()
            return None

    return None  # 理论上不会执行到这里


"""
==================
    功能执行区
==================
"""


def main(conf):
    try:
        logging.info("程序启动")

        if not os.path.exists('questions.json'):
            with open('questions.json', 'w') as f:
                json.dump([], f)

        path = conf['chrome_path']  # 请改为你电脑内Chrome可执行文件路径
        # print(path)
        co = ChromiumOptions().set_browser_path(path)

        # 连接浏览器
        browser = Chromium(co)



        # 新建标签页,打开网址
        tab = browser.new_tab(
            url=conf['course_url'])



        # 检查是否需要登录
        if "login" in tab.url:
            login(tab,conf)


        print('开始学习')
        print('正在获取学习进度......')
        # 查找并点击我的任务
        if tab.wait.doc_loaded(timeout=10, raise_err=True):
            tab.ele('xpath://span[text()="我的任务"]').click(by_js=True)
            tab.wait(1)
            tab.ele('x://span[text()="全部"]').click(by_js=True)

        item = tab.eles('xpath://div[contains(@class,"knowledge-item")]')

        # 获取当前任务状态
        data = []
        for i in item:
            knowledge_title = i.ele('xpath:.//div[@class="task-title"]/text()')
            knowledge_status = i.ele('xpath:.//div[@class="status-tag"]/span/text()')
            knowledge_schedule = i.ele('xpath:.//div[@class="task-schedule"]/div[@class="text-schedule"]/text()')
            knowledge_time = i.ele('xpath://div[@class="task-time"]/text()')
            data.append({
                '章节': knowledge_title,
                '学习状态': knowledge_status,
                '学习进度': knowledge_schedule,
                '任务期限': knowledge_time
            })

        # 对字典按照截止时间重新排序
        sorted_data = process_tasks(data)
        print(f"需要学习的章节：{sorted_data}")

        # 　开始按照顺序学习
        for task in sorted_data:
            print(f"\n{'=' * 30}\n进入章节：{task['章节']}")

            # 通过章节标题定位对应元素
            tab.ele(f'xpath://div[text()="{task["章节"]}" and @class="task-title"]').click(by_js=True)

            # 确认进入对应章节
            task_name = task["章节"][0:3]
            if task_name not in tab.ele('x://div[@class="task-details-name"]').text:
                tab.ele('x://div[contains(text(),"第四章") and @class="task-title"]').click(by_js=True)
                tab.wait(1, 3)
                tab.ele(f'xpath://div[text()="{task["章节"]}" and @class="task-title"]').click(by_js=True)
                tab.wait(1)

            # 等待知识点加载（关键）
            tab.wait(1, 3)

            # 解析知识点
            points = parse_knowledge_points(tab)

            # 打印带特殊标记的结果
            for p in points:
                if p['特殊状态']:
                    # 免考核项目特殊格式
                    print(f"{p['名称']: <25} | [ {p['特殊状态']} ]")
                else:
                    # 常规项目显示进度和掌握度
                    print(f"{p['名称']: <25} | 进度：{p['进度']: <5} | 掌握度：{p['掌握度']: <5}")

            # enter = input("请选择：\n1.刷学习进度\n2.提升掌握度\n")
            # print("请选择：\n1.刷学习进度\n2.提升掌握度\n")


            enter = get_valid_input("\n请选择：\n1.刷学习进度\n2.提升掌握度", valid_choices=["1", "2"],Tab=browser)
            print()
            if enter == "1":
                print('稍等......')

                # 过滤掉免考核和进度100%的
                point = [p for p in points if (p['特殊状态'] != "免考核") and (p['进度'] != "100%")]
                # print(point)

                # 遍历需要学习的课程名称并执行点击---学习
                for p_dict in point:

                    if not tab.ele('x://div[@class="tab-item active"]//span[text()="全部"]'):
                        tab.ele('xpath://span[text()="我的任务"]').click(by_js=True)
                        tab.wait(1)
                        tab.ele('x://span[text()="全部"]').click(by_js=True)
                        tab.wait(1)

                    p_name = p_dict["名称"]
                    tab.wait(1)  # 延迟1s
                    tab.ele(f'xpath://span[contains(normalize-space(), "{p_name}") and @class="text-content"]').click(by_js=True)

                    # 等待页面加载
                    tab.wait.doc_loaded()
                    # 调用学习功能
                    study_knowledge_points(tab, browser)
                    tab.wait(1)
                    # 返回任务界面
                    tab.ele('xpath://img[@class="w-[40px] h-[40px] cursor-pointer"]').click(by_js=True)
                    tab.wait(1)
                    tab.ele('xpath://span[text()="我的任务"]').click(by_js=True)
                    tab.wait(1)

                    tab.ele('x://span[text()="全部"]').click(by_js=True)
                    tab.wait(1)

                    # 确认进入对应章节
                    task_name = task["章节"][0:3]
                    if task_name not in tab.ele('x://div[@class="task-details-name"]').text:
                        tab.ele('x://div[contains(text(),"第四章") and @class="task-title"]').click(by_js=True)
                        tab.wait(1, 3)
                        tab.ele(f'xpath://div[text()="{task["章节"]}" and @class="task-title"]').click(by_js=True)
                        tab.wait(1)

            elif enter == "2":
                print('稍等......')
                # 过滤掉免考核和进度100%且掌握度100%的
                point = [p for p in points if (p['掌握度'] != "100%") and (p['特殊状态'] != "免考核")]

                # 遍历需要学习的课程名称并执行点击---学习
                for p_dict in point:

                    if not tab.ele('x://div[@class="tab-item active"]//span[text()="全部"]'):
                        tab.ele('xpath://span[text()="我的任务"]').click(by_js=True)
                        tab.wait(1)
                        tab.ele('x://span[text()="全部"]').click(by_js=True)
                        tab.wait(1)

                    p_name = p_dict["名称"]
                    tab.wait(1)  # 延迟1s
                    tab.ele(f'xpath://span[contains(normalize-space(), "{p_name}") and @class="text-content"]').click(by_js=True)

                    # 等待页面加载
                    tab.wait.doc_loaded()
                    # 调用学习功能
                    # study_knowledge_points(tab, browser)
                    # tab.wait(1)

                    # 调用提升掌握度功能
                    mastery(tab,browser)
                    tab.wait(1)

                    # 返回任务界面
                    tab.ele('xpath://img[@class="w-[40px] h-[40px] cursor-pointer"]').click(by_js=True)
                    tab.wait(1)
                    tab.ele('xpath://span[text()="我的任务"]').click(by_js=True)
                    tab.wait(1)
                    tab.ele('x://span[text()="全部"]').click(by_js=True)
                    tab.wait(1)

                    # 确认进入对应章节
                    task_name = task["章节"][0:3]
                    if task_name not in tab.ele('x://div[@class="task-details-name"]').text:
                        tab.ele('x://div[contains(text(),"第四章") and @class="task-title"]').click(by_js=True)
                        tab.wait(1, 3)
                        tab.ele(f'xpath://div[text()="{task["章节"]}" and @class="task-title"]').click(by_js=True)
                        tab.wait(1)






        print("\n---再见---")



    except Exception as e:
        logging.critical("主程序异常终止", exc_info=True)
        raise  # 触发全局异常处理器


# ======================
#      执行入口
# ======================


if __name__ == '__main__':
    try:
        conf = load_config()
        # print("\033[32m欢迎使用本项目૮(˶ᵔ ᵕ ᵔ˶)ა\n本项目完全免费！如果觉得不错就打赏一下吧૮(˶ᵔ ᵕ ᵔ˶)ა\n使用前请先查看README文档\n遇到问题请打包好两个日志文件发送至下方邮箱⬇️\033[0m")
        # print('loez-527@outlook.com 或 3466017194@qq.com')

        main(conf)
    except Exception as e:
        print(str(e))
