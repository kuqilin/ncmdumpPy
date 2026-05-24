# ncmdumpPy

一个用于解密网易云音乐 `.ncm` 文件的 Python 工具。支持提取音频文件、写入元数据、封面图像，并可批量处理目录中的 `.ncm` 文件。

## 特性

- 解密 `.ncm` 文件并输出标准音频格式
- 自动提取并写入音乐元数据
- 支持 MP3 和 FLAC 标签写入
- 支持封面图片嵌入
- 支持单文件和目录批量处理

## 安装

>[warning] 建议使用虚拟环境运行，防止`pycryptodemo`库出问题

1. 克隆仓库或下载脚本。
2. 安装依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
python ncmdumpR.py -i path/to/file1.ncm [path/to/file2.ncm ...] 
```

批量处理目录：

```bash
python ncmdumpR.py -d path/to/directory
```

如果想在解密后删除原始 `.ncm` 文件，添加 `-r` 参数：

```bash
python ncmdumpR.py -i path/to/file.ncm -r
```

## 依赖

- pycryptodome
- mutagen

依赖已在 `requirements.txt` 中列出。

## 说明

>[warning] 此 README 由 Copilot 根据程序生成。

- 输出文件会保存在与 `.ncm` 文件相同的目录中。
- 文件格式会根据 `.ncm` 中的元数据自动选择，默认输出为 MP3。
