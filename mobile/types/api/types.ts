// Auto-generated common API types
// This file provides convenient type aliases for common API responses

import type { paths } from './schema'

// API Path types for type-safe API calls
export type ApiPaths = paths

// Helper type for extracting response types from paths
export type ApiResponse<T extends keyof paths, M extends keyof paths[T]> = 
  paths[T][M] extends { responses: infer R } 
    ? R extends { 200: { content: { 'application/json': infer D } } }
      ? D
      : R extends { 201: { content: { 'application/json': infer D } } }
        ? D
        : never
    : never

// Helper type for extracting request body types from paths
export type ApiRequestBody<T extends keyof paths, M extends keyof paths[T]> = 
  paths[T][M] extends { requestBody: { content: { 'application/json': infer B } } }
    ? B
    : never
