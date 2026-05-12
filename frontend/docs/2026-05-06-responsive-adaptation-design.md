# Design: ArtTouch管理后台全面响应式适配

## Problem Statement
ArtTouch管理后台在手机端访问时，Layout侧边栏固定220px宽度，占据屏幕2/3，严重挤压主内容区。所有页面均无移动端适配，表格溢出、按钮过小、排版错乱。

## Approach
方案C — 抽屉式侧边栏 + 全局响应式CSS系统 + 各页面移动端微调。

## Architecture / Components

### 1. Layout.vue — 抽屉式侧边栏
- 桌面端(≥768px)：保持现有固定侧边栏
- 移动端(<768px)：侧边栏改为抽屉弹层，顶部汉堡按钮呼出
- 遮罩层点击关闭抽屉
- 用户头像和名称简化显示

### 2. 全局响应式CSS系统 (App.vue 全局样式中增加)
- CSS媒体查询断点: 768px
- 表格在移动端自动横向滚动 (overflow-x: auto)
- 按钮、输入框触屏友好尺寸 (min-height: 44px)
- 卡片边距缩小
- el-dialog 移动端全屏

### 3. 各页面微调
- 表格列min-width保证不溢出
- 搜索/操作栏按钮自适应换行
- 统计卡片grid响应式

## Data Flow
无数据流变化，纯UI/UX改造。

## Testing Strategy
1. `npm run build` 编译无报错
2. 浏览器缩放模拟移动端验证
3. 截图对比前后效果

## Success Criteria
- [ ] 手机端侧边栏不遮挡主内容
- [ ] 所有页面在320px-1920px宽度下可正常操作
- [ ] 按钮点击区域≥44px触屏标准
- [ ] 表格可横向滚动查看完整列
- [ ] 编译无报错

## Scope
- In: Layout.vue, App.vue (全局样式), 所有views/*.vue
- Out: 交互逻辑、API调用、数据流
