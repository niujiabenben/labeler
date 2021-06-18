# 标注工具模板

本项目提供标注工具的基础模板, 其他具体的标注工具可以在这个模板的基础之上进行开发.

### 检查代码的风格

``` shell
pylint lib tools     # 使用本目录中的.lintrc
yapf -ir lib tools   # 使用本目录中的.style.yapf
```


### 中文字体支持

lib.util.draw_chinese_textlines()方法用的是宋体, 字体文件为simsun.ttc.
Linux系统中, 可以用`fc-list :lang=zh-cn`命令查看当前机器的所有字体.
如果没有simsun.ttc, 则将Windows中对应的文件拷贝到Linux中即可.

Windows文件路径: `C:\Windows\Fonts\simsun.ttc`

Linux文件路径: `/usr/share/fonts/simsun.ttc`
