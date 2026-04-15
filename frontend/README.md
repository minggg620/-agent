# Zero Realm Social Agent Frontend

美观的 Web 界面，用于与 Zero Realm Social Agent 交互。

## 功能特点

- 🎨 **现代化 UI 设计** - 使用 React + TailwindCSS 构建的玻璃拟态界面
- 🚀 **实时交互** - 通过 FastAPI 后端与 Agent 实时通信
- 🎯 **需求清晰识别** - 专门设计的输入界面，确保 Agent 不会忽略用户需求
- 📊 **可视化结果** - 实时显示 Agent 运行结果和性能指标
- 🌐 **多模式支持** - 支持 passive、active、competitive、defensive 四种运行模式

## 技术栈

- **前端**: React 18 + Vite
- **样式**: TailwindCSS + 自定义玻璃拟态设计
- **图标**: Lucide React
- **HTTP 客户端**: Axios
- **后端**: FastAPI (Python)

## 安装和运行

### 前置要求

- Node.js 18+ 
- Python 3.8+
- npm 或 yarn

### 安装步骤

1. **安装前端依赖**:
```bash
cd frontend
npm install
```

2. **安装后端依赖**:
```bash
cd ..
pip install -r requirements.txt
```

### 运行应用

1. **启动后端服务器**:
```bash
python -m api.server
```
后端将在 http://localhost:8000 运行

2. **启动前端开发服务器**:
```bash
cd frontend
npm run dev
```
前端将在 http://localhost:3000 运行

## 使用说明

1. **选择运行模式**:
   - **Passive**: 监控和观察模式
   - **Active**: 主动互动模式
   - **Competitive**: 完全竞争模式
   - **Defensive**: 防御和保护模式

2. **选择挑战类型**:
   - **Injection**: 对话注入挑战
   - **Credibility**: 信誉建立挑战
   - **Influence**: 影响力扩展挑战
   - **Monitor**: 信息监控挑战

3. **输入您的需求**:
   - 在文本框中详细描述您的需求
   - Agent 会认真分析并执行，不会忽略任何重要信息

4. **运行 Agent**:
   - 点击"运行 Agent"按钮
   - 查看实时运行结果和性能指标

## 项目结构

```
frontend/
├── src/
│   ├── App.jsx          # 主应用组件
│   ├── main.jsx         # 应用入口
│   └── index.css        # 全局样式
├── index.html           # HTML 模板
├── package.json         # 依赖配置
├── vite.config.js       # Vite 配置
├── tailwind.config.js   # TailwindCSS 配置
└── postcss.config.js    # PostCSS 配置
```

## API 端点

- `GET /api/v1/health` - 健康检查
- `GET /api/v1/modes` - 获取可用模式
- `GET /api/v1/challenges` - 获取可用挑战类型
- `POST /api/v1/run` - 运行 Agent

## 特性说明

### 需求清晰识别

前端界面专门设计以确保用户需求被正确传递：

1. **大文本输入区域** - 提供充足的空间详细描述需求
2. **明确提示** - 提醒用户 Agent 会认真分析需求
3. **结构化输入** - 将需求与其他参数分离，确保优先级
4. **实时反馈** - 显示 Agent 处理过程，让用户了解需求被正确处理

### 美观设计

- **玻璃拟态效果** - 现代化的半透明玻璃效果
- **渐变色彩** - 青色到蓝色的渐变主题
- **流畅动画** - 平滑的过渡和悬停效果
- **响应式布局** - 适配不同屏幕尺寸

## 开发

### 添加新功能

1. 在 `src/App.jsx` 中添加新的 UI 组件
2. 在 `api/server.py` 中添加新的 API 端点
3. 使用 TailwindCSS 进行样式定制

### 构建生产版本

```bash
npm run build
```

构建产物将生成在 `dist/` 目录中。

## 故障排除

### 前端无法连接后端

- 确保后端服务器正在运行 (http://localhost:8000)
- 检查 CORS 配置
- 查看浏览器控制台的错误信息

### 样式未加载

- 确保 TailwindCSS 依赖已正确安装
- 检查 `tailwind.config.js` 配置
- 重新启动开发服务器

## 许可证

MIT License
