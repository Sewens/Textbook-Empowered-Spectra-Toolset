# Base Framework 设计说明

本文档用于指导后续页面设计与 React 实现。当前阶段的核心不是完整工具页，而是先固定网站级 `base_framework`：顶部品牌与用户入口、语言切换、工具路由 tab，以及承载子页面的主窗格 `main_frame`。

## 1. 当前交付文件

- 原型入口：`od-prototype/preview/index.html`
- 设计说明：`od-prototype/BASE_FRAMEWORK_DESIGN.md`
- 视觉参考：JupyterLab 风格的数据工作台，强调白/浅灰工作区、细分隔线、高密度信息和克制的蓝色选中态。

## 2. 框架目标

`base_framework` 只解决全站共用结构，不承载复杂业务管理。

必须保留：

1. `banner`：产品名称、简短定位、右侧用户登录/账户入口。
2. `i18n`：中英语言切换，切换后只更新界面文案，不改变路由状态。
3. `tool_tabs`：醒目的页面路由/工具选择 tab。
4. `main_frame`：当前工具页面的唯一显示窗格。
5. `footer`：轻量 schema/API 状态信息，可在后续产品化时替换为系统状态栏。

当前不放入：

- 项目目录树。
- 项目管理子选项卡。
- 管理台式二级导航。
- 搜索当前工具页面。
- 复制接口 / 复制 evidence ID 等开发辅助入口。

这些能力后续应作为独立工具页或工具页内部组件设计，而不是放进基础框架。

## 3. 垂直层级

页面结构必须保持以下顺序：

```text
banner：品牌、产品定位、账户入口、i18n
↓
tool_tabs：功能路由 / 工具选择
↓
main_frame：当前工具页面内容
↓
footer：schema / 当前路由状态
```

不要在 `banner` 和 `tool_tabs` 之间插入管理菜单，也不要在 `main_frame` 外侧放项目目录侧栏。基础框架在当前网站阶段应保持轻量。

## 4. 路由与子页面接入

当前原型中的路由数据集中在 `routes` 配置。后续 React 实现时建议拆成：

```text
BaseFramework
├─ Banner
├─ AccountEntry
├─ LanguageSwitch
├─ ToolTabs
├─ MainFrame
└─ StatusFooter
```

推荐 React 数据结构：

```ts
type ToolRoute = {
  key: string;
  title: { zh: string; en: string };
  subtitle: string;
  endpoint?: string;
  component: React.ComponentType<ToolPageProps>;
  requiredPermission?: string;
};
```

推荐渲染方式：

```tsx
<BaseFramework
  routes={toolRoutes}
  activeRoute={activeRoute}
  locale={locale}
  user={session.user}
  onRouteChange={setActiveRoute}
  onLocaleChange={setLocale}
>
  <ActiveToolPage />
</BaseFramework>
```

`main_frame` 只接收当前路由组件，不直接知道具体业务页内部结构。新增子页面时只需要新增 `ToolRoute` 和对应组件，不修改 `Banner`、`ToolTabs`、`MainFrame` 的结构。

## 5. 当前推荐工具页

现阶段保留以下一级工具入口：

| Route key | 中文名 | 作用 | 数据契约 |
|---|---|---|---|
| `groups` | 功能基团卡片 | 浏览功能基团与振动模板概览 | `FG_*.json`, `/groups` |
| `spectrum` | 谱图查看 | 查看谱图、峰位和 assignment | `/spectra/{spectrum_id}`, `peaks`, `assignments` |
| `figures` | 图解构 | 查看图像区域、资产和解构结果 | `assets`, `figure regions` |
| `evidence` | 证据追踪 | 查看 source claims 与 evidence spans | `/evidence/{evidence_id}` |
| `curation` | 标注流转 | 表达校验、复核、提交状态 | `schema validation`, `quality audit` |

后续如果要增加“项目目录管理”，应作为新的一级工具页或业务页内部模块，不应回到基础框架侧栏。

## 6. 视觉系统规则

基础视觉应持续贴近 JupyterLab 式数据产品，而不是营销页或后台管理台。

