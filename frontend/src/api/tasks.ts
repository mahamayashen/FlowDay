import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from './client'
import type { Task, TaskCreate, TaskUpdate } from '../types/task'

export const TASK_KEYS = {
  byProject: (projectId: string) => ['tasks', projectId] as const,
  detail: (projectId: string, taskId: string) => ['tasks', projectId, taskId] as const,
}

export async function fetchProjectTasks(projectId: string): Promise<Task[]> {
  const res = await apiClient.get(`/projects/${projectId}/tasks`)
  if (!res.ok) throw new Error('Failed to fetch tasks')
  return res.json() as Promise<Task[]>
}

async function fetchTask(projectId: string, taskId: string): Promise<Task> {
  const res = await apiClient.get(`/projects/${projectId}/tasks/${taskId}`)
  if (!res.ok) throw new Error('Failed to fetch task')
  return res.json() as Promise<Task>
}

async function createTask(projectId: string, data: TaskCreate): Promise<Task> {
  const res = await apiClient.post(`/projects/${projectId}/tasks`, data)
  if (!res.ok) throw new Error('Failed to create task')
  return res.json() as Promise<Task>
}

async function updateTask(projectId: string, taskId: string, data: TaskUpdate): Promise<Task> {
  const res = await apiClient.patch(`/projects/${projectId}/tasks/${taskId}`, data)
  if (!res.ok) throw new Error('Failed to update task')
  return res.json() as Promise<Task>
}

async function deleteTask(projectId: string, taskId: string): Promise<void> {
  const res = await apiClient.delete(`/projects/${projectId}/tasks/${taskId}`)
  if (!res.ok) throw new Error('Failed to delete task')
}

export function useProjectTasks(projectId: string) {
  return useQuery({
    queryKey: TASK_KEYS.byProject(projectId),
    queryFn: () => fetchProjectTasks(projectId),
    enabled: Boolean(projectId),
  })
}

export function useTask(projectId: string, taskId: string) {
  return useQuery({
    queryKey: TASK_KEYS.detail(projectId, taskId),
    queryFn: () => fetchTask(projectId, taskId),
    enabled: Boolean(projectId) && Boolean(taskId),
  })
}

export function useCreateTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: string; data: TaskCreate }) =>
      createTask(projectId, data),
    onSuccess: (_result, { projectId }) =>
      queryClient.invalidateQueries({ queryKey: TASK_KEYS.byProject(projectId) }),
  })
}

export function useUpdateTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ projectId, taskId, data }: { projectId: string; taskId: string; data: TaskUpdate }) =>
      updateTask(projectId, taskId, data),
    onSuccess: (_result, { projectId }) =>
      queryClient.invalidateQueries({ queryKey: TASK_KEYS.byProject(projectId) }),
  })
}

export function useDeleteTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ projectId, taskId }: { projectId: string; taskId: string }) =>
      deleteTask(projectId, taskId),
    onSuccess: (_result, { projectId }) =>
      queryClient.invalidateQueries({ queryKey: TASK_KEYS.byProject(projectId) }),
  })
}
