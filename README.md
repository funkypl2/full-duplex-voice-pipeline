# Full-Duplex-Voice-Pipeline: Real-Time Interactive Voice System

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Architecture: Full Duplex](https://img.shields.io/badge/Architecture-Full%20Duplex%20%7C%20Barge--in-blueviolet.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-WebSocket-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Full-Duplex-Voice-Pipeline** 是一个基于异步协程事件驱动的**低延迟全双工语音交互引擎**。全面支持**双向并发音频流**、**实时流式 ASR**、**流式 LLM 首字快速吐字**、**流式标点断句预取 TTS**，以及核心的**随时打断机制（Barge-In Arbiter）**。

---

## 🔄 全双工状态机与打断机制 (State Machine & Barge-In)

```
                     ┌──────────────────┐
                     │       IDLE       │
                     └────────┬─────────┘
            User Starts       │         ▲
            Speaking          ▼         │ Playback Finished
                     ┌──────────────────┐
                     │    LISTENING     │
                     └────────┬─────────┘
              User Silence    │
              (ASR Endpoint)  ▼
                     ┌──────────────────┐
                     │     THINKING     │
                     └────────┬─────────┘
         First Token /        │
         Audio Chunk Ready    ▼
                     ┌──────────────────┐
         ┌───────────│     SPEAKING     │────────────┐
         │           └──────────────────┘            │
         │                                           │
         │ User Speaks (Barge-In)                    │
         ▼                                           │
 ┌───────────────┐                                   │
 │  INTERRUPTED  │                                   │
 └───────┬───────┘                                   │
         │                                           │
         │ • Dispatch Cancellation Token to LLM      │
         │ • Flush Audio Playback Buffer Queue       │
         │ • Transition immediately to LISTENING     │
         ▼                                           ▼
 ┌───────────────┐                           ┌───────────────┐
 │   LISTENING   │                           │     IDLE      │
 └───────────────┘                           └───────────────┘
```

### ⚡ 为什么需要全双工？
- **传统半双工 (Half-Duplex)**：类似对讲机，必须机械地等待机器把一段长回答全部读完，无法插话，交互体验僵硬生硬。
- **全双工 (Full-Duplex)**：类似真实真人通电话。用户任何时刻开口插话，系统在 **50ms 内立即停止播报并清空音频缓冲区**，中断大模型生成，无缝接管并倾听用户最新的意图。

---

## 🚀 快速上手 (Quick Start)

### 1. 安装依赖
```bash
cd 04-full-duplex-voice-pipeline
pip install -r requirements.txt
```

### 2. 运行全双工与打断机制仿真 Demo
无需声卡硬件，直接在终端中观察完整的全双工状态机流转与中途插话（Barge-In）即时切断过程：
```bash
python simulation_duplex.py
```

### 3. 启动 WebSocket 全双工网关服务
```bash
python server.py
# 或使用 uvicorn 直接启动
uvicorn server:app --host 0.0.0.0 --port 8000
```

服务就绪后，客户端可通过 `ws://localhost:8000/ws/duplex` 进行双向二进制音频流传输与 JSON 控制消息交互。

### 4. 运行单元测试
```bash
pytest tests/ -v
```

---

## 📡 WebSocket 控制协议规范

| 消息类型 (`type`) | 方向 | 说明 |
| :--- | :--- | :--- |
| `ready` | Server -> Client | 握手建立，全双工通道就绪 |
| `user_speech_start` | Client -> Server | VAD 检测到用户开始发声（可能触发打断） |
| `user_speech_end` | Client -> Server | 用户发声结束，包含转写文本 `text` |
| `barge_in` | Both | 显式触发即刻打断指令 |
| `log` | Server -> Client | 状态机流转与执行细节日志 |

---

## 📄 开源许可证
本项目采用 [MIT License](LICENSE) 授权协议。
