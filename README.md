# ncmdumpPy

> [!WARNING]
> 此 README 部分由 Copilot 根据程序生成。

一个用于解密网易云音乐 `.ncm` 文件的 Python 工具。支持提取音频文件、写入元数据、封面图像，并可批量处理目录中的 `.ncm` 文件。
参考 [ncmdump](https://github.com/taurusxin/ncmdump) 和 [ncmdump](https://github.com/QCloudHao/ncmdump) 项目。

## 特性

- 解密 `.ncm` 文件并输出标准音频格式
- 自动提取并写入音乐元数据
- 支持 MP3 和 FLAC 标签写入
- 支持封面图片嵌入
- 支持单文件和目录批量处理

## 运行

### 方法一：使用 Python 运行

> [!WARNING]
> 建议使用虚拟环境运行，防止`pycryptodemo`库出问题

1. 克隆仓库或下载脚本。
2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 运行以下命令查看帮助信息：

```bash
python ncmdumpPy.py -h # 显示帮助信息
```

### 方法二：使用二进制文件运行

下载 Releses 里发布的编译好的二进制文件即可。

## 使用方法

> [!MESSAGE]
> 如果你使用 Python 来运行，请使用 `python ncmdumpPy.py` 开始的方法
> 如果你下载了编译好的二进制文件，请使用 `ncmdumpPy` 开始的方法

```bash
python ncmdumpPy.py -i path/to/file1.ncm [path/to/file2.ncm ...] 
# 或者
ncmdumpPy -i path/to/file1.ncm  [path/to/file2.ncm ...]
```

批量处理目录：

```bash
python ncmdumpPy.py -d path/to/directory
# 或者
ncmdumpPy -d path/to/directory
```

如果想在解密后删除原始 `.ncm` 文件，添加 `-r` 参数：

```bash
python ncmdumpPy.py -i path/to/file.ncm -r
python ncmdumpPy.py -d path/to/directory -r
# 或者
ncmdumpPy -i path/to/file.ncm -r
ncmdumpPy -d path/to/directory -r
```

## 依赖

- pycryptodome
- mutagen

依赖已在 `requirements.txt` 中列出。

## 说明

- 输出文件会保存在与 `.ncm` 文件相同的目录中。
- 文件格式会根据 `.ncm` 中的元数据自动选择，默认输出为 MP3。
