import { describe, it, expect, beforeEach } from 'vitest';
import { useUIStore } from './uiStore';

describe('UIStore', () => {
  beforeEach(() => {
    // 重置 store
    useUIStore.getState().reset();
  });

  describe('sidebar', () => {
    it('should have initial sidebar state', () => {
      const state = useUIStore.getState();
      expect(state.sidebarOpen).toBe(true);
      expect(state.sidebarWidth).toBe(280);
    });

    it('should toggle sidebar', () => {
      const { toggleSidebar } = useUIStore.getState();
      
      toggleSidebar();
      expect(useUIStore.getState().sidebarOpen).toBe(false);
      
      toggleSidebar();
      expect(useUIStore.getState().sidebarOpen).toBe(true);
    });

    it('should set sidebar width within bounds', () => {
      const { setSidebarWidth } = useUIStore.getState();
      
      setSidebarWidth(300);
      expect(useUIStore.getState().sidebarWidth).toBe(300);
      
      // 測試最小值限制
      setSidebarWidth(100);
      expect(useUIStore.getState().sidebarWidth).toBe(200);
      
      // 測試最大值限制
      setSidebarWidth(500);
      expect(useUIStore.getState().sidebarWidth).toBe(400);
    });
  });

  describe('theme', () => {
    it('should have default theme as system', () => {
      expect(useUIStore.getState().theme).toBe('system');
    });

    it('should change theme', () => {
      const { setTheme } = useUIStore.getState();
      
      setTheme('dark');
      expect(useUIStore.getState().theme).toBe('dark');
      
      setTheme('light');
      expect(useUIStore.getState().theme).toBe('light');
    });
  });

  describe('notifications', () => {
    it('should add notification', () => {
      const { addNotification } = useUIStore.getState();
      
      addNotification({
        type: 'success',
        title: 'Test',
        message: 'Test message',
      });

      const notifications = useUIStore.getState().notifications;
      expect(notifications).toHaveLength(1);
      expect(notifications[0].title).toBe('Test');
      expect(notifications[0].type).toBe('success');
      expect(notifications[0].id).toBeDefined();
      expect(notifications[0].timestamp).toBeDefined();
    });

    it('should remove notification', () => {
      const { addNotification, removeNotification } = useUIStore.getState();
      
      addNotification({ type: 'info', title: 'Test 1' });
      addNotification({ type: 'info', title: 'Test 2' });

      const notifications = useUIStore.getState().notifications;
      expect(notifications).toHaveLength(2);

      removeNotification(notifications[0].id);
      expect(useUIStore.getState().notifications).toHaveLength(1);
      expect(useUIStore.getState().notifications[0].title).toBe('Test 2');
    });

    it('should clear all notifications', () => {
      const { addNotification, clearNotifications } = useUIStore.getState();
      
      addNotification({ type: 'info', title: 'Test 1' });
      addNotification({ type: 'error', title: 'Test 2' });
      
      clearNotifications();
      expect(useUIStore.getState().notifications).toHaveLength(0);
    });
  });

  describe('reset', () => {
    it('should reset to initial state', () => {
      const { toggleSidebar, setTheme, addNotification, reset } = 
        useUIStore.getState();
      
      toggleSidebar();
      setTheme('dark');
      addNotification({ type: 'info', title: 'Test' });
      
      reset();
      
      const state = useUIStore.getState();
      expect(state.sidebarOpen).toBe(true);
      expect(state.theme).toBe('system');
      expect(state.notifications).toHaveLength(0);
    });
  });
});
