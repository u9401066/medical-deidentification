```skill
---
name: react-animation
description: Framer Motion 動畫最佳實踐。Triggers: animation, 動畫, framer, motion, 過場, transition.
---

# React Animation 動畫技能

## 描述

使用 Framer Motion 實現流暢的 React 動畫效果。

## 觸發條件

- 「animation」「動畫」
- 「framer」「motion」
- 「過場」「transition」

## 參照規範

- 子法：`.github/bylaws/frontend-ddd.md`

---

## 為什麼選擇 Framer Motion？

| 特點 | Framer Motion | React Spring | CSS |
|------|---------------|--------------|-----|
| 宣告式語法 | ✅ 最佳 | ✅ 良好 | ❌ |
| 手勢支援 | ✅ 內建 | ❌ 需外掛 | ❌ |
| 佈局動畫 | ✅ 自動 | ❌ | 困難 |
| Exit 動畫 | ✅ AnimatePresence | 複雜 | ❌ |
| Bundle | ~30KB | ~25KB | 0 |

---

## 基本使用

### 簡單動畫

```typescript
// presentation/components/AnimatedCard.tsx
import { motion } from 'framer-motion';

export function AnimatedCard({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      // 初始狀態
      initial={{ opacity: 0, y: 20 }}
      // 動畫目標
      animate={{ opacity: 1, y: 0 }}
      // 過渡設定
      transition={{ duration: 0.3, ease: 'easeOut' }}
      // hover 效果
      whileHover={{ scale: 1.02 }}
      // 點擊效果
      whileTap={{ scale: 0.98 }}
      className="rounded-lg bg-white p-4 shadow"
    >
      {children}
    </motion.div>
  );
}
```

### 進入/離開動畫 (AnimatePresence)

```typescript
import { motion, AnimatePresence } from 'framer-motion';

interface ToastProps {
  toasts: Array<{ id: string; message: string }>;
  onDismiss: (id: string) => void;
}

export function ToastContainer({ toasts, onDismiss }: ToastProps) {
  return (
    <div className="fixed bottom-4 right-4 space-y-2">
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            // 必須：讓 AnimatePresence 追蹤元素
            layout
            initial={{ opacity: 0, x: 100, scale: 0.8 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 100, scale: 0.8 }}
            transition={{ type: 'spring', stiffness: 500, damping: 30 }}
            className="rounded-lg bg-gray-800 px-4 py-2 text-white"
          >
            {toast.message}
            <button onClick={() => onDismiss(toast.id)} className="ml-2">
              ✕
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
```

---

## 進階模式

### Variants (動畫變體)

```typescript
// 定義可重用的動畫變體
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      // 子元素依序動畫
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { type: 'spring', stiffness: 300, damping: 24 },
  },
};

export function AnimatedList({ items }: { items: string[] }) {
  return (
    <motion.ul
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-2"
    >
      {items.map((item, index) => (
        <motion.li
          key={index}
          variants={itemVariants}
          className="rounded bg-gray-100 p-2"
        >
          {item}
        </motion.li>
      ))}
    </motion.ul>
  );
}
```

### 佈局動畫 (Layout Animation)

```typescript
import { motion, LayoutGroup } from 'framer-motion';

interface Tab {
  id: string;
  label: string;
}

export function AnimatedTabs({ tabs, activeTab, onChange }: {
  tabs: Tab[];
  activeTab: string;
  onChange: (id: string) => void;
}) {
  return (
    <LayoutGroup>
      <div className="flex gap-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className="relative px-4 py-2"
          >
            {tab.label}
            {activeTab === tab.id && (
              <motion.div
                layoutId="activeTab"
                className="absolute inset-0 rounded-lg bg-blue-500/20"
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              />
            )}
          </button>
        ))}
      </div>
    </LayoutGroup>
  );
}
```

### 手勢動畫 (Gestures)

```typescript
import { motion, useMotionValue, useTransform } from 'framer-motion';

export function DraggableCard() {
  // 追蹤拖曳位置
  const x = useMotionValue(0);
  // 根據 x 計算旋轉角度
  const rotate = useTransform(x, [-200, 200], [-15, 15]);
  // 根據 x 計算透明度
  const opacity = useTransform(x, [-200, 0, 200], [0.5, 1, 0.5]);

  return (
    <motion.div
      drag="x"
      dragConstraints={{ left: -200, right: 200 }}
      style={{ x, rotate, opacity }}
      whileDrag={{ cursor: 'grabbing' }}
      className="cursor-grab rounded-lg bg-white p-8 shadow-lg"
    >
      向左或向右拖曳
    </motion.div>
  );
}
```

### 進度條動畫

```typescript
import { motion, useSpring } from 'framer-motion';

