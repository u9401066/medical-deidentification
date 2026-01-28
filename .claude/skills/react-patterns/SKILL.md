```skill
---
name: react-patterns
description: React 進階元件模式：Compound Components, Render Props, HOC, Custom Hooks。Triggers: pattern, 模式, compound, render props, HOC, 元件設計.
---

# React Patterns 進階元件模式技能

## 描述

實現可組合、可重用、可維護的 React 元件設計模式。

## 觸發條件

- 「pattern」「模式」
- 「compound」「compound components」
- 「render props」「HOC」
- 「元件設計」「component design」

## 參照規範

- 子法：`.github/bylaws/frontend-ddd.md`

---

## 模式選擇指南

| 需求 | 推薦模式 |
|------|----------|
| 多個相關元件共享狀態 | Compound Components |
| 邏輯重用 (無 UI) | Custom Hooks |
| UI + 邏輯重用 | Render Props |
| 橫切關注點 (logging, auth) | HOC |
| 控制反轉 | Slots / Children as Function |

---

## 1. Compound Components 複合元件

適用於需要多個子元件協作的 UI，如 Tabs、Accordion、Select。

```typescript
// presentation/components/Accordion/index.tsx
import React, { createContext, useContext, useState, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// 1. 建立 Context
interface AccordionContextType {
  openItems: Set<string>;
  toggle: (id: string) => void;
  allowMultiple: boolean;
}

const AccordionContext = createContext<AccordionContextType | null>(null);

function useAccordion() {
  const context = useContext(AccordionContext);
  if (!context) {
    throw new Error('Accordion components must be used within <Accordion>');
  }
  return context;
}

// 2. 根元件
interface AccordionProps {
  children: ReactNode;
  allowMultiple?: boolean;
  defaultOpen?: string[];
}

export function Accordion({ 
  children, 
  allowMultiple = false,
  defaultOpen = [],
}: AccordionProps) {
  const [openItems, setOpenItems] = useState<Set<string>>(
    new Set(defaultOpen)
  );

  const toggle = (id: string) => {
    setOpenItems((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        if (!allowMultiple) next.clear();
        next.add(id);
      }
      return next;
    });
  };

  return (
    <AccordionContext.Provider value={{ openItems, toggle, allowMultiple }}>
      <div className="divide-y rounded-lg border">{children}</div>
    </AccordionContext.Provider>
  );
}

// 3. Item 元件
interface ItemContextType {
  isOpen: boolean;
  id: string;
}

const ItemContext = createContext<ItemContextType | null>(null);

function useItem() {
  const context = useContext(ItemContext);
  if (!context) {
    throw new Error('Accordion.Item components must be used within <Accordion.Item>');
  }
  return context;
}

interface ItemProps {
  children: ReactNode;
  id: string;
}

Accordion.Item = function AccordionItem({ children, id }: ItemProps) {
  const { openItems } = useAccordion();
  const isOpen = openItems.has(id);

  return (
    <ItemContext.Provider value={{ isOpen, id }}>
      <div className="bg-white">{children}</div>
    </ItemContext.Provider>
  );
};

// 4. Trigger 元件
interface TriggerProps {
  children: ReactNode;
}

Accordion.Trigger = function AccordionTrigger({ children }: TriggerProps) {
  const { toggle } = useAccordion();
  const { id, isOpen } = useItem();

  return (
    <button
      onClick={() => toggle(id)}
      className="flex w-full items-center justify-between px-4 py-3 text-left"
      aria-expanded={isOpen}
    >
      {children}
      <motion.span
        animate={{ rotate: isOpen ? 180 : 0 }}
        transition={{ duration: 0.2 }}
      >
        ▼
      </motion.span>
    </button>
  );
};

// 5. Content 元件
Accordion.Content = function AccordionContent({ children }: { children: ReactNode }) {
  const { isOpen } = useItem();

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="overflow-hidden"
        >
          <div className="px-4 pb-3">{children}</div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
```

### 使用方式

```tsx
<Accordion allowMultiple defaultOpen={['faq-1']}>
  <Accordion.Item id="faq-1">
    <Accordion.Trigger>什麼是 PHI？</Accordion.Trigger>
    <Accordion.Content>
      PHI (Protected Health Information) 是受保護的健康資訊...
    </Accordion.Content>
  </Accordion.Item>
  
  <Accordion.Item id="faq-2">
    <Accordion.Trigger>支援哪些檔案格式？</Accordion.Trigger>
    <Accordion.Content>
      支援 PDF、TXT、DOCX 等格式...
    </Accordion.Content>
  </Accordion.Item>
</Accordion>
```

---

## 2. Render Props 渲染屬性

適用於需要向子元件暴露內部狀態或行為。

```typescript
// presentation/components/DataFetcher.tsx
import { useState, useEffect, ReactNode } from 'react';

interface DataFetcherProps<T> {
  url: string;
  children: (state: {
    data: T | null;
    isLoading: boolean;
    error: Error | null;
    refetch: () => void;
  }) => ReactNode;
}

export function DataFetcher<T>({ url, children }: DataFetcherProps<T>) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error('Fetch failed');
      const json = await response.json();
      setData(json);
    } catch (e) {
      setError(e as Error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [url]);

  return <>{children({ data, isLoading, error, refetch: fetchData })}</>;
}
```

### 使用方式

```tsx
<DataFetcher<Task[]> url="/api/tasks">
  {({ data, isLoading, error, refetch }) => {
    if (isLoading) return <Spinner />;
    if (error) return <ErrorMessage error={error} onRetry={refetch} />;
    return <TaskList tasks={data!} />;
  }}
