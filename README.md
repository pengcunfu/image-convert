# 图片格式转换器 (Image Converter)

一个基于 Rust + Tauri + React + TailwindCSS 构建的现代化图片格式转换工具。

## ✨ 特性

- 🚀 **高性能**: 使用 Rust 和并行处理，转换速度快
- 🎨 **现代化界面**: 使用 React + TailwindCSS 构建的美观 UI
- 📦 **批量转换**: 支持同时转换多个图片文件
- 🔄 **多格式支持**: 支持 JPEG, PNG, GIF, BMP, WebP, TIFF, ICO 等格式
- ⚙️ **可调参数**: 支持自定义输出质量
- 🎯 **跨平台**: 支持 Windows, macOS, Linux

## 🎯 支持的格式

### 输入格式
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)
- WebP (.webp)
- TIFF (.tiff, .tif)
- ICO (.ico)

### 输出格式
- JPEG (.jpg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)
- WebP (.webp)
- TIFF (.tiff)
- ICO (.ico)

## 🛠️ 技术栈

- **后端**: Rust
  - `image` - 图片处理库
  - `rayon` - 并行处理
  - `tauri` - 桌面应用框架
  
- **前端**: React + TypeScript
  - `React` - UI 框架
  - `TailwindCSS` - 样式框架
  - `Lucide React` - 图标库
  - `Vite` - 构建工具

## 📦 安装与运行

### 前置要求

1. **Node.js** (v16 或更高版本)
2. **Rust** (最新稳定版)
3. **系统依赖** (根据操作系统):
   - Windows: 需要 Microsoft C++ Build Tools
   - macOS: 需要 Xcode Command Line Tools
   - Linux: 需要 `libwebkit2gtk-4.0-dev`, `build-essential`, `curl`, `wget`, `libssl-dev`, `libgtk-3-dev`, `libayatana-appindicator3-dev`, `librsvg2-dev`

### 安装步骤

1. **克隆或下载项目**
```bash
cd convert-images
```

2. **安装前端依赖**
```bash
npm install
```

3. **开发模式运行**
```bash
npm run tauri dev
```

4. **构建生产版本**
```bash
npm run tauri build
```

构建完成后，可执行文件将位于 `src-tauri/target/release/` 目录中。

## 🎮 使用方法

1. **选择图片文件**: 点击"选择图片文件"按钮，选择一个或多个要转换的图片
2. **选择输出目录**: 点击"选择输出目录"按钮，选择转换后图片的保存位置
3. **设置输出格式**: 从下拉菜单中选择目标格式（JPEG, PNG, GIF 等）
4. **调整质量**: 使用滑块调整输出图片的质量（1-100）
5. **开始转换**: 点击"开始转换"按钮开始转换
6. **查看结果**: 转换完成后会显示统计信息和任何错误

## 📸 截图

应用程序提供了一个现代化的深色主题界面，包含：
- 文件选择区域
- 输出目录选择
- 格式和质量设置
- 实时转换进度
- 详细的结果统计

## 🔧 项目结构

```
convert-images/
├── src/                    # React 前端源码
│   ├── App.tsx            # 主应用组件
│   ├── main.tsx           # 入口文件
│   └── styles.css         # 全局样式
├── src-tauri/             # Tauri 后端源码
│   ├── src/
│   │   ├── main.rs        # Rust 主入口
│   │   └── converter.rs   # 图片转换逻辑
│   ├── Cargo.toml         # Rust 依赖配置
│   └── tauri.conf.json    # Tauri 配置
├── package.json           # Node.js 依赖配置
├── vite.config.ts         # Vite 配置
├── tailwind.config.js     # TailwindCSS 配置
└── README.md              # 项目文档
```

## 🚀 性能优化

- 使用 `rayon` 进行并行处理，充分利用多核 CPU
- 优化的图片编码参数
- 智能的内存管理
- 异步文件操作

## 🐛 故障排除

### Windows 用户
- 如果遇到构建错误，请确保安装了 Microsoft C++ Build Tools
- 某些防病毒软件可能会阻止应用程序，请添加例外

### macOS 用户
- 首次运行可能需要在"系统偏好设置 > 安全性与隐私"中允许应用

### Linux 用户
- 确保安装了所有必需的系统依赖
- 某些发行版可能需要额外的库

## 📝 许可证

本项目仅供学习和个人使用。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

如有问题或建议，请通过 GitHub Issues 联系。

---

使用 ❤️ 和 Rust 构建