export function AnimatedProgress({ value }: { value: number }) {
  // 使用 spring 讓數值變化更平滑
  const springValue = useSpring(value, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001,
  });

  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
      <motion.div
        className="h-full bg-blue-500"
        style={{ width: springValue.get() + '%' }}
        initial={{ width: 0 }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
      />
    </div>
  );
}
```

---

## 常用動畫模式

### 頁面過場

```typescript
// presentation/layouts/PageTransition.tsx
import { motion } from 'framer-motion';

const pageVariants = {
  initial: { opacity: 0, x: -20 },
  enter: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 20 },
};

export function PageTransition({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="enter"
      exit="exit"
      transition={{ duration: 0.3 }}
    >
      {children}
    </motion.div>
  );
}
```

### Modal 動畫

```typescript
import { motion, AnimatePresence } from 'framer-motion';

const backdropVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
};

const modalVariants = {
  hidden: { opacity: 0, scale: 0.95, y: 20 },
  visible: { 
    opacity: 1, 
    scale: 1, 
    y: 0,
    transition: { type: 'spring', stiffness: 300, damping: 25 },
  },
  exit: { 
    opacity: 0, 
    scale: 0.95, 
    y: 20,
    transition: { duration: 0.2 },
  },
};

export function AnimatedModal({ isOpen, onClose, children }: {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          variants={backdropVariants}
          initial="hidden"
          animate="visible"
          exit="hidden"
          onClick={onClose}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        >
          <motion.div
            variants={modalVariants}
            onClick={(e) => e.stopPropagation()}
            className="rounded-lg bg-white p-6 shadow-xl"
          >
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

### 載入狀態

```typescript
export function LoadingSpinner() {
  return (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
      className="h-8 w-8 rounded-full border-2 border-gray-300 border-t-blue-500"
    />
  );
}

export function PulsingDots() {
  return (
    <div className="flex gap-1">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          animate={{ scale: [1, 1.2, 1] }}
          transition={{
            repeat: Infinity,
            duration: 0.6,
            delay: i * 0.2,
          }}
          className="h-2 w-2 rounded-full bg-blue-500"
        />
      ))}
    </div>
  );
}
```

---

## 效能優化

```typescript
// 1. 使用 layout prop 時限制範圍
<motion.div layout="position"> {/* 只動畫位置，不動畫大小 */}

// 2. 使用 layoutId 時確保唯一性
<motion.div layoutId={`card-${id}`}>

// 3. 對複雜動畫使用 will-change
<motion.div style={{ willChange: 'transform' }}>

// 4. 使用 useReducedMotion 支援無障礙
import { useReducedMotion } from 'framer-motion';

function AccessibleAnimation() {
  const shouldReduceMotion = useReducedMotion();
  
  return (
    <motion.div
      animate={{ x: 100 }}
      transition={{ duration: shouldReduceMotion ? 0 : 0.5 }}
    />
  );
}
```

---

## 測試

```typescript
// tests/unit/components/AnimatedCard.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AnimatedCard } from '@/presentation/components/AnimatedCard';

describe('AnimatedCard', () => {
  it('should render children', () => {
    render(<AnimatedCard>Test Content</AnimatedCard>);
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  // 動畫測試通常著重於最終狀態，而非動畫過程
  it('should have correct initial styles', () => {
    const { container } = render(<AnimatedCard>Content</AnimatedCard>);
    const card = container.firstChild;
    expect(card).toHaveClass('rounded-lg');
  });
});
```

---

## 檔案結構

```text
web/frontend/src/
└── presentation/
    ├── components/
    │   └── animations/
    │       ├── AnimatedCard.tsx
    │       ├── AnimatedList.tsx
    │       ├── AnimatedProgress.tsx
    │       └── LoadingSpinner.tsx
    │
    └── layouts/
        └── PageTransition.tsx
```

---

## 檢查清單

建立動畫時必須：

- [ ] 使用 AnimatePresence 包裹可能離開的元素
- [ ] 設定合理的 transition 時長 (300-500ms)
- [ ] 考慮 useReducedMotion 無障礙需求
- [ ] 複雜動畫使用 variants 組織
- [ ] 避免過度使用動畫影響效能
- [ ] 測試聚焦於功能而非動畫過程

---

## 輸出格式

```text
✨ 動畫元件建立完成

檔案：presentation/components/animations/AnimatedModal.tsx

✅ 動畫效果
  └─ 進入：fade + scale up + slide
  └─ 離開：fade + scale down
  └─ 背景：fade overlay
  └─ 過渡：spring (stiffness: 300)

🎯 使用方式
  └─ <AnimatedModal isOpen={isOpen} onClose={close}>
  └─ 需要 AnimatePresence 包裝

⚙️ 效能考量
  └─ 使用 stopPropagation 防止事件冒泡
  └─ exit 動畫使用較短 duration
```

```