</DataFetcher>
```

---

## 3. Custom Hooks 自訂 Hooks

適用於可重用的狀態邏輯抽取。

```typescript
// application/hooks/useLocalStorage.ts
import { useState, useEffect, useCallback } from 'react';

export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((val: T) => T)) => void, () => void] {
  // 讀取初始值
  const readValue = useCallback((): T => {
    if (typeof window === 'undefined') return initialValue;
    try {
      const item = window.localStorage.getItem(key);
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch {
      return initialValue;
    }
  }, [key, initialValue]);

  const [storedValue, setStoredValue] = useState<T>(readValue);

  // 設定值
  const setValue = useCallback(
    (value: T | ((val: T) => T)) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
        window.dispatchEvent(new Event('local-storage'));
      } catch (error) {
        console.warn(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, storedValue]
  );

  // 刪除值
  const removeValue = useCallback(() => {
    try {
      window.localStorage.removeItem(key);
      setStoredValue(initialValue);
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  // 監聽其他 tab 的變更
  useEffect(() => {
    const handleStorageChange = () => {
      setStoredValue(readValue());
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('local-storage', handleStorageChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('local-storage', handleStorageChange);
    };
  }, [readValue]);

  return [storedValue, setValue, removeValue];
}
```

### 更多實用 Hooks

```typescript
// application/hooks/useDebounce.ts
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// application/hooks/useToggle.ts
export function useToggle(initial = false): [boolean, () => void, (value: boolean) => void] {
  const [value, setValue] = useState(initial);
  const toggle = useCallback(() => setValue((v) => !v), []);
  return [value, toggle, setValue];
}

// application/hooks/usePrevious.ts
export function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T>();
  useEffect(() => {
    ref.current = value;
  }, [value]);
  return ref.current;
}

// application/hooks/useOnClickOutside.ts
export function useOnClickOutside(
  ref: RefObject<HTMLElement>,
  handler: () => void
) {
  useEffect(() => {
    const listener = (event: MouseEvent | TouchEvent) => {
      if (!ref.current || ref.current.contains(event.target as Node)) {
        return;
      }
      handler();
    };

    document.addEventListener('mousedown', listener);
    document.addEventListener('touchstart', listener);

    return () => {
      document.removeEventListener('mousedown', listener);
      document.removeEventListener('touchstart', listener);
    };
  }, [ref, handler]);
}
```

---

## 4. Higher-Order Components (HOC)

適用於橫切關注點，如認證、錯誤邊界、效能監控。

```typescript
// application/hocs/withAuth.tsx
import { ComponentType, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/infrastructure/store/authStore';

interface WithAuthOptions {
  redirectTo?: string;
  requiredRoles?: string[];
}

export function withAuth<P extends object>(
  WrappedComponent: ComponentType<P>,
  options: WithAuthOptions = {}
) {
  const { redirectTo = '/login', requiredRoles = [] } = options;

  return function AuthenticatedComponent(props: P) {
    const navigate = useNavigate();
    const { isAuthenticated, user, isLoading } = useAuthStore();

    useEffect(() => {
      if (!isLoading && !isAuthenticated) {
        navigate(redirectTo);
      }

      if (requiredRoles.length > 0 && user) {
        const hasRole = requiredRoles.some((role) => user.roles.includes(role));
        if (!hasRole) {
          navigate('/unauthorized');
        }
      }
    }, [isAuthenticated, isLoading, user, navigate]);

    if (isLoading) {
      return <LoadingSpinner />;
    }

    if (!isAuthenticated) {
      return null;
    }

    return <WrappedComponent {...props} />;
  };
}

// 使用方式
const ProtectedDashboard = withAuth(Dashboard, { requiredRoles: ['admin'] });
```

### 錯誤邊界 HOC

```typescript
// application/hocs/withErrorBoundary.tsx
import { Component, ComponentType, ErrorInfo, ReactNode } from 'react';

interface FallbackProps {
  error: Error;
  resetError: () => void;
}

interface Options {
  fallback: ComponentType<FallbackProps>;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

export function withErrorBoundary<P extends object>(
  WrappedComponent: ComponentType<P>,
  { fallback: Fallback, onError }: Options
) {
  return class ErrorBoundary extends Component<P, { error: Error | null }> {
    state = { error: null };

    static getDerivedStateFromError(error: Error) {
      return { error };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
      onError?.(error, errorInfo);
    }

    resetError = () => {
      this.setState({ error: null });
    };

    render(): ReactNode {
      if (this.state.error) {
        return <Fallback error={this.state.error} resetError={this.resetError} />;
      }
      return <WrappedComponent {...this.props} />;
    }
  };
}
```

---

## 5. Slots 插槽模式

適用於需要靈活內容區域的元件。

```typescript
// presentation/components/Card/index.tsx
import { ReactNode, Children, isValidElement } from 'react';

interface CardProps {
  children: ReactNode;
}

function CardHeader({ children }: { children: ReactNode }) {
  return <div className="border-b p-4 font-semibold">{children}</div>;
}

function CardBody({ children }: { children: ReactNode }) {
  return <div className="p-4">{children}</div>;
}

function CardFooter({ children }: { children: ReactNode }) {
  return <div className="border-t bg-gray-50 p-4">{children}</div>;
}

export function Card({ children }: CardProps) {
  // 分離子元件
  let header: ReactNode = null;
  let body: ReactNode = null;
  let footer: ReactNode = null;

  Children.forEach(children, (child) => {
    if (!isValidElement(child)) return;
    
    if (child.type === CardHeader) header = child;
    else if (child.type === CardBody) body = child;
    else if (child.type === CardFooter) footer = child;
  });

  return (
    <div className="overflow-hidden rounded-lg border shadow">
      {header}
      {body}
      {footer}
    </div>
  );
}

Card.Header = CardHeader;
Card.Body = CardBody;
Card.Footer = CardFooter;
```

### 使用方式

```tsx
<Card>
  <Card.Header>任務詳情</Card.Header>
  <Card.Body>
    <p>檔案名稱：report.pdf</p>
    <p>狀態：處理中</p>
  </Card.Body>
  <Card.Footer>
    <Button>取消</Button>
    <Button variant="primary">確認</Button>
  </Card.Footer>
</Card>
```

---

## 測試

```typescript
// tests/unit/components/Accordion.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Accordion } from '@/presentation/components/Accordion';

describe('Accordion', () => {
  it('should toggle content visibility', async () => {
    render(
      <Accordion>
        <Accordion.Item id="1">
          <Accordion.Trigger>Question</Accordion.Trigger>
          <Accordion.Content>Answer</Accordion.Content>
        </Accordion.Item>
      </Accordion>
    );

    expect(screen.queryByText('Answer')).not.toBeInTheDocument();
    
    await userEvent.click(screen.getByText('Question'));
    
    expect(screen.getByText('Answer')).toBeInTheDocument();
  });

  it('should only allow one open item when allowMultiple is false', async () => {
    render(
      <Accordion>
        <Accordion.Item id="1">
          <Accordion.Trigger>Q1</Accordion.Trigger>
          <Accordion.Content>A1</Accordion.Content>
        </Accordion.Item>
        <Accordion.Item id="2">
          <Accordion.Trigger>Q2</Accordion.Trigger>
          <Accordion.Content>A2</Accordion.Content>
        </Accordion.Item>
      </Accordion>
    );

    await userEvent.click(screen.getByText('Q1'));
    expect(screen.getByText('A1')).toBeInTheDocument();

    await userEvent.click(screen.getByText('Q2'));
    expect(screen.queryByText('A1')).not.toBeInTheDocument();
    expect(screen.getByText('A2')).toBeInTheDocument();
  });
});
```

---

## 檔案結構

```text
web/frontend/src/
├── application/
│   ├── hooks/
│   │   ├── useLocalStorage.ts
│   │   ├── useDebounce.ts
│   │   ├── useToggle.ts
│   │   └── useOnClickOutside.ts
│   └── hocs/
│       ├── withAuth.tsx
│       └── withErrorBoundary.tsx
│
└── presentation/
    └── components/
        ├── Accordion/
        │   └── index.tsx
        ├── Card/
        │   └── index.tsx
        └── DataFetcher.tsx
```

---

## 檢查清單

設計進階元件時必須：

- [ ] 選擇最適合需求的模式
- [ ] Context 錯誤使用時拋出明確錯誤
- [ ] 提供完整的 TypeScript 類型
- [ ] 使用 displayName 方便 DevTools 調試
- [ ] 建立完整的使用範例
- [ ] 撰寫涵蓋主要場景的測試

---

## 輸出格式

```text
🧩 Compound Component 建立完成

元件：Accordion
檔案：presentation/components/Accordion/index.tsx

✅ 子元件
  └─ Accordion.Item：項目容器
  └─ Accordion.Trigger：觸發按鈕
  └─ Accordion.Content：內容區域

⚙️ Props
  └─ allowMultiple: boolean (預設 false)
  └─ defaultOpen: string[] (預設 [])

📋 使用範例
  <Accordion allowMultiple>
    <Accordion.Item id="1">...</Accordion.Item>
  </Accordion>
```

```
