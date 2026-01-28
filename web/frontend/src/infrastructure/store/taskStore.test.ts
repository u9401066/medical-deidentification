import { describe, it, expect, beforeEach } from 'vitest';
import { useTaskStore } from './taskStore';

describe('TaskStore', () => {
  beforeEach(() => {
    useTaskStore.getState().reset();
  });

  describe('localTasks', () => {
    it('should have empty initial state', () => {
      const state = useTaskStore.getState();
      expect(state.localTasks).toEqual([]);
      expect(state.selectedTaskId).toBeNull();
      expect(state.filterStatus).toBe('all');
    });

    it('should add local task', () => {
      const { addLocalTask } = useTaskStore.getState();
      
      addLocalTask({
        id: 'task-1',
        filename: 'test.pdf',
        status: 'uploading',
        progress: 0,
      });

      const tasks = useTaskStore.getState().localTasks;
      expect(tasks).toHaveLength(1);
      expect(tasks[0].id).toBe('task-1');
      expect(tasks[0].filename).toBe('test.pdf');
      expect(tasks[0].status).toBe('uploading');
      expect(tasks[0].createdAt).toBeDefined();
    });

    it('should update local task', () => {
      const { addLocalTask, updateLocalTask } = useTaskStore.getState();
      
      addLocalTask({
        id: 'task-1',
        filename: 'test.pdf',
        status: 'uploading',
        progress: 0,
      });

      updateLocalTask('task-1', { status: 'processing', progress: 50 });

      const task = useTaskStore.getState().localTasks[0];
      expect(task.status).toBe('processing');
      expect(task.progress).toBe(50);
    });

    it('should remove local task', () => {
      const { addLocalTask, removeLocalTask } = useTaskStore.getState();
      
      addLocalTask({ id: 'task-1', filename: 'a.pdf', status: 'completed', progress: 100 });
      addLocalTask({ id: 'task-2', filename: 'b.pdf', status: 'queued', progress: 0 });
      
      removeLocalTask('task-1');

      const tasks = useTaskStore.getState().localTasks;
      expect(tasks).toHaveLength(1);
      expect(tasks[0].id).toBe('task-2');
    });
  });

  describe('selection', () => {
    it('should set selected task', () => {
      const { setSelectedTask } = useTaskStore.getState();
      
      setSelectedTask('task-123');
      expect(useTaskStore.getState().selectedTaskId).toBe('task-123');
      
      setSelectedTask(null);
      expect(useTaskStore.getState().selectedTaskId).toBeNull();
    });
  });

  describe('filter', () => {
    it('should set filter status', () => {
      const { setFilterStatus } = useTaskStore.getState();
      
      setFilterStatus('processing');
      expect(useTaskStore.getState().filterStatus).toBe('processing');
      
      setFilterStatus('completed');
      expect(useTaskStore.getState().filterStatus).toBe('completed');
      
      setFilterStatus('all');
      expect(useTaskStore.getState().filterStatus).toBe('all');
    });
  });

  describe('reset', () => {
    it('should reset to initial state', () => {
      const { addLocalTask, setSelectedTask, setFilterStatus, reset } =
        useTaskStore.getState();
      
      addLocalTask({ id: 't1', filename: 'f.pdf', status: 'completed', progress: 100 });
      setSelectedTask('t1');
      setFilterStatus('completed');
      
      reset();
      
      const state = useTaskStore.getState();
      expect(state.localTasks).toEqual([]);
      expect(state.selectedTaskId).toBeNull();
      expect(state.filterStatus).toBe('all');
    });
  });
});
