export interface User {
  id: string
  email: string
  name: string
  settings_json: Record<string, unknown>
  created_at: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}
