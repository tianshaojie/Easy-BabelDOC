## FastAPI 单文件可执行程序打包计划（Windows）

### 目标
- 为 Easy-BabelDOC 提供 Windows 下“一键双击即可运行”的部署形式。
- 将 React 前端编译为静态资源，并由 FastAPI 统一对外提供，不再需要用户手动启动前后端。
- 通过 PyInstaller 生成单个 `.exe`，简化分发，适合对命令行不熟悉的用户。

### 前提准备
1. 开发机安装依赖：
   - Node.js 18+（负责前端构建）。
   - Python 3.10+（建议与生产一致，便于调试）。
   - PyInstaller（`pip install pyinstaller`）。
2. 项目目录结构假设保持现状：`frontend` 代码位于 `src/`，后端位于 `backend/`。
3. FastAPI 代码需要能够在单个进程中既服务 API，又通过 `StaticFiles` 提供构建后的前端资源。

### 实施步骤

#### 1. 前端编译与资源整合
1. 进入项目根目录执行：
   ```bash
   npm install
   npm run build
   ```
   生成的静态文件位于 `dist/`。
2. 在 `backend/` 下创建 `static/` 目录（例如 `backend/static/dist`），将 `dist` 全量复制到该目录。
3. 更新 FastAPI `main.py`（已完成）：
   - 使用 `fastapi.staticfiles.StaticFiles` 在 `/` 提供 `backend/static/dist`，以 `html=True` 兼容 SPA。
   - 注册统一的兜底处理：非 `/api` GET 请求若命中文件 404，则返回 `index.html` 让 React Router 接管。
   - API 统一前缀 `/api/...` 保持不变，并新增 `/api/health` 用于快速检查版本、静态资源与数据目录状态。
   - 运行时会根据环境自动定位静态资源：优先 `_MEIPASS/static/dist`（PyInstaller）、其次 exe 同级或源码目录。
   - 支持 `python3 backend/main.py` / `uvicorn backend.main:app` 直接验证，确保前端已被后端托管。

#### 2. 打包时要关注的配置
- 维护一个 `backend/__init__.py` 或 `backend/app/__init__.py`（可选），方便 PyInstaller 指定入口。
- 在项目根目录保留 `pyproject.toml` 或 `requirements.txt` 说明依赖，便于创建打包环境。
- 若运行时需要可配置项（如端口、API key 默认值），在 `backend/config.yaml` 中提供，并允许通过同目录下的配置覆盖。
- 处理文件路径：
  - 使用 `importlib.resources` 或 `Path(__file__).resolve().parent` 获取静态资源目录。
  - 运行时检测是否在 PyInstaller 环境（`sys._MEIPASS`）以定位资源。

#### 3. 运行时目录与文件写入
- 运行时自动将用户数据写入可写目录，优先级如下：
  1. 环境变量 `EASY_BABELDOC_DATA_DIR`。
  2. Windows：`%APPDATA%\Easy-BabelDOC`（若不可用则尝试 `%LOCALAPPDATA%`）。
  3. 其他平台打包态：exe 同级的 `data/` 目录。
  4. 其他平台开发态：`~/.easy-babeldoc/`。
- 启动时会确保 `uploads/`, `outputs/`, `glossaries/`, `translation_history.json` 所在目录存在，并在日志中打印选定路径。
- 确保打包后的可执行文件具备写权限，并在启动时检测 / 创建所需目录。
- 端口绑定策略：
  - 默认监听 `0.0.0.0:8000`，可通过环境变量或 CLI 参数（`--host`, `--port`）覆盖。
  - 程序会在端口被占用时向上尝试递增端口，最大尝试次数由 `EASY_BABELDOC_PORT_SEARCH_LIMIT` 或 `--port-search-limit` 控制，并在日志中提示最终选择的端口。

#### 4. PyInstaller 打包命令
1. 在干净的虚拟环境中安装依赖并进入 `backend/`：
   ```bash
   pyinstaller main.py ^
     --onefile ^
     --noconfirm ^
     --add-data "static;static" ^
     --hidden-import "babeldoc" ^
     --hidden-import "onnxruntime" ^
     --hidden-import "skimage" ^
     --collect-submodules "babeldoc" ^
     --collect-data "babeldoc"
   ```
   说明：
   - `--add-data`：将静态前端资源打包到 exe 内部。
   - `--collect-*`：BabelDOC 依赖 ONNX、RapidOCR 等，需显式收集数据/子模块。
   - 根据实际依赖补充 `--collect-data`（如 `rapidocr_onnxruntime`, `huggingface_hub` 等）。
2. 打包完成后，PyInstaller 会生成 `dist/main.exe`。可以重命名为 `Easy-BabelDOC.exe` 并与 README、默认配置一起打包发布。

#### 5. 质量验证
- 在干净的 Windows 虚拟机/物理机上测试：
  - 双击 exe 是否能启动，并在浏览器访问 `http://127.0.0.1:8000`。
  - 翻译流程是否完整：上传 PDF → 查看进度 → 下载结果 → 查看历史记录。
  - 断电/重启后，历史记录与输出文件是否仍可访问。
- 检查安全：
  - 确认不会在日志或历史文件里写入 API key 等敏感信息。
  - 默认防止跨站访问（CORS 仅允许本地地址或可配置）。
- 体积与性能：
  - 记录 exe 大小（预估 400–800 MB）。
  - 记录首次启动时间、内存占用。

#### 6. 发布与更新策略
- 打包产物与说明一起压缩发布：
  - `Easy-BabelDOC.exe`
  - `README_RUN_FIRST.txt`（说明默认端口、如何修改配置、常见问题）。
  - 可选：在首次运行时弹出提示（控制台或简单 GUI），介绍使用方式。
- 如需在线更新，可考虑：
  - 提供版本号接口，让应用在启动时检查更新。
  - 使用第三方更新器（例如 WinSparkle）或手动引导用户重新下载。

### 后续扩展
- **macOS / Linux**：需在对应平台使用 PyInstaller 重新打包，可考虑 universal 方案（如 PyOxidizer）。
- **安装程序**：用 NSIS/Inno Setup 将 exe + 数据目录打成安装包（可创建桌面快捷方式、卸载程序）。
- **一键脚本备份**：保留 `start.sh` / `start.bat` 作为开发模式入口，方便贡献者本地调试。
