##  智慧树ai课-细胞生物学定制版

智慧树视频课辅助脚本，开启挂机摸鱼时代~



------

#### 2025/3/30  更新
**近期更新:**

- 修复了部分人先刷掌握度而进度为0导致获取到的进度信息列表超索引问题
- 摒弃黑色控制台的运行方式，为程序增加了ui界面
- 舍弃文件形式，将程序打包成单程序（但体积会略微增大）

#### 2025/3/27  更新

- 优化登录功能
- 可在配置文件config.ini修改账号密码等 !
- 增加新功能---提升掌握度
- 可自动答题（优先题库搜索）
- 将解析页面题目及答案自动存入题库
- 优化写入题库逻辑，自动去重，采用哈希算法MD5对题目进行唯一标识
- 优化搜索逻辑，采用模糊匹配，增加容错率
- 修复了重新答题bug--点击后可能出现错误提示导致没能成功跳转到新页面
- 修复部分选项文字在浏览器上显示正常（实际上有不可见字符），但题目始终匹配不上的问题
- 修复了重新答题bug--点击后判定不准确问题

#### 2025/3/23  更新
- 修复了非视频资源弹出的新标签页，将其正确关闭
- 由于大多数Chrome浏览器没有安装再C盘，导致启动失败，添加了浏览器路径自定义功能
- 添加全局异常捕获，并保存到日志

------

#### 一、程序介绍:

**项目简介：**

这是一个可无人监督的自动化程序，基于开源的DrissionPage，由Python编写而成；相对于常见的油猴脚本，本程序可有效防止被网页检测。核心原理是使浏览器模拟用户的点击操作。

**程序功能:**
- **支持半自动登录**
- **自动播放和提升掌握度**
- **跳过弹窗和弹出的题目**
- **检测资源类型（视频、文档、外链）按需学习**
- **支持智慧树ai课**
- 检测当前学习进度并后台实时更新
- 视频支持进度条展示
- 各种自定义配置

#### 二、使用须知:

1.请确保系统为windows10及以上，**仅限本院学生使用！**

2.填写配置文件

- 需要使用Chrome（没有就去下载），edge还没适配
- 文件里的 **chrome_path项** 用于自定义浏览器路径, 但必须精确到**浏览器可执行文件的位置**; **注意: 所有配置项都不加"引号"**

​    若不填此项, 就会启动位于系统默认位置的浏览器

​    不知浏览器的安装路径? 请看文件内提示 ！ 

3.根据文件内的说明填写好配置信息，一定要**保存后**再退出

4.运行 **智慧树-细胞生物学学习脚本3.0.exe**，也可以在这里填写和修改配置（第一次使用建议去config.ini填写，里面有提示！）

5.开始学习
- 配置都填写完成后，点击开始学习

- 这时会启动chrome浏览器打开一个网页，就是课程的地址，默认是细胞生物学

- 脚本会自动将账号密码填写到登录网页中（如果课程网页没关闭就不会登录，直接进入学习了）

- **先进行滑块验证**，**进入课程页面后**再在控制台输入**y**，回车确定

- 这时脚本会获取当前进行中的任务及进度

- 可以选择提升学习进度（1）或者提升掌握度（2）（**学习某一个后可以再次点击开始学习选择提升另外一个**）

- 如果选择学习进度，脚本会按顺序依次进入课程页面，根据不同类型的学习资源智能化学习，直到列表中进度都达到100%

- 如果选择掌握度，由于作者本身也没有题库૮(˶ᵔ ᵕ ᵔ˶)ა，所以第一次会默认选第一个选项，提交后会到解析页面自动提取题目和答案并保存到题库中（目录下会自动生成json文件）



------

**问题/bug:**

**!!!在滑块验证时不要拖动程序窗口，不然会卡。解决方式：同时按键盘Tab+Alt!!!**


有什么需求和bug请打包好两个日志文件（error.log，app.log）发送到邮箱⬇️

本项目完全免费，但还是建议打赏一下，刷掌握度的时候，文件夹内会自动生成2个题库文件questions.json，question_bank.json(***理论应该只有一个的，但本着能运行就不动的原则，所以就这样吧***)建议一起发我邮箱૮(˶ᵔ ᵕ ᵔ˶)ა



<img src="README.assets/mm_reward_qrcode_1743064061535.png" alt="mm_reward_qrcode_1743064061535" style="zoom:50%;" />

**作者的mail:** loez-527@outlook.com 或 3466017194@qq.com
       

**免责声明：本程序只可用于学习和研究计算机原理，严禁将此文件夹及其内容用于任何商业或非法用途。对于因违反此规定而产生的任何法律后果，用户需自行承担全部责任。**

**本免责声明的最终解释权归声明者所有！**