- 背景：浅灰工作台 `--bg`，主内容白色 `--surface`。
- 分隔：主要靠 1px border 区分区域，不使用重阴影。
- 圆角：保持小半径，当前为 2px 级别。
- 强调色：蓝色只用于激活 tab、焦点态、主操作和少量选中态。
- 字体：Windows 优先使用 `Segoe UI Variable` / `Aptos`，代码和 schema 用 `Cascadia Mono`。
- 密度：信息密度可以高，但基础框架本身不能拥挤；复杂度留给 `main_frame` 内部页面。

避免：

- 大面积渐变背景。
- 紫色/靛蓝默认 AI 风格主色。
- Emoji 图标。
- 卡片左侧彩色边框堆叠。
- 在产品 UI 中展示“设计说明”“demo controls”“screen count”等设计过程信息。

## 7. 交互规则

基础框架只负责全局级交互：

- tab 点击切换当前工具页。
- 语言切换更新所有框架文案和当前页面文案。
- 登录/账户入口弹窗或跳转。
- footer 跟随当前路由显示轻量状态。

基础框架不负责：

- 当前工具页搜索。
- 数据表过滤。
- 复制接口地址。
- Evidence ID 复制。
- 项目目录展开/折叠。
- 业务表单提交。

这些动作应由具体工具页组件自己实现。

## 8. i18n 规则

- 文案使用稳定 key，不在组件内部硬编码中文或英文长句。
- `locale` 应作为 `BaseFramework` 的上层状态传入。
- 切换语言不能重置当前路由、已选数据行或表单状态。
- 中文必须使用 UTF-8 保存；检查项应包含 `连续问号乱码` 和 `U+FFFD` 乱码扫描。

建议检查命令：

```powershell
rg "[?]{4}" od-prototype/preview/index.html
```

## 9. 状态设计要求

每个后续子页面组件至少要设计并实现以下状态：

- `loading`：数据加载中。
- `empty`：当前筛选或数据集为空。
- `error`：API 或解析失败。
- `forbidden`：后端 RBAC 拒绝，前端只做 UX 提示。
- `readonly`：可读不可编辑。
- `populated`：正常数据态。

RBAC 的安全边界在后端。前端只能隐藏或禁用按钮，不能作为权限判断来源。

## 10. 从原型迁移到 React 的步骤

1. 保留 `BaseFramework` 的垂直结构不变。
2. 将 CSS token 迁移到全局 theme 或 Ant Design token 映射。
3. 将 `routes` 从原型对象拆成 `toolRoutes.ts`。
4. 将 `main_frame` 内容拆为独立页面组件。
5. 每个页面组件只接收自己的 API 数据和状态，不反向修改框架结构。
6. 将示例数据替换为 TanStack Query / API client 返回值。
7. 为每个页面补齐 loading、empty、error、forbidden、readonly、populated 状态。
8. 用 Playwright 或组件测试验证 tab 切换、语言切换、账户入口和路由保持。

## 11. 设计验收清单

提交新页面或修改框架前，至少检查：

- `banner → tool_tabs → main_frame` 层级未被破坏。
- 基础框架没有新增项目目录侧栏或管理台式二级导航。
- 子页面内容只出现在 `main_frame`。
- 中文模式无 `连续问号乱码` 或 `U+FFFD`。
- tab 激活态明显，键盘 focus 可见。
- 页面没有搜索/复制接口等无用全局控件。
- 没有把设计说明、调试面板、接口复制按钮显示给最终用户。
- 新增业务操作由具体子页面组件负责，而不是塞进基础框架。

## 12. 下一步建议

下一阶段优先把 `main_frame` 内部页面拆成单独原型或 React 组件：

1. `FunctionalGroupCardsPage`
2. `SpectrumViewerPage`
3. `FigureDeconstructionPage`
4. `EvidenceTracePage`
5. `CurationFlowPage`

每个页面单独定义数据输入、空态、错误态和权限态。基础框架只提供容器和路由，不承担业务页面复杂度。


