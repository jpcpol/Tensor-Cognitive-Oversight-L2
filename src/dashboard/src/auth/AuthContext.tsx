// SPDX-License-Identifier: AGPL-3.0
// Copyright (C) 2026 Juan Pablo Chancay
//
// Authentication context for the CAL experiment platform.
// Security model:
//   - JWT stored in sessionStorage (cleared on tab close; XSS-safer than localStorage)
//   - Automatic logout on 401 responses (via setLogoutCallback in experimentClient)
//   - Role-based access: 'participant' | 'admin'
//   - Participant ID stored alongside token for session association

import React, {
  createContext, useCallback, useContext, useEffect, useMemo, useState,
} from 'react'
import { tokenStore, setLogoutCallback } from '../api/experimentClient'
import type { Role } from '../api/types'

interface AuthState {
  token: string | null
  role: Role | null
  participantId: string | null
  isAuthenticated: boolean
  isAdmin: boolean
}

interface AuthContextValue extends AuthState {
  login: (token: string, role: Role, participantId: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

const ROLE_KEY = 'cal_role'
const PID_KEY  = 'cal_pid'

function readSession(): Omit<AuthState, 'isAuthenticated' | 'isAdmin'> {
  return {
    token:         tokenStore.get(),
    role:          (sessionStorage.getItem(ROLE_KEY) as Role | null),
    participantId: sessionStorage.getItem(PID_KEY),
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<Omit<AuthState, 'isAuthenticated' | 'isAdmin'>>(readSession)

  const logout = useCallback(() => {
    tokenStore.clear()
    sessionStorage.removeItem(ROLE_KEY)
    sessionStorage.removeItem(PID_KEY)
    setState({ token: null, role: null, participantId: null })
  }, [])

  const login = useCallback((token: string, role: Role, participantId: string) => {
    tokenStore.set(token)
    sessionStorage.setItem(ROLE_KEY, role)
    sessionStorage.setItem(PID_KEY, participantId)
    setState({ token, role, participantId })
  }, [])

  useEffect(() => {
    setLogoutCallback(logout)
  }, [logout])

  const value = useMemo<AuthContextValue>(() => ({
    ...state,
    isAuthenticated: !!state.token,
    isAdmin: state.role === 'admin',
    login,
    logout,
  }), [state, login, logout])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
