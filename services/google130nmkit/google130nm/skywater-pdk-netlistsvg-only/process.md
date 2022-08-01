# 此文件夹的处理方式

需求为只保留netlistsvg需要用到的文件 其他的文件都可以删掉

```
find . -name *.json ! -name definition.json -delete
find . -name *.svg ! -name *.schematic.svg -delete
```

