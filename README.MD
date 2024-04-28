## 词达人自动刷题脚本
`词达人自动过班级任务,自学任务`
- 自动过自学任务
- 过班级任务
- 随时可能失效,**且用且珍惜**
- 可选择过某一章节
- 得分95+（异常情况下可能90+） 


## 日志

**2024-4-28**
+ 使用本地模型获取单词原型（速度可能有所下降）

**2024-04-26**
+ 在原有源码的基础上添加了手动选择章节功能
+ 将token等设置从config文件改为了在控制台输入

<!-- <details> <summary> <b>日志(点击查看进程)</b> </summary>

</details> -->


## 声明
本项目初始源码来源自 [github123666/cidaren](https://github.com/github123666/cidaren)

**遵循MIT协议,仅供学习参考。**

### **删除请联系harold.lach.lei@gmail.com**

## 配置方法
```angular2html
pip install -r requirements.txt
```

安装模型
```angular2html
pip install spacy
python -m spacy download en_core_web_sm
```