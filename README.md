# commercial-trend

> 预测哪些研究领域正在走向商业化 —— 用**多源信号 + 诚实基线**，
> 而不是单一语料的词汇共现故事。
>
> Predict which research fields are about to commercialize —
> multi-source signals, honest baselines, leak-free evaluation.

[![Build & Deploy](https://github.com/zmath01/commercial-trend/actions/workflows/pages.yml/badge.svg)](https://github.com/zmath01/commercial-trend/actions/workflows/pages.yml)

**Live dashboard**: https://zmath01.github.io/commercial-trend/

## 追踪领域 / Tracked fields

统一采用与 `commercial-trend-fusion` 相同的 **15 个监测领域 / 32 个 arXiv 分类**：

AI/ML · 应用数学 · 计算机科学 · 软件工程 · 安全/加密 · 量化金融 · 金融科技 ·
量子计算 · 量子材料/电子 · 统计/复杂系统/涌现 · 量子模拟/超冷物质 · 光子学 ·
计算物理/科学计算 · 芯片（GPU/存储/架构） · 数字市场/机制设计

其中 FinTech 没有专属 arXiv 分类，使用 OpenAlex/GitHub/StackOverflow 多源信号；其余 14 个研究型领域由 32 个 arXiv 分类提供研究范围。完整 canonical mapping 见 `pipeline/topics.py`；fusion 语料抓取配置见
`commercial-trend-fusion/config.yaml`。

## 它做什么 / What it does

每个领域是一条多变量年度序列：**论文数（OpenAlex）、新建 GitHub
仓库数（GitHub Search）、StackOverflow 提问量（Stack Exchange API）**——
全部免 key、可脚本化、可完整回溯。管线计算：

- **CSI（商业化信号指数）** — 逐年归一化的多信号加权和（权重见 `pipeline/topics.py`，显式声明）；
- **Kleinberg 突发检测** — 统计显著的爆发区间（KDD 2002，两状态 Viterbi DP）；
- **动量** — YoY / 3 年 CAGR / 横截面 z-score；
- **共现图链接预测指标** — 共同邻居 / Jaccard / Adamic-Adar / 优先连接 /
  两跳有效电导（**作为基线**，不是卖点）；
- **逻辑回归预测** — 预测未来 2 年 CSI 增长是否超过中位数，
  用 **walk-forward 时间切分**评估，与持续性 / 先验 / 纯共现图三个基线对比。

完整论证见 [docs/THEORY.md](docs/THEORY.md)。

## 与"共现-电导"类项目的本质区别

| | 词汇共现类项目 | 本项目 |
|---|---|---|
| 预测目标 | 概念何时首次共现（词汇事件） | 领域何时商业化（经济事件） |
| 数据源 | 单一语料 | 文献 + 代码托管 + 问答社区（+专利可选） |
| 基线 | 随机 | 持续性 + 先验 + 共现图启发式 |
| 验证 | 单次回测 | walk-forward，无未来泄漏 |
| 资源 | 16G 内存跑 48 小时 | 流式逐领域处理，任意机器几分钟 |

## 快速开始 / Quickstart（WSL2 / Linux / macOS）

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 离线、确定性演示（CI 用的就是这个，无需任何 key）
.venv/bin/python main.py --sample

# 真实数据（自动磁盘缓存到 data/cache/；GitHub 限速可用 token 提速）
export GITHUB_TOKEN=ghp_xxx        # 可选
.venv/bin/python main.py --live --save-panel data/panel.json

# 本地预览
cd dist && python3 -m http.server 8000
# 打开 http://localhost:8000
```

## 部署到 GitHub Pages

仓库已带 `.github/workflows/pages.yml`：push 到 `main` 或每月 1 日 02:00 UTC
自动构建并部署。首次使用需在仓库设置里
**Settings → Pages → Build and deployment → Source 选 "GitHub Actions"**。

CI 现在跑 `--live`，使用 GitHub Actions 内置的 `GITHUB_TOKEN`，不把个人 token
写入仓库。若需要更高的 GitHub API 配额，应通过 GitHub Actions secret 配置个人
token，而不是把 token 写进代码或 workflow。

## 目录结构

```
pipeline/
  topics.py    # 十五领域 + 32 个 arXiv 分类映射 + CSI 权重
  ingest.py    # OpenAlex / GitHub / Stack Exchange 客户端 + 确定性样本生成器
  signals.py   # 增长、Kleinberg 突发、CSI、共现图与链接预测指标
  model.py     # 特征、逻辑回归、walk-forward 评估、当前排名
  site.py      # 静态看板生成（Chart.js，单文件 HTML）
main.py        # CLI 入口
docs/THEORY.md # 方法论与诚实局限
.github/workflows/pages.yml
```

## 诚实局限（先看这里再引用结论）

样本量是"领域×年"（十五级领域 × 十年），适合做**排序参考**，
不适合做精确预测；GitHub/SO 信号天然偏向工程领域；
OpenAlex 主题有注册延迟。详见 THEORY.md 第 4 节。

## License

MIT — 见 [LICENSE](LICENSE)。欢迎 fork、换领域配置、打脸我们的预测。
