import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from './client'
import type { Project, ProjectCreate, ProjectUpdate } from '../types/project'

export const PROJECTS_KEYS = {
  all: ['projects'] as const,
  detail: (id: string) => ['projects', id] as const,
}

async function fetchProjects(): Promise<Project[]> {
  const res = await apiClient.get('/projects')
  if (!res.ok) throw new Error('Failed to fetch projects')
  return res.json() as Promise<Project[]>
}

async function fetchProject(id: string): Promise<Project> {
  const res = await apiClient.get(`/projects/${id}`)
  if (!res.ok) throw new Error('Failed to fetch project')
  return res.json() as Promise<Project>
}

async function createProject(data: ProjectCreate): Promise<Project> {
  const res = await apiClient.post('/projects', data)
  if (!res.ok) throw new Error('Failed to create project')
  return res.json() as Promise<Project>
}

async function updateProject(id: string, data: ProjectUpdate): Promise<Project> {
  const res = await apiClient.patch(`/projects/${id}`, data)
  if (!res.ok) throw new Error('Failed to update project')
  return res.json() as Promise<Project>
}

async function deleteProject(id: string): Promise<void> {
  const res = await apiClient.delete(`/projects/${id}`)
  if (!res.ok) throw new Error('Failed to delete project')
}

export function useProjects() {
  return useQuery({ queryKey: PROJECTS_KEYS.all, queryFn: fetchProjects })
}

export function useProject(id: string) {
  return useQuery({ queryKey: PROJECTS_KEYS.detail(id), queryFn: () => fetchProject(id) })
}

export function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createProject,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PROJECTS_KEYS.all }),
  })
}

export function useUpdateProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProjectUpdate }) => updateProject(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PROJECTS_KEYS.all }),
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteProject,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PROJECTS_KEYS.all }),
  })
}
